"""
Dashboard API usage example.

This example demonstrates how to use the built-in dashboard API
to query and visualize error metrics in real-time.
"""

from fastapi import FastAPI, HTTPException
from fastapi_error_codes import (
    BaseAppException,
    setup_exception_handler,
    ErrorHandlerConfig,
    MetricsConfig,
    MetricsPreset,
)
from fastapi_error_codes.metrics import ErrorMetricsCollector

# Create FastAPI app
app = FastAPI(title="Dashboard API Example")

# Setup error handler with dashboard enabled
error_config = ErrorHandlerConfig(
    default_locale="en",
    debug_mode=True,
)

# Dashboard configuration
metrics_config = MetricsConfig(
    enabled=True,
    collection_interval_ms=60000,
    max_events=10000,
    prometheus_enabled=True,
    sentry_enabled=False,
    dashboard_enabled=True,  # Enable dashboard API
)

setup_exception_handler(
    app,
    config=error_config,
    metrics_config=metrics_config,
)


# Define custom exceptions
class DataNotFoundError(BaseAppException):
    def __init__(self, resource_id: str):
        super().__init__(
            error_code=301,
            message=f"Data not found: {resource_id}",
            status_code=404,
            detail={"resource_id": resource_id},
        )


class ValidationFailedError(BaseAppException):
    def __init__(self, field: str, value: str):
        super().__init__(
            error_code=401,
            message=f"Validation failed for {field}",
            status_code=422,
            detail={"field": field, "value": value},
        )


class PermissionDeniedError(BaseAppException):
    def __init__(self, resource: str, action: str):
        super().__init__(
            error_code=203,
            message=f"Permission denied: {action} on {resource}",
            status_code=403,
            detail={"resource": resource, "action": action},
        )


class ServerInternalError(BaseAppException):
    def __init__(self, component: str):
        super().__init__(
            error_code=500,
            message=f"Internal error in {component}",
            status_code=500,
            detail={"component": component},
        )


# Demo endpoints that generate various errors
@app.get("/")
async def root():
    """Root endpoint with dashboard links."""
    return {
        "message": "Dashboard API Example",
        "dashboard_endpoints": {
            "summary": "/api/metrics/summary",
            "recent": "/api/metrics/recent?limit=100",
            "by_code": "/api/metrics/by-code/{error_code}",
            "top_errors": "/api/metrics/top-errors?limit=10",
            "prometheus": "/metrics",
        },
        "demo_endpoints": {
            "not_found": "/demo/404",
            "validation": "/demo/422",
            "permission": "/demo/403",
            "server_error": "/demo/500",
            "random_error": "/demo/random",
            "clear_metrics": "/demo/clear",
        },
    }


@app.get("/demo/404")
async def demo_not_found():
    """Generate 404 error."""
    raise DataNotFoundError(resource_id="user-12345")


@app.get("/demo/422")
async def demo_validation():
    """Generate 422 validation error."""
    raise ValidationFailedError(field="email", value="invalid-email")


@app.get("/demo/403")
async def demo_permission():
    """Generate 403 permission error."""
    raise PermissionDeniedError(resource="user-123", action="delete")


@app.get("/demo/500")
async def demo_server_error():
    """Generate 500 server error."""
    raise ServerInternalError(component="database")


@app.get("/demo/random")
async def demo_random_error():
    """Generate a random error for testing."""
    import random

    error_type = random.choice(["404", "422", "403", "500"])
    if error_type == "404":
        raise DataNotFoundError(resource_id=f"resource-{random.randint(1000, 9999)}")
    elif error_type == "422":
        raise ValidationFailedError(
            field=random.choice(["email", "phone", "name"]),
            value="invalid"
        )
    elif error_type == "403":
        raise PermissionDeniedError(
            resource=random.choice(["user", "post", "comment"]),
            action=random.choice(["delete", "update", "create"])
        )
    else:
        raise ServerInternalError(
            component=random.choice(["database", "cache", "api"])
        )


@app.get("/demo/clear")
async def demo_clear_metrics():
    """Clear all collected metrics."""
    collector: ErrorMetricsCollector = app.state.metrics_collector
    collector.clear()
    return {"message": "Metrics cleared", "total_events": collector.total_events}


@app.get("/demo/generate/{count}")
async def demo_generate_errors(count: int):
    """
    Generate multiple errors for testing the dashboard.

    Args:
        count: Number of errors to generate (max 100)
    """
    if count > 100:
        raise HTTPException(status_code=400, detail="Count must be <= 100")

    import random

    for _ in range(count):
        error_type = random.choice(["404", "422", "403", "500"], weights=[40, 30, 20, 10])
        try:
            if error_type == "404":
                raise DataNotFoundError(resource_id=f"resource-{random.randint(1000, 9999)}")
            elif error_type == "422":
                raise ValidationFailedError(
                    field=random.choice(["email", "phone", "name", "age"]),
                    value="invalid"
                )
            elif error_type == "403":
                raise PermissionDeniedError(
                    resource=random.choice(["user", "post", "comment", "settings"]),
                    action=random.choice(["delete", "update", "create", "read"])
                )
            else:
                raise ServerInternalError(
                    component=random.choice(["database", "cache", "api", "storage"])
                )
        except BaseAppException:
            pass  # Exception handled by middleware

    collector: ErrorMetricsCollector = app.state.metrics_collector
    return {
        "message": f"Generated {count} errors",
        "total_events": collector.total_events,
    }


@app.get("/demo/stats")
async def demo_stats():
    """Get quick stats from metrics collector."""
    collector: ErrorMetricsCollector = app.state.metrics_collector
    snapshot = collector.get_snapshot()
    return {
        "total_errors": snapshot.total_errors,
        "bucket_count": snapshot.bucket_count,
        "error_codes": list(snapshot.error_counts.keys()),
        "top_errors": sorted(
            snapshot.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5],
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("Dashboard API Example - Error Metrics Visualization")
    print("=" * 70)
    print("\nDashboard Endpoints:")
    print("  GET /api/metrics/summary          : Overall metrics summary")
    print("  GET /api/metrics/recent?limit=100 : Recent error events")
    print("  GET /api/metrics/by-code/404      : Metrics for error code 404")
    print("  GET /api/metrics/top-errors       : Top error codes by count")
    print("  GET /metrics                      : Prometheus metrics")
    print("\nDemo Endpoints:")
    print("  GET /demo/404                     : Generate 404 error")
    print("  GET /demo/422                     : Generate 422 error")
    print("  GET /demo/403                     : Generate 403 error")
    print("  GET /demo/500                     : Generate 500 error")
    print("  GET /demo/random                  : Generate random error")
    print("  GET /demo/generate/50             : Generate 50 random errors")
    print("  GET /demo/clear                   : Clear all metrics")
    print("  GET /demo/stats                   : Quick stats summary")
    print("\nExample Workflow:")
    print("  1. Visit http://localhost:8000/ for full documentation")
    print("  2. Generate errors: GET /demo/generate/50")
    print("  3. View summary: GET /api/metrics/summary")
    print("  4. Check recent errors: GET /api/metrics/recent")
    print("  5. See top errors: GET /api/metrics/top-errors")
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000)
