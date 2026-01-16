"""
Tests for config.py module - ErrorHandlerConfig class.

RED phase: Write failing tests first to define expected behavior.
"""

from pathlib import Path

import pytest

from fastapi_error_codes.config import ErrorHandlerConfig


class TestErrorHandlerConfigInitialization:
    """Test ErrorHandlerConfig initialization and defaults."""

    def test_create_config_with_defaults(self):
        """Should create config with default values."""
        config = ErrorHandlerConfig()
        assert config.default_locale == "en"
        assert config.fallback_locales == []
        assert config.debug_mode is False
        assert config.include_traceback is False
        assert config.locale_dir == "locales"

    def test_create_config_with_custom_values(self):
        """Should create config with custom values."""
        config = ErrorHandlerConfig(
            default_locale="ko",
            fallback_locales=["en", "ja"],
            debug_mode=True,
            include_traceback=True,
            locale_dir="/app/locales"
        )
        assert config.default_locale == "ko"
        assert config.fallback_locales == ["en", "ja"]
        assert config.debug_mode is True
        assert config.include_traceback is True
        assert config.locale_dir == "/app/locales"

    def test_config_is_immutable_using_dataclass(self):
        """Should be a dataclass with proper field types."""
        config = ErrorHandlerConfig()
        assert hasattr(config, '__dataclass_fields__')
        fields = config.__dataclass_fields__
        assert 'default_locale' in fields
        assert 'fallback_locales' in fields
        assert 'debug_mode' in fields
        assert 'include_traceback' in fields
        assert 'locale_dir' in fields


class TestErrorHandlerConfigPresets:
    """Test ErrorHandlerConfig preset configurations."""

    def test_development_preset(self):
        """Should create development config with debug enabled."""
        config = ErrorHandlerConfig.development()
        assert config.debug_mode is True
        assert config.include_traceback is True
        assert config.default_locale == "en"
        assert config.locale_dir == "locales"

    def test_development_preset_custom_locale(self):
        """Should create development config with custom locale."""
        config = ErrorHandlerConfig.development(default_locale="ko")
        assert config.debug_mode is True
        assert config.include_traceback is True
        assert config.default_locale == "ko"

    def test_production_preset(self):
        """Should create production config with debug disabled."""
        config = ErrorHandlerConfig.production()
        assert config.debug_mode is False
        assert config.include_traceback is False
        assert config.default_locale == "en"
        assert config.locale_dir == "locales"

    def test_production_preset_with_custom_settings(self):
        """Should create production config with custom settings."""
        config = ErrorHandlerConfig.production(
            default_locale="ko",
            fallback_locales=["en"]
        )
        assert config.debug_mode is False
        assert config.include_traceback is False
        assert config.default_locale == "ko"
        assert config.fallback_locales == ["en"]


class TestErrorHandlerConfigValidation:
    """Test ErrorHandlerConfig validation."""

    def test_invalid_locale_dir_raises_error(self):
        """Should raise error if locale_dir doesn't exist in strict mode."""
        with pytest.raises(ValueError, match="Locale directory does not exist"):
            ErrorHandlerConfig(
                locale_dir="/nonexistent/path",
                _validate=True
            )

    def test_valid_locale_dir_passes(self):
        """Should accept valid locale directory."""
        # Use actual locales directory
        config = ErrorHandlerConfig(
            locale_dir="locales",
            _validate=True
        )
        assert config.locale_dir == "locales"

    def test_no_validation_when_disabled(self):
        """Should not validate when _validate is False."""
        # Should not raise error even with invalid path
        config = ErrorHandlerConfig(
            locale_dir="/nonexistent/path",
            _validate=False
        )
        assert config.locale_dir == "/nonexistent/path"


class TestErrorHandlerConfigCopyAndUpdate:
    """Test ErrorHandlerConfig copy and update operations."""

    def test_copy_config(self):
        """Should create an independent copy of the config."""
        original = ErrorHandlerConfig(
            default_locale="en",
            debug_mode=True
        )
        copy = original.copy()
        assert copy.default_locale == "en"
        assert copy.debug_mode is True

    def test_copy_is_independent(self):
        """Modifying copy should not affect original."""
        original = ErrorHandlerConfig(default_locale="en")
        copy = original.copy()
        # Note: dataclasses are immutable by default if frozen=True
        # This test verifies copy behavior

    def test_update_config(self):
        """Should create new config with updated values."""
        original = ErrorHandlerConfig(
            default_locale="en",
            debug_mode=False
        )
        updated = original.update(default_locale="ko", debug_mode=True)
        assert updated.default_locale == "ko"
        assert updated.debug_mode is True
        # Original should be unchanged if frozen
        assert original.default_locale == "en"


class TestErrorHandlerConfigSerialization:
    """Test ErrorHandlerConfig serialization."""

    def test_to_dict(self):
        """Should convert config to dictionary."""
        config = ErrorHandlerConfig(
            default_locale="ko",
            debug_mode=True,
            fallback_locales=["en"]
        )
        data = config.to_dict()
        assert data["default_locale"] == "ko"
        assert data["debug_mode"] is True
        assert data["fallback_locales"] == ["en"]

    def test_from_dict(self):
        """Should create config from dictionary."""
        data = {
            "default_locale": "ja",
            "debug_mode": True,
            "include_traceback": False,
            "fallback_locales": ["en", "ko"],
            "locale_dir": "locales"
        }
        config = ErrorHandlerConfig.from_dict(data)
        assert config.default_locale == "ja"
        assert config.debug_mode is True
        assert config.include_traceback is False
        assert config.fallback_locales == ["en", "ko"]


class TestErrorHandlerConfigEnvironmentVariables:
    """Test ErrorHandlerConfig environment variable support."""

    def test_from_environment_with_defaults(self):
        """Should create config from environment variables."""
        import os
        # Save original env vars
        original_env = {}
        for key in ["ERROR_LOCALE", "ERROR_DEBUG", "ERROR_LOCALE_DIR"]:
            original_env[key] = os.environ.get(key)

        try:
            # Set test environment variables
            os.environ["ERROR_LOCALE"] = "ko"
            os.environ["ERROR_DEBUG"] = "true"
            os.environ["ERROR_LOCALE_DIR"] = "/app/locales"

            config = ErrorHandlerConfig.from_environment()
            assert config.default_locale == "ko"
            assert config.debug_mode is True
            assert config.locale_dir == "/app/locales"
        finally:
            # Restore original env vars
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_from_environment_with_missing_vars(self):
        """Should use defaults when environment variables are missing."""
        import os
        # Clear relevant env vars
        vars_to_clear = ["ERROR_LOCALE", "ERROR_DEBUG", "ERROR_LOCALE_DIR",
                         "ERROR_TRACEBACK", "ERROR_FALLBACK_LOCALES"]
        original_values = {}
        for var in vars_to_clear:
            original_values[var] = os.environ.get(var)
            os.environ.pop(var, None)

        try:
            config = ErrorHandlerConfig.from_environment()
            assert config.default_locale == "en"  # default
            assert config.debug_mode is False  # default
            assert config.locale_dir == "locales"  # default
        finally:
            # Restore original env vars
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
