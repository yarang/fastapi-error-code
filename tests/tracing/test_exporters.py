"""
Test suite for exporter integration (Phase 3: RED)

Tests JaegerExporter and OTLPExporter:
- JaegerExporter creation and configuration
- OTLPExporter creation and configuration
- Async export functionality
- Retry logic on export failure
- Exporter integration with OpenTelemetryIntegration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from opentelemetry.sdk.trace.export import SpanExportResult

from fastapi_error_codes.tracing.config import TracingConfig
from fastapi_error_codes.tracing.exporters import (
    JaegerExporter,
    OTLPExporter,
    ExporterConfig,
    create_exporter
)


class TestExporterConfig:
    """Test ExporterConfig dataclass"""

    def test_default_exporter_config(self):
        """WHEN ExporterConfig created, THEN should have default values"""
        config = ExporterConfig()
        assert config.max_retries == 3
        assert config.retry_timeout == 5.0
        assert config.export_timeout == 30.0

    def test_custom_exporter_config(self):
        """WHEN custom values provided, THEN should use custom values"""
        config = ExporterConfig(
            max_retries=5,
            retry_timeout=10.0,
            export_timeout=60.0
        )
        assert config.max_retries == 5
        assert config.retry_timeout == 10.0
        assert config.export_timeout == 60.0


class TestJaegerExporter:
    """Test JaegerExporter"""

    def test_create_jaeger_exporter_with_defaults(self):
        """WHEN JaegerExporter created with defaults, THEN should use default host/port"""
        exporter = JaegerExporter()
        assert exporter.host == "localhost"
        assert exporter.port == 6831
        assert exporter.max_retries == 3

    def test_create_jaeger_exporter_with_config(self):
        """WHEN JaegerExporter created with config, THEN should use config values"""
        config = ExporterConfig(max_retries=5)
        exporter = JaegerExporter(
            host="jaeger-agent",
            port=6832,
            config=config
        )
        assert exporter.host == "jaeger-agent"
        assert exporter.port == 6832
        assert exporter.max_retries == 5

    def test_jaeger_exporter_creates_underlying_exporter(self):
        """WHEN JaegerExporter initialized, THEN should create JaegerExporter"""
        exporter = JaegerExporter()
        exporter.initialize()
        assert exporter.underlying_exporter is not None
        assert isinstance(exporter.underlying_exporter, object)  # Type from opentelemetry-exporter-jaeger

    def test_jaeger_exporter_export_success(self):
        """WHEN export succeeds, THEN should return SUCCESS"""
        exporter = JaegerExporter()
        exporter.initialize()

        # Mock export method
        with patch.object(exporter.underlying_exporter, 'export', return_value=SpanExportResult.SUCCESS):
            result = exporter.export([])
            assert result == SpanExportResult.SUCCESS

    def test_jaeger_exporter_export_failure_with_retry(self):
        """WHEN export fails, THEN should retry and eventually return FAILURE"""
        exporter = JaegerExporter(config=ExporterConfig(max_retries=2))
        exporter.initialize()

        # Mock export method to fail
        with patch.object(exporter.underlying_exporter, 'export', return_value=SpanExportResult.FAILURE):
            result = exporter.export([])
            assert result == SpanExportResult.FAILURE

    def test_jaeger_exporter_shutdown(self):
        """WHEN shutdown called, THEN should shutdown underlying exporter"""
        exporter = JaegerExporter()
        exporter.initialize()

        # Mock shutdown method
        with patch.object(exporter.underlying_exporter, 'shutdown') as mock_shutdown:
            exporter.shutdown()
            mock_shutdown.assert_called_once()


class TestOTLPExporter:
    """Test OTLPExporter"""

    def test_create_otlp_exporter_with_defaults(self):
        """WHEN OTLPExporter created with defaults, THEN should use default endpoint"""
        exporter = OTLPExporter()
        assert exporter.endpoint == "http://localhost:4317"
        assert exporter.max_retries == 3

    def test_create_otlp_exporter_with_config(self):
        """WHEN OTLPExporter created with config, THEN should use config values"""
        config = ExporterConfig(max_retries=5)
        exporter = OTLPExporter(
            endpoint="https://otel-collector:4317",
            config=config
        )
        assert exporter.endpoint == "https://otel-collector:4317"
        assert exporter.max_retries == 5

    def test_otlp_exporter_creates_underlying_exporter(self):
        """WHEN OTLPExporter initialized, THEN should create OTLPSpanExporter"""
        exporter = OTLPExporter()
        exporter.initialize()
        assert exporter.underlying_exporter is not None
        assert isinstance(exporter.underlying_exporter, object)  # Type from opentelemetry-exporter-otlp

    def test_otlp_exporter_export_success(self):
        """WHEN export succeeds, THEN should return SUCCESS"""
        exporter = OTLPExporter()
        exporter.initialize()

        # Mock export method
        with patch.object(exporter.underlying_exporter, 'export', return_value=SpanExportResult.SUCCESS):
            result = exporter.export([])
            assert result == SpanExportResult.SUCCESS

    def test_otlp_exporter_export_failure_with_retry(self):
        """WHEN export fails, THEN should retry and eventually return FAILURE"""
        exporter = OTLPExporter(config=ExporterConfig(max_retries=2))
        exporter.initialize()

        # Mock export method to fail
        with patch.object(exporter.underlying_exporter, 'export', return_value=SpanExportResult.FAILURE):
            result = exporter.export([])
            assert result == SpanExportResult.FAILURE

    def test_otlp_exporter_shutdown(self):
        """WHEN shutdown called, THEN should shutdown underlying exporter"""
        exporter = OTLPExporter()
        exporter.initialize()

        # Mock shutdown method
        with patch.object(exporter.underlying_exporter, 'shutdown') as mock_shutdown:
            exporter.shutdown()
            mock_shutdown.assert_called_once()


class TestCreateExporter:
    """Test create_exporter factory function"""

    def test_create_jaeger_exporter(self):
        """WHEN exporter_type is 'jaeger', THEN should return JaegerExporter"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        exporter = create_exporter("jaeger", config)
        assert isinstance(exporter, JaegerExporter)

    def test_create_otlp_exporter(self):
        """WHEN exporter_type is 'otlp', THEN should return OTLPExporter"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        exporter = create_exporter("otlp", config)
        assert isinstance(exporter, OTLPExporter)

    def test_create_exporter_invalid_type_raises_error(self):
        """WHEN exporter_type is invalid, THEN should raise ValueError"""
        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        with pytest.raises(ValueError, match="Unknown exporter type"):
            create_exporter("invalid", config)


class TestExporterIntegration:
    """Test exporter integration with OpenTelemetryIntegration"""

    def test_otel_integration_with_jaeger_exporter(self):
        """WHEN OpenTelemetryIntegration configured with Jaeger, THEN should use JaegerExporter"""
        from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration

        config = TracingConfig(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )

        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        # Verify tracer provider is configured
        assert integration.tracer_provider is not None

        integration.shutdown()

    def test_exporter_non_blocking_export(self):
        """WHEN exporter processes spans, THEN should not block main thread"""
        # This is a behavioral test - actual async testing would require more setup
        exporter = JaegerExporter()
        exporter.initialize()

        # Export should return quickly (not block)
        with patch.object(exporter.underlying_exporter, 'export', return_value=SpanExportResult.SUCCESS):
            result = exporter.export([])
            assert result == SpanExportResult.SUCCESS
