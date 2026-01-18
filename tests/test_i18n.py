"""
Tests for i18n.py module - MessageProvider class.

RED phase: Write failing tests first to define expected behavior.
"""

import json
import tempfile
from pathlib import Path

import pytest

from fastapi_error_codes.i18n import MessageProvider


class TestMessageProviderInitialization:
    """Test MessageProvider initialization and configuration."""

    def test_initialize_with_locale_dir(self):
        """Should initialize with a valid locale directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create en.json
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "Test message"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")
            assert provider.locale_dir == tmpdir
            assert provider.default_locale == "en"

    def test_initialize_with_nonexistent_locale_dir(self):
        """Should raise ValueError if locale_dir does not exist."""
        with pytest.raises(ValueError, match="Locale directory does not exist"):
            MessageProvider(locale_dir="/nonexistent/path", default_locale="en")

    def test_initialize_with_invalid_default_locale(self):
        """Should raise ValueError if default_locale file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create ko.json but not en.json
            ko_file = Path(tmpdir) / "ko.json"
            ko_file.write_text(json.dumps({"errors": {"test": "테스트"}}))

            with pytest.raises(ValueError, match="Default locale file not found"):
                MessageProvider(locale_dir=tmpdir, default_locale="en")


class TestMessageProviderNestedJSONParsing:
    """Test nested JSON parsing with dot notation."""

    def test_get_message_simple_key(self):
        """Should retrieve message with simple key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "Test message"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")
            message = provider.get_message("errors.test")
            assert message == "Test message"

    def test_get_message_nested_key(self):
        """Should retrieve deeply nested message with dot notation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            content = {
                "errors": {
                    "auth": {
                        "required": "Authentication required"
                    }
                }
            }
            en_file.write_text(json.dumps(content))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")
            message = provider.get_message("errors.auth.required")
            assert message == "Authentication required"

    def test_get_message_nonexistent_key(self):
        """Should return key as fallback when message not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "Test"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")
            message = provider.get_message("errors.nonexistent")
            assert message == "errors.nonexistent"

    def test_get_message_invalid_dot_notation(self):
        """Should handle invalid dot notation gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "Test"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")
            # Empty key
            assert provider.get_message("") == ""


class TestMessageProviderLocaleLoading:
    """Test loading messages from different locale files."""

    def test_load_messages_for_locale(self):
        """Should load messages for specified locale."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create en.json
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "English message"}}))

            # Create ko.json
            ko_file = Path(tmpdir) / "ko.json"
            ko_file.write_text(json.dumps({"errors": {"test": "한국어 메시지"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")

            # Get English message
            en_msg = provider.get_message("errors.test", locale="en")
            assert en_msg == "English message"

            # Get Korean message
            ko_msg = provider.get_message("errors.test", locale="ko")
            assert ko_msg == "한국어 메시지"

    def test_load_nonexistent_locale(self):
        """Should fall back to default locale when requested locale doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "English"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")

            # Request non-existent locale
            message = provider.get_message("errors.test", locale="fr")
            assert message == "English"  # Falls back to default


class TestMessageProviderFallbackChain:
    """Test fallback chain: requested locale -> default locale -> original message."""

    def test_fallback_to_default_locale(self):
        """Should fall back to default locale when key missing in requested locale."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create en.json with full content
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({
                "errors": {
                    "auth": {"required": "Auth required"},
                    "validation": {"invalid": "Invalid input"}
                }
            }))

            # Create ko.json with partial content
            ko_file = Path(tmpdir) / "ko.json"
            ko_file.write_text(json.dumps({
                "errors": {
                    "auth": {"required": "인증 필요"}
                    # validation.invalid is missing
                }
            }))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")

            # Korean message exists
            ko_msg = provider.get_message("errors.auth.required", locale="ko")
            assert ko_msg == "인증 필요"

            # Falls back to English for missing Korean
            en_msg = provider.get_message("errors.validation.invalid", locale="ko")
            assert en_msg == "Invalid input"

    def test_fallback_to_original_message(self):
        """Should return original message when key missing in both locales."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "Test"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")

            # Key doesn't exist in any locale
            message = provider.get_message("errors.missing", locale="ko")
            assert message == "errors.missing"

    def test_fallback_with_custom_default_message(self):
        """Should use custom default message when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "Test"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")

            message = provider.get_message("errors.missing", default="Custom default")
            assert message == "Custom default"


class TestMessageProviderCaching:
    """Test message caching for performance."""

    def test_messages_are_cached(self):
        """Should cache loaded locale messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "Test"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")

            # First call loads from file
            msg1 = provider.get_message("errors.test")

            # Second call uses cache
            msg2 = provider.get_message("errors.test")

            assert msg1 == msg2 == "Test"

    def test_cache_invalidation_on_reload(self):
        """Should be able to reload locale messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({"errors": {"test": "Original"}}))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")

            # Get original message
            msg1 = provider.get_message("errors.test")
            assert msg1 == "Original"

            # Update file
            en_file.write_text(json.dumps({"errors": {"test": "Updated"}}))

            # Reload
            provider.reload_locale("en")

            # Get updated message
            msg2 = provider.get_message("errors.test")
            assert msg2 == "Updated"


class TestMessageProviderFormatting:
    """Test message formatting with parameters."""

    def test_format_message_with_parameters(self):
        """Should format message with provided parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({
                "errors": {
                    "user_not_found": "User {user_id} not found"
                }
            }))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")
            message = provider.get_message("errors.user_not_found", user_id=123)
            assert message == "User 123 not found"

    def test_format_message_with_multiple_parameters(self):
        """Should format message with multiple parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({
                "errors": {
                    "validation_error": "Field '{field}' has {error}"
                }
            }))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")
            message = provider.get_message(
                "errors.validation_error",
                field="email",
                error="invalid format"
            )
            assert message == "Field 'email' has invalid format"

    def test_format_message_missing_parameter(self):
        """Should leave placeholder when parameter is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            en_file = Path(tmpdir) / "en.json"
            en_file.write_text(json.dumps({
                "errors": {
                    "test": "Value {x} and {y}"
                }
            }))

            provider = MessageProvider(locale_dir=tmpdir, default_locale="en")
            # Only provide x, not y
            message = provider.get_message("errors.test", x=1)
            assert "1" in message
            assert "{y}" in message or "y" in message  # Placeholder remains


class TestMessageProviderMultipleFallbackLocales:
    """Test fallback chain with multiple fallback locales."""

    def test_multiple_fallback_loales(self):
        """Should try multiple fallback locales in order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create locale files
            (Path(tmpdir) / "en.json").write_text(json.dumps({
                "errors": {
                    "common": "Common error",
                    "en_only": "English only"
                }
            }))
            (Path(tmpdir) / "ko.json").write_text(json.dumps({
                "errors": {
                    "common": "일반적인 오류"
                    # en_only is missing
                }
            }))
            (Path(tmpdir) / "ja.json").write_text(json.dumps({
                "errors": {
                    "common": "一般的なエラー"
                }
            }))

            provider = MessageProvider(
                locale_dir=tmpdir,
                default_locale="en",
                fallback_locales=["ko", "ja"]
            )

            # Japanese exists
            msg = provider.get_message("errors.common", locale="ja")
            assert msg == "一般的なエラー"

            # Korean falls back to English for en_only
            msg = provider.get_message("errors.en_only", locale="ko")
            assert msg == "English only"
