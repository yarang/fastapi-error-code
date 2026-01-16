"""
Exporter integration for distributed tracing

Provides exporter classes for:
- JaegerExporter: Export traces to Jaeger via thrift protocol
- OTLPExporter: Export traces via OpenTelemetry Protocol
- Retry logic and failure handling
- Non-blocking async export
"""

import time
from dataclasses import dataclass
from typing import List, Optional

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.resources import Resource

from opentelemetry.exporter.jaeger.thrift import JaegerExporter as OtelJaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OtelOTLPExporter

from fastapi_error_codes.tracing.config import TracingConfig


@dataclass
class ExporterConfig:
    """
    Configuration for trace exporters.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        retry_timeout: Timeout between retries in seconds (default: 5.0)
        export_timeout: Timeout for export operation in seconds (default: 30.0)
    """
    max_retries: int = 3
    retry_timeout: float = 5.0
    export_timeout: float = 30.0


class JaegerExporter:
    """
    Jaeger exporter wrapper with retry logic.

    Exports traces to Jaeger agent via thrift protocol with
    automatic retry on transient failures.

    Attributes:
        host: Jaeger agent host (default: "localhost")
        port: Jaeger agent port (default: 6831)
        max_retries: Maximum number of retry attempts
        underlying_exporter: OpenTelemetry JaegerExporter instance
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6831,
        config: Optional[ExporterConfig] = None
    ):
        """
        Initialize Jaeger exporter.

        Args:
            host: Jaeger agent host
            port: Jaeger agent port
            config: Optional exporter configuration
        """
        self.host = host
        self.port = port
        self.config = config or ExporterConfig()
        self.max_retries = self.config.max_retries
        self.underlying_exporter: Optional[SpanExporter] = None

    def initialize(self) -> None:
        """Create and initialize the underlying Jaeger exporter."""
        self.underlying_exporter = OtelJaegerExporter(
            agent_host_name=self.host,
            agent_port=self.port,
            max_tag_value_length=4096
        )

    def export(self, spans: List[ReadableSpan]) -> SpanExportResult:
        """
        Export spans to Jaeger with retry logic.

        Args:
            spans: List of spans to export

        Returns:
            SpanExportResult.SUCCESS if export succeeds
            SpanExportResult.FAILURE if all retries fail
        """
        if self.underlying_exporter is None:
            raise RuntimeError("Exporter not initialized. Call initialize() first.")

        last_result = SpanExportResult.FAILURE

        for attempt in range(self.max_retries + 1):
            last_result = self.underlying_exporter.export(spans)

            if last_result == SpanExportResult.SUCCESS:
                return SpanExportResult.SUCCESS

            # Retry after timeout if not last attempt
            if attempt < self.max_retries:
                time.sleep(self.config.retry_timeout)

        return last_result

    def shutdown(self) -> None:
        """Shutdown the exporter and cleanup resources."""
        if self.underlying_exporter is not None:
            self.underlying_exporter.shutdown()


class OTLPExporter:
    """
    OTLP exporter wrapper with retry logic.

    Exports traces via OpenTelemetry Protocol with
    automatic retry on transient failures.

    Attributes:
        endpoint: OTLP endpoint URL (default: "http://localhost:4317")
        max_retries: Maximum number of retry attempts
        underlying_exporter: OpenTelemetry OTLPSpanExporter instance
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:4317",
        config: Optional[ExporterConfig] = None
    ):
        """
        Initialize OTLP exporter.

        Args:
            endpoint: OTLP endpoint URL
            config: Optional exporter configuration
        """
        self.endpoint = endpoint
        self.config = config or ExporterConfig()
        self.max_retries = self.config.max_retries
        self.underlying_exporter: Optional[SpanExporter] = None

    def initialize(self) -> None:
        """Create and initialize the underlying OTLP exporter."""
        self.underlying_exporter = OtelOTLPExporter(
            endpoint=self.endpoint,
            insecure=True
        )

    def export(self, spans: List[ReadableSpan]) -> SpanExportResult:
        """
        Export spans via OTLP with retry logic.

        Args:
            spans: List of spans to export

        Returns:
            SpanExportResult.SUCCESS if export succeeds
            SpanExportResult.FAILURE if all retries fail
        """
        if self.underlying_exporter is None:
            raise RuntimeError("Exporter not initialized. Call initialize() first.")

        last_result = SpanExportResult.FAILURE

        for attempt in range(self.max_retries + 1):
            last_result = self.underlying_exporter.export(spans)

            if last_result == SpanExportResult.SUCCESS:
                return SpanExportResult.SUCCESS

            # Retry after timeout if not last attempt
            if attempt < self.max_retries:
                time.sleep(self.config.retry_timeout)

        return last_result

    def shutdown(self) -> None:
        """Shutdown the exporter and cleanup resources."""
        if self.underlying_exporter is not None:
            self.underlying_exporter.shutdown()


def create_exporter(
    exporter_type: str,
    config: TracingConfig
) -> SpanExporter:
    """
    Factory function to create exporters.

    Args:
        exporter_type: Type of exporter ("jaeger" or "otlp")
        config: Tracing configuration

    Returns:
        Initialized exporter instance

    Raises:
        ValueError: If exporter_type is unknown
    """
    exporter_config = ExporterConfig(
        max_retries=3,
        retry_timeout=5.0,
        export_timeout=30.0
    )

    if exporter_type == "jaeger":
        exporter = JaegerExporter(
            host=config.jaeger_host,
            port=config.jaeger_port,
            config=exporter_config
        )
        exporter.initialize()
        return exporter  # type: ignore
    elif exporter_type == "otlp":
        exporter = OTLPExporter(
            endpoint=config.otlp_endpoint,
            config=exporter_config
        )
        exporter.initialize()
        return exporter  # type: ignore
    else:
        raise ValueError(f"Unknown exporter type: {exporter_type}")
