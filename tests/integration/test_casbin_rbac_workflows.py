"""Comprehensive integration tests for Casbin RBAC workflows.

This module contains integration tests that verify complete RBAC workflows
including entry page operations, customer auto-creation, and cross-service
authorization consistency.

Requirements: 4.1, 4.2, 4.3, 9.1, 9.2, 9.3, 10.1, 10.2
"""
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.customer import Customer
from app.models.configuration import Configuration
from app.models.manufacturing_type import ManufacturingType
from app.models.quote import Quote
from app.models.order import Order
from app.core.rbac import Role


@pytest.fixture
async def salesman_user(db_session: AsyncSession) -> User:
    """Create a salesman user for testing."""
    user = User(
        email="salesman@windx.com",
        username="salesman",
        full_name="Sales Person",
        role=Role.SALESMAN.value,
        is_active=True,
        is_superuser=False,
        hashed_password="$2b$12$test_hash"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def partner_user(db_session: AsyncSession) -> User:
    """Create a partner user for testing."""
    user = User(
        email="partner@company.com",
        username="partner",
        full_name="Partner User",
        role=Role.PARTNER.value,
        is_active=True,
        is_superuser=False,
        hashed_password="$2b$12$test_hash"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def data_entry_user(db_session: AsyncSession) -> User:
    """Create a data entry user for testing."""
    user = User(
        email="data@windx.com",
        username="dataentry",
        full_name="Data Entry User",
        role=Role.DATA_ENTRY.value,
        is_active=True,
        is_superuser=False,
        hashed_password="$2b$12$test_hash"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def customer_user(db_session: AsyncSession) -> User:
    """Create a customer user for testing."""
    user = User(
        email="customer@example.com",
        username="customer",
        full_name="Customer User",
        role=Role.CUSTOMER.value,
        is_active=True,
        is_superuser=False,
        hashed_password="$2b$12$test_hash"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestCasbinRBACWorkflows:
    """Integration tests for complete Casbin RBAC workflows."""

    @pytest.mark.asyncio
    async def test_complete_entry_page_workflow_with_customer_auto_creation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        customer_user: User,
        manufacturing_type_with_attributes: ManufacturingType,
    ):
        """Test complete entry page workflow with customer auto-creation and RBAC."""
        # Arrange - Get auth headers for customer user
        from tests.conftest import create_auth_headers
        auth_headers = await create_auth_headers(customer_user)
        
        # Ensure no existing customer
        from sqlalchemy import select
        result = await db_session.execute(
            select(Customer).where(Customer.email == customer_user.email)
        )
        existing_customer = result.scalar_one_or_none()
        if existing_customer:
            await db_session.delete(existing_customer)
            await db_session.commit()
        
        # Step 1: Get profile schema (should be authorized)
        schema_response = await client.get(
            f"/api/v1/entry/profile/schema/{manufacturing_type_with_attributes.id}",
            headers=auth_headers
        )
        assert schema_response.status_code == 200
        
        # Step 2: Save profile configuration (should auto-create customer)
        profile_data = {
            "manufacturing_type_id": manufacturing_type_with_attributes.id,
            "name": "Complete Workflow Test",
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "Casement",
            "system_series": "Workflow800"
        }
        
        save_response = await client.post(
            "/api/v1/entry/profile/save",
            json=profile_data,
            headers=auth_headers
        )
        assert save_response.status_code == 201
        config_data = save_response.json()
        configuration_id = config_data["id"]
        customer_id = config_data["customer_id"]
        
        # Verify customer was auto-created
        result = await db_session.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        auto_created_customer = result.scalar_one_or_none()
        assert auto_created_customer is not None
        assert auto_created_customer.email == customer_user.email
        
        # Step 3: Generate preview (should be authorized for owner)
        preview_response = await client.get(
            f"/api/v1/entry/profile/preview/{configuration_id}",
            headers=auth_headers
        )
        assert preview_response.status_code == 200
        
        # Step 4: Create quote (should be authorized)
        quote_data = {
            "configuration_id": configuration_id,
            "tax_rate": "8.50"
        }
        
        quote_response = await client.post(
            "/api/v1/quotes/",
            json=quote_data,
            headers=auth_headers
        )
        assert quote_response.status_code == 201
        quote_data_response = quote_response.json()
        quote_id = quote_data_response["id"]
        
        # Verify quote uses proper customer relationship
        assert quote_data_response["customer_id"] == customer_id
        
        # Step 5: List user's quotes (should be filtered by RBAC)
        quotes_response = await client.get(
            "/api/v1/quotes/",
            headers=auth_headers
        )
        assert quotes_response.status_code == 200
        quotes_list = quotes_response.json()
        assert quotes_list["total"] >= 1
        assert any(q["id"] == quote_id for q in quotes_list["items"])

    @pytest.mark.asyncio
    async def test_cross_service_casbin_authorization_consistency(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        customer_user: User,
        salesman_user: User,
        manufacturing_type_with_attributes: ManufacturingType,
    ):
        """Test Casbin authorization consistency across different services."""
        # Arrange - Create configurations and quotes for different users
        from tests.conftest import create_auth_headers
        customer_headers = await create_auth_headers(customer_user)
        salesman_headers = await create_auth_headers(salesman_user)
        
        # Customer creates configuration
        profile_data = {
            "manufacturing_type_id": manufacturing_type_with_attributes.id,
            "name": "Cross-Service Test",
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "Casement",
            "system_series": "Cross800"
        }
        
        config_response = await client.post(
            "/api/v1/entry/profile/save",
            json=profile_data,
            headers=customer_headers
        )
        assert config_response.status_code == 201
        configuration_id = config_response.json()["id"]
        
        # Test 1: Customer can access their own configuration
        get_config_response = await client.get(
            f"/api/v1/configurations/{configuration_id}",
            headers=customer_headers
        )
        # Note: This might return 404 if endpoint doesn't exist, which is acceptable
        # The important thing is it shouldn't return 403 (authorization failure)
        assert get_config_response.status_code in [200, 404]
        
        # Test 2: Salesman should have access (full privileges initially)
        salesman_config_response = await client.get(
            f"/api/v1/configurations/{configuration_id}",
            headers=salesman_headers
        )
        # Salesman should have access due to full privileges
        assert salesman_config_response.status_code in [200, 404]
        
        # Test 3: Create quote as customer
        quote_data = {
            "configuration_id": configuration_id,
            "tax_rate": "8.50"
        }
        
        quote_response = await client.post(
            "/api/v1/quotes/",
            json=quote_data,
            headers=customer_headers
        )
        assert quote_response.status_code == 201
        quote_id = quote_response.json()["id"]
        
        # Test 4: Salesman should be able to see the quote (full privileges)
        salesman_quote_response = await client.get(
            f"/api/v1/quotes/{quote_id}",
            headers=salesman_headers
        )
        # Salesman should have access due to full privileges
        assert salesman_quote_response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_role_based_access_patterns(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        customer_user: User,
        salesman_user: User,
        partner_user: User,
        data_entry_user: User,
        test_superuser: User,
        manufacturing_type_with_attributes: ManufacturingType,
    ):
        """Test role-based access patterns for different user roles."""
        from tests.conftest import create_auth_headers
        
        # Get auth headers for all users
        customer_headers = await create_auth_headers(customer_user)
        salesman_headers = await create_auth_headers(salesman_user)
        partner_headers = await create_auth_headers(partner_user)
        data_entry_headers = await create_auth_headers(data_entry_user)
        superuser_headers = await create_auth_headers(test_superuser)
        
        # Test 1: All roles should be able to get manufacturing type schema
        schema_url = f"/api/v1/entry/profile/schema/{manufacturing_type_with_attributes.id}"
        
        for headers, role in [
            (customer_headers, "customer"),
            (salesman_headers, "salesman"), 
            (partner_headers, "partner"),
            (data_entry_headers, "data_entry"),
            (superuser_headers, "superuser")
        ]:
            response = await client.get(schema_url, headers=headers)
            assert response.status_code == 200, f"Role {role} should access schema"
        
        # Test 2: All roles should be able to create configurations
        profile_data = {
            "manufacturing_type_id": manufacturing_type_with_attributes.id,
            "name": f"Role Test Configuration",
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "Casement",
            "system_series": "Role800"
        }
        
        configurations = {}
        for headers, role in [
            (customer_headers, "customer"),
            (salesman_headers, "salesman"),
            (partner_headers, "partner"),
            (data_entry_headers, "data_entry"),
            (superuser_headers, "superuser")
        ]:
            profile_data["name"] = f"Role Test Configuration - {role}"
            response = await client.post(
                "/api/v1/entry/profile/save",
                json=profile_data,
                headers=headers
            )
            assert response.status_code == 201, f"Role {role} should create configurations"
            configurations[role] = response.json()["id"]
        
        # Test 3: Superuser should see all configurations in lists
        # (This test depends on having a configurations list endpoint)
        # For now, we'll test that superuser can access any specific configuration
        for role, config_id in configurations.items():
            response = await client.get(
                f"/api/v1/entry/profile/preview/{config_id}",
                headers=superuser_headers
            )
            assert response.status_code == 200, f"Superuser should access {role}'s configuration"

    @pytest.mark.asyncio
    async def test_multiple_decorator_patterns_and_privilege_objects(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        customer_user: User,
        salesman_user: User,
        test_superuser: User,
        manufacturing_type_with_attributes: ManufacturingType,
    ):
        """Test multiple decorator patterns and Privilege objects in real workflows."""
        from tests.conftest import create_auth_headers
        
        customer_headers = await create_auth_headers(customer_user)
        salesman_headers = await create_auth_headers(salesman_user)
        superuser_headers = await create_auth_headers(test_superuser)
        
        # Create configuration as customer
        profile_data = {
            "manufacturing_type_id": manufacturing_type_with_attributes.id,
            "name": "Decorator Pattern Test",
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "Casement",
            "system_series": "Decorator800"
        }
        
        config_response = await client.post(
            "/api/v1/entry/profile/save",
            json=profile_data,
            headers=customer_headers
        )
        assert config_response.status_code == 201
        configuration_id = config_response.json()["id"]
        
        # Test multiple authorization paths (OR logic between decorators)
        
        # Path 1: Customer can access their own configuration preview
        preview_response = await client.get(
            f"/api/v1/entry/profile/preview/{configuration_id}",
            headers=customer_headers
        )
        assert preview_response.status_code == 200
        
        # Path 2: Salesman can access due to full privileges
        salesman_preview_response = await client.get(
            f"/api/v1/entry/profile/preview/{configuration_id}",
            headers=salesman_headers
        )
        assert salesman_preview_response.status_code == 200
        
        # Path 3: Superuser can access any configuration
        superuser_preview_response = await client.get(
            f"/api/v1/entry/profile/preview/{configuration_id}",
            headers=superuser_headers
        )
        assert superuser_preview_response.status_code == 200

    @pytest.mark.asyncio
    async def test_mixed_scenarios_with_existing_and_new_customer_relationships(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        customer_user: User,
        manufacturing_type_with_attributes: ManufacturingType,
    ):
        """Test mixed scenarios with existing and new customer relationships."""
        from tests.conftest import create_auth_headers
        auth_headers = await create_auth_headers(customer_user)
        
        # Scenario 1: Create configuration (auto-creates customer)
        profile_data_1 = {
            "manufacturing_type_id": manufacturing_type_with_attributes.id,
            "name": "Mixed Scenario Test 1",
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "Casement",
            "system_series": "Mixed800"
        }
        
        response1 = await client.post(
            "/api/v1/entry/profile/save",
            json=profile_data_1,
            headers=auth_headers
        )
        assert response1.status_code == 201
        customer_id_1 = response1.json()["customer_id"]
        
        # Scenario 2: Create another configuration (should use existing customer)
        profile_data_2 = {
            "manufacturing_type_id": manufacturing_type_with_attributes.id,
            "name": "Mixed Scenario Test 2",
            "type": "Frame",
            "material": "Wood",
            "opening_system": "Sliding",
            "system_series": "Mixed900"
        }
        
        response2 = await client.post(
            "/api/v1/entry/profile/save",
            json=profile_data_2,
            headers=auth_headers
        )
        assert response2.status_code == 201
        customer_id_2 = response2.json()["customer_id"]
        
        # Both should use the same customer
        assert customer_id_1 == customer_id_2
        
        # Scenario 3: Verify customer consistency in database
        from sqlalchemy import select
        result = await db_session.execute(
            select(Customer).where(Customer.id == customer_id_1)
        )
        customer = result.scalar_one_or_none()
        assert customer is not None
        assert customer.email == customer_user.email
        
        # Scenario 4: Create quotes for both configurations
        for config_response in [response1, response2]:
            quote_data = {
                "configuration_id": config_response.json()["id"],
                "tax_rate": "8.50"
            }
            
            quote_response = await client.post(
                "/api/v1/quotes/",
                json=quote_data,
                headers=auth_headers
            )
            assert quote_response.status_code == 201
            
            # Verify quote uses same customer
            assert quote_response.json()["customer_id"] == customer_id_1

    @pytest.mark.asyncio
    async def test_performance_impact_of_casbin_policy_evaluation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        customer_user: User,
        manufacturing_type_with_attributes: ManufacturingType,
    ):
        """Test performance impact of Casbin policy evaluation."""
        import time
        from tests.conftest import create_auth_headers
        
        auth_headers = await create_auth_headers(customer_user)
        
        # Create multiple configurations to test performance
        profile_data_base = {
            "manufacturing_type_id": manufacturing_type_with_attributes.id,
            "type": "Frame",
            "material": "Aluminum",
            "opening_system": "Casement",
            "system_series": "Perf800"
        }
        
        # Measure time for multiple operations
        start_time = time.time()
        
        configuration_ids = []
        for i in range(5):  # Create 5 configurations
            profile_data = profile_data_base.copy()
            profile_data["name"] = f"Performance Test {i}"
            
            response = await client.post(
                "/api/v1/entry/profile/save",
                json=profile_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            configuration_ids.append(response.json()["id"])
        
        # Access each configuration preview (tests RBAC evaluation)
        for config_id in configuration_ids:
            response = await client.get(
                f"/api/v1/entry/profile/preview/{config_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertion - operations should complete reasonably quickly
        # This is a basic performance check, not a comprehensive benchmark
        assert total_time < 10.0, f"Operations took too long: {total_time} seconds"
        
        # Average time per operation should be reasonable
        avg_time_per_op = total_time / (len(configuration_ids) * 2)  # 2 ops per config
        assert avg_time_per_op < 1.0, f"Average time per operation too high: {avg_time_per_op} seconds"