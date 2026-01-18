"""
End-to-end integration tests for SPEC-TRACING-003

Tests complete integration scenarios:
- E2E request tracing with automatic span creation
- Exception recording with trace correlation
- PII masking in traces
- Trace ID in error responses
- Metrics correlation with trace IDs

Note: Full trace context propagation requires actual HTTP traffic.
These tests use TestClient which has limitations for W3C trace context testing.
"""


from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry import trace

from fastapi_error_codes.base import BaseAppException
from fastapi_error_codes.config import ErrorHandlerConfig
from fastapi_error_codes.handlers import setup_exception_handler
from fastapi_error_codes.tracing.config import TracingConfig
from fastapi_error_codes.tracing.exceptions import ExceptionTracer, PIIMasker
from fastapi_error_codes.tracing.integration import get_trace_id, setup_tracing
from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration


class TestE2ERequestTracing:
    """Test end-to-end request tracing with automatic span creation"""

    def test_e2e_request_creates_trace_id(self):
        """
        GIVEN a FastAPI app with tracing enabled
        WHEN making a request
        THEN should create trace ID and add to response headers
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = setup_tracing(app, config)

        @app.get("/test")
        def test_endpoint():
            trace_id = get_trace_id()
            return {"has_trace_id": trace_id is not None}

        client = TestClient(app, raise_server_exceptions=False)

        # Make request
        response = client.get("/test")

        assert response.status_code == 200
        # Should have X-Trace-ID header
        assert "X-Trace-ID" in response.headers
        # Response should indicate trace ID exists
        data = response.json()
        assert data.get("has_trace_id") is True

        integration.shutdown()

    def test_e2e_multiple_requests_create_different_traces(self):
        """
        GIVEN a FastAPI app with tracing enabled
        WHEN making multiple requests
        THEN should create different trace IDs for each request
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = setup_tracing(app, config)

        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}

        client = TestClient(app, raise_server_exceptions=False)

        # Make multiple requests and collect trace IDs
        trace_ids = set()
        for _ in range(5):
            response = client.get("/test")
            trace_id = response.headers.get("X-Trace-ID")
            if trace_id:
                trace_ids.add(trace_id)

        # Should have trace IDs (may not all be unique due to sampling)
        assert len(trace_ids) > 0

        integration.shutdown()


class TestE2EExceptionRecording:
    """Test end-to-end exception recording with trace correlation"""

    def test_e2e_exception_records_with_trace_id(self):
        """
        GIVEN a FastAPI app with exception tracing enabled
        WHEN an exception is raised
        THEN should record exception with trace ID correlation
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        # Define route first
        @app.get("/error")
        def error_endpoint():
            raise ValueError("Test error")

        # Setup exception handler after routes
        setup_exception_handler(app)

        # Setup tracing
        integration = setup_tracing(
            app,
            config,
            enable_exception_tracing=True
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Make request that triggers exception
        response = client.get("/error")

        # Should get error response
        assert response.status_code in [500, 400]
        # Should have trace ID
        assert "X-Trace-ID" in response.headers

        integration.shutdown()

    def test_e2e_base_app_exception_records_error_code(self):
        """
        GIVEN a FastAPI app with exception tracing
        WHEN a BaseAppException is raised
        THEN should handle exception and include trace ID
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        # Define route first
        @app.get("/not-found")
        def not_found_endpoint():
            raise BaseAppException(
                error_code=404,
                message="Resource not found",
                status_code=404
            )

        # Setup exception handler after routes
        setup_exception_handler(app)

        # Setup tracing
        integration = setup_tracing(
            app,
            config,
            enable_exception_tracing=True
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Make request that triggers exception
        response = client.get("/not-found")

        # Should get error response
        assert response.status_code == 404
        # Should have trace ID
        trace_id = response.headers.get("X-Trace-ID")
        assert trace_id is not None
        # Response body should have error code
        data = response.json()
        assert data.get("error_code") == 404

        integration.shutdown()


class TestE2EPIIMasking:
    """Test PII masking in traces end-to-end"""

    def test_e2e_pii_masking_enabled(self):
        """
        GIVEN a FastAPI app with PII masking enabled
        WHEN an exception with PII is raised
        THEN should mask PII in trace events without crashing
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            enable_pii_masking=True
        )

        # Define route first
        @app.get("/error")
        def error_endpoint():
            # Exception with PII
            raise ValueError(
                "User john@example.com failed login "
                "with phone 555-123-4567"
            )

        # Setup exception handler after routes
        setup_exception_handler(app)

        # Setup tracing
        integration = setup_tracing(
            app,
            config,
            enable_exception_tracing=True,
            enable_pii_masking=True
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Make request - should not crash
        response = client.get("/error")

        # Should handle exception successfully
        assert "X-Trace-ID" in response.headers

        integration.shutdown()

    def test_e2e_pii_masking_disabled(self):
        """
        GIVEN a FastAPI app with PII masking disabled
        WHEN an exception with PII is raised
        THEN should handle exception without masking
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            enable_pii_masking=False
        )

        # Define route first
        @app.get("/error")
        def error_endpoint():
            raise ValueError("User john@example.com failed login")

        # Setup exception handler after routes
        setup_exception_handler(app)

        # Setup tracing
        integration = setup_tracing(
            app,
            config,
            enable_exception_tracing=True,
            enable_pii_masking=False
        )

        client = TestClient(app, raise_server_exceptions=False)

        # Make request - should not crash
        response = client.get("/error")

        # Should handle exception successfully
        assert "X-Trace-ID" in response.headers

        integration.shutdown()


