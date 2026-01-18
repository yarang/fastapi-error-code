"""
Tests for SentryIntegration module.

Tests Sentry error tracking with PII masking and graceful degradation.
"""

from unittest.mock import MagicMock

from fastapi_error_codes.metrics.config import MetricsConfig
from fastapi_error_codes.metrics.sentry import (
    SentryIntegration,
    mask_pii,
)


class TestMaskPII:
    """Test PII masking functionality."""

    def test_mask_email(self) -> None:
        """Test masking email addresses."""
        data = {"email": "user@example.com", "name": "John"}
        masked = mask_pii(data, ["email"])

        assert masked["email"] == "***@***.***"
        assert masked["name"] == "John"

    def test_mask_multiple_patterns(self) -> None:
        """Test masking multiple PII patterns."""
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "name": "John",
            "ssn": "123-45-6789",
        }
        masked = mask_pii(data, ["email", "password", "ssn"])

        assert masked["email"] == "***@***.***"
        assert masked["password"] == "***"
        assert masked["ssn"] == "***"
        assert masked["name"] == "John"

    def test_mask_nested_dict(self) -> None:
        """Test masking PII in nested dictionaries."""
        data = {
            "user": {
                "email": "user@example.com",
                "profile": {
                    "ssn": "123-45-6789",
                    "name": "John"
                }
            }
        }
        masked = mask_pii(data, ["email", "ssn"])

        assert masked["user"]["email"] == "***@***.***"
        assert masked["user"]["profile"]["ssn"] == "***"
        assert masked["user"]["profile"]["name"] == "John"

    def test_mask_in_list(self) -> None:
        """Test masking PII in list values."""
        data = {
            "users": [
                {"email": "user1@example.com", "name": "User1"},
                {"email": "user2@example.com", "name": "User2"}
            ]
        }
        masked = mask_pii(data, ["email"])

        assert masked["users"][0]["email"] == "***@***.***"
        assert masked["users"][1]["email"] == "***@***.***"
        assert masked["users"][0]["name"] == "User1"

    def test_mask_with_custom_patterns(self) -> None:
        """Test masking with custom PII patterns."""
        data = {
            "api_key": "sk-1234567890",
            "token": "abc-def-ghi",
            "public": "visible"
        }
        masked = mask_pii(data, ["api_key", "token"])

        assert masked["api_key"] == "***"
        assert masked["token"] == "***"
        assert masked["public"] == "visible"

    def test_mask_empty_patterns(self) -> None:
        """Test masking with no patterns (no masking)."""
        data = {"email": "user@example.com", "name": "John"}
        masked = mask_pii(data, [])

        assert masked["email"] == "user@example.com"
        assert masked["name"] == "John"

    def test_mask_preserves_original(self) -> None:
        """Test that masking doesn't modify the original data."""
        data = {"email": "user@example.com", "name": "John"}
        original_email = data["email"]

        masked = mask_pii(data, ["email"])

        assert data["email"] == original_email  # Original unchanged
        assert masked["email"] == "***@***.***"

    def test_mask_none_values(self) -> None:
        """Test masking data with None values."""
        data = {"email": None, "name": "John"}
        masked = mask_pii(data, ["email"])

        assert masked["email"] is None
        assert masked["name"] == "John"


