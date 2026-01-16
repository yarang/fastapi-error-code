"""
Cross-service trace context propagation example.

This example demonstrates:
1. W3C Trace Context propagation across services
2. Injecting traceparent header in downstream requests
3. Extracting trace context from incoming requests
4. Building distributed traces across multiple services
"""

import asyncio
from typing import Optional
from fastapi import FastAPI, Request
from fastapi_error_codes import BaseAppException, register_exception
from fastapi_error_codes.tracing import TracingConfig, setup_tracing, get_trace_id
import httpx


# Create three services to demonstrate cross-service tracing
service_a = FastAPI(title="Service A - API Gateway")
service_b = FastAPI(title="Service B - User Service")
service_c = FastAPI(title="Service C - Payment Service")


# Setup tracing for all services
def setup_service_tracing(app: FastAPI, service_name: str):
    """Setup distributed tracing for a service."""
    config = TracingConfig(
        service_name=service_name,
        endpoint="http://localhost:4317",
        sample_rate=1.0,
    )
    return setup_tracing(app, config, exporter_type="otlp")


# Initialize tracing for each service
integration_a = setup_service_tracing(service_a, "service-a")
integration_b = setup_service_tracing(service_b, "service-b")
integration_c = setup_service_tracing(service_c, "service-c")


# Define exceptions
@register_exception(error_code=301, message="User not found", status_code=404)
class UserNotFoundException(BaseAppException):
    """Raised when user is not found."""
    pass


@register_exception(error_code=601, message="Payment failed", status_code=402)
class PaymentFailedException(BaseAppException):
    """Raised when payment fails."""
    pass


# ===== SERVICE A: API Gateway =====

@service_a.get("/")
async def root():
    """Root endpoint of API Gateway."""
    return {
        "service": "service-a (API Gateway)",
        "endpoints": ["/checkout", "/users/{user_id}"],
    }


@service_a.post("/checkout")
async def checkout(user_id: int, amount: float):
    """
    Checkout endpoint - calls Service B and Service C.

    This demonstrates:
    1. Creating a child span for the HTTP client call
    2. Injecting traceparent header into downstream request
    3. Correlating spans across service boundaries
    """
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.propagate import inject

    tracer = trace.get_tracer(__name__)

    # Get current trace ID
    current_trace_id = get_trace_id()

    async with httpx.AsyncClient() as client:
        # Call Service B to get user info
        with tracer.start_as_current_span("http:get_user") as span:
            headers = {}
            inject(headers)  # Inject trace context into headers

            try:
                response = await client.get(
                    "http://localhost:8001/users/{user_id}",
                    headers=headers
                )
                user_data = response.json()
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

        # Call Service C to process payment
        with tracer.start_as_current_span("http:process_payment") as span:
            headers = {}
            inject(headers)  # Inject trace context into headers

            span.set_attribute("payment.amount", amount)

            try:
                response = await client.post(
                    "http://localhost:8002/payments",
                    json={"user_id": user_id, "amount": amount},
                    headers=headers
                )
                payment_data = response.json()
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    return {
        "trace_id": current_trace_id,
        "user": user_data,
        "payment": payment_data,
        "status": "checkout_complete",
    }


@service_a.get("/users/{user_id}")
async def get_user_from_a(user_id: int):
    """Proxy user request to Service B."""
    from opentelemetry.propagate import inject

    async with httpx.AsyncClient() as client:
        headers = {}
        inject(headers)

        response = await client.get(
            f"http://localhost:8001/users/{user_id}",
            headers=headers
        )
        return response.json()


# ===== SERVICE B: User Service =====

@service_b.get("/")
async def service_b_root():
    """Root endpoint of User Service."""
    return {"service": "service-b (User Service)"}


@service_b.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    Get user by ID.

    This service receives the traceparent header from Service A
    and continues the trace with a child span.
    """
    # Get trace ID from incoming request context
    trace_id = get_trace_id()

    # Simulate user lookup
    if user_id != 1:
        raise UserNotFoundException(
            detail={
                "user_id": user_id,
                "trace_id": trace_id,
                "service": "service-b"
            }
        )

    return {
        "user_id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "trace_id": trace_id,
        "service": "service-b",
    }


# ===== SERVICE C: Payment Service =====

@service_c.get("/")
async def service_c_root():
    """Root endpoint of Payment Service."""
    return {"service": "service-c (Payment Service)"}


@service_c.post("/payments")
async def process_payment(user_id: int, amount: float):
    """
    Process payment.

    This service receives the traceparent header from Service A
    and continues the trace with a child span.
    """
    from opentelemetry import trace

    # Get current span
    current_span = trace.get_current_span()
    trace_id = get_trace_id()

    # Add custom attributes
    if current_span.is_recording():
        current_span.set_attribute("payment.user_id", user_id)
        current_span.set_attribute("payment.amount", amount)
        current_span.set_attribute("payment.currency", "USD")

    # Simulate payment processing
    if amount > 1000:
        raise PaymentFailedException(
            detail={
                "amount": amount,
                "reason": "amount_exceeded",
                "limit": 1000,
                "trace_id": trace_id,
                "service": "service-c"
            }
        )

    return {
        "payment_id": "pay_12345",
        "amount": amount,
        "status": "completed",
        "trace_id": trace_id,
        "service": "service-c",
    }


# ===== Helper to run all services =====

async def run_services():
    """Run all three services concurrently."""
    import uvicorn

    print("=" * 60)
    print("Cross-Service Distributed Tracing Example")
    print("=" * 60)
    print("\nArchitecture:")
    print("  Service A (port 8000) - API Gateway")
    print("    ├── calls Service B for user data")
    print("    └── calls Service C for payment processing")
    print("\n  Service B (port 8001) - User Service")
    print("  Service C (port 8002) - Payment Service")
    print("\nTo view the complete distributed trace:")
    print("  1. Start Jaeger: docker run -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one")
    print("  2. Open Jaeger UI: http://localhost:16686")
    print("  3. Select service: service-a")
    print("  4. Search for traces")
    print("\nExample request flow:")
    print("  1. POST http://localhost:8000/checkout?user_id=1&amount=100")
    print("  2. Service A creates root span")
    print("  3. Service A calls Service B (child span)")
    print("  4. Service A calls Service C (child span)")
    print("  5. All spans share the same trace_id")
    print("\nTrace Context Propagation:")
    print("  - traceparent header automatically injected")
    print("  - W3C Trace Context standard")
    print("  - Child spans linked to parent spans")
    print("=" * 60)

    # Run services in background tasks
    config = uvicorn.Config(app=service_a, host="127.0.0.1", port=8000, log_level="info")
    server_a = uvicorn.Server(config)

    config = uvicorn.Config(app=service_b, host="127.0.0.1", port=8001, log_level="info")
    server_b = uvicorn.Server(config)

    config = uvicorn.Config(app=service_c, host="127.0.0.1", port=8002, log_level="info")
    server_c = uvicorn.Server(config)

    # Start all servers
    task_a = asyncio.create_task(server_a.serve())
    task_b = asyncio.create_task(server_b.serve())
    task_c = asyncio.create_task(server_c.serve())

    try:
        await asyncio.gather(task_a, task_b, task_c)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(run_services())
