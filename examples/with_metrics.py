"""
Basic error metrics collection example.

This example demonstrates basic usage of the error metrics collection system
with automatic error tracking.
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
app = FastAPI(title="Metrics Example")

# Setup error handler with metrics
error_config = ErrorHandlerConfig(
    default_locale="en",
    debug_mode=True,
)

# Use development preset for metrics (no Sentry, local dashboard only)
metrics_config = MetricsPreset.development()

# Setup exception handler with metrics enabled
setup_exception_handler(
    app,
    config=error_config,
    metrics_config=metrics_config,
)


# Define custom exceptions
class UserNotFoundException(BaseAppException):
    def __init__(self, user_id: int):
        super().__init__(
            error_code=301,
            message="User not found",
            status_code=404,
            detail={"user_id": user_id},
        )


class ValidationException(BaseAppException):
    def __init__(self, field: str, reason: str):
        super().__init__(
            error_code=401,
            message=f"Validation failed for {field}",
            status_code=422,
            detail={"field": field, "reason": reason},
        )


# API endpoints
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID - raises UserNotFoundException if not found."""
    # Simulate user not found
    if user_id != 1:
        raise UserNotFoundException(user_id)
    return {"id": user_id, "name": "Test User"}


@app.post("/users")
async def create_user(email: str, name: str):
    """Create a new user - demonstrates validation error."""
    if not email or "@" not in email:
        raise ValidationException("email", "Invalid email format")
    return {"id": 1, "email": email, "name": name}


@app.get("/dashboard")
async def get_dashboard():
    """Access metrics collector from app state."""
    collector = app.state.metrics_collector
    snapshot = collector.get_snapshot()
    return {
        "total_errors": snapshot.total_errors,
        "error_counts": snapshot.error_counts,
        "recent_events": [
            {
                "error_code": e.error_code,
                "message": e.message,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in snapshot.recent_events[:5]
        ],
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("FastAPI Error Metrics Example")
    print("=" * 60)
    print("\nAvailable endpoints:")
    print("  - GET /users/{user_id}  : Get user (404 if user_id != 1)")
    print("  - POST /users           : Create user (validation on email)")
    print("  - GET /dashboard        : View metrics summary")
    print("\nMonitoring endpoints:")
    print("  - GET /metrics          : Prometheus metrics")
    print("  - GET /api/metrics/summary      : Metrics summary")
    print("  - GET /api/metrics/recent       : Recent errors")
    print("  - GET /api/metrics/top-errors   : Top error codes")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
