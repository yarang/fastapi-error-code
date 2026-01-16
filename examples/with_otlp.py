"""
OTLP (OpenTelemetry Protocol) exporter example.

This example demonstrates:
1. Setting up tracing with OTLP exporter
2. Configuring OTLP endpoint
3. Integration with OpenTelemetry Collector
4. Compatibility with Grafana Tempo
"""

from fastapi import FastAPI
from fastapi_error_codes import BaseAppException, register_exception
from fastapi_error_codes.tracing import TracingConfig, setup_tracing

# Create FastAPI app
app = FastAPI(title="OTLP Tracing Example")

# Setup distributed tracing with OTLP exporter
tracing_config = TracingConfig(
    service_name="otlp-demo-service",
    endpoint="http://localhost:4317",  # OTLP endpoint (gRPC)
    sample_rate=1.0,
)

integration = setup_tracing(
    app,
    config=tracing_config,
    exporter_type="otlp",  # Use OTLP exporter
    enable_exception_tracing=True,
    enable_pii_masking=True,
)


# Define custom exceptions
@register_exception(error_code=401, message="Invalid API key", status_code=401)
class InvalidAPIKeyException(BaseAppException):
    """Raised when API key is invalid."""
    pass


@register_exception(error_code=429, message="Rate limit exceeded", status_code=429)
class RateLimitException(BaseAppException):
    """Raised when rate limit is exceeded."""
    pass


# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "OTLP tracing example",
        "service": "otlp-demo-service",
        "exporter": "OTLP",
        "endpoint": "http://localhost:4317",
    }


@app.get("/api/data")
async def get_data(api_key: str):
    """
    Get data - demonstrates exception tracing with API key masking.

    The API key in the exception detail will be masked before
    being recorded in the span.
    """
    # Simulate API key validation
    if not api_key or len(api_key) < 20:
        raise InvalidAPIKeyException(detail={"api_key": api_key})

    # Simulate data retrieval
    return {"data": [1, 2, 3, 4, 5], "source": "external-api"}


@app.get("/api/search")
async def search(query: str, limit: int = 10):
    """
    Search endpoint - demonstrates custom span attributes.

    This endpoint shows how to add custom attributes to spans
    for better observability.
    """
    from opentelemetry import trace

    current_span = trace.get_current_span()
    if current_span.is_recording():
        # Add custom attributes to the span
        current_span.set_attribute("search.query", query)
        current_span.set_attribute("search.limit", limit)
        current_span.set_attribute("search.result_count", min(limit, 100))

    # Simulate search
    if len(query) < 3:
        raise BaseAppException(
            error_code=401,
            message="Query too short",
            status_code=400,
            detail={"query": query, "min_length": 3},
        )

    results = [f"result-{i}" for i in range(min(limit, 100))]
    return {"query": query, "results": results, "count": len(results)}


@app.post("/api/batch")
async def batch_process(items: list):
    """
    Batch processing endpoint with custom child spans.

    Demonstrates creating child spans for better trace granularity.
    """
    from opentelemetry import trace

    tracer = trace.get_tracer(__name__)

    results = []

    with tracer.start_as_current_span("batch_processing") as parent:
        parent.set_attribute("batch.item_count", len(items))

        for i, item in enumerate(items):
            with tracer.start_as_current_span(f"process_item_{i}") as child:
                child.set_attribute("item.id", item.get("id", i))
                child.set_attribute("item.type", item.get("type", "unknown"))

                # Simulate processing
                result = {"id": item.get("id", i), "status": "processed"}
                results.append(result)

    return {"processed": len(results), "results": results}


@app.get("/api/protected")
async def protected_resource():
    """Protected resource - demonstrates rate limiting."""
    # Simulate rate limit check
    raise RateLimitException(
        detail={"limit": 100, "window": "1m", "retry_after": 30}
    )


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("OTLP Distributed Tracing Example")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  1. Start OpenTelemetry Collector:")
    print("     docker run -p 4317:4317 -v ./config.yaml:/etc/otelcol/config.yaml \\")
    print("       otel/opentelemetry-collector:latest")
    print("\n  2. Or start Grafana Tempo:")
    print("     docker run -p 4317:4317 -p 3200:3200 grafana/tempo:latest")
    print("\nAvailable endpoints:")
    print("  - GET /              : Root endpoint")
    print("  - GET /api/data      : Get data (API key required)")
    print("  - GET /api/search    : Search endpoint")
    print("  - POST /api/batch    : Batch processing")
    print("  - GET /api/protected : Rate limit demo")
    print("\nViewing traces:")
    print("  - Grafana Tempo: http://localhost:3200")
    print("  - Jaeger (if configured): http://localhost:16686")
    print("\nOTLP features:")
    print("  - OpenTelemetry Protocol (OTLP) export")
    print("  - gRPC transport")
    print("  - Compatible with Grafana Tempo")
    print("  - Retry logic with 3 attempts")
    print("  - Batch span processing")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
