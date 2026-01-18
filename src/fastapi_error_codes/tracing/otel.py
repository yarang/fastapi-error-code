"""
OpenTelemetry SDK integration for distributed tracing

Provides OpenTelemetryIntegration class for:
- SDK initialization with resource attributes
- Tracer provider configuration
- Sampling strategy setup
- Tracer creation
- Shutdown cleanup
"""

from typing import TYPE_CHECKING, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import Sampler as SDKSampler
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from fastapi_error_codes.tracing.config import TracingConfig

if TYPE_CHECKING:
    pass


class OpenTelemetryIntegration:
    """
    OpenTelemetry SDK integration wrapper.

    Manages the lifecycle of OpenTelemetry tracing including
    provider initialization, resource configuration, and cleanup.

    Attributes:
        config: Tracing configuration
        service_version: Optional service version string
        tracer_provider: OpenTelemetry TracerProvider instance
    """

    def __init__(
        self,
        config: TracingConfig,
        service_version: Optional[str] = None
    ):
        """
        Initialize OpenTelemetry integration.

        Args:
            config: Tracing configuration
            service_version: Optional service version for resource attributes
        """
        self.config = config
        self.service_version = service_version
        self.tracer_provider: Optional[TracerProvider] = None

    def initialize(self) -> None:
        """
        Initialize OpenTelemetry SDK with configured resources and sampling.

        Creates TracerProvider with:
        - Resource attributes (service.name, service.version)
        - Sampling strategy based on config.sample_rate
        - BatchSpanProcessor for efficient export
        - Sets as global tracer provider
        """
        # Create resource with service attributes
        resource_attributes = {
            "service.name": self.config.service_name,
        }

        if self.service_version:
            resource_attributes["service.version"] = self.service_version

        resource = Resource.create(resource_attributes)

        # Create tracer provider with resource
        self.tracer_provider = TracerProvider(resource=resource)

        # Configure sampling strategy
        sampler = self._create_sampler()
        self.tracer_provider._sampler = sampler

        # Add batch span processor (exporter will be added in Phase 3)
        # For now, we create a simple processor that doesn't export
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        self.tracer_provider.add_span_processor(processor)

        # Set as global tracer provider
        trace.set_tracer_provider(self.tracer_provider)

    def _create_sampler(self) -> SDKSampler:
        """
        Create sampler based on configured sample rate.

        Returns:
            Sampler instance for the tracer provider

        """
        # TraceIdRatioBased sampler samples based on trace ID
        # sample_rate of 1.0 samples all traces
        # sample_rate of 0.0 samples no traces
        return TraceIdRatioBased(self.config.sample_rate)

    def get_tracer(
        self,
        name: str,
        version: Optional[str] = None
    ) -> trace.Tracer:
        """
        Get a tracer instance from the provider.

        Args:
            name: Instrumentation name (e.g., package name)
            version: Optional instrumentation version

        Returns:
            OpenTelemetry Tracer instance

        Raises:
            RuntimeError: If initialize has not been called
        """
        if self.tracer_provider is None:
            raise RuntimeError(
                "OpenTelemetryIntegration not initialized. "
                "Call initialize() first."
            )

        # OpenTelemetry API uses positional arguments for get_tracer
        if version is not None:
            return self.tracer_provider.get_tracer(name, version)
        return self.tracer_provider.get_tracer(name)

    def shutdown(self) -> None:
        """
        Shutdown the tracer provider and cleanup resources.

        This method flushes pending spans and releases resources.
        It is safe to call multiple times.
        """
        if self.tracer_provider is not None:
            self.tracer_provider.shutdown()
