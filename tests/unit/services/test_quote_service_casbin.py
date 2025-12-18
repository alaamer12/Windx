"""Unit tests for Quote Service with Casbin decorators.

This module contains unit tests for the Quote Service with RBAC decorators,
customer relationships, and RBACQueryFilter automatic filtering.

Tests cover:
- Quote creation with proper customer references
- Casbin decorator authorization on quote operations
- RBACQueryFilter for quote filtering by customer relationships
- Privilege object evaluation

Requirements: 2.1, 2.2, 8.1, 9.1, 9.3
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.exceptions import NotFoundException
from app.core.rbac import RBACQueryFilter, Role
from app.models.configuration import Configuration
from app.models.customer import Customer
from app.models.quote import Quote
from app.models.user import User
from app.services.quote import AdminQuoteAccess, QuoteManagement, QuoteReader, QuoteService


class TestQuoteServiceCasbin:
    """Unit tests for Quote Service with Casbin decorators."""

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
    def sample_admin(self):
        """Create sample admin user for testing."""
        return User(
            id=3,
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
            status="draft",
        )

    @pytest.mark.asyncio
    async def test_generate_quote_uses_customer_id_from_configuration(
        self, mock_db, sample_user, sample_configuration
    ):
        """Test that generate_quote uses customer.id from configuration to maintain relationship consistency."""
        # Setup
        quote_service = QuoteService(mock_db)

        # Mock configuration repository
        quote_service.config_repo.get = AsyncMock(return_value=sample_configuration)

        # Mock quote repository
        quote_service.quote_repo.create = AsyncMock()
        quote_service.quote_repo.get_by_quote_number = AsyncMock(return_value=None)

        # Mock quote number generation
        quote_service._generate_quote_number = AsyncMock(return_value="Q-20250101-001")

        # Execute
        await quote_service.generate_quote(
            configuration_id=1, user=sample_user, tax_rate=Decimal("8.50")
        )

        # Verify quote creation used customer_id from configuration
        quote_service.quote_repo.create.assert_called_once()
        quote_data = quote_service.quote_repo.create.call_args[0][0]

        assert quote_data.customer_id == sample_configuration.customer_id
        assert quote_data.configuration_id == sample_configuration.id

    @pytest.mark.asyncio
    async def test_generate_quote_casbin_decorator_authorization(
        self, mock_db, sample_user, sample_configuration
    ):
        """Test Casbin decorator authorization on generate_quote."""
        # Setup
        quote_service = QuoteService(mock_db)
        quote_service.config_repo.get = AsyncMock(return_value=sample_configuration)
        quote_service.quote_repo.create = AsyncMock()
        quote_service._generate_quote_number = AsyncMock(return_value="Q-20250101-001")

        # Mock Casbin decorator to allow access
        with patch("app.core.rbac.require") as mock_require:
            mock_decorator = MagicMock()
            mock_decorator.return_value = lambda func: func  # Pass through
            mock_require.return_value = mock_decorator

            # Execute
            await quote_service.generate_quote(
                configuration_id=1, user=sample_user, tax_rate=Decimal("8.50")
            )

            # Verify decorator was applied
            mock_require.assert_called()

    @pytest.mark.asyncio
    async def test_list_quotes_rbac_query_filter(self, mock_db, sample_user):
        """Test that list_quotes uses RBACQueryFilter for automatic filtering by customer relationships."""
        # Setup
        quote_service = QuoteService(mock_db)

        # Mock query result
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Mock RBACQueryFilter
        with patch.object(RBACQueryFilter, "filter_quotes") as mock_filter:
            mock_query = select(Quote)
            mock_filter.return_value = mock_query

            # Execute
            await quote_service.list_quotes(sample_user)

            # Verify RBACQueryFilter was called
            mock_filter.assert_called_once()
            call_args = mock_filter.call_args
            assert call_args[0][1] == sample_user  # Second argument should be user

    @pytest.mark.asyncio
    async def test_get_quote_multiple_decorators_or_logic(
        self, mock_db, sample_user, sample_admin, sample_quote
    ):
        """Test get_quote with multiple @require decorators (OR logic)."""
        # Setup
        quote_service = QuoteService(mock_db)
        quote_service.quote_repo.get = AsyncMock(return_value=sample_quote)

        # Mock Casbin decorators to simulate OR logic
        with patch("app.core.rbac.require") as mock_require:

            def mock_decorator_factory(requirement):
                def decorator(func):
                    async def wrapper(*args, **kwargs):
                        user = args[2] if len(args) > 2 else kwargs.get("user")

                        # Simulate different authorization rules
                        if requirement == QuoteReader:
                            # Regular users can read their own quotes
                            if user.role == Role.CUSTOMER.value and sample_quote.customer_id == 100:
                                return await func(*args, **kwargs)
                        elif requirement == AdminQuoteAccess:
                            # Admins can read any quote
                            if user.role == Role.SUPERADMIN.value:
                                return await func(*args, **kwargs)

                        raise HTTPException(status_code=403, detail="Access denied")

                    return wrapper

                return decorator

            mock_require.side_effect = mock_decorator_factory

            # Test 1: Customer can read their own quote
            result = await quote_service.get_quote(1, sample_user)
            assert result == sample_quote

            # Test 2: Admin can read any quote
            result = await quote_service.get_quote(1, sample_admin)
            assert result == sample_quote

    @pytest.mark.asyncio
    async def test_quote_customer_relationship_consistency(
        self, mock_db, sample_user, sample_configuration
    ):
        """Test that quote-customer relationship consistency is maintained."""
        # Setup
        quote_service = QuoteService(mock_db)
        quote_service.config_repo.get = AsyncMock(return_value=sample_configuration)
        quote_service.quote_repo.create = AsyncMock()
        quote_service._generate_quote_number = AsyncMock(return_value="Q-20250101-001")

        # Test with explicit customer_id (should use configuration's customer_id)
        await quote_service.generate_quote(
            configuration_id=1,
            user=sample_user,
            customer_id=999,  # Different from configuration's customer_id
            tax_rate=Decimal("8.50"),
        )

        # Verify quote uses explicit customer_id when provided
        quote_service.quote_repo.create.assert_called_once()
        quote_data = quote_service.quote_repo.create.call_args[0][0]
        assert quote_data.customer_id == 999

        # Reset and test without explicit customer_id
        quote_service.quote_repo.create.reset_mock()

        await quote_service.generate_quote(
            configuration_id=1, user=sample_user, tax_rate=Decimal("8.50")
        )

        # Verify quote uses configuration's customer_id when not explicitly provided
        quote_service.quote_repo.create.assert_called_once()
        quote_data = quote_service.quote_repo.create.call_args[0][0]
        assert quote_data.customer_id == sample_configuration.customer_id

    @pytest.mark.asyncio
    async def test_privilege_objects_evaluation(self):
        """Test Privilege objects functionality for Quote Service."""
        # Test QuoteManagement privilege
        assert Role.SALESMAN in QuoteManagement.roles
        assert Role.PARTNER in QuoteManagement.roles
        assert QuoteManagement.permission.resource == "quote"
        assert QuoteManagement.permission.action == "create"
        assert QuoteManagement.resource.resource_type == "customer"

        # Test QuoteReader privilege
        assert Role.CUSTOMER in QuoteReader.roles
        assert Role.SALESMAN in QuoteReader.roles
        assert Role.PARTNER in QuoteReader.roles
        assert QuoteReader.permission.resource == "quote"
        assert QuoteReader.permission.action == "read"
        assert QuoteReader.resource.resource_type == "quote"

        # Test AdminQuoteAccess privilege
        assert Role.SUPERADMIN in AdminQuoteAccess.roles
        assert AdminQuoteAccess.permission.resource == "*"
        assert AdminQuoteAccess.permission.action == "*"

    @pytest.mark.asyncio
    async def test_rbac_query_filter_customer_filtering(self, mock_db, sample_user):
        """Test RBACQueryFilter for quote filtering by customer access."""
        # Setup
        quote_service = QuoteService(mock_db)

        # Mock accessible customers
        accessible_customers = [100, 200, 300]

        # Mock RBACQueryFilter behavior
        with patch.object(RBACQueryFilter, "filter_quotes") as mock_filter:
            # Simulate filtered query
            original_query = select(Quote)
            filtered_query = original_query.where(Quote.customer_id.in_(accessible_customers))
            mock_filter.return_value = filtered_query

            # Mock query execution
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            # Execute
            await quote_service.list_quotes(sample_user, status="draft")

            # Verify filter was applied
            mock_filter.assert_called_once()

            # Verify query was executed with additional filters
            mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_quote_totals_calculation_with_customer_context(
        self, mock_db, sample_user, sample_configuration
    ):
        """Test quote totals calculation maintains customer context."""
        # Setup
        quote_service = QuoteService(mock_db)
        quote_service.config_repo.get = AsyncMock(return_value=sample_configuration)
        quote_service.quote_repo.create = AsyncMock()
        quote_service._generate_quote_number = AsyncMock(return_value="Q-20250101-001")

        # Execute with specific tax rate and discount
        await quote_service.generate_quote(
            configuration_id=1,
            user=sample_user,
            tax_rate=Decimal("8.50"),
            discount_amount=Decimal("25.00"),
        )

        # Verify totals calculation
        quote_service.quote_repo.create.assert_called_once()
        quote_data = quote_service.quote_repo.create.call_args[0][0]

        # Verify calculations
        expected_subtotal = sample_configuration.total_price
        expected_tax = (expected_subtotal * Decimal("8.50") / Decimal("100")).quantize(
            Decimal("0.01")
        )
        expected_total = expected_subtotal + expected_tax - Decimal("25.00")

        assert quote_data.subtotal == expected_subtotal
        assert quote_data.tax_amount == expected_tax
        assert quote_data.discount_amount == Decimal("25.00")
        assert quote_data.total_amount == expected_total

    @pytest.mark.asyncio
    async def test_configuration_not_found_error_handling(self, mock_db, sample_user):
        """Test error handling when configuration is not found."""
        # Setup
        quote_service = QuoteService(mock_db)
        quote_service.config_repo.get = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await quote_service.generate_quote(configuration_id=999, user=sample_user)

        assert "Configuration" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_quote_not_found_error_handling(self, mock_db, sample_user):
        """Test error handling when quote is not found."""
        # Setup
        quote_service = QuoteService(mock_db)
        quote_service.quote_repo.get = AsyncMock(return_value=None)

        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await quote_service.get_quote(999, sample_user)

        assert "Quote" in str(exc_info.value)