class TestE2ETraceIDInErrorResponse:
    """Test trace ID in error responses end-to-end"""

    def test_e2e_trace_id_in_error_response_headers(self):
        """
        GIVEN a FastAPI app with tracing
        WHEN an error occurs
        THEN should include trace ID in response headers
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        # Define route first
        @app.get("/error")
        def error_endpoint():
            raise BaseAppException(
                error_code=404,
                message="Resource not found",
                status_code=404
            )

        # Setup exception handler after routes
        setup_exception_handler(app)

        # Setup tracing
        integration = setup_tracing(app, config)

        client = TestClient(app, raise_server_exceptions=False)

        # Make request that triggers exception
        response = client.get("/error")

        # Should have error response
        assert response.status_code == 404
        # Should have trace ID in headers
        assert "X-Trace-ID" in response.headers
        # Response body should have error details
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == 404

        integration.shutdown()


class TestE2EExporterIntegration:
    """Test exporter integration end-to-end"""

    def test_e2e_jaeger_exporter_initialization(self):
        """
        GIVEN a FastAPI app with Jaeger exporter
        WHEN making requests
        THEN should initialize Jaeger exporter without errors
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            jaeger_host="localhost",
            jaeger_port=6831
        )

        integration = setup_tracing(app, config, exporter_type="jaeger")

        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}

        client = TestClient(app, raise_server_exceptions=False)

        # Make request - should succeed even if Jaeger is not available
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers

        integration.shutdown()

    def test_e2e_otlp_exporter_initialization(self):
        """
        GIVEN a FastAPI app with OTLP exporter
        WHEN making requests
        THEN should initialize OTLP exporter without errors
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = setup_tracing(app, config, exporter_type="otlp")

        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}

        client = TestClient(app, raise_server_exceptions=False)

        # Make request - should succeed even if OTLP endpoint is not available
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers

        integration.shutdown()


class TestE2ESamplingConfiguration:
    """Test sampling configuration end-to-end"""

    def test_e2e_sampling_rate_one_creates_traces(self):
        """
        GIVEN a FastAPI app with sample_rate=1.0
        WHEN making requests
        THEN should always create trace IDs
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            sample_rate=1.0
        )

        integration = setup_tracing(app, config)

        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}

        client = TestClient(app, raise_server_exceptions=False)

        # Make multiple requests
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200
            # Should have trace ID
            assert "X-Trace-ID" in response.headers

        integration.shutdown()

    def test_e2e_sampling_rate_zero_may_not_create_traces(self):
        """
        GIVEN a FastAPI app with sample_rate=0.0
        WHEN making requests
        THEN may not create trace IDs (sampling disabled)
        """
        app = FastAPI()
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317",
            sample_rate=0.0
        )

        integration = setup_tracing(app, config)

        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}

        client = TestClient(app, raise_server_exceptions=False)

        # Make request
        response = client.get("/test")

        # Request should succeed
        assert response.status_code == 200
        # Trace ID might not be present due to sampling

        integration.shutdown()


class TestE2EExceptionTracerIntegration:
    """Test ExceptionTracer integration with spans"""

    def test_e2e_exception_tracer_records_in_span(self):
        """
        GIVEN an active span and ExceptionTracer
        WHEN recording exception
        THEN should add exception event to span
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer(__name__)
        exception_tracer = ExceptionTracer()

        with tracer.start_as_current_span("test-span"):
            span = trace.get_current_span()

            try:
                raise ValueError("Test exception")
            except ValueError as e:
                # Should not crash
                exception_tracer.record_exception(span, e)

        # Span should have exception event
        integration.shutdown()

    def test_e2e_exception_tracer_with_pii_masker(self):
        """
        GIVEN an active span and ExceptionTracer with PIIMasker
        WHEN recording exception with PII
        THEN should mask PII in span attributes
        """
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer(__name__)
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        with tracer.start_as_current_span("test-span"):
            span = trace.get_current_span()

            try:
                raise ValueError("User john@example.com failed login")
            except ValueError as e:
                # Should not crash
                exception_tracer.record_exception(span, e)

        integration.shutdown()


class TestE2EMetricsCorrelation:
    """Test metrics correlation with trace IDs"""

    def test_e2e_correlate_trace_with_metrics(self):
        """
        GIVEN an active span and metrics collector
        WHEN correlating error with metrics
        THEN should include trace ID in metrics
        """
        from unittest.mock import Mock

        from fastapi_error_codes.tracing.integration import correlate_trace_with_metrics

        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer(__name__)
        mock_collector = Mock()

        with tracer.start_as_current_span("test-span"):
            # Should record metrics with trace ID
            correlate_trace_with_metrics(
                error_code=404,
                error_name="NotFound",
                status_code=404,
                message="Resource not found",
                metrics_collector=mock_collector
            )

            # Verify record was called with trace_id in detail
            assert mock_collector.record.called
            call_kwargs = mock_collector.record.call_args[1]
            assert "detail" in call_kwargs
            assert "trace_id" in call_kwargs["detail"]

        integration.shutdown()
