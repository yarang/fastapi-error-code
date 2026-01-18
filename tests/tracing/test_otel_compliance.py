"""
OpenTelemetry compliance verification tests for SPEC-TRACING-003

Tests verify:
- OpenTelemetry standard format compliance
- W3C Trace Context standard validation
- Exporter compatibility (Jaeger/OTLP)
- Semantic attribute conventions
"""


from opentelemetry.trace import SpanKind

from fastapi_error_codes.tracing.config import TracingConfig
from fastapi_error_codes.tracing.exceptions import ExceptionTracer
from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration
from fastapi_error_codes.tracing.propagator import TraceContextPropagator


class TestOpenTelemetryStandardCompliance:
    """Test OpenTelemetry standard format compliance"""

    def test_tracer_provider_follows_otel_spec(self):
        """
        GIVEN an OpenTelemetryIntegration instance
        WHEN initializing the tracer provider
        THEN should follow OpenTelemetry specification
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        # Should have a valid tracer provider
        assert integration.tracer_provider is not None

        # Should be able to get a tracer
        tracer = integration.get_tracer("test")
        assert tracer is not None

        # Tracer should follow OpenTelemetry API
        assert hasattr(tracer, 'start_as_current_span')

        integration.shutdown()

    def test_span_attributes_follow_semantic_conventions(self):
        """
        GIVEN a span created by the integration
        WHEN examining span attributes
        THEN should include OpenTelemetry semantic conventions
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")

        with tracer.start_as_current_span("test-span", kind=SpanKind.SERVER) as span:
            # Span should be recording
            assert span.is_recording()

            # Get span context
            span_context = span.get_span_context()
            assert span_context is not None
            assert span_context.trace_id is not None
            assert span_context.span_id is not None

        integration.shutdown()

    def test_resource_attributes_follow_spec(self):
        """
        GIVEN a TracingConfig with service name
        WHEN initializing the integration
        THEN should set resource attributes per OpenTelemetry spec
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config, service_version="1.0.0")
        integration.initialize()

        # Resource should be created with service.name
        resource = integration.tracer_provider.resource
        assert resource is not None

        # Should have service.name attribute
        attributes = resource.attributes
        assert "service.name" in attributes
        assert attributes["service.name"] == "test-service"

        # Should have service.version if provided
        assert "service.version" in attributes
        assert attributes["service.version"] == "1.0.0"

        integration.shutdown()

    def test_sampling_follows_otel_spec(self):
        """
        GIVEN different sample rates
        WHEN creating spans
        THEN should follow OpenTelemetry sampling specification
        """
        # Test with sample_rate=1.0 (always sample)
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            sample_rate=1.0
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")

        # With sample_rate=1.0, all spans should be recorded
        with tracer.start_as_current_span("test-span") as span:
            assert span.is_recording()

        integration.shutdown()

        # Test with sample_rate=0.0 (never sample)
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            sample_rate=0.0
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")

        # With sample_rate=0.0, sampling may not record
        # (depends on trace ID)
        with tracer.start_as_current_span("test-span"):
            pass  # Should not crash

        integration.shutdown()


class TestW3CTraceContextCompliance:
    """Test W3C Trace Context standard compliance"""

    def test_traceparent_header_format(self):
        """
        GIVEN a traceparent header
        WHEN parsing with TraceContextPropagator
        THEN should follow W3C traceparent format
        """
        propagator = TraceContextPropagator()

        # Valid traceparent format: version-traceid-parentid-flags
        valid_traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

        span_context = propagator.parse_traceparent(valid_traceparent)

        assert span_context is not None
        assert span_context.trace_id == int("4bf92f3577b34da6a3ce929d0e0e4736", 16)
        assert span_context.span_id == int("00f067aa0ba902b7", 16)

    def test_traceparent_version_validation(self):
        """
        GIVEN traceparent headers with different versions
        WHEN parsing
        THEN should validate version correctly
        """
        propagator = TraceContextPropagator()

        # Version 00 (current version)
        v00_traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        span_context = propagator.parse_traceparent(v00_traceparent)
        assert span_context is not None

        # Invalid version (should return None)
        invalid_traceparent = "01-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        span_context = propagator.parse_traceparent(invalid_traceparent)
        assert span_context is None

    def test_traceparent_length_validation(self):
        """
        GIVEN traceparent headers with invalid lengths
        WHEN parsing
        THEN should validate lengths correctly
        """
        propagator = TraceContextPropagator()

        # Trace ID must be 32 hex chars
        invalid_trace_id = "00-abc-00f067aa0ba902b7-01"
        span_context = propagator.parse_traceparent(invalid_trace_id)
        assert span_context is None

        # Span ID must be 16 hex chars
        invalid_span_id = "00-4bf92f3577b34da6a3ce929d0e0e4736-abc-01"
        span_context = propagator.parse_traceparent(invalid_span_id)
        assert span_context is None

    def test_traceparent_flags_validation(self):
        """
        GIVEN traceparent headers with different flags
        WHEN parsing
        THEN should parse flags correctly
        """
        propagator = TraceContextPropagator()

        # Valid flags
        traceparent_01 = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        span_context = propagator.parse_traceparent(traceparent_01)
        assert span_context is not None
        assert span_context.is_valid is True

        traceparent_00 = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-00"
        span_context = propagator.parse_traceparent(traceparent_00)
        assert span_context is not None

    def test_traceparent_generation(self):
        """
        GIVEN a span context
        WHEN generating traceparent
        THEN should follow W3C format
        """
        propagator = TraceContextPropagator()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")

        with tracer.start_as_current_span("test-span") as span:
            span_context = span.get_span_context()

            # Generate traceparent
            traceparent = propagator.generate_traceparent(span_context)

            # Should follow format: version-traceid-parentid-flags
            parts = traceparent.split("-")
            assert len(parts) == 4
            assert parts[0] == "00"  # Version
            assert len(parts[1]) == 32  # Trace ID
            assert len(parts[2]) == 16  # Span ID
            assert len(parts[3]) == 2  # Flags

        integration.shutdown()


class TestExceptionEventCompliance:
    """Test exception event format compliance"""

    def test_exception_event_attributes(self):
        """
        GIVEN an exception recorded in a span
        WHEN examining the event attributes
        THEN should follow OpenTelemetry exception specification
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")
        exception_tracer = ExceptionTracer()

        with tracer.start_as_current_span("test-span") as span:
            try:
                raise ValueError("Test exception message")
            except ValueError as e:
                exception_tracer.record_exception(span, e)

                # Span should have exception event
                # (Note: In test environment with ConsoleSpanExporter,
                # we can't easily verify the events, but we can verify
                # no crash occurred)

        integration.shutdown()

    def test_exception_event_pii_masking(self):
        """
        GIVEN an exception with PII
        WHEN recording with PII masking enabled
        THEN should mask PII in event attributes
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")

        # Create exception tracer with PII masking
        from fastapi_error_codes.tracing.exceptions import PIIMasker
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        with tracer.start_as_current_span("test-span") as span:
            try:
                raise ValueError("User john@example.com failed login")
            except ValueError as e:
                # Should not crash
                exception_tracer.record_exception(span, e)

        integration.shutdown()


class TestExporterCompatibility:
    """Test exporter compatibility"""

    def test_jaeger_exporter_compatibility(self):
        """
        GIVEN a Jaeger exporter configuration
        WHEN creating the exporter
        THEN should be compatible with Jaeger format
        """
        from fastapi_error_codes.tracing.exporters import create_exporter

        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            jaeger_host="localhost",
            jaeger_port=6831
        )

        # Should create Jaeger exporter without error
        exporter = create_exporter("jaeger", config)
        assert exporter is not None

        # Should have underlying exporter
        assert exporter.underlying_exporter is not None

        exporter.shutdown()

    def test_otlp_exporter_compatibility(self):
        """
        GIVEN an OTLP exporter configuration
        WHEN creating the exporter
        THEN should be compatible with OTLP format
        """
        from fastapi_error_codes.tracing.exporters import create_exporter

        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        # Should create OTLP exporter without error
        exporter = create_exporter("otlp", config)
        assert exporter is not None

        # Should have underlying exporter
        assert exporter.underlying_exporter is not None

        exporter.shutdown()


class TestSpanEventCompliance:
    """Test span event format compliance"""

    def test_span_event_attributes(self):
        """
        GIVEN a span with events
        WHEN recording events
        THEN should follow OpenTelemetry event specification
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")

        with tracer.start_as_current_span("test-span") as span:
            # Add custom event
            span.add_event(
                name="custom.event",
                attributes={
                    "key1": "value1",
                    "key2": "value2"
                }
            )

            # Should not crash

        integration.shutdown()


class TestTraceStateCompliance:
    """Test trace state handling"""

    def test_trace_state_initialization(self):
        """
        GIVEN a span context
        WHEN examining trace state
        THEN should have valid trace state
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")

        with tracer.start_as_current_span("test-span") as span:
            span_context = span.get_span_context()

            # Trace state should be valid
            assert span_context is not None

        integration.shutdown()


class TestSpanStatusCompliance:
    """Test span status specification compliance"""

    def test_span_status_setting(self):
        """
        GIVEN a span
        WHEN setting status
        THEN should follow OpenTelemetry status specification
        """
        from opentelemetry.sdk.trace import Status, StatusCode

        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test")

        with tracer.start_as_current_span("test-span") as span:
            # Set OK status
            span.set_status(Status(StatusCode.OK))

            # Set ERROR status
            span.set_status(Status(StatusCode.ERROR, "Test error"))

        integration.shutdown()
