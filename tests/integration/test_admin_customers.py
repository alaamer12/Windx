"""Integration tests for admin customers endpoints.

This module tests the admin customer management endpoints including:
- List customers with pagination, search, and filters
- Create customer with validation
- View customer details
- Edit customer form
- Update customer
- Delete customer
- Authorization checks
- Feature flag behavior

Test Coverage:
    - Pagination and filtering
    - Search functionality
    - Form validation
    - Duplicate email handling
    - Authorization (superuser only)
    - Feature flag enabled/disabled
    - Error handling and redirects
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from httpx import AsyncClient

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User

pytestmark = pytest.mark.asyncio


class TestListCustomers:
    """Test customer list endpoint."""

    async def test_list_customers_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test listing customers successfully."""
        from tests.factories.customer_factory import CustomerFactory

        # Create test customers
        await CustomerFactory.create_batch(db_session, 5)

        # Make request
        response = await client.get(
            "/api/v1/admin/customers",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Check that customers are in the response
        assert b"Customers" in response.content

    async def test_list_customers_with_pagination(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test customer list pagination."""
        from tests.factories.customer_factory import CustomerFactory

        # Create 25 customers (more than one page)
        await CustomerFactory.create_batch(db_session, 25)

        # Request first page
        response = await client.get(
            "/api/v1/admin/customers?page=1",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        # Should show page 1 content
        assert b"page=2" in response.content  # Next page link

    async def test_list_customers_with_search(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test customer search functionality."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customers with specific names
        await CustomerFactory.create(
            db_session,
            company_name="Acme Corporation",
            contact_person="John Doe",
        )
        await CustomerFactory.create(
            db_session,
            company_name="Beta Industries",
            contact_person="Jane Smith",
        )

        # Search for "Acme"
        response = await client.get(
            "/api/v1/admin/customers?search=Acme",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert b"Acme Corporation" in response.content
        assert b"Beta Industries" not in response.content

    async def test_list_customers_filter_by_type(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test filtering customers by type."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customers of different types
        await CustomerFactory.create(db_session, customer_type="residential")
        await CustomerFactory.create(db_session, customer_type="commercial")
        await CustomerFactory.create(db_session, customer_type="contractor")

        # Filter by commercial
        response = await client.get(
            "/api/v1/admin/customers?type=commercial",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        # Should only show commercial customers
        assert b"commercial" in response.content.lower()

    async def test_list_customers_filter_by_status(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test filtering customers by active status."""
        from tests.factories.customer_factory import CustomerFactory

        # Create active and inactive customers
        await CustomerFactory.create(db_session, is_active=True, company_name="Active Corp")
        await CustomerFactory.create(db_session, is_active=False, company_name="Inactive Corp")

        # Filter by active
        response = await client.get(
            "/api/v1/admin/customers?status_filter=active",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert b"Active Corp" in response.content
        assert b"Inactive Corp" not in response.content

    async def test_list_customers_unauthorized(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test that non-superuser cannot access customer list."""
        response = await client.get(
            "/api/v1/admin/customers",
            headers=auth_headers,
        )

        # Should return 403 Forbidden
        assert response.status_code == 403

    async def test_list_customers_unauthenticated(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that unauthenticated user cannot access customer list."""
        response = await client.get("/api/v1/admin/customers")

        # Should return 401 Unauthorized
        assert response.status_code == 401

    async def test_list_customers_feature_disabled(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test customer list when feature flag is disabled."""
        # Mock the feature flag to be disabled
        with patch("app.api.v1.endpoints.admin_customers.get_settings") as mock_settings:
            mock_settings.return_value.windx.experimental_customers_page = False

            response = await client.get(
                "/api/v1/admin/customers",
                headers=superuser_auth_headers,
                follow_redirects=False,
            )

            # Should redirect to dashboard
            assert response.status_code == 303
            assert "/api/v1/admin/dashboard" in response.headers["location"]


class TestCreateCustomer:
    """Test customer creation endpoint."""

    async def test_create_customer_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test creating a customer successfully."""
        customer_data = {
            "company_name": "New Company",
            "contact_person": "John Doe",
            "email": "john@newcompany.com",
            "phone": "555-1234",
            "customer_type": "commercial",
        }

        response = await client.post(
            "/api/v1/admin/customers",
            headers=superuser_auth_headers,
            data=customer_data,
            follow_redirects=False,
        )

        # Should redirect to customer list with success message
        assert response.status_code == 303
        assert "/api/v1/admin/customers" in response.headers["location"]
        assert (
            "message=" in response.headers["location"] or "success=" in response.headers["location"]
        )

    async def test_create_customer_duplicate_email(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test creating customer with duplicate email."""
        from tests.factories.customer_factory import CustomerFactory

        # Create existing customer
        existing = await CustomerFactory.create(db_session, email="unique-existing@example.com")

        customer_data = {
            "company_name": "Another Company",
            "contact_person": "Jane Doe",
            "email": "unique-existing@example.com",  # Duplicate
            "customer_type": "residential",
        }

        response = await client.post(
            "/api/v1/admin/customers",
            headers=superuser_auth_headers,
            data=customer_data,
            follow_redirects=False,
        )

        # Should redirect to new customer form with error message
        assert response.status_code == 303
        assert "/api/v1/admin/customers/new" in response.headers["location"]
        # Error message should be in redirect URL as query parameter
        assert "error=" in response.headers["location"].lower()

    async def test_create_customer_invalid_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test creating customer with invalid data."""
        customer_data = {
            # Missing required fields
            "company_name": "",
            "email": "invalid-email",  # Invalid email format
        }

        response = await client.post(
            "/api/v1/admin/customers",
            headers=superuser_auth_headers,
            data=customer_data,
            follow_redirects=False,
        )

        # Should return 422 with validation errors (not redirect)
        assert response.status_code == 422
        assert b"validation" in response.content.lower() or b"error" in response.content.lower()

    async def test_create_customer_unauthorized(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test that non-superuser cannot create customer."""
        customer_data = {
            "company_name": "Test Company",
            "contact_person": "Test User",
            "email": "test@company.com",
            "customer_type": "residential",
        }

        response = await client.post(
            "/api/v1/admin/customers",
            headers=auth_headers,
            data=customer_data,
        )

        # Should return 403 Forbidden
        assert response.status_code == 403


class TestViewCustomer:
    """Test customer detail view endpoint."""

    async def test_view_customer_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test viewing customer details."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customer
        customer = await CustomerFactory.create(
            db_session,
            company_name="View Test Company",
        )

        response = await client.get(
            f"/api/v1/admin/customers/{customer.id}",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert b"View Test Company" in response.content

    async def test_view_customer_not_found(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test viewing non-existent customer."""
        response = await client.get(
            "/api/v1/admin/customers/99999",
            headers=superuser_auth_headers,
            follow_redirects=False,
        )

        # Should redirect with error message
        assert response.status_code == 303
        assert "error" in response.headers["location"].lower()


class TestEditCustomerForm:
    """Test customer edit form endpoint."""

    async def test_edit_customer_form_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test displaying edit form with pre-filled data."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customer
        customer = await CustomerFactory.create(
            db_session,
            company_name="Edit Test Company",
            email="edit@test.com",
        )

        response = await client.get(
            f"/api/v1/admin/customers/{customer.id}/edit",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert b"Edit Test Company" in response.content
        assert b"edit@test.com" in response.content

    async def test_edit_customer_form_not_found(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test edit form for non-existent customer."""
        response = await client.get(
            "/api/v1/admin/customers/99999/edit",
            headers=superuser_auth_headers,
            follow_redirects=False,
        )

        # Should redirect with error message
        assert response.status_code == 303
        assert "error" in response.headers["location"].lower()


class TestUpdateCustomer:
    """Test customer update endpoint."""

    async def test_update_customer_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test updating customer successfully."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customer
        customer = await CustomerFactory.create(
            db_session,
            company_name="Original Name",
        )

        update_data = {
            "company_name": "Updated Name",
            "contact_person": customer.contact_person,
            "email": customer.email,
            "customer_type": customer.customer_type,
        }

        response = await client.post(
            f"/api/v1/admin/customers/{customer.id}/edit",
            headers=superuser_auth_headers,
            data=update_data,
            follow_redirects=False,
        )

        # Should redirect to customer detail with success message
        assert response.status_code == 303
        assert f"/api/v1/admin/customers/{customer.id}" in response.headers["location"]

    async def test_update_customer_invalid_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test updating customer with invalid data."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customer
        customer = await CustomerFactory.create(db_session)

        update_data = {
            "email": "invalid-email",  # Invalid format
        }

        response = await client.post(
            f"/api/v1/admin/customers/{customer.id}/edit",
            headers=superuser_auth_headers,
            data=update_data,
            follow_redirects=False,
        )

        # Should return 422 with validation errors (not redirect)
        assert response.status_code == 422

    async def test_update_customer_not_found(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test updating non-existent customer."""
        update_data = {
            "company_name": "Test",
            "email": "test@example.com",
        }

        response = await client.post(
            "/api/v1/admin/customers/99999/edit",
            headers=superuser_auth_headers,
            data=update_data,
            follow_redirects=False,
        )

        # Should redirect with error
        assert response.status_code == 303
        assert "error" in response.headers["location"].lower()


class TestDeleteCustomer:
    """Test customer deletion endpoint."""

    async def test_delete_customer_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test deleting customer successfully."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customer
        customer = await CustomerFactory.create(db_session)

        response = await client.post(
            f"/api/v1/admin/customers/{customer.id}/delete",
            headers=superuser_auth_headers,
            follow_redirects=False,
        )

        # Should redirect to customer list with success message
        assert response.status_code == 303
        assert "/api/v1/admin/customers" in response.headers["location"]

        # Verify customer is deleted (hard delete - record removed)
        from app.repositories.customer import CustomerRepository

        customer_repo = CustomerRepository(db_session)
        deleted_customer = await customer_repo.get(customer.id)
        assert deleted_customer is None  # Customer should be completely removed

    async def test_delete_customer_not_found(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test deleting non-existent customer."""
        response = await client.post(
            "/api/v1/admin/customers/99999/delete",
            headers=superuser_auth_headers,
            follow_redirects=False,
        )

        # Should redirect with error
        assert response.status_code == 303
        assert "error" in response.headers["location"].lower()

    async def test_delete_customer_unauthorized(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test that non-superuser cannot delete customer."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customer
        customer = await CustomerFactory.create(db_session)

        response = await client.post(
            f"/api/v1/admin/customers/{customer.id}/delete",
            headers=auth_headers,
        )

        # Should return 403 Forbidden
        assert response.status_code == 403


class TestNewCustomerForm:
    """Test new customer form endpoint."""

    async def test_new_customer_form_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test displaying new customer form."""
        response = await client.get(
            "/api/v1/admin/customers/new",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert b"New Customer" in response.content or b"Create Customer" in response.content

    async def test_new_customer_form_unauthorized(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        auth_headers: dict[str, str],
    ):
        """Test that non-superuser cannot access new customer form."""
        response = await client.get(
            "/api/v1/admin/customers/new",
            headers=auth_headers,
        )

        # Should return 403 Forbidden
        assert response.status_code == 403
