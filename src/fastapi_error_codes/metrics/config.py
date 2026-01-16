"""
Configuration management for error metrics collection.

This module provides MetricsConfig, a frozen dataclass with validation,
presets, and environment variable support for configuring error metrics.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class MetricsConfig:
    """
    Configuration for error metrics collection.

    This frozen dataclass provides validated configuration settings for
    error metrics collection, Prometheus export, Sentry integration,
    and dashboard API.

    Attributes:
        enabled: Enable/disable metrics collection (default: True)
        collection_interval_ms: Metrics collection interval in milliseconds (min: 1000, default: 60000)
        max_events: Maximum number of events to keep in memory (min: 100, max: 1000000, default: 10000)
        prometheus_enabled: Enable Prometheus metrics export (default: True)
        sentry_enabled: Enable Sentry error tracking (default: False)
        sentry_dsn: Sentry DSN for error tracking (required if sentry_enabled=True)
        dashboard_enabled: Enable dashboard API endpoints (default: True)
        pii_patterns: List of PII field patterns to mask (default: common patterns)

    Example:
        ```python
        config = MetricsConfig(
            enabled=True,
            collection_interval_ms=30000,
            max_events=5000,
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/project"
        )
        ```
    """

    enabled: bool = True
    collection_interval_ms: int = 60000
    max_events: int = 10000
    prometheus_enabled: bool = True
    sentry_enabled: bool = False
    sentry_dsn: Optional[str] = None
    dashboard_enabled: bool = True
    pii_patterns: List[str] = field(default_factory=lambda: [
        "email",
        "password",
        "ssn",
        "credit_card",
        "api_key",
        "token",
        "secret",
        "phone",
    ])

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.collection_interval_ms < 1000:
            raise ValueError("collection_interval_ms must be at least 1000")

        if self.max_events < 100:
            raise ValueError("max_events must be at least 100")

        if self.max_events > 1_000_000:
            raise ValueError("max_events must not exceed 1000000")

        if self.sentry_enabled and not self.sentry_dsn:
            raise ValueError("sentry_dsn is required when sentry_enabled is True")

    def to_dict(self) -> Dict[str, object]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration

        Example:
            ```python
            config = MetricsConfig(enabled=True)
            config_dict = config.to_dict()
            # {'enabled': True, 'collection_interval_ms': 60000, ...}
            ```
        """
        return {
            "enabled": self.enabled,
            "collection_interval_ms": self.collection_interval_ms,
            "max_events": self.max_events,
            "prometheus_enabled": self.prometheus_enabled,
            "sentry_enabled": self.sentry_enabled,
            "sentry_dsn": self.sentry_dsn,
            "dashboard_enabled": self.dashboard_enabled,
            "pii_patterns": list(self.pii_patterns),  # Create a mutable copy
        }


