"""Integration tests for admin authentication endpoints.

Tests the admin authentication flow including login, logout, and
dashboard access with redirect behavior for unauthenticated users.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
class TestAdminLoginPage:
    """Tests for GET /api/v1/admin/login endpoint."""

    async def test_login_page_renders(self, client: AsyncClient):
        """Test that login page renders without authentication."""
        response = await client.get("/api/v1/admin/login")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"login" in response.content.lower()

    async def test_login_page_accessible_without_auth(self, client: AsyncClient):
        """Test that login page is accessible without authentication."""
        response = await client.get("/api/v1/admin/login")

        assert response.status_code == 200
        # Should not redirect
        assert "location" not in response.headers


@pytest.mark.asyncio
class TestAdminLogin:
    """Tests for POST /api/v1/admin/login endpoint."""

    async def test_login_success_superuser(
        self,
        client: AsyncClient,
        test_superuser: User,
    ):
        """Test successful login with superuser credentials."""
        response = await client.post(
            "/api/v1/admin/login",
            data={
                "username": test_superuser.username,
                "password": "TestPassword123!",
            },
            follow_redirects=False,
        )

        # Should redirect to dashboard
        assert response.status_code == 302
        assert "/api/v1/admin/dashboard" in response.headers["location"]

        # Should set authentication cookie
        assert "access_token" in response.cookies

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials returns error."""
        response = await client.post(
            "/api/v1/admin/login",
            data={
                "username": "nonexistent",
                "password": "wrongpassword",
            },
            follow_redirects=False,
        )

        # Should return 401 with error message
        assert response.status_code == 401
        assert b"Invalid username or password" in response.content

    async def test_login_inactive_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test login with inactive user account."""
        from app.core.security import get_password_hash

        # Create inactive user
        inactive_user = User(
            username="inactive_user",
            email="inactive@example.com",
            hashed_password=get_password_hash("TestPassword123!"),
            is_active=False,
            is_superuser=True,
        )
        db_session.add(inactive_user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/admin/login",
            data={
                "username": "inactive_user",
                "password": "TestPassword123!",
            },
            follow_redirects=False,
        )

        # Should return 400 with error message
        assert response.status_code == 400
        assert b"User account is inactive" in response.content

    async def test_login_non_superuser(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Test login with non-superuser account."""
        response = await client.post(
            "/api/v1/admin/login",
            data={
                "username": test_user.username,
                "password": "TestPassword123!",
            },
            follow_redirects=False,
        )

        # Should return 403 with error message
        assert response.status_code == 403
        assert b"Not enough permissions" in response.content


@pytest.mark.asyncio
class TestAdminLogout:
    """Tests for GET /api/v1/admin/logout endpoint."""

    async def test_logout_clears_cookie(self, client: AsyncClient):
        """Test that logout clears authentication cookie."""
        response = await client.get(
            "/api/v1/admin/logout",
            follow_redirects=False,
        )

        # Should redirect to login
        assert response.status_code == 302
        assert "/api/v1/admin/login" in response.headers["location"]

        # Should clear cookie (set to empty with max_age=0)
        assert "access_token" in response.cookies
        # Cookie should be deleted (empty value or expired)

    async def test_logout_accessible_without_auth(self, client: AsyncClient):
        """Test that logout is accessible without authentication."""
        response = await client.get(
            "/api/v1/admin/logout",
            follow_redirects=False,
        )

        # Should still redirect to login
        assert response.status_code == 302


@pytest.mark.asyncio
class TestAdminDashboard:
    """Tests for GET /api/v1/admin/dashboard endpoint."""

    async def test_dashboard_success_with_superuser(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test dashboard renders successfully for authenticated superuser."""
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"dashboard" in response.content.lower()

    async def test_dashboard_redirects_unauthenticated(
        self,
        client: AsyncClient,
    ):
        """Test dashboard redirects unauthenticated users to login."""
        response = await client.get(
            "/api/v1/admin/dashboard",
            follow_redirects=False,
        )

        # Should redirect to login (302, not 401)
        assert response.status_code == 302
        assert "/api/v1/admin/login" in response.headers["location"]

    async def test_dashboard_redirects_non_superuser(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test dashboard redirects non-superuser to login with error."""
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers=auth_headers,
            follow_redirects=False,
        )

        # Should redirect to login with error message (302, not 403)
        assert response.status_code == 302
        location = response.headers["location"]
        assert "/api/v1/admin/login" in location
        assert "error=" in location
        assert "permissions" in location.lower()

    async def test_dashboard_with_invalid_token(
        self,
        client: AsyncClient,
    ):
        """Test dashboard redirects with invalid authentication token."""
        response = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": "Bearer invalid_token_here"},
            follow_redirects=False,
        )

        # Should redirect to login (302, not 401)
        assert response.status_code == 302
        assert "/api/v1/admin/login" in response.headers["location"]

    async def test_dashboard_with_expired_token(
        self,
        client: AsyncClient,
    ):
        """Test dashboard redirects with expired authentication token."""
        # Create an expired token (this would need token creation with past expiry)
        expired_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDk0NTkyMDB9.invalid"

        response = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": expired_token},
            follow_redirects=False,
        )

        # Should redirect to login (302, not 401)
        assert response.status_code == 302
        assert "/api/v1/admin/login" in response.headers["location"]


@pytest.mark.asyncio
class TestAdminAuthFlow:
    """Integration tests for complete admin authentication flow."""

    async def test_complete_login_logout_flow(
        self,
        client: AsyncClient,
        test_superuser: User,
    ):
        """Test complete flow: login -> access dashboard -> logout."""
        # Step 1: Login
        login_response = await client.post(
            "/api/v1/admin/login",
            data={
                "username": test_superuser.username,
                "password": "TestPassword123!",
            },
            follow_redirects=False,
        )

        assert login_response.status_code == 302
        assert "access_token" in login_response.cookies

        # Step 2: Access dashboard with cookie
        cookie_value = login_response.cookies["access_token"]
        dashboard_response = await client.get(
            "/api/v1/admin/dashboard",
            cookies={"access_token": cookie_value},
        )

        assert dashboard_response.status_code == 200

        # Step 3: Logout
        logout_response = await client.get(
            "/api/v1/admin/logout",
            follow_redirects=False,
        )

        assert logout_response.status_code == 302
        assert "/api/v1/admin/login" in logout_response.headers["location"]

    async def test_redirect_preserves_intended_destination(
        self,
        client: AsyncClient,
    ):
        """Test that redirect to login could preserve intended destination."""
        # Try to access dashboard without auth
        response = await client.get(
            "/api/v1/admin/dashboard",
            follow_redirects=False,
        )

        # Should redirect to login
        assert response.status_code == 302
        assert "/api/v1/admin/login" in response.headers["location"]

        # Note: Future enhancement could add ?next=/admin/dashboard
        # to redirect back after login
