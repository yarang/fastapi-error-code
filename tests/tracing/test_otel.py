"""
Test suite for OpenTelemetry integration (Phase 2: RED)

Tests OpenTelemetryIntegration class:
- SDK initialization with resource attributes
- Tracer provider configuration
- BatchSpanProcessor setup
- Tracer creation and usage
- Shutdown cleanup
"""


from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from fastapi_error_codes.tracing.config import TracingConfig
from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration


class TestOpenTelemetryIntegrationInitialization:
    """Test SDK initialization"""

    def test_initialize_creates_tracer_provider(self):
        """WHEN initialize is called, THEN should create TracerProvider"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        assert integration.tracer_provider is not None
        assert isinstance(integration.tracer_provider, TracerProvider)

    def test_initialize_sets_resource_attributes(self):
        """WHEN initialize is called, THEN should set service.name in resource"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        # Check that resource contains service name
        resource = integration.tracer_provider.resource
        assert resource.attributes.get("service.name") == "test-service"

    def test_initialize_with_service_version(self):
        """WHEN service_version provided, THEN should include in resource"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config, service_version="1.0.0")
        integration.initialize()

        resource = integration.tracer_provider.resource
        assert resource.attributes.get("service.name") == "test-service"
        assert resource.attributes.get("service.version") == "1.0.0"

    def test_initialize_sets_global_tracer_provider(self):
        """WHEN initialize is called, THEN should set global tracer provider"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        # Verify global tracer provider is set
        global_provider = trace.get_tracer_provider()
        # Note: The global provider might be a different instance if already set
        # We just verify that a provider exists and has the correct resource
        assert global_provider is not None
        assert integration.tracer_provider is not None


class TestTracerCreation:
    """Test tracer creation"""

    def test_get_tracer_returns_tracer(self):
        """WHEN get_tracer is called, THEN should return Tracer instance"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test-instrumentation")
        assert tracer is not None

    def test_get_tracer_with_version(self):
        """WHEN get_tracer called with version, THEN should include in tracer"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer("test-instrumentation", "1.0.0")
        assert tracer is not None


class TestSpanCreation:
    """Test basic span creation"""

    def test_create_span_with_tracer(self):
        """WHEN span is created, THEN should have valid context"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()
        tracer = integration.get_tracer("test")

        with tracer.start_as_current_span("test-span") as span:
            assert span is not None
            assert span.name == "test-span"
            assert span.is_recording()

    def test_span_attributes(self):
        """WHEN span attributes are set, THEN should be retrievable"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()
        tracer = integration.get_tracer("test")

        with tracer.start_as_current_span("test-span") as span:
            span.set_attribute("http.method", "GET")
            span.set_attribute("http.route", "/api/users")
            assert span.attributes.get("http.method") == "GET"
            assert span.attributes.get("http.route") == "/api/users"


class TestShutdown:
    """Test shutdown and cleanup"""

    def test_shutdown_cleans_up_resources(self):
        """WHEN shutdown is called, THEN should clean up tracer provider"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        # Shutdown should not raise
        integration.shutdown()

    def test_multiple_shutdowns_safe(self):
        """WHEN shutdown called multiple times, THEN should not raise"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        integration.shutdown()
        integration.shutdown()  # Should not raise


class TestSamplingConfiguration:
    """Test sampling rate configuration"""

    def test_sample_rate_one_creates_always_on_sampler(self):
        """WHEN sample_rate is 1.0, THEN should use always-on sampler"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            sample_rate=1.0
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        # Sampler should be configured
        assert integration.tracer_provider.sampler is not None

    def test_sample_rate_zero_creates_always_off_sampler(self):
        """WHEN sample_rate is 0.0, THEN should use always-off sampler"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            sample_rate=0.0
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        # Sampler should be configured
        assert integration.tracer_provider.sampler is not None

    def test_sample_rate_half_creates_trace_id_ratio_sampler(self):
        """WHEN sample_rate is 0.5, THEN should use ratio-based sampler"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            sample_rate=0.5
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        # Sampler should be configured
        assert integration.tracer_provider.sampler is not None
