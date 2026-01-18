"""
Tests for MetricsConfig module.

Tests configuration management for error metrics collection.
"""

import os
from dataclasses import FrozenInstanceError
from typing import Any, Dict

import pytest

from fastapi_error_codes.metrics.config import (
    MetricsConfig,
    MetricsPreset,
    get_config_from_env,
)


class TestMetricsConfig:
    """Test MetricsConfig dataclass with validation."""

    def test_create_default_config(self) -> None:
        """Test creating a config with default values."""
        config = MetricsConfig()

        assert config.enabled is True
        assert config.collection_interval_ms == 60000
        assert config.max_events == 10000
        assert config.prometheus_enabled is True
        assert config.sentry_enabled is False
        assert config.dashboard_enabled is True

    def test_create_custom_config(self) -> None:
        """Test creating a config with custom values."""
        config = MetricsConfig(
            enabled=False,
            collection_interval_ms=30000,
            max_events=5000,
            prometheus_enabled=False,
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/project",
            dashboard_enabled=False,
        )

        assert config.enabled is False
        assert config.collection_interval_ms == 30000
        assert config.max_events == 5000
        assert config.prometheus_enabled is False
        assert config.sentry_enabled is True
        assert config.sentry_dsn == "https://key@sentry.io/project"
        assert config.dashboard_enabled is False

    def test_config_is_immutable(self) -> None:
        """Test that MetricsConfig is frozen (immutable)."""
        config = MetricsConfig()

        with pytest.raises(FrozenInstanceError):
            config.enabled = False  # type: ignore[misc]

    def test_collection_interval_validation(self) -> None:
        """Test collection interval must be at least 1000ms."""
        with pytest.raises(ValueError, match="collection_interval_ms must be at least 1000"):
            MetricsConfig(collection_interval_ms=500)

    def test_max_events_validation(self) -> None:
        """Test max_events must be at least 100."""
        with pytest.raises(ValueError, match="max_events must be at least 100"):
            MetricsConfig(max_events=50)

    def test_max_events_upper_limit(self) -> None:
        """Test max_events cannot exceed 1000000."""
        with pytest.raises(ValueError, match="max_events must not exceed 1000000"):
            MetricsConfig(max_events=2000000)

    def test_sentry_dsn_validation_when_enabled(self) -> None:
        """Test sentry_dsn is required when sentry_enabled is True."""
        with pytest.raises(ValueError, match="sentry_dsn is required when sentry_enabled is True"):
            MetricsConfig(sentry_enabled=True, sentry_dsn=None)

    def test_sentry_dsn_not_required_when_disabled(self) -> None:
        """Test sentry_dsn is optional when sentry_enabled is False."""
        config = MetricsConfig(sentry_enabled=False, sentry_dsn=None)
        assert config.sentry_dsn is None

    def test_environment_parsing(self) -> None:
        """Test parsing config from environment variables."""
        env_vars: Dict[str, str] = {
            "METRICS_ENABLED": "false",
            "METRICS_COLLECTION_INTERVAL_MS": "30000",
            "METRICS_MAX_EVENTS": "5000",
            "METRICS_PROMETHEUS_ENABLED": "false",
            "METRICS_SENTRY_ENABLED": "true",
            "METRICS_SENTRY_DSN": "https://key@sentry.io/123",
            "METRICS_DASHBOARD_ENABLED": "false",
            "METRICS_PII_PATTERNS": "email,ssn,credit_card",
        }

        # Store original env vars
        original_env: Dict[str, Any] = {
            key: os.environ.get(key) for key in env_vars
        }

        try:
            # Set environment variables
            for key, value in env_vars.items():
                os.environ[key] = value

            config = get_config_from_env()

            assert config.enabled is False
            assert config.collection_interval_ms == 30000
            assert config.max_events == 5000
            assert config.prometheus_enabled is False
            assert config.sentry_enabled is True
            assert config.sentry_dsn == "https://key@sentry.io/123"
            assert config.dashboard_enabled is False
            assert "email" in config.pii_patterns
            assert "ssn" in config.pii_patterns
            assert "credit_card" in config.pii_patterns
        finally:
            # Restore original env vars
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

    def test_environment_parsing_defaults(self) -> None:
        """Test parsing config from environment with missing variables uses defaults."""
        # Clear all metrics env vars
        env_keys = [
            "METRICS_ENABLED",
            "METRICS_COLLECTION_INTERVAL_MS",
            "METRICS_MAX_EVENTS",
            "METRICS_PROMETHEUS_ENABLED",
            "METRICS_SENTRY_ENABLED",
            "METRICS_SENTRY_DSN",
            "METRICS_DASHBOARD_ENABLED",
            "METRICS_PII_PATTERNS",
        ]

        original_env: Dict[str, Any] = {key: os.environ.get(key) for key in env_keys}

        try:
            for key in env_keys:
                os.environ.pop(key, None)

            config = get_config_from_env()

            # Should use default values
            assert config.enabled is True
            assert config.collection_interval_ms == 60000
            assert config.max_events == 10000
            assert config.prometheus_enabled is True
            assert config.sentry_enabled is False
            assert config.dashboard_enabled is True
        finally:
            for key, original_value in original_env.items():
                if original_value is not None:
                    os.environ[key] = original_value

    def test_preset_development(self) -> None:
        """Test development preset configuration."""
        config = MetricsPreset.development()

        assert config.enabled is True
        assert config.collection_interval_ms == 60000
        assert config.max_events == 1000
        assert config.prometheus_enabled is True
        assert config.sentry_enabled is False
        assert config.dashboard_enabled is True

    def test_preset_production(self) -> None:
        """Test production preset configuration."""
        config = MetricsPreset.production(
            sentry_dsn="https://key@sentry.io/123"
        )

        assert config.enabled is True
        assert config.collection_interval_ms == 30000
        assert config.max_events == 50000
        assert config.prometheus_enabled is True
        assert config.sentry_enabled is True
        assert config.sentry_dsn == "https://key@sentry.io/123"
        assert config.dashboard_enabled is True

    def test_preset_production_requires_sentry_dsn(self) -> None:
        """Test production preset requires sentry_dsn."""
        with pytest.raises(ValueError, match="sentry_dsn is required for production preset"):
            MetricsPreset.production(sentry_dsn=None)

    def test_preset_testing(self) -> None:
        """Test testing preset configuration."""
        config = MetricsPreset.testing()

        assert config.enabled is False
        assert config.max_events == 500
        assert config.prometheus_enabled is False
        assert config.sentry_enabled is False
        assert config.dashboard_enabled is False

    def test_preset_disabled(self) -> None:
        """Test disabled preset configuration."""
        config = MetricsPreset.disabled()

        assert config.enabled is False
        assert config.prometheus_enabled is False
        assert config.sentry_enabled is False
        assert config.dashboard_enabled is False

    def test_pii_patterns_validation(self) -> None:
        """Test custom PII patterns can be provided."""
        config = MetricsConfig(
            pii_patterns=["custom_field_1", "custom_field_2"]
        )

        assert "custom_field_1" in config.pii_patterns
        assert "custom_field_2" in config.pii_patterns

    def test_pii_patterns_from_env_comma_separated(self) -> None:
        """Test PII patterns can be parsed from comma-separated env var."""
        original = os.environ.get("METRICS_PII_PATTERNS")

        try:
            os.environ["METRICS_PII_PATTERNS"] = "email,password,token"
            config = get_config_from_env()

            assert "email" in config.pii_patterns
            assert "password" in config.pii_patterns
            assert "token" in config.pii_patterns
        finally:
            if original is None:
                os.environ.pop("METRICS_PII_PATTERNS", None)
            else:
                os.environ["METRICS_PII_PATTERNS"] = original

    def test_to_dict(self) -> None:
        """Test converting config to dictionary."""
        config = MetricsConfig(
            enabled=True,
            collection_interval_ms=30000,
            max_events=5000,
        )

        config_dict = config.to_dict()

        assert config_dict["enabled"] is True
        assert config_dict["collection_interval_ms"] == 30000
        assert config_dict["max_events"] == 5000
        assert config_dict["prometheus_enabled"] is True
        assert "pii_patterns" in config_dict

    def test_equality(self) -> None:
        """Test config equality."""
        config1 = MetricsConfig(enabled=True, max_events=5000)
        config2 = MetricsConfig(enabled=True, max_events=5000)
        config3 = MetricsConfig(enabled=False, max_events=5000)

        assert config1 == config2
        assert config1 != config3
