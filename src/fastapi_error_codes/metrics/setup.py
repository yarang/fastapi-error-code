"""
FastAPI metrics integration setup.

This module provides setup_metrics() function for complete
FastAPI integration with error metrics collection.
"""

from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from fastapi_error_codes.metrics.collector import ErrorMetricsCollector
from fastapi_error_codes.metrics.config import MetricsConfig
from fastapi_error_codes.metrics.dashboard import DashboardAPI
from fastapi_error_codes.metrics.prometheus import PrometheusExporter
from fastapi_error_codes.metrics.sentry import SentryIntegration


def setup_metrics(
    app: FastAPI,
    config: Optional[MetricsConfig] = None,
) -> dict:
    """
    Setup error metrics collection for FastAPI application.

    This function configures:
    - ErrorMetricsCollector for metrics collection
    - PrometheusExporter for /metrics endpoint
    - SentryIntegration for error tracking
    - DashboardAPI for /api/metrics/* endpoints
    - Non-blocking metrics collection hook

    Args:
        app: FastAPI application instance
        config: Metrics configuration (uses defaults if None)

    Returns:
        Dictionary with metrics components:
        - collector: ErrorMetricsCollector instance
        - exporter: PrometheusExporter instance
        - sentry: SentryIntegration instance
        - dashboard: DashboardAPI instance

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_error_codes.metrics import setup_metrics, MetricsConfig

        app = FastAPI()
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        metrics = setup_metrics(app, config)

        # Now errors are automatically tracked
        @app.get("/users/{user_id}")
        def get_user(user_id: int):
            if not user_exists(user_id):
                raise BaseAppException(
                    error_code=404,
                    message="User not found",
                    status_code=404
                )
        ```
    """
    if config is None:
        config = MetricsConfig()

    # Initialize components
    collector = ErrorMetricsCollector(config)
    exporter = PrometheusExporter(
        collector,
        enabled=config.prometheus_enabled,
    )
    sentry = SentryIntegration(config)
    dashboard = DashboardAPI(collector)

    # Initialize Sentry
    if sentry.enabled:
        sentry.initialize()

    # Setup metrics routes
    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        return PlainTextResponse(
            content=exporter.generate_metrics(),
            media_type="text/plain",
        )

    # Include dashboard routes
    if config.dashboard_enabled:
        app.include_router(
            dashboard.router,
            prefix="/api/metrics",
            tags=["metrics"],
        )

    # Setup metrics collection hook
    @app.middleware("http")
    async def metrics_collection_middleware(request: Request, call_next):
        """Non-blocking metrics collection middleware."""
        response = await call_next(request)

        # Record errors from response status if needed
        # This is non-blocking and doesn't affect request processing
        if response.status_code >= 400:
            # The error was already recorded by the exception handler
            pass

        return response

    # Store metrics in app state for access
    app.state.metrics_collector = collector
    app.state.metrics_exporter = exporter
    app.state.metrics_sentry = sentry

    return {
        "collector": collector,
        "exporter": exporter,
        "sentry": sentry,
        "dashboard": dashboard,
    }
