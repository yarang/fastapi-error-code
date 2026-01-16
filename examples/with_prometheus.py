"""
Prometheus metrics integration example.

This example demonstrates how to use the Prometheus metrics export
for monitoring error rates in a Prometheus-compatible system.
"""

from fastapi import FastAPI
from fastapi_error_codes import (
    BaseAppException,
    setup_exception_handler,
    ErrorHandlerConfig,
    MetricsConfig,
    MetricsPreset,
)

# Create FastAPI app
app = FastAPI(title="Prometheus Metrics Example")

# Setup error handler with Prometheus metrics
error_config = ErrorHandlerConfig(
    default_locale="en",
    debug_mode=False,
)

# Enable Prometheus metrics
metrics_config = MetricsConfig(
    enabled=True,
    collection_interval_ms=60000,
    max_events=10000,
    prometheus_enabled=True,  # Enable Prometheus
    sentry_enabled=False,
    dashboard_enabled=True,
)

setup_exception_handler(
    app,
    config=error_config,
    metrics_config=metrics_config,
)


# Define custom exceptions
class RateLimitExceededError(BaseAppException):
    def __init__(self, limit: int):
        super().__init__(
            error_code=429,
            message=f"Rate limit exceeded (max {limit} requests)",
            status_code=429,
            detail={"limit": limit},
        )


class ServiceUnavailableError(BaseAppException):
    def __init__(self, service: str):
        super().__init__(
            error_code=503,
            message=f"Service {service} is unavailable",
            status_code=503,
            detail={"service": service},
        )


# API endpoints that generate errors for demonstration
@app.get("/api/data")
async def get_data():
    """Simulate various error conditions based on query parameters."""
    return {"status": "ok", "data": "sample"}


@app.get("/api/error/rate-limit")
async def trigger_rate_limit():
    """Trigger rate limit error for Prometheus metrics."""
    raise RateLimitExceededError(limit=100)


@app.get("/api/error/service-unavailable")
async def trigger_service_unavailable():
    """Trigger service unavailable error for Prometheus metrics."""
    raise ServiceUnavailableError(service="database")


@app.get("/api/error/not-found")
async def trigger_not_found():
    """Trigger not found error."""
    raise BaseAppException(
        error_code=404,
        message="Resource not found",
        status_code=404,
    )


@app.get("/api/error/server-error")
async def trigger_server_error():
    """Trigger server error."""
    raise BaseAppException(
        error_code=500,
        message="Internal server error",
        status_code=500,
    )


@app.get("/")
async def root():
    """
    Root endpoint with usage instructions.

    The /metrics endpoint is automatically available for Prometheus scraping.
    """
    return {
        "message": "Prometheus Metrics Example",
        "endpoints": {
            "metrics": "/metrics",
            "api": {
                "data": "/api/data",
                "rate_limit_error": "/api/error/rate-limit",
                "service_error": "/api/error/service-unavailable",
                "not_found": "/api/error/not-found",
                "server_error": "/api/error/server-error",
            },
            "dashboard": {
                "summary": "/api/metrics/summary",
                "recent": "/api/metrics/recent",
                "top_errors": "/api/metrics/top-errors",
            },
        },
        "prometheus_setup": """
# Configure Prometheus to scrape metrics
scrape_configs:
  - job_name: 'fastapi-errors'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
        """,
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Prometheus Metrics Example")
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET /                          : Usage information")
    print("  GET /metrics                   : Prometheus metrics endpoint")
    print("  GET /api/data                  : Normal response")
    print("  GET /api/error/rate-limit      : Trigger 429 error")
    print("  GET /api/error/service-error   : Trigger 503 error")
    print("  GET /api/error/not-found       : Trigger 404 error")
    print("  GET /api/error/server-error    : Trigger 500 error")
    print("\nPrometheus Configuration:")
    print("""
scrape_configs:
  - job_name: 'fastapi-errors'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    """)
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
