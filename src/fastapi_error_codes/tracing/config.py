"""
Tracing configuration with validation

Provides TracingConfig frozen dataclass for distributed tracing setup.
Validates service names, endpoints, sampling rates, and PII masking settings.
"""

import re
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class TracingConfig:
    """
    Frozen configuration for distributed tracing with validation.

    Attributes:
        service_name: Name of the service (alphanumeric, hyphens, underscores)
        endpoint: Primary endpoint for trace export (HTTP/HTTPS URL)
        sample_rate: Sampling rate from 0.0 to 1.0 (default: 1.0)
        jaeger_host: Jaeger agent host (default: "localhost")
        jaeger_port: Jaeger agent port (default: 6831)
        otlp_endpoint: OTLP endpoint URL (default: "http://localhost:4317")
        enable_pii_masking: Enable PII masking in spans (default: True)
        pii_patterns: Custom regex patterns for PII detection (default: {})
    """

    service_name: str
    endpoint: str
    sample_rate: float = 1.0
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    otlp_endpoint: str = "http://localhost:4317"
    enable_pii_masking: bool = True
    pii_patterns: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration fields after initialization."""
        self._validate_service_name()
        self._validate_endpoint()
        self._validate_sample_rate()

    def _validate_service_name(self) -> None:
        """Validate service name is non-empty and contains only valid characters."""
        if not self.service_name or not self.service_name.strip():
            raise ValueError("Service name cannot be empty")

        # Service name should contain only alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.service_name):
            raise ValueError(
                "Service name must contain only alphanumeric characters, hyphens, and underscores"
            )

    def _validate_endpoint(self) -> None:
        """Validate endpoint is a valid HTTP or HTTPS URL."""
        # Check if URL contains ://
        if '://' not in self.endpoint:
            raise ValueError("Endpoint must be a valid URL with http or https scheme")

        # Extract scheme from URL
        try:
            scheme = self.endpoint.split('://')[0]
            if scheme not in ('http', 'https'):
                raise ValueError("Endpoint must use http or https scheme")
        except IndexError:
            raise ValueError("Endpoint must be a valid URL with http or https scheme") from None

    def _validate_sample_rate(self) -> None:
        """Validate sampling rate is between 0.0 and 1.0."""
        if not 0.0 <= self.sample_rate <= 1.0:
            raise ValueError("Sample rate must be between 0.0 and 1.0")
