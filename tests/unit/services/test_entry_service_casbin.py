"""Unit tests for Entry Service with Casbin decorators.

This module contains unit tests for the Entry Service with RBAC decorators,
customer auto-creation, and Privilege object evaluation.

Tests cover:
- Customer auto-creation with various user data
- Casbin decorator authorization on Entry Service methods
- Privilege object evaluation
- Customer lookup by email
- Error handling for duplicate emails and constraint violations
- Customer data mapping from user fields

Requirements: 1.1, 1.3, 1.4, 8.1, 8.2, 9.3
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import DatabaseException, NotFoundException
from app.core.rbac import Role
from app.models.configuration import Configuration
from app.models.customer import Customer
from app.models.manufacturing_type import ManufacturingType
from app.models.user import User
from app.schemas.entry import ProfileEntryData
from app.services.entry import AdminAccess, ConfigurationCreator, ConfigurationViewer, EntryService
from app.services.rbac import RBACService


class TestEntryServiceCasbin:
    """Unit tests for Entry Service with Casbin decorators."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()
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
            is_superuser=False,
        )

    @pytest.fixture
    def sample_customer(self):
        """Create sample customer for testing."""
        return Customer(
            id=100,
            email="test@example.com",
            contact_person="Test User",
            customer_type="residential",
            is_active=True,
            notes="Auto-created from user: testuser",
        )

    @pytest.fixture
    def sample_manufacturing_type(self):
        """Create sample manufacturing type for testing."""
        return ManufacturingType(
            id=1,
            name="Test Window",
            base_price=Decimal("200.00"),
            base_weight=Decimal("15.00"),
            is_active=True,
        )

    @pytest.fixture
    def sample_profile_data(self):
        """Create sample profile entry data for testing."""
        return ProfileEntryData(manufacturing_type_id=1, name="Test Configuration", type="window")

    @pytest.mark.asyncio
    async def test_customer_auto_creation_with_full_name(self, mock_db, sample_user):
        """Test customer auto-creation with user having full name."""
        # Setup
        rbac_service = RBACService(mock_db)

        # Mock no existing customer
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock successful customer creation
        created_customer = Customer(
            id=100,
            email=sample_user.email,
            contact_person=sample_user.full_name,
            customer_type="residential",
            is_active=True,
            notes=f"Auto-created from user: {sample_user.username}",
        )

        async def mock_refresh_side_effect(obj):
            if isinstance(obj, Customer):
                obj.id = 100

        mock_db.refresh.side_effect = mock_refresh_side_effect

        # Execute
        customer = await rbac_service.get_or_create_customer_for_user(sample_user)

        # Verify customer creation
        mock_db.add.assert_called_once()
        added_customer = mock_db.add.call_args[0][0]

        assert added_customer.email == sample_user.email
        assert added_customer.contact_person == sample_user.full_name
        assert added_customer.customer_type == "residential"
        assert added_customer.is_active is True
        assert "Auto-created from user:" in added_customer.notes

    @pytest.mark.asyncio
    async def test_customer_auto_creation_with_username_fallback(self, mock_db):
        """Test customer auto-creation when user has no full name."""
        # Setup user without full name
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name=None,  # No full name
            role=Role.CUSTOMER.value,
            is_active=True,
        )

        rbac_service = RBACService(mock_db)

        # Mock no existing customer
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Execute
        await rbac_service.get_or_create_customer_for_user(user)

        # Verify fallback to username
        mock_db.add.assert_called_once()
        added_customer = mock_db.add.call_args[0][0]

        assert added_customer.contact_person == user.username

    @pytest.mark.asyncio
    async def test_customer_lookup_by_email_existing(self, mock_db, sample_user, sample_customer):
        """Test customer lookup when customer already exists."""
        # Setup
        rbac_service = RBACService(mock_db)

        # Mock existing customer found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_customer
        mock_db.execute.return_value = mock_result

        # Execute
        customer = await rbac_service.get_or_create_customer_for_user(sample_user)

        # Verify existing customer returned
        assert customer == sample_customer
        mock_db.add.assert_not_called()  # Should not create new customer

    @pytest.mark.asyncio
    async def test_customer_creation_integrity_error_race_condition(
        self, mock_db, sample_user, sample_customer
    ):
        """Test handling of race condition during customer creation."""
        # Setup
        rbac_service = RBACService(mock_db)

        # Mock no existing customer initially
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.side_effect = [
            None,
            sample_customer,
        ]  # First None, then found
        mock_db.execute.return_value = mock_result

        # Mock IntegrityError on commit (race condition)
        mock_db.commit.side_effect = IntegrityError("duplicate key", None, None)

        # Execute
        customer = await rbac_service.get_or_create_customer_for_user(sample_user)

        # Verify race condition handled gracefully
        assert customer == sample_customer
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_customer_creation_integrity_error_no_recovery(self, mock_db, sample_user):
        """Test handling of IntegrityError when customer still not found after rollback."""
        # Setup
        rbac_service = RBACService(mock_db)

        # Mock no existing customer (both times)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock IntegrityError on commit
        mock_db.commit.side_effect = IntegrityError("some other error", None, None)

        # Execute and verify exception
        with pytest.raises(DatabaseException) as exc_info:
            await rbac_service.get_or_create_customer_for_user(sample_user)

        assert "Failed to create customer record" in str(exc_info.value)
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_profile_configuration_casbin_decorator_authorization(
        self, mock_db, sample_user, sample_customer, sample_manufacturing_type, sample_profile_data
    ):
        """Test Casbin decorator authorization on save_profile_configuration."""
        # Setup
        entry_service = EntryService(mock_db)

        # Mock RBAC service
        mock_rbac_service = AsyncMock()
        mock_rbac_service.get_or_create_customer_for_user.return_value = sample_customer
        entry_service.rbac_service = mock_rbac_service

        # Mock manufacturing type query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_manufacturing_type
        mock_db.execute.return_value = mock_result

        # Mock validation
        entry_service.validate_profile_data = AsyncMock()

        # Mock Casbin decorator to allow access
        with patch("app.core.rbac.require") as mock_require:
            mock_decorator = MagicMock()
            mock_decorator.return_value = lambda func: func  # Pass through
            mock_require.return_value = mock_decorator

            # Execute
            result = await entry_service.save_profile_configuration(
                sample_profile_data, sample_user
            )

            # Verify decorator was applied
            mock_require.assert_called()

    @pytest.mark.asyncio
    async def test_save_profile_configuration_uses_customer_id(
        self, mock_db, sample_user, sample_customer, sample_manufacturing_type, sample_profile_data
    ):
        """Test that save_profile_configuration uses customer.id instead of user.id."""
        # Setup
        entry_service = EntryService(mock_db)

        # Mock RBAC service
        mock_rbac_service = AsyncMock()
        mock_rbac_service.get_or_create_customer_for_user.return_value = sample_customer
        entry_service.rbac_service = mock_rbac_service

        # Mock manufacturing type query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_manufacturing_type
        mock_db.execute.return_value = mock_result

        # Mock validation
        entry_service.validate_profile_data = AsyncMock()

        # Execute
        await entry_service.save_profile_configuration(sample_profile_data, sample_user)

        # Verify configuration uses customer.id, not user.id
        mock_db.add.assert_called()
        added_config = mock_db.add.call_args_list[0][0][0]  # First call, first arg

        assert isinstance(added_config, Configuration)
        assert added_config.customer_id == sample_customer.id
        assert added_config.customer_id != sample_user.id

    @pytest.mark.asyncio
    async def test_generate_preview_data_multiple_decorators(self, mock_db, sample_user):
        """Test generate_preview_data with multiple @require decorators (OR logic)."""
        # Setup
        entry_service = EntryService(mock_db)

        # Mock configuration query
        mock_config = Configuration(
            id=1, customer_id=100, name="Test Config", manufacturing_type_id=1
        )
        mock_config.selections = []

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        # Mock Casbin decorators - simulate OR logic where one passes
        with patch("app.core.rbac.require") as mock_require:
            # First decorator (ConfigurationViewer) fails, second (AdminAccess) passes
            def mock_decorator_factory(requirement):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        # Simulate AdminAccess allowing access for superuser
                        if sample_user.is_superuser or requirement == AdminAccess:
                            return await func(*args, **kwargs)
                        else:
                            raise HTTPException(status_code=403, detail="Access denied")

                    return wrapper

                return decorator

            mock_require.side_effect = mock_decorator_factory

            # Test with superuser (should pass AdminAccess)
            sample_user.is_superuser = True

            # Execute
            result = await entry_service.generate_preview_data(1, sample_user)

            # Verify method executed successfully
            assert result is not None

    @pytest.mark.asyncio
    async def test_privilege_object_evaluation(self):
        """Test Privilege object functionality."""
        # Test ConfigurationCreator privilege
        assert Role.CUSTOMER in ConfigurationCreator.roles
        assert Role.SALESMAN in ConfigurationCreator.roles
        assert Role.PARTNER in ConfigurationCreator.roles
        assert ConfigurationCreator.permission.resource == "configuration"
        assert ConfigurationCreator.permission.action == "create"

        # Test ConfigurationViewer privilege
        assert ConfigurationViewer.resource is not None
        assert ConfigurationViewer.resource.resource_type == "configuration"

        # Test AdminAccess privilege
        assert Role.SUPERADMIN in AdminAccess.roles
        assert AdminAccess.permission.resource == "*"
        assert AdminAccess.permission.action == "*"

    @pytest.mark.asyncio
    async def test_manufacturing_type_not_found_error(
        self, mock_db, sample_user, sample_profile_data
    ):
        """Test error handling when manufacturing type is not found."""
        # Setup
        entry_service = EntryService(mock_db)

        # Mock manufacturing type not found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock validation
        entry_service.validate_profile_data = AsyncMock()

        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await entry_service.save_profile_configuration(sample_profile_data, sample_user)

        assert "Manufacturing type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_customer_data_mapping_from_user_fields(self, mock_db):
        """Test that customer data is correctly mapped from user fields."""
        # Setup user with various field combinations
        user = User(
            id=1,
            email="user@company.com",
            username="companyuser",
            full_name="Company User Name",
            role=Role.CUSTOMER.value,
            is_active=True,
        )

        rbac_service = RBACService(mock_db)

        # Mock no existing customer
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Execute
        await rbac_service.get_or_create_customer_for_user(user)

        # Verify correct field mapping
        mock_db.add.assert_called_once()
        added_customer = mock_db.add.call_args[0][0]

        assert added_customer.email == user.email
        assert (
            added_customer.contact_person == user.full_name
        )  # Should use full_name when available
        assert added_customer.customer_type == "residential"  # Default for entry page users
        assert added_customer.is_active is True
        assert user.username in added_customer.notes