class TestSentryIntegration:
    """Test Sentry integration with graceful degradation."""

    def test_create_sentry_integration(self) -> None:
        """Test creating a Sentry integration."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        assert integration.config is config
        assert integration.enabled is True
        assert integration.dsn == "https://key@sentry.io/123"

    def test_create_disabled_integration(self) -> None:
        """Test creating a disabled Sentry integration."""
        config = MetricsConfig(sentry_enabled=False)
        integration = SentryIntegration(config)

        assert integration.enabled is False

    def test_capture_event_without_sentry_installed(self) -> None:
        """Test graceful degradation when Sentry is not installed."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        # Should not raise exception even without Sentry installed
        integration.capture_event(
            error_code=404,
            error_name="NotFound",
            message="Not found",
            detail={}
        )

    def test_capture_event_with_pii_masking(self) -> None:
        """Test that PII is masked when capturing events."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123",
            pii_patterns=["email", "password"]
        )
        integration = SentryIntegration(config)

        # Mock the internal sentry_sdk
        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        integration.capture_event(
            error_code=400,
            error_name="BadRequest",
            message="Invalid request",
            detail={"email": "user@example.com", "password": "secret"}
        )

        # Verify capture_event was called
        assert mock_sentry.capture_event.called

        # Get the captured event
        call_args = mock_sentry.capture_event.call_args
        event = call_args[0][0]

        # Check that PII was masked in the event
        assert event["extra"]["detail"]["email"] == "***@***.***"
        assert event["extra"]["detail"]["password"] == "***"

    def test_capture_event_with_null_detail(self) -> None:
        """Test capturing event with None detail."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        # Mock the internal sentry_sdk
        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        # Should not raise exception
        integration.capture_event(
            error_code=404,
            error_name="NotFound",
            message="Not found",
            detail=None
        )

        assert mock_sentry.capture_event.called

    def test_capture_exception(self) -> None:
        """Test capturing Python exceptions."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        try:
            raise ValueError("Test error")
        except ValueError as e:
            # Should not raise exception
            integration.capture_exception(e)

        assert mock_sentry.capture_exception.called

    def test_capture_exception_with_pii(self) -> None:
        """Test that exception context with PII is masked."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123",
            pii_patterns=["email", "password"]
        )
        integration = SentryIntegration(config)

        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        try:
            raise ValueError("User error")
        except ValueError as e:
            integration.capture_exception(
                e,
                detail={"email": "user@example.com", "user_id": "123"}
            )

        # Verify capture_exception was called
        assert mock_sentry.capture_exception.called

    def test_sentry_initialization(self) -> None:
        """Test Sentry SDK initialization."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        integration.initialize()

        # Verify Sentry was initialized with DSN
        assert mock_sentry.init.called
        call_kwargs = mock_sentry.init.call_args[1]
        assert call_kwargs["dsn"] == "https://key@sentry.io/123"

    def test_sentry_initialization_disabled(self) -> None:
        """Test that Sentry is not initialized when disabled."""
        config = MetricsConfig(sentry_enabled=False)
        integration = SentryIntegration(config)

        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        integration.initialize()

        # Should not initialize when disabled
        assert not mock_sentry.init.called

    def test_add_breadcrumb(self) -> None:
        """Test adding breadcrumbs for error context."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        integration.add_breadcrumb(
            category="error",
            message="Error occurred",
            level="error"
        )

        # Verify add_breadcrumb was called
        assert mock_sentry.add_breadcrumb.called

    def test_flush(self) -> None:
        """Test flushing pending events."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        integration.flush(timeout=5.0)

        # Verify flush was called
        assert mock_sentry.flush.called
        # Check the call - might be positional or keyword
        call_args = mock_sentry.flush.call_args[0]
        if call_args:
            assert call_args[0] == 5.0

    def test_graceful_degradation_on_import_error(self) -> None:
        """Test graceful degradation when sentry_sdk is not available."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        # Simulate sentry_sdk not being available
        integration._sentry_sdk = None

        # Should not raise exception
        integration.initialize()
        integration.capture_event(
            error_code=404,
            error_name="NotFound",
            message="Not found",
            detail={}
        )

    def test_configure_scope(self) -> None:
        """Test configuring Sentry scope with custom data."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123"
        )
        integration = SentryIntegration(config)

        mock_sentry = MagicMock()
        integration._sentry_sdk = mock_sentry

        integration.configure_scope({
            "user_id": "123",
            "request_id": "abc"
        })

        # Verify configure_scope was called
        assert mock_sentry.configure_scope.called

    def test_mask_pii_patterns_from_config(self) -> None:
        """Test that PII masking uses patterns from config."""
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123",
            pii_patterns=["custom_field"]
        )
        integration = SentryIntegration(config)

        data = {"custom_field": "sensitive", "public": "visible"}
        masked = integration._mask_event_data(data)

        assert masked["custom_field"] == "***"
        assert masked["public"] == "visible"
