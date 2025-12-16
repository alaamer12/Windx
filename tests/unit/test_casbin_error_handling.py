"""Unit tests for Casbin error handling scenarios.

This module tests error handling in the RBAC system including:
- Casbin authorization failure handling
- Customer creation failure handling  
- Foreign key constraint violation handling
- Casbin policy loading failures
- Privilege object evaluation errors
- Race condition handling in customer creation

Requirements: 8.1, 8.2, 8.3, 8.4
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    CasbinAuthorizationException,
    PolicyEvaluationException,
    CustomerCreationException,
    DatabaseConstraintException,
    PrivilegeEvaluationException
)
from app.core.rbac import Role, Permission, Privilege
from app.models.customer import Customer
from app.models.user import User
from app.services.rbac import RBACService


class TestCasbinAuthorizationFailures:
    """Test Casbin authorization failure handling."""
    
    @pytest.fixture
    def rbac_service(self, mock_db):
        """Create RBAC service with mocked database."""
        with patch('casbin.Enforcer'):
            service = RBACService(mock_db)
            service.enforcer = MagicMock()
            return service
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.role = Role.CUSTOMER.value
        return user
    
    @pytest.mark.asyncio
    async def test_casbin_authorization_exception_creation(self):
        """Test CasbinAuthorizationException creation and logging."""
        with patch('app.core.exceptions.logger') as mock_logger:
            exception = CasbinAuthorizationException(
                user_email="test@example.com",
                resource="configuration",
                action="delete",
                resource_id=123,
                context={"reason": "insufficient_privileges"}
            )
            
            # Verify exception properties
            assert exception.status_code == 403
            assert "test@example.com" in exception.detail
            assert "delete" in exception.detail
            assert "configuration 123" in exception.detail
            
            # Verify audit logging
            mock_logger.warning.assert_called_once()
            log_call = mock_logger.warning.call_args[0][0]
            assert "Authorization denied" in log_call
            assert "test@example.com" in log_call
            assert "configuration" in log_call
            assert "delete" in log_call
    
    @pytest.mark.asyncio
    async def test_permission_check_casbin_failure(self, rbac_service, user):
        """Test permission check when Casbin enforcer fails."""
        # Mock Casbin enforcer to raise exception
        rbac_service.enforcer.enforce.side_effect = Exception("Casbin connection failed")
        
        # Should raise PolicyEvaluationException
        with pytest.raises(PolicyEvaluationException) as exc_info:
            await rbac_service.check_permission(user, "configuration", "read")
        
        assert "Failed to check permission" in str(exc_info.value)
        assert "test@example.com" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_privilege_evaluation_failure(self, rbac_service, user):
        """Test privilege evaluation when underlying checks fail."""
        # Create privilege object
        privilege = Privilege(
            roles=[Role.CUSTOMER],
            permission=Permission("configuration", "read")
        )
        
        # Mock permission check to fail
        rbac_service.check_permission = AsyncMock(side_effect=Exception("Permission check failed"))
        
        # Should raise PrivilegeEvaluationException
        with pytest.raises(PrivilegeEvaluationException) as exc_info:
            await rbac_service.check_privilege(user, privilege)
        
        assert "Failed to evaluate privilege" in str(exc_info.value)
        assert "test@example.com" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_policy_evaluation_exception_logging(self):
        """Test PolicyEvaluationException logging and context."""
        with patch('app.core.exceptions.logger') as mock_logger:
            context = {"policy_file": "rbac_policy.csv", "line": 5}
            
            exception = PolicyEvaluationException(
                "Invalid policy syntax",
                policy_context=context
            )
            
            # Verify exception properties
            assert "Policy evaluation failed" in str(exception)
            assert exception.policy_context == context
            
            # Verify error logging
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args[0][0]
            assert "Policy evaluation error" in log_call
            assert "Invalid policy syntax" in log_call


class TestCustomerCreationFailures:
    """Test customer creation failure handling."""
    
    @pytest.fixture
    def rbac_service(self, mock_db):
        """Create RBAC service with mocked database."""
        with patch('casbin.Enforcer'):
            service = RBACService(mock_db)
            service.enforcer = MagicMock()
            service.commit = AsyncMock()
            service.rollback = AsyncMock()
            service.refresh = AsyncMock()
            return service
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.role = Role.CUSTOMER.value
        return user
    
    @pytest.mark.asyncio
    async def test_customer_creation_missing_email(self, rbac_service):
        """Test customer creation failure when user has no email."""
        user = User()
        user.id = 1
        user.username = "testuser"
        user.email = None  # Missing email
        
        with pytest.raises(CustomerCreationException) as exc_info:
            await rbac_service._create_customer_from_user(user)
        
        assert "user email is required" in str(exc_info.value)
        assert exc_info.value.user_email == "<missing>"
    
    @pytest.mark.asyncio
    async def test_customer_creation_unique_constraint_violation(self, rbac_service, user, mock_db):
        """Test customer creation failure due to unique constraint violation."""
        # Mock database to raise IntegrityError for unique constraint
        mock_db.add.side_effect = IntegrityError(
            "duplicate key value violates unique constraint",
            "UNIQUE constraint failed: customers.email",
            None
        )
        
        # Mock finding existing customer after constraint violation
        rbac_service._find_customer_by_email = AsyncMock(return_value=None)
        
        with pytest.raises(DatabaseConstraintException) as exc_info:
            await rbac_service._create_customer_from_user(user)
        
        assert exc_info.value.constraint_type == "unique"
        assert "already exists" in str(exc_info.value)
        assert exc_info.value.constraint_details["field"] == "email"
        
        # Verify rollback was called
        rbac_service.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customer_creation_foreign_key_violation(self, rbac_service, user, mock_db):
        """Test customer creation failure due to foreign key constraint violation."""
        # Mock database to raise IntegrityError for foreign key constraint
        mock_db.add.side_effect = IntegrityError(
            "foreign key constraint failed",
            "FOREIGN KEY constraint failed",
            None
        )
        
        with pytest.raises(DatabaseConstraintException) as exc_info:
            await rbac_service._create_customer_from_user(user)
        
        assert exc_info.value.constraint_type == "foreign_key"
        assert "Foreign key constraint violation" in str(exc_info.value)
        
        # Verify rollback was called
        rbac_service.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customer_creation_race_condition_recovery(self, rbac_service, user, mock_db):
        """Test customer creation race condition handling."""
        # Mock database to raise IntegrityError
        mock_db.add.side_effect = IntegrityError(
            "duplicate key value violates unique constraint",
            "UNIQUE constraint failed: customers.email",
            None
        )
        
        # Mock finding existing customer after race condition
        existing_customer = Customer()
        existing_customer.id = 123
        existing_customer.email = user.email
        rbac_service._find_customer_by_email = AsyncMock(return_value=existing_customer)
        
        # Should return existing customer instead of raising exception
        result = await rbac_service._create_customer_from_user(user)
        
        assert result == existing_customer
        assert result.id == 123
        
        # Verify rollback was called
        rbac_service.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customer_creation_unexpected_error(self, rbac_service, user, mock_db):
        """Test customer creation failure due to unexpected error."""
        # Mock database to raise unexpected exception
        mock_db.add.side_effect = Exception("Unexpected database error")
        
        # Mock finding no existing customer during recovery
        rbac_service._find_customer_by_email = AsyncMock(return_value=None)
        
        with pytest.raises(CustomerCreationException) as exc_info:
            await rbac_service._create_customer_from_user(user)
        
        assert "Failed to create customer record" in str(exc_info.value)
        assert exc_info.value.user_email == user.email
        assert exc_info.value.original_error is not None
        
        # Verify rollback was called
        rbac_service.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customer_creation_exception_logging(self, user):
        """Test CustomerCreationException logging and context."""
        with patch('app.core.exceptions.logger') as mock_logger:
            user_data = {"email": user.email, "username": user.username}
            original_error = Exception("Database connection failed")
            
            exception = CustomerCreationException(
                "Failed to create customer",
                user_email=user.email,
                user_data=user_data,
                original_error=original_error
            )
            
            # Verify exception properties
            assert exception.user_email == user.email
            assert exception.user_data == user_data
            assert exception.original_error == original_error
            
            # Verify error logging
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args[0][0]
            assert "Customer creation failed" in log_call
            assert user.email in log_call


class TestPolicyLoadingFailures:
    """Test Casbin policy loading failure handling."""
    
    @pytest.mark.asyncio
    async def test_rbac_service_initialization_failure(self, mock_db):
        """Test RBAC service initialization when Casbin fails to load."""
        with patch('casbin.Enforcer', side_effect=Exception("Policy file not found")):
            with pytest.raises(PolicyEvaluationException) as exc_info:
                RBACService(mock_db)
            
            assert "Failed to initialize RBAC system" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_policy_file_corruption_handling(self, mock_db):
        """Test handling of corrupted policy files."""
        with patch('casbin.Enforcer') as mock_enforcer_class:
            # Mock enforcer to raise exception during policy loading
            mock_enforcer = MagicMock()
            mock_enforcer.enforce.side_effect = Exception("Policy syntax error")
            mock_enforcer_class.return_value = mock_enforcer
            
            service = RBACService(mock_db)
            user = User()
            user.email = "test@example.com"
            
            with pytest.raises(PolicyEvaluationException):
                await service.check_permission(user, "configuration", "read")


class TestRaceConditionHandling:
    """Test race condition handling in customer creation."""
    
    @pytest.fixture
    def rbac_service(self, mock_db):
        """Create RBAC service with mocked database."""
        with patch('casbin.Enforcer'):
            service = RBACService(mock_db)
            service.enforcer = MagicMock()
            service.commit = AsyncMock()
            service.rollback = AsyncMock()
            service.refresh = AsyncMock()
            return service
    
    @pytest.fixture
    def user(self):
        """Create test user."""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.role = Role.CUSTOMER.value
        return user
    
    @pytest.mark.asyncio
    async def test_concurrent_customer_creation_success(self, rbac_service, user):
        """Test successful handling of concurrent customer creation."""
        # Mock the scenario where another process creates customer during our attempt
        existing_customer = Customer()
        existing_customer.id = 456
        existing_customer.email = user.email
        
        # First call to _find_customer_by_email returns None (no customer)
        # Second call (during recovery) returns existing customer
        rbac_service._find_customer_by_email = AsyncMock(side_effect=[None, existing_customer])
        
        # Mock get_or_create to simulate the race condition
        rbac_service.db.add = MagicMock()
        rbac_service.commit = AsyncMock(side_effect=IntegrityError(
            "duplicate key", "unique constraint", None
        ))
        
        # Should return the existing customer found during recovery
        result = await rbac_service.get_or_create_customer_for_user(user)
        
        assert result == existing_customer
        assert result.id == 456
    
    @pytest.mark.asyncio
    async def test_race_condition_recovery_failure(self, rbac_service, user, mock_db):
        """Test race condition recovery when customer still not found."""
        # Mock database to raise IntegrityError
        mock_db.add.side_effect = IntegrityError(
            "duplicate key", "unique constraint", None
        )
        
        # Mock finding no customer during recovery (shouldn't happen but test edge case)
        rbac_service._find_customer_by_email = AsyncMock(return_value=None)
        
        with pytest.raises(DatabaseConstraintException):
            await rbac_service._create_customer_from_user(user)
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations_caching(self, rbac_service, user):
        """Test caching behavior during concurrent operations."""
        # Clear cache initially
        rbac_service.clear_cache()
        
        # Mock permission check
        rbac_service.enforcer.enforce.return_value = True
        
        # First call should hit the enforcer
        result1 = await rbac_service.check_permission(user, "configuration", "read")
        assert result1 is True
        assert rbac_service.enforcer.enforce.call_count == 1
        
        # Second call should hit the cache
        result2 = await rbac_service.check_permission(user, "configuration", "read")
        assert result2 is True
        assert rbac_service.enforcer.enforce.call_count == 1  # No additional calls
        
        # Verify cache statistics
        stats = rbac_service.get_cache_stats()
        assert stats["permission_cache_size"] == 1
        assert stats["cache_age_minutes"] >= 0


class TestErrorRecoveryMechanisms:
    """Test error recovery mechanisms in RBAC operations."""
    
    @pytest.fixture
    def rbac_service(self, mock_db):
        """Create RBAC service with mocked database."""
        with patch('casbin.Enforcer'):
            service = RBACService(mock_db)
            service.enforcer = MagicMock()
            return service
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_error(self, rbac_service):
        """Test cache invalidation when errors occur."""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        
        # Populate cache with successful result
        rbac_service._permission_cache["1:configuration:read"] = True
        
        # Clear cache on error
        rbac_service.clear_cache()
        
        # Verify cache is empty
        assert len(rbac_service._permission_cache) == 0
        assert len(rbac_service._customer_cache) == 0
        assert len(rbac_service._privilege_cache) == 0
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_casbin_failure(self, rbac_service, user):
        """Test graceful degradation when Casbin is unavailable."""
        # Mock Casbin to be completely unavailable
        rbac_service.enforcer = None
        
        # Should handle gracefully and raise appropriate exception
        with pytest.raises(AttributeError):
            await rbac_service.check_permission(user, "configuration", "read")
    
    @pytest.mark.asyncio
    async def test_error_context_preservation(self):
        """Test that error context is preserved through exception chain."""
        original_error = IntegrityError("constraint failed", "detail", None)
        
        customer_error = CustomerCreationException(
            "Customer creation failed",
            user_email="test@example.com",
            user_data={"email": "test@example.com"},
            original_error=original_error
        )
        
        # Verify original error is preserved
        assert customer_error.original_error == original_error
        assert customer_error.user_email == "test@example.com"
        assert "Customer creation failed" in str(customer_error)