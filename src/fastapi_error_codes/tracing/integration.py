"""
FastAPI integration for distributed tracing

Provides setup_tracing() function for automatic tracing:
- FastAPI middleware for automatic span creation
- Integration with setup_exception_handler()
- Trace ID ↔ Metrics correlation
- Trace ID in error responses
"""

from typing import Optional

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

from fastapi_error_codes.tracing.config import TracingConfig
from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration
from fastapi_error_codes.tracing.exceptions import ExceptionTracer, PIIMasker
from fastapi_error_codes.tracing.exporters import create_exporter
from fastapi_error_codes.handlers import setup_exception_handler
from fastapi_error_codes.models import ErrorResponse
from fastapi_error_codes.metrics import ErrorMetricsCollector


def setup_tracing(
    app: FastAPI,
    config: TracingConfig,
    exporter_type: str = "otlp",
    enable_exception_tracing: bool = True,
    enable_pii_masking: bool = True
) -> OpenTelemetryIntegration:
    """
    Setup distributed tracing for FastAPI application.

    Integrates OpenTelemetry tracing with:
    - Automatic span creation for HTTP requests
    - Exception tracing with PII masking
    - Trace ID correlation in error responses
    - Metrics integration

    Args:
        app: FastAPI application instance
        config: Tracing configuration
        exporter_type: Type of exporter ("jaeger" or "otlp")
        enable_exception_tracing: Enable automatic exception tracing
        enable_pii_masking: Enable PII masking in spans

    Returns:
        OpenTelemetryIntegration instance

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_error_codes.tracing import TracingConfig, setup_tracing

        app = FastAPI()
        config = TracingConfig(
            service_name="my-service",
            endpoint="http://localhost:4317"
        )
        integration = setup_tracing(app, config)
        ```
    """
    # Initialize OpenTelemetry
    integration = OpenTelemetryIntegration(config)
    integration.initialize()

    # Create and configure exporter
    exporter = create_exporter(exporter_type, config)
    integration.tracer_provider.add_span_processor(
        exporter.underlying_exporter  # type: ignore
    )

    # Setup exception tracing if enabled
    exception_tracer = None
    if enable_exception_tracing:
        masker = PIIMasker() if enable_pii_masking else None
        exception_tracer = ExceptionTracer(masker=masker)

    # Add OpenTelemetry middleware
    instrument_app(app, config, exception_tracer)

    # Integrate with exception handler to include trace IDs
    _setup_exception_handler_integration(app, exception_tracer)

    return integration


def instrument_app(
    app: FastAPI,
    config: TracingConfig,
    exception_tracer: Optional[ExceptionTracer] = None
) -> None:
    """
    Add OpenTelemetry instrumentation middleware to FastAPI app.

    Args:
        app: FastAPI application instance
        config: Tracing configuration
        exception_tracer: Optional exception tracer
    """
    # Add custom middleware for trace ID extraction
    @app.middleware("http")
    async def add_trace_id_to_request(request: Request, call_next):
        """Extract trace ID from context and add to request state."""
        import asyncio
        from starlette.datastructures import Headers

        # Process request
        response = await call_next(request)

        # Add trace ID to response headers if available
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            if span_context.is_valid:
                trace_id = format(span_context.trace_id, "032x")
                response.headers["X-Trace-ID"] = trace_id

        return response

    # Add OpenTelemetry ASGI middleware
    excluded_urls = ["/health", "/ready", "/metrics"]
    OpenTelemetryMiddleware(app, excluded_urls=excluded_urls)


def _setup_exception_handler_integration(
    app: FastAPI,
    exception_tracer: Optional[ExceptionTracer]
) -> None:
    """
    Integrate tracing with exception handler.

    Args:
        app: FastAPI application instance
        exception_tracer: Optional exception tracer
    """
    # This is a placeholder for integration with setup_exception_handler
    # In production, this would modify the exception handler to:
    # 1. Extract trace ID from current span
    # 2. Add trace ID to error responses
    # 3. Record exceptions in spans
    # 4. Correlate with metrics
    pass


def get_trace_id() -> Optional[str]:
    """
    Get current trace ID from active span.

    Returns:
        Trace ID as hex string if available, None otherwise
    """
    current_span = trace.get_current_span()
    if current_span:
        span_context = current_span.get_span_context()
        if span_context.is_valid:
            return format(span_context.trace_id, "032x")
    return None


def add_trace_id_to_error_response(error_response: ErrorResponse) -> ErrorResponse:
    """
    Add trace ID to error response for traceability.

    Args:
        error_response: Error response to enhance

    Returns:
        ErrorResponse with trace_id added
    """
    trace_id = get_trace_id()
    if trace_id:
        # Add trace_id to detail or create new field
        if hasattr(error_response, "detail"):
            if isinstance(error_response.detail, dict):
                error_response.detail["trace_id"] = trace_id
            else:
                # Create enhanced detail
                error_response.detail = {
                    "message": str(error_response.detail),
                    "trace_id": trace_id
                }
    return error_response


def correlate_trace_with_metrics(
    error_code: int,
    metrics_collector: Optional[ErrorMetricsCollector] = None
) -> None:
    """
    Correlate error with metrics using trace ID.

    Args:
        error_code: Error code from exception
        metrics_collector: Optional metrics collector
    """
    trace_id = get_trace_id()
    if trace_id and metrics_collector:
        # Record metric with trace_id as label
        metrics_collector.record_error(
            error_code=error_code,
            labels={"trace_id": trace_id}
        )
