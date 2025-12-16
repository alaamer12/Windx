"""Unit tests for Configuration Service with Casbin decorators.

This module contains unit tests for the Configuration Service with RBAC decorators,
customer relationships, and RBACQueryFilter automatic filtering.

Tests cover:
- Configuration creation with customer relationships
- Casbin decorator authorization on all methods
- RBACQueryFilter automatic filtering
- Multiple decorator patterns (OR logic)
- Customer context extraction and ownership validation

Requirements: 2.1, 2.2, 2.3, 8.1, 9.1, 9.2
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from sqlalchemy import select

from app.models.user import User
from app.models.customer import Customer
from app.models.configuration import Configuration
from app.models.manufacturing_type import ManufacturingType
from app.services.configuration import ConfigurationService, ConfigurationManagement, ConfigurationOwnership, ConfigurationReader, AdminPrivileges
from app.services.rbac import RBACService
from app.schemas.configuration import ConfigurationCreate, ConfigurationUpdate
from app.core.rbac import Role, RBACQueryFilter
from app.core.exceptions import NotFoundException
from fastapi import HTTPException


class TestConfigurationServiceCasbin:
    """Unit tests for Configuration Service with Casbin decorators."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=Role.CUSTOMER.value,
            is_active=True,
            is_superuser=False
        )

    @pytest.fixture
    def sample_salesman(self):
        """Create sample salesman user for testing."""
        return User(
            id=2,
            email="salesman@company.com",
            username="salesman",
            full_name="Sales Person",
            role=Role.SALESMAN.value,
            is_active=True,
            is_superuser=False
        )

    @pytest.fixture
    def sample_admin(self):
        """Create sample admin user for testing."""
        return User(
            id=3,
            email="admin@company.com",
            username="admin",
            full_name="Admin User",
            role=Role.SUPERADMIN.value,
            is_active=True,
            is_superuser=True
        )

    @pytest.fixture
    def sample_customer(self):
        """Create sample customer for testing."""
        return Customer(
            id=100,
            email="test@example.com",
            contact_person="Test User",
            customer_type="residential",
            is_active=True
        )

    @pytest.fixture
    def sample_manufacturing_type(self):
        """Create sample manufacturing type for testing."""
        return ManufacturingType(
            id=1,
            name="Test Window",
            base_price=Decimal("200.00"),
            base_weight=Decimal("15.00"),
            is_active=True
        )

    @pytest.fixture
    def sample_configuration(self, sample_customer):
        """Create sample configuration for testing."""
        return Configuration(
            id=1,
            manufacturing_type_id=1,
            customer_id=sample_customer.id,
            name="Test Configuration",
            status="draft",
            base_price=Decimal("200.00"),
            total_price=Decimal("250.00"),
            calculated_weight=Decimal("15.00")
        )

    @pytest.mark.asyncio
    async def test_create_configuration_uses_customer_relationship(self, mock_db, sample_user, sample_customer, sample_manufacturing_type):
        """Test that create_configuration uses proper customer relationship."""
        # Setup
        config_service = ConfigurationService(mock_db)
        
        # Mock RBAC service
        mock_rbac_service = AsyncMock()
        mock_rbac_service.get_or_create_customer_for_user.return_value = sample_customer
        config_service.rbac_service = mock_rbac_service
        
        # Mock manufacturing type repository
        config_service.mfg_type_repo.get = AsyncMock(return_value=sample_manufacturing_type)
        
        # Mock configuration creation data
        config_data = ConfigurationCreate(
            manufacturing_type_id=1,
            name="Test Configuration"
        )
        
        # Execute
        await config_service.create_configuration(config_data, sample_user)
        
        # Verify customer relationship used
        mock_rbac_service.get_or_create_customer_for_user.assert_called_once_with(sample_user)
        
        # Verify configuration created with customer.id
        mock_db.add.assert_called_once()
        added_config = mock_db.add.call_args[0][0]
        assert added_config.customer_id == sample_customer.id
        assert added_config.customer_id != sample_user.id

    @pytest.mark.asyncio
    async def test_list_configurations_rbac_query_filter(self, mock_db, sample_user):
        """Test that list_configurations uses RBACQueryFilter for automatic filtering."""
        # Setup
        config_service = ConfigurationService(mock_db)
        
        # Mock query result
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        # Mock RBACQueryFilter
        with patch.object(RBACQueryFilter, 'filter_configurations') as mock_filter:
            mock_query = select(Configuration)
            mock_filter.return_value = mock_query
            
            # Execute
            await config_service.list_configurations(sample_user)
            
            # Verify RBACQueryFilter was called
            mock_filter.assert_called_once()
            call_args = mock_filter.call_args
            assert call_args[0][1] == sample_user  # Second argument should be user

    @pytest.mark.asyncio
    async def test_update_configuration_multiple_decorators_or_logic(self, mock_db, sample_user, sample_salesman, sample_admin, sample_configuration):
        """Test update_configuration with multiple @require decorators (OR logic)."""
        # Setup
        config_service = ConfigurationService(mock_db)
        config_service.config_repo.get = AsyncMock(return_value=sample_configuration)
        
        update_data = ConfigurationUpdate(name="Updated Configuration")
        
        # Mock Casbin decorators to simulate OR logic
        with patch('app.core.rbac.require') as mock_require:
            def mock_decorator_factory(requirement):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        user = args[2] if len(args) > 2 else kwargs.get('user')
                        
                        # Simulate different authorization rules
                        if requirement == ConfigurationManagement:
                            # Salesmen can update configurations for their customers
                            if user.role == Role.SALESMAN.value:
                                return await func(*args, **kwargs)
                        elif requirement == ConfigurationOwnership:
                            # Customers can update their own configurations
                            if user.role == Role.CUSTOMER.value and sample_configuration.customer_id == 100:
                                return await func(*args, **kwargs)
                        elif requirement == AdminPrivileges:
                            # Superadmins can update any configuration
                            if user.role == Role.SUPERADMIN.value:
                                return await func(*args, **kwargs)
                        
                        raise HTTPException(status_code=403, detail="Access denied")
                    return wrapper
                return decorator
            
            mock_require.side_effect = mock_decorator_factory
            
            # Test 1: Customer can update their own configuration
            result = await config_service.update_configuration(1, update_data, sample_user)
            assert result is not None
            
            # Test 2: Salesman can update configuration for their customer
            result = await config_service.update_configuration(1, update_data, sample_salesman)
            assert result is not None
            
            # Test 3: Admin can update any configuration
            result = await config_service.update_configuration(1, update_data, sample_admin)
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_configuration_with_details_casbin_authorization(self, mock_db, sample_user, sample_configuration):
        """Test get_configuration_with_details with Casbin decorator authorization."""
        # Setup
        config_service = ConfigurationService(mock_db)
        
        # Mock configuration query with relationships
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_configuration
        mock_db.execute.return_value = mock_result
        
        # Mock Casbin decorator to allow access
        with patch('app.core.rbac.require') as mock_require:
            mock_decorator = MagicMock()
            mock_decorator.return_value = lambda func: func  # Pass through
            mock_require.return_value = mock_decorator
            
            # Execute
            result = await config_service.get_configuration_with_details(1, sample_user)
            
            # Verify decorator was applied and method executed
            mock_require.assert_called()
            assert result == sample_configuration

    @pytest.mark.asyncio
    async def test_customer_context_extraction_and_ownership_validation(self, mock_db, sample_user, sample_configuration):
        """Test customer context extraction and ownership validation."""
        # Setup
        config_service = ConfigurationService(mock_db)
        
        # Mock RBAC service for ownership validation
        mock_rbac_service = AsyncMock()
        mock_rbac_service.check_resource_ownership.return_value = True
        config_service.rbac_service = mock_rbac_service
        
        # Mock configuration retrieval
        config_service.config_repo.get = AsyncMock(return_value=sample_configuration)
        
        # Mock Casbin decorator that checks ownership
        with patch('app.core.rbac.require') as mock_require:
            def mock_decorator_factory(requirement):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        # Extract configuration_id from function parameters
                        config_id = args[1] if len(args) > 1 else kwargs.get('config_id')
                        user = args[2] if len(args) > 2 else kwargs.get('user')
                        
                        # Simulate ownership validation
                        if requirement == ConfigurationOwnership:
                            has_ownership = await mock_rbac_service.check_resource_ownership(
                                user, "configuration", config_id
                            )
                            if not has_ownership:
                                raise HTTPException(status_code=403, detail="Access denied")
                        
                        return await func(*args, **kwargs)
                    return wrapper
                return decorator
            
            mock_require.side_effect = mock_decorator_factory
            
            # Execute
            update_data = ConfigurationUpdate(name="Updated")
            await config_service.update_configuration(1, update_data, sample_user)
            
            # Verify ownership was checked
            mock_rbac_service.check_resource_ownership.assert_called_with(
                sample_user, "configuration", 1
            )

    @pytest.mark.asyncio
    async def test_delete_configuration_casbin_authorization(self, mock_db, sample_user, sample_configuration):
        """Test delete_configuration with Casbin authorization."""
        # Setup
        config_service = ConfigurationService(mock_db)
        config_service.config_repo.get = AsyncMock(return_value=sample_configuration)
        config_service.config_repo.delete = AsyncMock()
        
        # Mock Casbin decorator to allow access
        with patch('app.core.rbac.require') as mock_require:
            mock_decorator = MagicMock()
            mock_decorator.return_value = lambda func: func  # Pass through
            mock_require.return_value = mock_decorator
            
            # Execute
            await config_service.delete_configuration(1, sample_user)
            
            # Verify deletion was performed
            config_service.config_repo.delete.assert_called_once_with(1)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_privilege_objects_functionality(self):
        """Test Privilege objects functionality for Configuration Service."""
        # Test ConfigurationManagement privilege
        assert Role.SALESMAN in ConfigurationManagement.roles
        assert Role.PARTNER in ConfigurationManagement.roles
        assert ConfigurationManagement.permission.resource == "configuration"
        assert ConfigurationManagement.permission.action == "update"
        assert ConfigurationManagement.resource.resource_type == "customer"
        
        # Test ConfigurationOwnership privilege
        assert Role.CUSTOMER in ConfigurationOwnership.roles
        assert ConfigurationOwnership.permission.resource == "configuration"
        assert ConfigurationOwnership.permission.action == "update"
        assert ConfigurationOwnership.resource.resource_type == "configuration"
        
        # Test ConfigurationReader privilege
        assert Role.CUSTOMER in ConfigurationReader.roles
        assert Role.SALESMAN in ConfigurationReader.roles
        assert Role.PARTNER in ConfigurationReader.roles
        assert ConfigurationReader.permission.action == "read"
        
        # Test AdminPrivileges
        assert Role.SUPERADMIN in AdminPrivileges.roles
        assert AdminPrivileges.permission.resource == "*"
        assert AdminPrivileges.permission.action == "*"

    @pytest.mark.asyncio
    async def test_rbac_query_filter_integration(self, mock_db, sample_user):
        """Test RBACQueryFilter integration with Configuration Service."""
        # Setup
        config_service = ConfigurationService(mock_db)
        
        # Mock accessible customers
        accessible_customers = [100, 200, 300]
        
        # Mock RBACQueryFilter behavior
        with patch.object(RBACQueryFilter, 'filter_configurations') as mock_filter:
            # Simulate filtered query
            original_query = select(Configuration)
            filtered_query = original_query.where(Configuration.customer_id.in_(accessible_customers))
            mock_filter.return_value = filtered_query
            
            # Mock query execution
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result
            
            # Execute
            await config_service.list_configurations(sample_user, manufacturing_type_id=1)
            
            # Verify filter was applied
            mock_filter.assert_called_once()
            
            # Verify query was executed with filters
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_configuration_not_found_error_handling(self, mock_db, sample_user):
        """Test error handling when configuration is not found."""
        # Setup
        config_service = ConfigurationService(mock_db)
        config_service.config_repo.get = AsyncMock(return_value=None)
        
        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await config_service.get_configuration(999, sample_user)
        
        assert "Configuration" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_manufacturing_type_not_found_in_create(self, mock_db, sample_user):
        """Test error handling when manufacturing type is not found during creation."""
        # Setup
        config_service = ConfigurationService(mock_db)
        config_service.mfg_type_repo.get = AsyncMock(return_value=None)
        
        config_data = ConfigurationCreate(
            manufacturing_type_id=999,
            name="Test Configuration"
        )
        
        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await config_service.create_configuration(config_data, sample_user)
        
        assert "ManufacturingType" in str(exc_info.value)