"""Integration tests for admin entry endpoints.

This module tests the admin entry page functionality including
authentication, template rendering, and API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manufacturing_type import ManufacturingType
from app.models.user import User


@pytest.fixture
async def simple_manufacturing_type(db_session: AsyncSession) -> ManufacturingType:
    """Create a simple manufacturing type for testing."""
    from decimal import Decimal
    import uuid
    
    # Use a unique name to avoid conflicts
    unique_name = f"Test Window Type {uuid.uuid4().hex[:8]}"
    
    mfg_type = ManufacturingType(
        name=unique_name,
        description="Test window type for admin entry tests",
        base_price=Decimal("200.00"),
        base_weight=Decimal("25.00"),
        is_active=True
    )
    
    db_session.add(mfg_type)
    await db_session.commit()
    await db_session.refresh(mfg_type)
    
    return mfg_type


class TestAdminEntry:
    """Test admin entry page functionality."""

    @pytest.mark.asyncio
    async def test_admin_entry_profile_page_requires_auth(
        self,
        client: AsyncClient,
    ):
        """Test that admin entry profile page requires authentication."""
        response = await client.get("/api/v1/admin/entry/profile")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_entry_profile_page_requires_superuser(
        self,
        client: AsyncClient,
        test_user_with_rbac: User,
    ):
        """Test that admin entry profile page requires superuser privileges."""
        # Login as regular user
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_with_rbac.username,
                "password": "UserPassword123!",  # Use the standard test password
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Try to access admin entry page
        response = await client.get(
            "/api/v1/admin/entry/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_entry_profile_page_success(
        self,
        client: AsyncClient,
        test_superuser_with_rbac: User,
    ):
        """Test that superuser can access admin entry profile page."""
        # Login as superuser
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_superuser_with_rbac.username,
                "password": "AdminPassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Access admin entry page
        response = await client.get(
            "/api/v1/admin/entry/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Profile Data Entry" in response.text

    @pytest.mark.asyncio
    async def test_admin_entry_accessories_page_success(
        self,
        client: AsyncClient,
        test_superuser_with_rbac: User,
    ):
        """Test that superuser can access admin entry accessories page."""
        # Login as superuser
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_superuser_with_rbac.username,
                "password": "AdminPassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Access admin entry accessories page
        response = await client.get(
            "/api/v1/admin/entry/accessories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Accessories Data Entry" in response.text

    @pytest.mark.asyncio
    async def test_admin_entry_glazing_page_success(
        self,
        client: AsyncClient,
        test_superuser_with_rbac: User,
    ):
        """Test that superuser can access admin entry glazing page."""
        # Login as superuser
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_superuser_with_rbac.username,
                "password": "AdminPassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Access admin entry glazing page
        response = await client.get(
            "/api/v1/admin/entry/glazing",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Glazing Data Entry" in response.text

    @pytest.mark.asyncio
    async def test_admin_entry_schema_api_success(
        self,
        client: AsyncClient,
        test_superuser_with_rbac: User,
        simple_manufacturing_type: ManufacturingType,
    ):
        """Test that admin entry schema API works for superuser."""
        # Login as superuser
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_superuser_with_rbac.username,
                "password": "AdminPassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Get schema via admin API
        response = await client.get(
            f"/api/v1/admin/entry/profile/schema/{simple_manufacturing_type.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        schema = response.json()
        assert "manufacturing_type_id" in schema
        assert "sections" in schema

    @pytest.mark.asyncio
    async def test_admin_entry_save_api_success(
        self,
        client: AsyncClient,
        test_superuser_with_rbac: User,
        simple_manufacturing_type: ManufacturingType,
    ):
        """Test that admin entry save API works for superuser."""
        # Login as superuser
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_superuser_with_rbac.username,
                "password": "AdminPassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Save profile via admin API
        profile_data = {
            "manufacturing_type_id": simple_manufacturing_type.id,
            "name": "Admin Test Configuration",
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "Casement",
            "system_series": "Admin800",
        }
        
        response = await client.post(
            "/api/v1/admin/entry/profile/save",
            json=profile_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        configuration = response.json()
        assert configuration["name"] == "Admin Test Configuration"
        assert configuration["manufacturing_type_id"] == simple_manufacturing_type.id

    @pytest.mark.asyncio
    async def test_navigation_links_in_templates(
        self,
        client: AsyncClient,
        test_superuser_with_rbac: User,
    ):
        """Test that navigation links are correct in admin entry templates."""
        # Login as superuser
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_superuser_with_rbac.username,
                "password": "AdminPassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Check profile page has correct navigation
        response = await client.get(
            "/api/v1/admin/entry/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        content = response.text
        assert "/api/v1/admin/entry/profile" in content
        assert "/api/v1/admin/entry/accessories" in content
        assert "/api/v1/admin/entry/glazing" in content
        
        # Check accessories page has correct navigation
        response = await client.get(
            "/api/v1/admin/entry/accessories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        content = response.text
        assert "/api/v1/admin/entry/profile" in content
        assert "/api/v1/admin/entry/accessories" in content
        assert "/api/v1/admin/entry/glazing" in content
        
        # Check glazing page has correct navigation
        response = await client.get(
            "/api/v1/admin/entry/glazing",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        content = response.text
        assert "/api/v1/admin/entry/profile" in content
        assert "/api/v1/admin/entry/accessories" in content
        assert "/api/v1/admin/entry/glazing" in content