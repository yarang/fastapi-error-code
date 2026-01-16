"""
Basic distributed tracing example for fastapi-error-codes.

This example demonstrates:
1. Setting up distributed tracing with OpenTelemetry
2. Automatic span creation for HTTP requests
3. Exception tracing with PII masking
4. Trace ID correlation in error responses
"""

from fastapi import FastAPI
from fastapi_error_codes import (
    BaseAppException,
    setup_exception_handler,
    ErrorHandlerConfig,
)
from fastapi_error_codes.tracing import TracingConfig, setup_tracing

# Create FastAPI app
app = FastAPI(title="Distributed Tracing Example")

# Setup error handler
error_config = ErrorHandlerConfig(
    default_locale="en",
    debug_mode=True,
)
setup_exception_handler(app, config=error_config)

# Setup distributed tracing
tracing_config = TracingConfig(
    service_name="demo-service",
    endpoint="http://localhost:4317",  # Default OTLP endpoint
    sample_rate=1.0,  # Sample 100% of traces for demo
)

integration = setup_tracing(
    app,
    config=tracing_config,
    exporter_type="otlp",
    enable_exception_tracing=True,
    enable_pii_masking=True,
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


class PaymentFailedException(BaseAppException):
    def __init__(self, amount: float, card_last4: str):
        super().__init__(
            error_code=601,
            message=f"Payment of ${amount} failed",
            status_code=402,
            detail={
                "amount": amount,
                "card_last4": card_last4,
                "email": "user@example.com",  # This will be masked
            },
        )


# API endpoints
@app.get("/")
async def root():
    """Root endpoint - creates a simple span."""
    return {"message": "Distributed tracing example", "service": "demo-service"}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    Get user by ID - demonstrates exception tracing.

    The exception will be automatically recorded in the span with:
    - Exception type and message
    - Error code attribute
    - Sanitized stack trace
    - PII masked in detail fields
    """
    # Simulate user lookup
    if user_id != 1:
        raise UserNotFoundException(user_id)

    return {"id": user_id, "name": "John Doe", "email": "john@example.com"}


@app.post("/payments")
async def create_payment(amount: float, card_number: str):
    """
    Create a payment - demonstrates PII masking in traces.

    Sensitive data like credit card numbers and emails are automatically
    masked before being recorded in spans.
    """
    # Simulate payment processing
    if amount > 1000:
        raise PaymentFailedException(amount, card_number[-4:])

    return {"status": "success", "amount": amount, "transaction_id": "txn_12345"}


@app.get("/health")
async def health_check():
    """Health check endpoint - excluded from tracing."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("FastAPI Distributed Tracing Example")
    print("=" * 60)
    print("\nAvailable endpoints:")
    print("  - GET /                     : Root endpoint")
    print("  - GET /users/{user_id}      : Get user (404 if user_id != 1)")
    print("  - POST /payments            : Create payment")
    print("  - GET /health               : Health check (no tracing)")
    print("\nTracing features:")
    print("  - Automatic span creation for all HTTP requests")
    print("  - Exception events recorded in spans")
    print("  - Trace ID added to error responses")
    print("  - PII automatically masked in spans")
    print("  - X-Trace-ID header added to responses")
    print("\nTo view traces:")
    print("  1. Start Jaeger: docker run -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one")
    print("  2. Open Jaeger UI: http://localhost:16686")
    print("  3. Select service: demo-service")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
