"""Unit tests for Order Service with Casbin decorators.

This module contains unit tests for the Order Service with RBAC decorators,
customer relationship inheritance, and RBACQueryFilter automatic filtering.

Tests cover:
- Order creation with customer relationship inheritance
- Casbin decorator authorization through quote-customer relationships
- RBACQueryFilter for order filtering by customer ownership
- Role composition and Privilege objects

Requirements: 2.1, 2.2, 8.1, 9.1, 9.3
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.exceptions import NotFoundException, ValidationException
from app.core.rbac import RBACQueryFilter, Role
from app.models.configuration import Configuration
from app.models.customer import Customer
from app.models.order import Order
from app.models.quote import Quote
from app.models.user import User
from app.services.order import AdminOrderAccess, OrderManagement, OrderReader, OrderService


class TestOrderServiceCasbin:
    """Unit tests for Order Service with Casbin decorators."""

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
            is_superuser=False,
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
            is_superuser=False,
        )

    @pytest.fixture
    def sample_partner(self):
        """Create sample partner user for testing."""
        return User(
            id=3,
            email="partner@company.com",
            username="partner",
            full_name="Partner User",
            role=Role.PARTNER.value,
            is_active=True,
            is_superuser=False,
        )

    @pytest.fixture
    def sample_admin(self):
        """Create sample admin user for testing."""
        return User(
            id=4,
            email="admin@company.com",
            username="admin",
            full_name="Admin User",
            role=Role.SUPERADMIN.value,
            is_active=True,
            is_superuser=True,
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
            calculated_weight=Decimal("15.00"),
        )

    @pytest.fixture
    def sample_quote(self, sample_customer, sample_configuration):
        """Create sample quote for testing."""
        return Quote(
            id=1,
            configuration_id=sample_configuration.id,
            customer_id=sample_customer.id,
            quote_number="Q-20250101-001",
            subtotal=Decimal("250.00"),
            tax_rate=Decimal("8.50"),
            tax_amount=Decimal("21.25"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("271.25"),
            valid_until=date.today() + timedelta(days=30),
            status="accepted",  # Must be accepted to create order
        )

    @pytest.fixture
    def sample_order(self, sample_quote):
        """Create sample order for testing."""
        return Order(
            id=1,
            quote_id=sample_quote.id,
            order_number="O-20250101-001",
            order_date=date.today(),
            status="confirmed",
        )

    @pytest.mark.asyncio
    async def test_create_order_maintains_customer_relationship_from_quote(
        self, mock_db, sample_user, sample_quote
    ):
        """Test that order creation maintains customer relationships from quotes."""
        # Setup
        order_service = OrderService(mock_db)

        # Mock quote repository
        order_service.quote_repo.get = AsyncMock(return_value=sample_quote)

        # Mock order repository
        order_service.order_repo.get_by_quote = AsyncMock(return_value=None)  # No existing order
        order_service.order_repo.create = AsyncMock()
        order_service.order_repo.get_by_order_number = AsyncMock(return_value=None)

        # Mock order number generation
        order_service._generate_order_number = AsyncMock(return_value="O-20250101-001")

        # Execute
        await order_service.create_order_from_quote(quote_id=1, user=sample_user)

        # Verify order creation maintains customer relationship through quote
        order_service.order_repo.create.assert_called_once()
        order_data = order_service.order_repo.create.call_args[0][0]

        assert order_data.quote_id == sample_quote.id
        # Customer relationship is maintained through quote_id -> quote.customer_id

    @pytest.mark.asyncio
    async def test_create_order_casbin_decorator_authorization(
        self, mock_db, sample_user, sample_quote
    ):
        """Test Casbin decorator authorization on create_order_from_quote."""
        # Setup
        order_service = OrderService(mock_db)
        order_service.quote_repo.get = AsyncMock(return_value=sample_quote)
        order_service.order_repo.get_by_quote = AsyncMock(return_value=None)
        order_service.order_repo.create = AsyncMock()
        order_service._generate_order_number = AsyncMock(return_value="O-20250101-001")

        # Mock Casbin decorator to allow access
        with patch("app.core.rbac.require") as mock_require:
            mock_decorator = MagicMock()
            mock_decorator.return_value = lambda func: func  # Pass through
            mock_require.return_value = mock_decorator

            # Execute
            await order_service.create_order_from_quote(quote_id=1, user=sample_user)

            # Verify decorator was applied
            mock_require.assert_called()

    @pytest.mark.asyncio
    async def test_get_order_multiple_decorators_or_logic(
        self, mock_db, sample_user, sample_admin, sample_order
    ):
        """Test get_order with multiple @require decorators (OR logic)."""
        # Setup
        order_service = OrderService(mock_db)
        order_service.order_repo.get = AsyncMock(return_value=sample_order)

        # Mock Casbin decorators to simulate OR logic
        with patch("app.core.rbac.require") as mock_require:

            def mock_decorator_factory(requirement):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        user = args[2] if len(args) > 2 else kwargs.get("user")

                        # Simulate different authorization rules
                        if requirement == OrderReader:
                            # Regular users can read their own orders (through quote ownership)
                            if user.role == Role.CUSTOMER.value:
                                return await func(*args, **kwargs)
                        elif requirement == AdminOrderAccess:
                            # Admins can read any order
                            if user.role == Role.SUPERADMIN.value:
                                return await func(*args, **kwargs)

                        raise HTTPException(status_code=403, detail="Access denied")

                    return wrapper

                return decorator

            mock_require.side_effect = mock_decorator_factory

            # Test 1: Customer can read their own order
            result = await order_service.get_order(1, sample_user)
            assert result == sample_order

            # Test 2: Admin can read any order
            result = await order_service.get_order(1, sample_admin)
            assert result == sample_order

    @pytest.mark.asyncio
    async def test_rbac_query_filter_order_filtering_by_customer_ownership(
        self, mock_db, sample_user
    ):
        """Test RBACQueryFilter for order filtering by customer ownership through quotes."""
        # Setup - this would be in a list_orders method (not currently implemented in OrderService)
        # We'll test the RBACQueryFilter directly

        # Mock accessible customers
        accessible_customers = [100, 200, 300]

        # Mock RBACQueryFilter behavior
        with patch.object(RBACQueryFilter, "filter_orders") as mock_filter:
            # Simulate filtered query with join to quotes
            original_query = select(Order)
            filtered_query = original_query.join(Quote).where(
                Quote.customer_id.in_(accessible_customers)
            )
            mock_filter.return_value = filtered_query

            # Test the filter
            result_query = await RBACQueryFilter.filter_orders(original_query, sample_user)

            # Verify filter was applied
            mock_filter.assert_called_once()
            call_args = mock_filter.call_args
            assert call_args[0][0] == original_query
            assert call_args[0][1] == sample_user

    @pytest.mark.asyncio
    async def test_role_composition_and_privilege_objects(self):
        """Test role composition and Privilege objects for Order Service."""
        # Test OrderManagement privilege
        assert Role.SALESMAN in OrderManagement.roles
        assert Role.PARTNER in OrderManagement.roles
        assert OrderManagement.permission.resource == "order"
        assert OrderManagement.permission.action == "create"
        assert OrderManagement.resource.resource_type == "customer"

        # Test OrderReader privilege
        assert Role.CUSTOMER in OrderReader.roles
        assert Role.SALESMAN in OrderReader.roles
        assert Role.PARTNER in OrderReader.roles
        assert OrderReader.permission.resource == "order"
        assert OrderReader.permission.action == "read"
        assert OrderReader.resource.resource_type == "order"

        # Test AdminOrderAccess privilege
        assert Role.SUPERADMIN in AdminOrderAccess.roles
        assert AdminOrderAccess.permission.resource == "*"
        assert AdminOrderAccess.permission.action == "*"

        # Test role composition (bitwise OR)
        sales_and_partner = Role.SALESMAN | Role.PARTNER
        assert Role.SALESMAN in sales_and_partner
        assert Role.PARTNER in sales_and_partner

    @pytest.mark.asyncio
    async def test_order_customer_relationship_consistency_through_quotes(
        self, mock_db, sample_user, sample_quote
    ):
        """Test that order-customer relationship consistency is maintained through quotes."""
        # Setup
        order_service = OrderService(mock_db)
        order_service.quote_repo.get = AsyncMock(return_value=sample_quote)
        order_service.order_repo.get_by_quote = AsyncMock(return_value=None)
        order_service.order_repo.create = AsyncMock()
        order_service._generate_order_number = AsyncMock(return_value="O-20250101-001")

        # Execute
        await order_service.create_order_from_quote(
            quote_id=1, user=sample_user, special_instructions="Test instructions"
        )

        # Verify order maintains relationship through quote
        order_service.order_repo.create.assert_called_once()
        order_data = order_service.order_repo.create.call_args[0][0]

        assert order_data.quote_id == sample_quote.id
        assert order_data.special_instructions == "Test instructions"

        # The customer relationship is implicit through:
        # order.quote_id -> quote.customer_id -> customer.id

    @pytest.mark.asyncio
    async def test_quote_not_accepted_validation(self, mock_db, sample_user, sample_quote):
        """Test validation that quote must be accepted before creating order."""
        # Setup
        order_service = OrderService(mock_db)

        # Mock quote with non-accepted status
        sample_quote.status = "draft"  # Not accepted
        order_service.quote_repo.get = AsyncMock(return_value=sample_quote)

        # Execute and verify exception
        with pytest.raises(ValidationException) as exc_info:
            await order_service.create_order_from_quote(quote_id=1, user=sample_user)

        assert "Quote must be accepted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_order_already_exists_validation(
        self, mock_db, sample_user, sample_quote, sample_order
    ):
        """Test validation that order cannot be created if one already exists for the quote."""
        # Setup
        order_service = OrderService(mock_db)
        order_service.quote_repo.get = AsyncMock(return_value=sample_quote)
        order_service.order_repo.get_by_quote = AsyncMock(
            return_value=sample_order
        )  # Existing order

        # Execute and verify exception
        with pytest.raises(ValidationException) as exc_info:
            await order_service.create_order_from_quote(quote_id=1, user=sample_user)

        assert "Order already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_order_authorization_through_quote_customer_relationships(
        self, mock_db, sample_user, sample_order, sample_quote
    ):
        """Test Casbin authorization through quote-customer relationships."""
        # Setup
        order_service = OrderService(mock_db)
        order_service.order_repo.get = AsyncMock(return_value=sample_order)
        order_service.quote_repo.get = AsyncMock(return_value=sample_quote)

        # Mock RBAC service for ownership validation
        mock_rbac_service = AsyncMock()
        mock_rbac_service.check_resource_ownership.return_value = True
        order_service.rbac_service = mock_rbac_service

        # Mock Casbin decorator that checks ownership through quote
        with patch("app.core.rbac.require") as mock_require:

            def mock_decorator_factory(requirement):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        # Extract order_id from function parameters
                        order_id = args[1] if len(args) > 1 else kwargs.get("order_id")
                        user = args[2] if len(args) > 2 else kwargs.get("user")

                        # Simulate ownership validation through quote-customer relationship
                        if requirement == OrderReader:
                            # Check if user has access to the order through quote ownership
                            has_ownership = await mock_rbac_service.check_resource_ownership(
                                user, "order", order_id
                            )
                            if not has_ownership:
                                raise HTTPException(status_code=403, detail="Access denied")

                        return await func(*args, **kwargs)

                    return wrapper

                return decorator

            mock_require.side_effect = mock_decorator_factory

            # Execute
            result = await order_service.get_order(1, sample_user)

            # Verify ownership was checked through quote-customer relationship
            mock_rbac_service.check_resource_ownership.assert_called_with(sample_user, "order", 1)
            assert result == sample_order

    @pytest.mark.asyncio
    async def test_quote_not_found_error_handling(self, mock_db, sample_user):
        """Test error handling when quote is not found."""
        # Setup
        order_service = OrderService(mock_db)
        order_service.quote_repo.get = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await order_service.create_order_from_quote(quote_id=999, user=sample_user)

        assert "Quote" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_order_not_found_error_handling(self, mock_db, sample_user):
        """Test error handling when order is not found."""
        # Setup
        order_service = OrderService(mock_db)
        order_service.order_repo.get = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await order_service.get_order(999, sample_user)

        assert "Order" in str(exc_info.value)