class MetricsPreset:
    """
    Preset configurations for common deployment scenarios.

    Provides factory methods for creating MetricsConfig instances
    optimized for different environments.

    Available presets:
    - development: Local development with minimal overhead
    - production: Full monitoring with Sentry integration
    - testing: Disabled for test environments
    - disabled: All monitoring disabled
    """

    @staticmethod
    def development() -> MetricsConfig:
        """
        Create a configuration optimized for development.

        Development preset:
        - Metrics collection enabled with 1-minute interval
        - Smaller event limit (1000 events)
        - Prometheus enabled for local monitoring
        - Sentry disabled (no errors sent to external service)
        - Dashboard enabled for local debugging

        Returns:
            MetricsConfig configured for development

        Example:
            ```python
            config = MetricsPreset.development()
            ```
        """
        return MetricsConfig(
            enabled=True,
            collection_interval_ms=60000,
            max_events=1000,
            prometheus_enabled=True,
            sentry_enabled=False,
            dashboard_enabled=True,
        )

    @staticmethod
    def production(sentry_dsn: str) -> MetricsConfig:
        """
        Create a configuration optimized for production.

        Production preset:
        - Metrics collection enabled with 30-second interval
        - Large event limit (50000 events)
        - Prometheus enabled for monitoring systems
        - Sentry enabled with required DSN
        - Dashboard enabled for observability

        Args:
            sentry_dsn: Sentry DSN for error tracking

        Returns:
            MetricsConfig configured for production

        Raises:
            ValueError: If sentry_dsn is None or empty

        Example:
            ```python
            config = MetricsPreset.production(
                sentry_dsn="https://key@sentry.io/123"
            )
            ```
        """
        if not sentry_dsn:
            raise ValueError("sentry_dsn is required for production preset")

        return MetricsConfig(
            enabled=True,
            collection_interval_ms=30000,
            max_events=50000,
            prometheus_enabled=True,
            sentry_enabled=True,
            sentry_dsn=sentry_dsn,
            dashboard_enabled=True,
        )

    @staticmethod
    def testing() -> MetricsConfig:
        """
        Create a configuration optimized for testing.

        Testing preset:
        - All monitoring disabled to avoid test interference
        - Minimal event limit (500 events)
        - No external integrations

        Returns:
            MetricsConfig configured for testing

        Example:
            ```python
            config = MetricsPreset.testing()
            ```
        """
        return MetricsConfig(
            enabled=False,
            max_events=500,
            prometheus_enabled=False,
            sentry_enabled=False,
            dashboard_enabled=False,
        )

    @staticmethod
    def disabled() -> MetricsConfig:
        """
        Create a configuration with all monitoring disabled.

        Disabled preset:
        - All monitoring and integrations disabled

        Returns:
            MetricsConfig with all features disabled

        Example:
            ```python
            config = MetricsPreset.disabled()
            ```
        """
        return MetricsConfig(
            enabled=False,
            prometheus_enabled=False,
            sentry_enabled=False,
            dashboard_enabled=False,
        )


def get_config_from_env() -> MetricsConfig:
    """
    Create MetricsConfig from environment variables.

    Environment variables:
    - METRICS_ENABLED: "true" or "false" (default: "true")
    - METRICS_COLLECTION_INTERVAL_MS: integer in milliseconds (default: 60000)
    - METRICS_MAX_EVENTS: integer (default: 10000)
    - METRICS_PROMETHEUS_ENABLED: "true" or "false" (default: "true")
    - METRICS_SENTRY_ENABLED: "true" or "false" (default: "false")
    - METRICS_SENTRY_DSN: Sentry DSN URL (default: None)
    - METRICS_DASHBOARD_ENABLED: "true" or "false" (default: "true")
    - METRICS_PII_PATTERNS: comma-separated list of patterns (default: built-in patterns)

    Returns:
        MetricsConfig configured from environment variables

    Example:
        ```python
        import os
        os.environ["METRICS_ENABLED"] = "false"
        os.environ["METRICS_MAX_EVENTS"] = "5000"
        config = get_config_from_env()
        ```
    """
    def parse_bool(value: Optional[str], default: bool = False) -> bool:
        """Parse boolean from environment variable string."""
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def parse_int(value: Optional[str], default: int) -> int:
        """Parse integer from environment variable string."""
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def parse_list(value: Optional[str], default: List[str]) -> List[str]:
        """Parse comma-separated list from environment variable string."""
        if value is None:
            return default
        if not value.strip():
            return default
        return [item.strip() for item in value.split(",") if item.strip()]

    return MetricsConfig(
        enabled=parse_bool(os.environ.get("METRICS_ENABLED"), True),
        collection_interval_ms=parse_int(
            os.environ.get("METRICS_COLLECTION_INTERVAL_MS"),
            60000
        ),
        max_events=parse_int(os.environ.get("METRICS_MAX_EVENTS"), 10000),
        prometheus_enabled=parse_bool(
            os.environ.get("METRICS_PROMETHEUS_ENABLED"),
            True
        ),
        sentry_enabled=parse_bool(
            os.environ.get("METRICS_SENTRY_ENABLED"),
            False
        ),
        sentry_dsn=os.environ.get("METRICS_SENTRY_DSN"),
        dashboard_enabled=parse_bool(
            os.environ.get("METRICS_DASHBOARD_ENABLED"),
            True
        ),
        pii_patterns=parse_list(
            os.environ.get("METRICS_PII_PATTERNS"),
            [
                "email",
                "password",
                "ssn",
                "credit_card",
                "api_key",
                "token",
                "secret",
                "phone",
            ]
        ),
    )
