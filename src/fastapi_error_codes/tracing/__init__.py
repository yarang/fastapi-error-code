"""
Distributed tracing system for fastapi-error-codes

This module provides OpenTelemetry-based distributed tracing:
- TracingConfig: Frozen configuration with validation
- OpenTelemetryIntegration: SDK wrapper for initialization
- Exporters: Jaeger and OTLP exporters
- Exception tracing: Automatic exception event recording
- PII masking: Sensitive data masking in spans
- Trace context propagation: W3C trace context support
- FastAPI integration: Automatic tracing middleware

Basic Usage:
    from fastapi import FastAPI
    from fastapi_error_codes.tracing import TracingConfig, setup_tracing

    app = FastAPI()
    config = TracingConfig(
        service_name="my-service",
        endpoint="http://localhost:4317"
    )
    integration = setup_tracing(app, config)
"""

from fastapi_error_codes.tracing.config import TracingConfig
from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration
from fastapi_error_codes.tracing.exporters import (
    JaegerExporter,
    OTLPExporter,
    ExporterConfig,
    create_exporter
)
from fastapi_error_codes.tracing.exceptions import (
    ExceptionTracer,
    PIIMasker,
    PIIPattern,
    sanitize_stacktrace
)
from fastapi_error_codes.tracing.propagator import (
    TraceContextPropagator
)
from fastapi_error_codes.tracing.integration import (
    setup_tracing,
    get_trace_id,
    add_trace_id_to_error_response,
    correlate_trace_with_metrics
)

__all__ = [
    # Configuration
    "TracingConfig",
    # Core integration
    "OpenTelemetryIntegration",
    "setup_tracing",
    # Exporters
    "JaegerExporter",
    "OTLPExporter",
    "ExporterConfig",
    "create_exporter",
    # Exception tracing
    "ExceptionTracer",
    "PIIMasker",
    "PIIPattern",
    "sanitize_stacktrace",
    # Context propagation
    "TraceContextPropagator",
    # Utilities
    "get_trace_id",
    "add_trace_id_to_error_response",
    "correlate_trace_with_metrics",
]
