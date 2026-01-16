"""
Jaeger exporter example for distributed tracing.

This example demonstrates:
1. Setting up tracing with Jaeger exporter
2. Configuring Jaeger agent connection
3. Viewing traces in Jaeger UI
4. Retry logic for export failures
"""

from fastapi import FastAPI
from fastapi_error_codes import BaseAppException, register_exception
from fastapi_error_codes.tracing import TracingConfig, setup_tracing

# Create FastAPI app
app = FastAPI(title="Jaeger Tracing Example")

# Setup distributed tracing with Jaeger exporter
tracing_config = TracingConfig(
    service_name="jaeger-demo-service",
    endpoint="http://localhost:4317",
    sample_rate=1.0,
    jaeger_host="localhost",  # Jaeger agent host
    jaeger_port=6831,  # Jaeger agent port (Thrift protocol)
)

integration = setup_tracing(
    app,
    config=tracing_config,
    exporter_type="jaeger",  # Use Jaeger exporter
    enable_exception_tracing=True,
    enable_pii_masking=True,
)


# Define custom exceptions
@register_exception(error_code=301, message="Order not found", status_code=404)
class OrderNotFoundException(BaseAppException):
    """Raised when an order is not found."""
    pass


@register_exception(error_code=501, message="Database connection failed", status_code=503)
class DatabaseConnectionException(BaseAppException):
    """Raised when database connection fails."""
    pass


# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Jaeger tracing example",
        "service": "jaeger-demo-service",
        "jaeger_ui": "http://localhost:16686",
    }


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    """
    Get order by ID - demonstrates exception tracing.

    Each request creates a span with:
    - HTTP method and URL attributes
    - Exception event if order not found
    - Error code attribute
    """
    # Simulate order lookup
    if order_id != 12345:
        raise OrderNotFoundException(detail={"order_id": order_id})

    return {
        "order_id": order_id,
        "status": "completed",
        "total": 99.99,
        "items": ["item1", "item2"],
    }


@app.get("/db-test")
async def test_database():
    """Test database connectivity - simulates database error."""
    # Simulate database connection failure
    raise DatabaseConnectionException(
        detail={"database": "orders_db", "host": "db.internal"}
    )


@app.post("/checkout")
async def checkout(user_id: int, items: list):
    """
    Process checkout - creates multiple spans.

    This endpoint demonstrates:
    1. Root span from HTTP request
    2. Child spans for sub-operations
    3. Exception handling and tracing
    """
    from opentelemetry import trace

    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("checkout_process"):
        with tracer.start_as_current_span("validate_items"):
            # Simulate item validation
            if not items:
                raise ValueError("No items in cart")

        with tracer.start_as_current_span("calculate_total"):
            # Simulate total calculation
            total = sum(item.get("price", 0) for item in items)

        with tracer.start_as_current_span("process_payment"):
            # Simulate payment processing
            if total > 10000:
                raise BaseAppException(
                    error_code=601,
                    message="Payment amount exceeds limit",
                    status_code=402,
                    detail={"total": total, "limit": 10000},
                )

        return {
            "status": "success",
            "order_id": "ORD-12345",
            "total": total,
        }


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Jaeger Distributed Tracing Example")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  Start Jaeger with Docker:")
    print("  docker run -d \\")
    print("    -p 5775:5775/udp \\")
    print("    -p 6831:6831/udp \\")
    print("    -p 6832:6832/udp \\")
    print("    -p 5778:5778 \\")
    print("    -p 16686:16686 \\")
    print("    -p 14268:14268 \\")
    print("    -p 14250:14250 \\")
    print("    -p 9411:9411 \\")
    print("    --name jaeger \\")
    print("    jaegertracing/all-in-one:latest")
    print("\nAvailable endpoints:")
    print("  - GET /                    : Root endpoint")
    print("  - GET /orders/{order_id}   : Get order (404 if not 12345)")
    print("  - GET /db-test             : Test database (simulates error)")
    print("  - POST /checkout           : Process checkout")
    print("\nJaeger UI:")
    print("  - URL: http://localhost:16686")
    print("  - Service: jaeger-demo-service")
    print("  - Search for traces by operation name")
    print("\nTracing features:")
    print("  - Automatic HTTP request span creation")
    print("  - Exception events in spans")
    print("  - Custom child spans for operations")
    print("  - Retry logic for export failures")
    print("  - Trace ID in response headers (X-Trace-ID)")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
