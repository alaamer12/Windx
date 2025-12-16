"""Integration tests for Entry Page frontend functionality.

This module contains integration tests that verify the entry page templates
and frontend functionality work correctly with the backend services.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manufacturing_type import ManufacturingType
from app.models.user import User


class TestEntryPageFrontend:
    """Integration tests for Entry Page frontend."""

    @pytest.mark.asyncio
    async def test_profile_page_renders(
        self,
        client: TestClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
        db_session: AsyncSession,
    ):
        """Test that the profile entry page renders correctly."""
        # Create a manufacturing type for testing
        import uuid
        unique_name = f"Test Window Type {uuid.uuid4().hex[:8]}"
        manufacturing_type = ManufacturingType(
            name=unique_name,
            description="Test window for entry page",
            base_price=200.00,
            base_weight=15.00,
            is_active=True
        )
        db_session.add(manufacturing_type)
        await db_session.commit()
        await db_session.refresh(manufacturing_type)
        
        # Test profile page renders
        response = await client.get(
            f"/api/v1/entry/profile?manufacturing_type_id={manufacturing_type.id}",
            headers=superuser_auth_headers
        )
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check that key elements are present in the HTML
        html_content = response.text
        assert "Profile Data Entry" in html_content
        assert "profileEntryApp" in html_content  # Alpine.js app
        assert "ConditionEvaluator" in html_content  # JavaScript evaluator
        assert "dual-view-container" in html_content  # CSS class
        assert "Input Form" in html_content
        assert "Live Preview" in html_content

    @pytest.mark.asyncio
    async def test_accessories_page_renders(
        self,
        client: TestClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that the accessories scaffold page renders correctly."""
        response = await client.get(
            "/api/v1/entry/accessories",
            headers=superuser_auth_headers
        )
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check scaffold content
        html_content = response.text
        assert "Accessories Data Entry" in html_content
        assert "Under Development" in html_content
        assert "Coming Soon" in html_content
        assert "Implementation Requirements" in html_content
        assert "Hardware Configuration" in html_content

    @pytest.mark.asyncio
    async def test_glazing_page_renders(
        self,
        client: TestClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that the glazing scaffold page renders correctly."""
        response = await client.get(
            "/api/v1/entry/glazing",
            headers=superuser_auth_headers
        )
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check scaffold content
        html_content = response.text
        assert "Glazing Data Entry" in html_content
        assert "Under Development" in html_content
        assert "Coming Soon" in html_content
        assert "Implementation Requirements" in html_content
        assert "Glass Type Selection" in html_content

    @pytest.mark.asyncio
    async def test_navigation_tabs_present(
        self,
        client: TestClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that navigation tabs are present on all entry pages."""
        pages = [
            "/api/v1/entry/profile",
            "/api/v1/entry/accessories", 
            "/api/v1/entry/glazing"
        ]
        
        for page_url in pages:
            response = await client.get(
                page_url,
                headers=superuser_auth_headers
            )
            
            assert response.status_code == 200
            html_content = response.text
            
            # Check navigation tabs are present
            assert "navigation-tabs" in html_content
            assert "Profile" in html_content
            assert "Accessories" in html_content
            assert "Glazing" in html_content
            
            # Check icons are present
            assert "fa-user-cog" in html_content
            assert "fa-puzzle-piece" in html_content
            assert "fa-window-maximize" in html_content

    @pytest.mark.asyncio
    async def test_profile_page_without_manufacturing_type(
        self,
        client: TestClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test profile page renders without manufacturing type parameter."""
        response = await client.get(
            "/api/v1/entry/profile",
            headers=superuser_auth_headers
        )
        
        assert response.status_code == 200
        html_content = response.text
        
        # Should still render but with null manufacturing type
        assert "Profile Data Entry" in html_content
        assert "manufacturing_type_id: null" in html_content or "manufacturing_type_id: None" in html_content

    @pytest.mark.asyncio
    async def test_entry_pages_require_authentication(
        self,
        client: TestClient,
    ):
        """Test that entry pages require authentication."""
        pages = [
            "/api/v1/entry/profile",
            "/api/v1/entry/accessories",
            "/api/v1/entry/glazing"
        ]
        
        for page_url in pages:
            response = await client.get(page_url)
            assert response.status_code == 401  # Unauthorized

    @pytest.mark.asyncio
    async def test_profile_page_css_and_js_structure(
        self,
        client: TestClient,
        test_superuser: User,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that profile page has correct CSS and JavaScript structure."""
        response = await client.get(
            "/api/v1/entry/profile",
            headers=superuser_auth_headers
        )
        
        assert response.status_code == 200
        html_content = response.text
        
        # Check CSS classes are present
        css_classes = [
            "dual-view-container",
            "input-view",
            "preview-view", 
            "form-section",
            "form-field",
            "preview-table",
            "loading-spinner"
        ]
        
        for css_class in css_classes:
            assert css_class in html_content
        
        # Check JavaScript functions are present
        js_functions = [
            "profileEntryApp",
            "ConditionEvaluator",
            "loadSchema",
            "updateField",
            "saveConfiguration",
            "getPreviewValue"
        ]
        
        for js_function in js_functions:
            assert js_function in html_content
        
        # Check Alpine.js directives are present
        alpine_directives = [
            "x-data",
            "x-init",
            "x-show",
            "x-text",
            "x-model",
            "@click",
            "@change"
        ]
        
        for directive in alpine_directives:
            assert directive in html_content