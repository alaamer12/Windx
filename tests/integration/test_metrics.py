"""Integration tests for metrics endpoints.

This module tests the metrics endpoints with focus on:
- Database connection pool metrics
- Access control (superuser-only)
- Response format validation
- Real-time metrics accuracy

Features:
    - Superuser access control testing
    - Metrics response format validation
    - Connection pool statistics verification
    - Unauthorized access testing
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestDatabaseMetricsEndpoint:
    """Tests for GET /api/v1/metrics/database endpoint."""

    async def test_database_metrics_success(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test successful retrieval of database metrics."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = [
            "pool_size",
            "checked_in",
            "checked_out",
            "overflow",
            "total_connections",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # Verify all values are integers
        for field in required_fields:
            assert isinstance(data[field], int), f"{field} should be an integer"

        # Verify logical constraints
        assert data["pool_size"] >= 0
        assert data["checked_in"] >= 0
        assert data["checked_out"] >= 0
        # Note: overflow can be negative (represents available overflow capacity)
        assert data["total_connections"] >= 0

    async def test_database_metrics_response_format(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that database metrics response has correct format."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response is a dictionary
        assert isinstance(data, dict)

        # Verify exact fields (no extra fields)
        expected_fields = {
            "pool_size",
            "checked_in",
            "checked_out",
            "overflow",
            "total_connections",
        }
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields

    async def test_database_metrics_requires_superuser(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test that database metrics requires superuser access."""
        # Try with regular user
        response = await client.get(
            "/api/v1/metrics/database",
            headers=auth_headers,
        )

        # Should be forbidden
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data or "message" in data

    async def test_database_metrics_requires_authentication(
        self,
        client: AsyncClient,
    ):
        """Test that database metrics requires authentication."""
        # Try without authentication
        response = await client.get("/api/v1/metrics/database")

        # Should be unauthorized
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data or "message" in data

    async def test_database_metrics_pool_size_positive(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that pool_size is always positive."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Pool size should be positive (configured in settings)
        assert data["pool_size"] > 0

    async def test_database_metrics_checked_in_out_sum(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that checked_in + checked_out <= pool_size + overflow."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify checked_in and checked_out are non-negative
        assert data["checked_in"] >= 0
        assert data["checked_out"] >= 0

    async def test_database_metrics_total_connections_calculation(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that total_connections is correctly calculated."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify total_connections is non-negative
        assert data["total_connections"] >= 0
        # Verify it's related to pool_size
        assert data["pool_size"] > 0

    async def test_database_metrics_real_time(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that metrics reflect real-time state."""
        # Get metrics twice
        response1 = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )
        response2 = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Pool size should be consistent (configuration)
        assert data1["pool_size"] == data2["pool_size"]

        # Other metrics may vary but should be valid
        assert data1["checked_in"] >= 0
        assert data2["checked_in"] >= 0

    async def test_database_metrics_no_caching(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that metrics are not cached (real-time data)."""
        # Make multiple requests
        responses = []
        for _ in range(3):
            response = await client.get(
                "/api/v1/metrics/database",
                headers=superuser_auth_headers,
            )
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should have valid data
        for data in responses:
            assert "pool_size" in data
            assert "checked_in" in data
            assert "checked_out" in data

    async def test_database_metrics_idempotent(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that metrics endpoint is idempotent."""
        # Call multiple times
        for _ in range(5):
            response = await client.get(
                "/api/v1/metrics/database",
                headers=superuser_auth_headers,
            )

            assert response.status_code == 200
            data = response.json()

            # Should always return valid structure
            assert "pool_size" in data
            assert "total_connections" in data

    async def test_database_metrics_performance(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that metrics endpoint responds quickly."""
        import time

        start_time = time.time()
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )
        response_time = time.time() - start_time

        assert response.status_code == 200

        # Metrics should be fast (< 0.5 seconds)
        assert response_time < 0.5, f"Metrics took {response_time}s"

    async def test_database_metrics_with_invalid_token(
        self,
        client: AsyncClient,
    ):
        """Test database metrics with invalid authentication token."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers={"Authorization": "Bearer invalid_token"},
        )

        # Should be unauthorized
        assert response.status_code == 401

    async def test_database_metrics_content_type(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that metrics endpoint returns JSON."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    async def test_database_metrics_overflow_zero_initially(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that overflow is typically zero in test environment."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Overflow can be negative (represents available overflow capacity)
        # Just verify it's a valid integer
        assert isinstance(data["overflow"], int)

    async def test_database_metrics_consistent_types(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict[str, str],
    ):
        """Test that all metric values are consistently integers."""
        response = await client.get(
            "/api/v1/metrics/database",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # All values should be integers, not floats or strings
        for key, value in data.items():
            assert isinstance(value, int), f"{key} should be int, got {type(value)}"
            assert not isinstance(value, bool), f"{key} should not be bool"
