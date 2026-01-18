"""
FastAPI integration for distributed tracing

Provides setup_tracing() function for automatic tracing:
- FastAPI middleware for automatic span creation
- Integration with setup_exception_handler()
- Trace ID ↔ Metrics correlation
- Trace ID in error responses
"""

from typing import Any, Optional

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from fastapi_error_codes.metrics import ErrorMetricsCollector
from fastapi_error_codes.models import ErrorResponse
from fastapi_error_codes.tracing.config import TracingConfig
from fastapi_error_codes.tracing.exceptions import ExceptionTracer, PIIMasker
from fastapi_error_codes.tracing.exporters import create_exporter
from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration


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
    # Wrap in BatchSpanProcessor for efficient export
    exporter = create_exporter(exporter_type, config)
    batch_processor = BatchSpanProcessor(exporter.underlying_exporter)
    integration.tracer_provider.add_span_processor(batch_processor)

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

    Note: Uses FastAPIInstrumentor for proper FastAPI integration.
    Custom middleware adds X-Trace-ID header after span creation.
    """
    # Instrument FastAPI app with OpenTelemetry
    # This creates spans automatically for all HTTP requests
    FastAPIInstrumentor.instrument_app(app)

    # Add custom middleware to add X-Trace-ID header
    # FastAPI middleware runs in LIFO order (last added runs first)
    @app.middleware("http")
    async def add_trace_id_to_response(request: Request, call_next):
        """Extract trace ID from context and add to response headers."""

        # Process request (span is created by FastAPIInstrumentor)
        response = await call_next(request)

        # Add trace ID to response headers if available
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            if span_context.is_valid:
                trace_id = format(span_context.trace_id, "032x")
                response.headers["X-Trace-ID"] = trace_id

        return response


def _setup_exception_handler_integration(
    app: FastAPI,
    exception_tracer: Optional[ExceptionTracer]
) -> None:
    """
    Integrate tracing with exception handler.

    This function stores the exception tracer in app state for use by
    the existing exception handler. The exception handler can access it
    via app.state.exception_tracer to record exceptions in spans.

    Args:
        app: FastAPI application instance
        exception_tracer: Optional exception tracer
    """
    # Store exception_tracer in app state for use in exception handler
    # The existing setup_exception_handler can access it via app.state.exception_tracer
    if exception_tracer:
        app.state.exception_tracer = exception_tracer

    # Note: We don't register a new exception handler here because:
    # 1. The user should call setup_exception_handler() first
    # 2. The setup_exception_handler can access app.state.exception_tracer
    # 3. Registering a new handler here could cause recursion
    #
    # If the user wants exception recording in spans, they should:
    # 1. Call setup_exception_handler(app, config)
    # 2. Call setup_tracing(app, tracing_config, enable_exception_tracing=True)
    #
    # The exception handler can then use app.state.exception_tracer if available


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
    error_name: str,
    status_code: int,
    message: str,
    metrics_collector: Optional[ErrorMetricsCollector] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
    detail: Any = None,
) -> None:
    """
    Correlate error with metrics using trace ID.

    Args:
        error_code: Error code from exception
        error_name: Exception class name
        status_code: HTTP status code
        message: Error message
        metrics_collector: Optional metrics collector
        path: Request path (optional)
        method: HTTP method (optional)
        detail: Additional error details (optional)
    """
    trace_id = get_trace_id()
    if trace_id and metrics_collector:
        # Add trace_id to detail for correlation
        enhanced_detail = detail or {}
        if isinstance(enhanced_detail, dict):
            enhanced_detail = dict(enhanced_detail)  # Make a copy
            enhanced_detail["trace_id"] = trace_id
        else:
            enhanced_detail = {"trace_id": trace_id, "value": enhanced_detail}

        # Record metric with trace_id in detail
        metrics_collector.record(
            error_code=error_code,
            error_name=error_name,
            status_code=status_code,
            message=message,
            detail=enhanced_detail,
            path=path,
            method=method,
        )
