"""Integration tests for Quote API endpoints.

Tests the complete quote workflow including:
- Quote creation with price calculation
- Quote retrieval and filtering
- Quote status management
- Authorization checks
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import Configuration
from app.models.manufacturing_type import ManufacturingType
from app.models.quote import Quote
from app.models.user import User


@pytest.fixture
async def manufacturing_type(db_session: AsyncSession) -> ManufacturingType:
    """Create a test manufacturing type."""
    mfg_type = ManufacturingType(
        name="Test Window",
        description="Test window type",
        base_category="window",
        base_price=Decimal("200.00"),
        base_weight=Decimal("15.00"),
        is_active=True,
    )
    db_session.add(mfg_type)
    await db_session.commit()
    await db_session.refresh(mfg_type)
    return mfg_type


@pytest.fixture
async def configuration(
    db_session: AsyncSession,
    manufacturing_type: ManufacturingType,
    test_user: User,
) -> Configuration:
    """Create a test configuration."""
    config = Configuration(
        manufacturing_type_id=manufacturing_type.id,
        customer_id=test_user.id,
        name="Test Configuration",
        description="Test configuration for quotes",
        status="draft",
        reference_code="TEST-CONFIG-001",
        base_price=manufacturing_type.base_price,
        total_price=Decimal("525.00"),
        calculated_weight=Decimal("23.00"),
        calculated_technical_data={},
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)
    return config


class TestQuoteCreation:
    """Tests for POST /api/v1/quotes - Create quote."""

    async def test_create_quote_success(
        self,
        client: AsyncClient,
        test_user: User,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test successful quote creation with automatic calculations."""
        # Arrange
        valid_until = date.today() + timedelta(days=30)
        quote_data = {
            "configuration_id": configuration.id,
            "tax_rate": "8.50",
            "discount_amount": "0.00",
            "valid_until": valid_until.isoformat(),
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["configuration_id"] == configuration.id
        assert data["customer_id"] == test_user.id
        assert data["quote_number"].startswith("Q-")
        assert Decimal(data["subtotal"]) == Decimal("525.00")
        assert Decimal(data["tax_rate"]) == Decimal("8.50")
        assert Decimal(data["tax_amount"]) == Decimal("44.63")  # 525 * 0.085
        assert Decimal(data["discount_amount"]) == Decimal("0.00")
        assert Decimal(data["total_amount"]) == Decimal("569.63")  # 525 + 44.63
        assert data["status"] == "draft"
        assert data["valid_until"] == valid_until.isoformat()

    async def test_create_quote_with_discount(
        self,
        client: AsyncClient,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test quote creation with discount applied."""
        # Arrange
        quote_data = {
            "configuration_id": configuration.id,
            "tax_rate": "8.50",
            "discount_amount": "25.00",
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert Decimal(data["subtotal"]) == Decimal("525.00")
        assert Decimal(data["tax_amount"]) == Decimal("44.63")
        assert Decimal(data["discount_amount"]) == Decimal("25.00")
        assert Decimal(data["total_amount"]) == Decimal("544.63")  # 525 + 44.63 - 25

    async def test_create_quote_default_valid_until(
        self,
        client: AsyncClient,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test quote creation with default valid_until (30 days)."""
        # Arrange
        quote_data = {
            "configuration_id": configuration.id,
            "tax_rate": "0.00",
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        expected_date = date.today() + timedelta(days=30)
        assert data["valid_until"] == expected_date.isoformat()

    async def test_create_quote_configuration_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test quote creation with non-existent configuration."""
        # Arrange
        quote_data = {
            "configuration_id": 99999,
            "tax_rate": "8.50",
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()

    async def test_create_quote_unauthorized_configuration(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test quote creation for another user's configuration."""
        # Arrange - Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(other_user)
        await db_session.commit()

        # Update configuration to belong to other user
        configuration.customer_id = other_user.id
        await db_session.commit()

        quote_data = {
            "configuration_id": configuration.id,
            "tax_rate": "8.50",
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 403

    async def test_create_quote_invalid_tax_rate(
        self,
        client: AsyncClient,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test quote creation with invalid tax rate."""
        # Arrange
        quote_data = {
            "configuration_id": configuration.id,
            "tax_rate": "150.00",  # > 100%
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 422

    async def test_create_quote_invalid_discount(
        self,
        client: AsyncClient,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test quote creation with discount exceeding subtotal."""
        # Arrange
        quote_data = {
            "configuration_id": configuration.id,
            "tax_rate": "8.50",
            "discount_amount": "1000.00",  # > subtotal
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 422

    async def test_create_quote_past_valid_until(
        self,
        client: AsyncClient,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test quote creation with past valid_until date."""
        # Arrange
        past_date = date.today() - timedelta(days=1)
        quote_data = {
            "configuration_id": configuration.id,
            "tax_rate": "8.50",
            "valid_until": past_date.isoformat(),
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 422
        assert "past" in response.json()["detail"][0]["msg"].lower()


class TestQuoteRetrieval:
    """Tests for GET /api/v1/quotes - List and retrieve quotes."""

    async def test_list_quotes_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test listing user's quotes."""
        # Arrange - Create quotes
        for i in range(3):
            quote = Quote(
                configuration_id=configuration.id,
                customer_id=test_user.id,
                quote_number=f"Q-TEST-{i:03d}",
                subtotal=Decimal("525.00"),
                tax_rate=Decimal("8.50"),
                tax_amount=Decimal("44.63"),
                discount_amount=Decimal("0.00"),
                total_amount=Decimal("569.63"),
                status="draft",
            )
            db_session.add(quote)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/quotes",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_list_quotes_with_status_filter(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test listing quotes filtered by status."""
        # Arrange - Create quotes with different statuses
        statuses = ["draft", "sent", "accepted"]
        for status in statuses:
            quote = Quote(
                configuration_id=configuration.id,
                customer_id=test_user.id,
                quote_number=f"Q-{status.upper()}-001",
                subtotal=Decimal("525.00"),
                tax_rate=Decimal("8.50"),
                tax_amount=Decimal("44.63"),
                discount_amount=Decimal("0.00"),
                total_amount=Decimal("569.63"),
                status=status,
            )
            db_session.add(quote)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/quotes?status=sent",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "sent"

    async def test_get_quote_by_id_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test retrieving a specific quote by ID."""
        # Arrange
        quote = Quote(
            configuration_id=configuration.id,
            customer_id=test_user.id,
            quote_number="Q-TEST-001",
            subtotal=Decimal("525.00"),
            tax_rate=Decimal("8.50"),
            tax_amount=Decimal("44.63"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("569.63"),
            status="draft",
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        # Act
        response = await client.get(
            f"/api/v1/quotes/{quote.id}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == quote.id
        assert data["quote_number"] == "Q-TEST-001"

    async def test_get_quote_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test retrieving non-existent quote."""
        # Act
        response = await client.get(
            "/api/v1/quotes/99999",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 404

    async def test_get_quote_unauthorized(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test retrieving another user's quote."""
        # Arrange - Create another user and their quote
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(other_user)
        await db_session.flush()

        quote = Quote(
            configuration_id=configuration.id,
            customer_id=other_user.id,
            quote_number="Q-OTHER-001",
            subtotal=Decimal("525.00"),
            tax_rate=Decimal("8.50"),
            tax_amount=Decimal("44.63"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("569.63"),
            status="draft",
        )
        db_session.add(quote)
        await db_session.commit()
        await db_session.refresh(quote)

        # Act
        response = await client.get(
            f"/api/v1/quotes/{quote.id}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 403


class TestQuoteAuthorization:
    """Tests for quote authorization rules."""

    async def test_superuser_can_see_all_quotes(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_superuser: User,
        configuration: Configuration,
        superuser_auth_headers: dict,
    ):
        """Test that superusers can see all quotes."""
        # Arrange - Create quotes for different users
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(other_user)
        await db_session.flush()

        quote = Quote(
            configuration_id=configuration.id,
            customer_id=other_user.id,
            quote_number="Q-OTHER-001",
            subtotal=Decimal("525.00"),
            tax_rate=Decimal("8.50"),
            tax_amount=Decimal("44.63"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("569.63"),
            status="draft",
        )
        db_session.add(quote)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/quotes",
            headers=superuser_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1  # At least the other user's quote

    async def test_regular_user_sees_only_own_quotes(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        configuration: Configuration,
        auth_headers: dict,
    ):
        """Test that regular users see only their own quotes."""
        # Arrange - Create quote for test user
        user_quote = Quote(
            configuration_id=configuration.id,
            customer_id=test_user.id,
            quote_number="Q-USER-001",
            subtotal=Decimal("525.00"),
            tax_rate=Decimal("8.50"),
            tax_amount=Decimal("44.63"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("569.63"),
            status="draft",
        )
        db_session.add(user_quote)

        # Create quote for another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(other_user)
        await db_session.flush()

        other_quote = Quote(
            configuration_id=configuration.id,
            customer_id=other_user.id,
            quote_number="Q-OTHER-001",
            subtotal=Decimal("525.00"),
            tax_rate=Decimal("8.50"),
            tax_amount=Decimal("44.63"),
            discount_amount=Decimal("0.00"),
            total_amount=Decimal("569.63"),
            status="draft",
        )
        db_session.add(other_quote)
        await db_session.commit()

        # Act
        response = await client.get(
            "/api/v1/quotes",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["customer_id"] == test_user.id


class TestQuoteUnauthenticated:
    """Tests for unauthenticated access to quote endpoints."""

    async def test_create_quote_unauthenticated(
        self,
        client: AsyncClient,
        configuration: Configuration,
    ):
        """Test that unauthenticated users cannot create quotes."""
        # Arrange
        quote_data = {
            "configuration_id": configuration.id,
            "tax_rate": "8.50",
        }

        # Act
        response = await client.post(
            "/api/v1/quotes",
            json=quote_data,
        )

        # Assert
        assert response.status_code == 401

    async def test_list_quotes_unauthenticated(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated users cannot list quotes."""
        # Act
        response = await client.get("/api/v1/quotes")

        # Assert
        assert response.status_code == 401

    async def test_get_quote_unauthenticated(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated users cannot get quotes."""
        # Act
        response = await client.get("/api/v1/quotes/1")

        # Assert
        assert response.status_code == 401
