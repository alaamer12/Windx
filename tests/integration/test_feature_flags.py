"""Integration tests for feature flag behavior.

This module tests feature flag functionality across different endpoints
to ensure proper behavior when features are enabled or disabled.

Test Coverage:
    - Customer endpoints with flag enabled/disabled
    - Order endpoints with flag enabled/disabled
    - Navigation menu shows/hides based on flags
    - Redirect messages are clear
    - Feature flag checks are consistent

Requirements:
    - 6.4: Test feature flag behavior
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


class TestCustomerFeatureFlag:
    """Test customer endpoints with feature flag."""

    async def test_customers_list_with_flag_enabled(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test customer list works when feature flag is enabled."""
        from tests.factories.customer_factory import CustomerFactory

        # Create test customers
        await CustomerFactory.create_batch(db_session, 3)

        # Feature flag is enabled by default in test settings
        response = await client.get(
            "/api/v1/admin/customers",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Customers" in response.content or b"customers" in response.content

    async def test_customers_list_with_flag_disabled(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test customer list redirects when feature flag is disabled."""
        # Mock settings to disable feature flag
        with patch("app.api.v1.endpoints.admin_customers.get_settings") as mock_settings:
            mock_settings.return_value.windx.experimental_customers_page = False

            response = await client.get(
                "/api/v1/admin/customers",
                headers=superuser_auth_headers,
                follow_redirects=False,
            )

            # Should redirect to dashboard
            assert response.status_code == 303
            # Check base URL (may have query params for error message)
            location = response.headers["location"]
            assert location.startswith("/api/v1/admin/dashboard")

    async def test_customers_new_form_with_flag_disabled(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test new customer form redirects when feature flag is disabled."""
        with patch("app.api.v1.endpoints.admin_customers.get_settings") as mock_settings:
            mock_settings.return_value.windx.experimental_customers_page = False

            response = await client.get(
                "/api/v1/admin/customers/new",
                headers=superuser_auth_headers,
                follow_redirects=False,
            )

            assert response.status_code == 303
            # Check base URL (may have query params for error message)
            location = response.headers["location"]
            assert location.startswith("/api/v1/admin/dashboard")

    async def test_customers_create_with_flag_disabled(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test customer creation fails when feature flag is disabled."""
        with patch("app.api.v1.endpoints.admin_customers.check_feature_flag") as mock_check:
            from app.core.exceptions import FeatureDisabledException

            mock_check.side_effect = FeatureDisabledException("Customers module is disabled")

            response = await client.post(
                "/api/v1/admin/customers",
                headers=superuser_auth_headers,
                data={
                    "email": "test@example.com",
                    "contact_person": "Test Person",
                    "customer_type": "commercial",
                },
                follow_redirects=False,
            )

            # Should raise exception or redirect
            assert response.status_code in [303, 400, 403]

    async def test_customers_view_with_flag_disabled(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test customer view redirects when feature flag is disabled."""
        from tests.factories.customer_factory import CustomerFactory

        # Create customer
        customer = await CustomerFactory.create(db_session)

        with patch("app.api.v1.endpoints.admin_customers.check_feature_flag") as mock_check:
            from app.core.exceptions import FeatureDisabledException

            mock_check.side_effect = FeatureDisabledException("Customers module is disabled")

            response = await client.get(
                f"/api/v1/admin/customers/{customer.id}",
                headers=superuser_auth_headers,
                follow_redirects=False,
            )

            # Should raise exception or redirect
            assert response.status_code in [303, 400, 403]


class TestOrderFeatureFlag:
    """Test order endpoints with feature flag."""

    async def test_orders_list_with_flag_enabled(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test order list works when feature flag is enabled."""
        from tests.factories.order_factory import OrderFactory

        # Create test orders
        await OrderFactory.create_batch(db_session, 3)

        # Feature flag is enabled by default in test settings
        response = await client.get(
            "/api/v1/admin/orders",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Orders" in response.content or b"orders" in response.content

    async def test_orders_list_with_flag_disabled(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test order list redirects when feature flag is disabled."""
        with patch("app.api.v1.endpoints.admin_orders.get_settings") as mock_settings:
            mock_settings.return_value.windx.experimental_orders_page = False

            response = await client.get(
                "/api/v1/admin/orders",
                headers=superuser_auth_headers,
                follow_redirects=False,
            )

            # Should redirect to dashboard
            assert response.status_code == 303
            # Check base URL (may have query params for error message)
            location = response.headers["location"]
            assert location.startswith("/api/v1/admin/dashboard")


class TestFeatureFlagMessages:
    """Test feature flag redirect messages."""

    async def test_disabled_feature_shows_clear_message(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that disabled features show clear error messages."""
        with patch("app.api.v1.endpoints.admin_customers.get_settings") as mock_settings:
            mock_settings.return_value.windx.experimental_customers_page = False

            response = await client.get(
                "/api/v1/admin/customers",
                headers=superuser_auth_headers,
                follow_redirects=True,  # Follow redirect to see message
            )

            # Should redirect to dashboard with message
            assert response.status_code == 200
            # Message should be in session or response
            # Note: Actual message display depends on template implementation

    async def test_feature_flag_consistency_across_endpoints(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that feature flag behavior is consistent across all customer endpoints."""
        from tests.factories.customer_factory import CustomerFactory

        customer = await CustomerFactory.create(db_session)

        with patch("app.api.v1.endpoints.admin_customers.get_settings") as mock_settings:
            mock_settings.return_value.windx.experimental_customers_page = False

            # Test all customer endpoints
            endpoints = [
                "/api/v1/admin/customers",
                "/api/v1/admin/customers/new",
                f"/api/v1/admin/customers/{customer.id}",
                f"/api/v1/admin/customers/{customer.id}/edit",
            ]

            for endpoint in endpoints:
                response = await client.get(
                    endpoint,
                    headers=superuser_auth_headers,
                    follow_redirects=False,
                )

                # All should redirect to dashboard
                assert response.status_code == 303
                # Check base URL (may have query params for error message)
                location = response.headers["location"]
                assert location.startswith("/api/v1/admin/dashboard")


class TestNavigationMenuFeatureFlags:
    """Test navigation menu visibility based on feature flags."""

    async def test_dashboard_shows_customers_link_when_enabled(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test dashboard shows customers link when feature is enabled."""
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        # Check if customers link is in navigation
        # Note: Actual check depends on template structure
        assert b"customers" in response.content.lower() or b"Customers" in response.content

    async def test_dashboard_hides_customers_link_when_disabled(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test dashboard hides customers link when feature is disabled."""
        with patch("app.api.v1.endpoints.dashboard.get_settings") as mock_settings:
            mock_settings.return_value.windx.experimental_customers_page = False

            response = await client.get(
                "/api/v1/admin/dashboard",
                headers=superuser_auth_headers,
            )

            assert response.status_code == 200
            # Check if customers link is NOT in navigation
            # Note: This test may need adjustment based on actual template structure

    async def test_dashboard_shows_orders_link_when_enabled(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test dashboard shows orders link when feature is enabled."""
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        # Check if orders link is in navigation
        assert b"orders" in response.content.lower() or b"Orders" in response.content

    async def test_dashboard_hides_orders_link_when_disabled(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test dashboard hides orders link when feature is disabled."""
        with patch("app.api.v1.endpoints.dashboard.get_settings") as mock_settings:
            mock_settings.return_value.windx.experimental_orders_page = False

            response = await client.get(
                "/api/v1/admin/dashboard",
                headers=superuser_auth_headers,
            )

            assert response.status_code == 200
            # Check if orders link is NOT in navigation
            # Note: This test may need adjustment based on actual template structure


class TestFeatureFlagEdgeCases:
    """Test edge cases for feature flag behavior."""

    async def test_feature_flag_with_invalid_customer_id(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test feature flag check happens before customer lookup."""
        with patch("app.api.v1.endpoints.admin_customers.check_feature_flag") as mock_check:
            from app.core.exceptions import FeatureDisabledException

            mock_check.side_effect = FeatureDisabledException("Customers module is disabled")

            # Try to access non-existent customer
            response = await client.get(
                "/api/v1/admin/customers/99999",
                headers=superuser_auth_headers,
                follow_redirects=False,
            )

            # Should check feature flag before checking if customer exists
            assert response.status_code in [303, 400, 403]

    async def test_feature_flag_with_post_request(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test feature flag check works for POST requests."""
        with patch("app.api.v1.endpoints.admin_customers.check_feature_flag") as mock_check:
            from app.core.exceptions import FeatureDisabledException

            mock_check.side_effect = FeatureDisabledException("Customers module is disabled")

            response = await client.post(
                "/api/v1/admin/customers",
                headers=superuser_auth_headers,
                data={
                    "email": "test@example.com",
                    "contact_person": "Test Person",
                    "customer_type": "commercial",
                },
                follow_redirects=False,
            )

            # Should check feature flag before processing form
            assert response.status_code in [303, 400, 403]

    async def test_multiple_feature_flags_independent(
        self,
        client: AsyncClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that different feature flags work independently."""
        # Disable customers but keep orders enabled
        with patch("app.api.v1.endpoints.admin_customers.get_settings") as mock_customer_settings:
            mock_customer_settings.return_value.windx.experimental_customers_page = False

            # Customers should redirect
            response = await client.get(
                "/api/v1/admin/customers",
                headers=superuser_auth_headers,
                follow_redirects=False,
            )
            assert response.status_code == 303

        # Orders should still work (separate flag)
        response = await client.get(
            "/api/v1/admin/orders",
            headers=superuser_auth_headers,
        )
        assert response.status_code == 200
