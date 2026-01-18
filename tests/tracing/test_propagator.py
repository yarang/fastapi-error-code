"""
Test suite for trace context propagation (Phase 5: RED)

Tests TraceContextPropagator:
- W3C traceparent header parsing
- Trace context extraction from headers
- Trace context injection to headers
- Cross-service tracing support
"""

from opentelemetry.trace import SpanContext

from fastapi_error_codes.tracing.propagator import TraceContextPropagator


class TestTraceContextPropagator:
    """Test trace context propagation"""

    def test_parse_valid_traceparent(self):
        """WHEN valid traceparent provided, THEN should parse successfully"""
        propagator = TraceContextPropagator()
        traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

        context = propagator.parse_traceparent(traceparent)
        assert context is not None
        assert context.trace_id == int("4bf92f3577b34da6a3ce929d0e0e4736", 16)
        assert context.span_id == int("00f067aa0ba902b7", 16)

    def test_parse_invalid_traceparent_wrong_format(self):
        """WHEN traceparent has wrong format, THEN should return None"""
        propagator = TraceContextPropagator()
        traceparent = "invalid-format"

        context = propagator.parse_traceparent(traceparent)
        assert context is None

    def test_parse_invalid_traceparent_wrong_length(self):
        """WHEN traceparent has wrong length, THEN should return None"""
        propagator = TraceContextPropagator()
        traceparent = "00-1234-5678-01"  # Too short

        context = propagator.parse_traceparent(traceparent)
        assert context is None

    def test_generate_traceparent(self):
        """WHEN span context provided, THEN should generate valid traceparent"""
        propagator = TraceContextPropagator()
        context = SpanContext(
            trace_id=int("4bf92f3577b34da6a3ce929d0e0e4736", 16),
            span_id=int("00f067aa0ba902b7", 16),
            is_remote=False
        )

        traceparent = propagator.generate_traceparent(context)
        assert traceparent == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

    def test_extract_from_headers(self):
        """WHEN headers contain traceparent, THEN should extract context"""
        propagator = TraceContextPropagator()
        headers = {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        }

        context = propagator.extract(headers)
        assert context is not None

    def test_extract_from_empty_headers(self):
        """WHEN headers empty, THEN should return None"""
        propagator = TraceContextPropagator()
        headers = {}

        context = propagator.extract(headers)
        assert context is None

    def test_inject_to_headers(self):
        """WHEN context injected, THEN should add traceparent to headers"""
        from fastapi_error_codes.tracing.config import TracingConfig
        from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration

        config = TracingConfig(service_name="test", endpoint="http://localhost:4317")
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer(__name__)

        # Create a span to have active trace context
        with tracer.start_as_current_span("test-span"):
            propagator = TraceContextPropagator()
            headers = {}
            propagator.inject(headers)

            assert "traceparent" in headers
            assert headers["traceparent"].startswith("00-")

        integration.shutdown()
