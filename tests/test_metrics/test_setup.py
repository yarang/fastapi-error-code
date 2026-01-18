"""
Tests for setup_metrics module.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_error_codes.metrics.config import MetricsConfig
from fastapi_error_codes.metrics.setup import setup_metrics


class TestSetupMetrics:
    """Test setup_metrics function."""

    def test_setup_metrics_default_config(self) -> None:
        """Test setup metrics with default configuration."""
        app = FastAPI()
        metrics = setup_metrics(app)

        assert "collector" in metrics
        assert "exporter" in metrics
        assert "sentry" in metrics
        assert "dashboard" in metrics

        # Check app state
        assert hasattr(app.state, "metrics_collector")
        assert hasattr(app.state, "metrics_exporter")
        assert hasattr(app.state, "metrics_sentry")

    def test_setup_metrics_custom_config(self) -> None:
        """Test setup metrics with custom configuration."""
        app = FastAPI()
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123",
        )
        metrics = setup_metrics(app, config)

        assert metrics["sentry"].enabled is True
        assert metrics["exporter"].enabled is True

    def test_metrics_endpoint_registered(self) -> None:
        """Test that /metrics endpoint is registered."""
        app = FastAPI()
        setup_metrics(app)

        client = TestClient(app)
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    def test_dashboard_routes_registered(self) -> None:
        """Test that dashboard routes are registered."""
        app = FastAPI()
        setup_metrics(app)

        client = TestClient(app)

        # Test summary endpoint
        response = client.get("/api/metrics/summary")
        assert response.status_code == 200

        # Test recent events endpoint
        response = client.get("/api/metrics/recent")
        assert response.status_code == 200

        # Test top errors endpoint
        response = client.get("/api/metrics/top-errors")
        assert response.status_code == 200

    def test_collector_accessible_from_state(self) -> None:
        """Test that collector is accessible from app state."""
        app = FastAPI()
        setup_metrics(app)

        collector = app.state.metrics_collector
        assert collector is not None

        # Record an error
        collector.record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )

        # Verify it was recorded
        assert collector.total_events == 1

    def test_sentry_enabled_in_config(self) -> None:
        """Test that Sentry is configured when enabled."""
        app = FastAPI()
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123",
        )
        metrics = setup_metrics(app, config)

        # Verify Sentry integration was created with enabled=True
        assert metrics["sentry"].enabled is True
        assert metrics["sentry"].dsn == "https://key@sentry.io/123"

    def test_prometheus_endpoint_content(self) -> None:
        """Test that Prometheus endpoint returns valid content."""
        app = FastAPI()
        metrics = setup_metrics(app)

        # Record some errors
        metrics["collector"].record(
            error_code=404,
            error_name="NotFound",
            status_code=404,
            message="Not found",
        )

        client = TestClient(app)
        response = client.get("/metrics")

        content = response.text
        assert "fastapi_errors_total" in content
        assert "fastapi_errors_by_code" in content
