"""
Tests for DashboardAPI module.
"""

from fastapi.testclient import TestClient
from fastapi import FastAPI

import pytest

from fastapi_error_codes.metrics.config import MetricsConfig
from fastapi_error_codes.metrics.collector import ErrorMetricsCollector
from fastapi_error_codes.metrics.dashboard import DashboardAPI


class TestDashboardAPI:
    """Test Dashboard API endpoints."""

    def test_create_dashboard_api(self) -> None:
        """Test creating dashboard API."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        dashboard = DashboardAPI(collector)

        assert dashboard.collector is collector
        assert dashboard.router is not None

    def test_summary_endpoint_empty(self) -> None:
        """Test summary endpoint with no data."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)
        dashboard = DashboardAPI(collector)

        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/metrics")

        client = TestClient(app)
        response = client.get("/api/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_errors"] == 0
        assert data["error_counts"] == {}
        assert "timestamp" in data

    def test_summary_endpoint_with_data(self) -> None:
        """Test summary endpoint with error data."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        # Record some errors
        for _ in range(5):
            collector.record(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message="Not found",
            )

        dashboard = DashboardAPI(collector)
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/metrics")

        client = TestClient(app)
        response = client.get("/api/metrics/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_errors"] == 5
        # JSON converts int keys to strings
        assert data["error_counts"].get("404") == 5 or data["error_counts"].get(404) == 5

    def test_recent_events_endpoint(self) -> None:
        """Test recent events endpoint."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        # Record errors
        for i in range(5):
            collector.record(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message=f"Not found {i}",
            )

        dashboard = DashboardAPI(collector)
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/metrics")

        client = TestClient(app)
        response = client.get("/api/metrics/recent?limit=3")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["events"]) == 3

    def test_by_code_endpoint(self) -> None:
        """Test endpoint for specific error code."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        collector.record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )

        dashboard = DashboardAPI(collector)
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/metrics")

        client = TestClient(app)
        response = client.get("/api/metrics/by-code/404")

        assert response.status_code == 200
        data = response.json()
        assert data["error_code"] == 404
        assert data["count"] == 1

    def test_top_errors_endpoint(self) -> None:
        """Test top errors endpoint."""
        config = MetricsConfig()
        collector = ErrorMetricsCollector(config)

        # Record different error codes
        for _ in range(10):
            collector.record(error_code=404, error_name="NotFound", status_code=404, message="Not found")
        for _ in range(5):
            collector.record(error_code=500, error_name="ServerError", status_code=500, message="Error")

        dashboard = DashboardAPI(collector)
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/metrics")

        client = TestClient(app)
        response = client.get("/api/metrics/top-errors?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["error_code"] == 404
        assert data[0]["count"] == 10
        assert data[0]["rank"] == 1
