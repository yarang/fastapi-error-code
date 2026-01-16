"""
Test suite for tracing configuration (Phase 1: RED)

Tests TracingConfig dataclass with validation:
- Service name validation (non-empty, alphanumeric with hyphens)
- Endpoint URL validation for exporters
- Sampling rate validation (0.0 to 1.0)
- Frozen dataclass for immutability
"""

import pytest
from dataclasses import FrozenInstanceError
from typing import Dict

from fastapi_error_codes.tracing.config import TracingConfig


class TestTracingConfigServiceName:
    """Test service name validation"""

    def test_valid_service_name_with_alphanumeric(self):
        """WHEN service name is alphanumeric, THEN should create config"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        assert config.service_name == "myservice"

    def test_valid_service_name_with_hyphens(self):
        """WHEN service name contains hyphens, THEN should create config"""
        config = TracingConfig(
            service_name="my-service",
            endpoint="http://localhost:4317"
        )
        assert config.service_name == "my-service"

    def test_valid_service_name_with_underscores(self):
        """WHEN service name contains underscores, THEN should create config"""
        config = TracingConfig(
            service_name="my_service",
            endpoint="http://localhost:4317"
        )
        assert config.service_name == "my_service"

    def test_invalid_service_name_empty_raises_error(self):
        """WHEN service name is empty, THEN should raise ValueError"""
        with pytest.raises(ValueError, match="Service name cannot be empty"):
            TracingConfig(
                service_name="",
                endpoint="http://localhost:4317"
            )

    def test_invalid_service_name_whitespace_only_raises_error(self):
        """WHEN service name is whitespace only, THEN should raise ValueError"""
        with pytest.raises(ValueError, match="Service name cannot be empty"):
            TracingConfig(
                service_name="   ",
                endpoint="http://localhost:4317"
            )

    def test_invalid_service_name_special_chars_raises_error(self):
        """WHEN service name contains special chars, THEN should raise ValueError"""
        with pytest.raises(ValueError, match="Service name must contain only"):
            TracingConfig(
                service_name="my$service",
                endpoint="http://localhost:4317"
            )


class TestTracingConfigEndpoint:
    """Test endpoint URL validation"""

    def test_valid_http_endpoint(self):
        """WHEN endpoint is valid HTTP URL, THEN should create config"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        assert config.endpoint == "http://localhost:4317"

    def test_valid_https_endpoint(self):
        """WHEN endpoint is valid HTTPS URL, THEN should create config"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="https://otel-collector:4317"
        )
        assert config.endpoint == "https://otel-collector:4317"

    def test_invalid_endpoint_missing_scheme_raises_error(self):
        """WHEN endpoint missing scheme, THEN should raise ValueError"""
        with pytest.raises(ValueError, match="Endpoint must be a valid URL"):
            TracingConfig(
                service_name="myservice",
                endpoint="localhost:4317"
            )

    def test_invalid_endpoint_invalid_scheme_raises_error(self):
        """WHEN endpoint has invalid scheme, THEN should raise ValueError"""
        with pytest.raises(ValueError, match="Endpoint must use http or https scheme"):
            TracingConfig(
                service_name="myservice",
                endpoint="ftp://localhost:4317"
            )


class TestTracingConfigSampleRate:
    """Test sampling rate validation"""

    def test_default_sample_rate_is_one(self):
        """WHEN sample rate not provided, THEN should default to 1.0"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        assert config.sample_rate == 1.0

    def test_valid_sample_rate_zero(self):
        """WHEN sample rate is 0.0, THEN should create config"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317",
            sample_rate=0.0
        )
        assert config.sample_rate == 0.0

    def test_valid_sample_rate_half(self):
        """WHEN sample rate is 0.5, THEN should create config"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317",
            sample_rate=0.5
        )
        assert config.sample_rate == 0.5

    def test_valid_sample_rate_one(self):
        """WHEN sample rate is 1.0, THEN should create config"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317",
            sample_rate=1.0
        )
        assert config.sample_rate == 1.0

    def test_invalid_sample_rate_negative_raises_error(self):
        """WHEN sample rate is negative, THEN should raise ValueError"""
        with pytest.raises(ValueError, match="Sample rate must be between 0.0 and 1.0"):
            TracingConfig(
                service_name="myservice",
                endpoint="http://localhost:4317",
                sample_rate=-0.1
            )

    def test_invalid_sample_rate_above_one_raises_error(self):
        """WHEN sample rate is above 1.0, THEN should raise ValueError"""
        with pytest.raises(ValueError, match="Sample rate must be between 0.0 and 1.0"):
            TracingConfig(
                service_name="myservice",
                endpoint="http://localhost:4317",
                sample_rate=1.1
            )


class TestTracingConfigJaegerSettings:
    """Test Jaeger exporter settings"""

    def test_default_jaeger_host(self):
        """WHEN Jaeger host not provided, THEN should default to localhost"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        assert config.jaeger_host == "localhost"

    def test_custom_jaeger_host(self):
        """WHEN custom Jaeger host provided, THEN should use custom value"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317",
            jaeger_host="jaeger-agent"
        )
        assert config.jaeger_host == "jaeger-agent"

    def test_default_jaeger_port(self):
        """WHEN Jaeger port not provided, THEN should default to 6831"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        assert config.jaeger_port == 6831

    def test_custom_jaeger_port(self):
        """WHEN custom Jaeger port provided, THEN should use custom value"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317",
            jaeger_port=6832
        )
        assert config.jaeger_port == 6832


class TestTracingConfigOTLPSettings:
    """Test OTLP exporter settings"""

    def test_default_otlp_endpoint(self):
        """WHEN OTLP endpoint not provided, THEN should default to standard endpoint"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        assert config.otlp_endpoint == "http://localhost:4317"

    def test_custom_otlp_endpoint(self):
        """WHEN custom OTLP endpoint provided, THEN should use custom value"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317",
            otlp_endpoint="https://otel-collector:4317"
        )
        assert config.otlp_endpoint == "https://otel-collector:4317"


class TestTracingConfigPIIMasking:
    """Test PII masking settings"""

    def test_default_pii_masking_enabled(self):
        """WHEN PII masking setting not provided, THEN should default to True"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        assert config.enable_pii_masking is True

    def test_disable_pii_masking(self):
        """WHEN PII masking explicitly disabled, THEN should be False"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317",
            enable_pii_masking=False
        )
        assert config.enable_pii_masking is False

    def test_default_pii_patterns_is_empty_dict(self):
        """WHEN PII patterns not provided, THEN should default to empty dict"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        assert config.pii_patterns == {}

    def test_custom_pii_patterns(self):
        """WHEN custom PII patterns provided, THEN should use custom patterns"""
        custom_patterns: Dict[str, str] = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"\d{3}-\d{3}-\d{4}"
        }
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317",
            pii_patterns=custom_patterns
        )
        assert config.pii_patterns == custom_patterns


class TestTracingConfigImmutability:
    """Test that TracingConfig is frozen (immutable)"""

    def test_cannot_modify_service_name(self):
        """WHEN attempting to modify service_name, THEN should raise FrozenInstanceError"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        with pytest.raises(FrozenInstanceError):
            config.service_name = "newservice"

    def test_cannot_modify_endpoint(self):
        """WHEN attempting to modify endpoint, THEN should raise FrozenInstanceError"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        with pytest.raises(FrozenInstanceError):
            config.endpoint = "http://newhost:4317"

    def test_cannot_modify_sample_rate(self):
        """WHEN attempting to modify sample_rate, THEN should raise FrozenInstanceError"""
        config = TracingConfig(
            service_name="myservice",
            endpoint="http://localhost:4317"
        )
        with pytest.raises(FrozenInstanceError):
            config.sample_rate = 0.5
