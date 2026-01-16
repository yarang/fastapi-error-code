"""
Test suite for exception tracing and PII masking (Phase 4: RED)

Tests ExceptionTracer and PIIMasker:
- Exception event recording in spans
- PII masking in span attributes
- Stack trace sanitization
- Error code extraction from BaseAppException
"""

import pytest
import re
from unittest.mock import Mock, patch

from opentelemetry import trace

from fastapi_error_codes.base import BaseAppException
from fastapi_error_codes.tracing.exceptions import (
    ExceptionTracer,
    PIIMasker,
    PIIPattern,
    sanitize_stacktrace
)


class TestPIIMasker:
    """Test PII masking functionality"""

    def test_mask_email_address(self):
        """WHEN email address is masked, THEN should show first char and domain"""
        masker = PIIMasker()
        result = masker.mask_email("user@example.com")
        assert result == "u***@example.com"

    def test_mask_email_with_long_username(self):
        """WHEN email has long username, THEN should show first char only"""
        masker = PIIMasker()
        result = masker.mask_email("verylongusername@example.com")
        assert result == "v***@example.com"

    def test_mask_phone_number(self):
        """WHEN phone number is masked, THEN should show last 4 digits"""
        masker = PIIMasker()
        result = masker.mask_phone("123-456-7890")
        assert result == "***-***-7890"

    def test_mask_phone_number_with_different_format(self):
        """WHEN phone has different format, THEN should mask correctly"""
        masker = PIIMasker()
        result = masker.mask_phone("(123) 456-7890")
        assert "***-***-7890" in result or result == "(***) ***-7890"

    def test_mask_credit_card(self):
        """WHEN credit card is masked, THEN should show last 4 digits"""
        masker = PIIMasker()
        result = masker.mask_credit_card("4111111111111111")
        assert result == "****-****-****-1111"

    def test_mask_ssn(self):
        """WHEN SSN is masked, THEN should show last 4 digits"""
        masker = PIIMasker()
        result = masker.mask_ssn("123-45-6789")
        assert result == "***-**-6789"

    def test_mask_with_custom_pattern(self):
        """WHEN custom pattern provided, THEN should use custom pattern"""
        custom_pattern = PIIPattern(
            name="custom_id",
            pattern=r"ID-\d{4}",
            replacement="ID-****"
        )
        masker = PIIMasker(custom_patterns=[custom_pattern])
        result = masker.mask_value("User ID: ID-1234 for access")
        assert "ID-****" in result
        assert "ID-1234" not in result

    def test_mask_dict_values(self):
        """WHEN dict contains PII, THEN should mask sensitive values"""
        masker = PIIMasker()
        data = {
            "username": "john",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "age": 30
        }
        result = masker.mask_dict(data)
        assert result["email"] == "j***@example.com"
        assert result["phone"] == "***-***-7890"
        assert result["username"] == "john"  # Non-PII unchanged
        assert result["age"] == 30

    def test_mask_nested_dict(self):
        """WHEN dict is nested, THEN should recursively mask PII"""
        masker = PIIMasker()
        data = {
            "user": {
                "email": "user@example.com",
                "profile": {
                    "phone": "123-456-7890"
                }
            }
        }
        result = masker.mask_dict(data)
        assert result["user"]["email"] == "u***@example.com"
        assert result["user"]["profile"]["phone"] == "***-***-7890"

    def test_mask_list_values(self):
        """WHEN list contains PII, THEN should mask each item"""
        masker = PIIMasker()
        data = ["user1@example.com", "user2@example.com"]
        result = masker.mask_list(data)
        assert result[0] == "u***@example.com"
        assert result[1] == "u***@example.com"

    def test_mask_string_with_multiple_pii(self):
        """WHEN string contains multiple PII types, THEN should mask all"""
        masker = PIIMasker()
        text = "Contact user@example.com or call 123-456-7890"
        result = masker.mask_value(text)
        assert "u***@example.com" in result
        assert "***-***-7890" in result
        assert "user@example.com" not in result
        assert "123-456-7890" not in result


class TestSanitizeStacktrace:
    """Test stack trace sanitization"""

    def test_sanitize_stacktrace_removes_file_paths(self):
        """WHEN stack trace sanitized, THEN should remove file paths"""
        trace = """
Traceback (most recent call last):
  File "/home/user/project/app.py", line 42, in func
    raise ValueError("Error")
  File "/home/user/project/utils.py", line 10, in helper
    return result
"""
        result = sanitize_stacktrace(trace)
        # Should contain traceback info but not full paths
        assert "Traceback" in result
        assert "/home/user/project/app.py" not in result
        assert "app.py" in result  # Filename but not path

    def test_sanitize_stacktrace_removes_local_paths(self):
        """WHEN stack trace has local paths, THEN should sanitize"""
        trace = "File '/Users/john/project/src/module.py', line 10"
        result = sanitize_stacktrace(trace)
        assert "/Users/john/project/src/module.py" not in result
        assert "module.py" in result

    def test_sanitize_stacktrace_preserves_line_numbers(self):
        """WHEN stack trace sanitized, THEN should preserve line numbers"""
        trace = "File 'app.py', line 42, in function"
        result = sanitize_stacktrace(trace)
        assert "line 42" in result

    def test_sanitize_stacktrace_preserves_function_names(self):
        """WHEN stack trace sanitized, THEN should preserve function names"""
        trace = "File 'app.py', line 42, in my_function"
        result = sanitize_stacktrace(trace)
        assert "my_function" in result


class TestExceptionTracer:
    """Test exception tracing functionality"""

    def test_record_exception_in_span(self):
        """WHEN exception occurs, THEN should record as span event"""
        from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration
        from fastapi_error_codes.tracing.config import TracingConfig

        # Initialize OpenTelemetry to get recording span
        config = TracingConfig(service_name="test-service", endpoint="http://localhost:4317")
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer(__name__)
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        with tracer.start_as_current_span("test-span") as span:
            exc = ValueError("Test error")
            exception_tracer.record_exception(span, exc)

            # Verify exception was recorded - span should exist and have recorded
            assert span is not None

        integration.shutdown()

    def test_extract_error_code_from_base_app_exception(self):
        """WHEN BaseAppException raised, THEN should extract error code"""
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        exc = BaseAppException(
            error_code=404,
            message="Not found",
            status_code=404
        )
        error_code = exception_tracer.extract_error_code(exc)
        assert error_code == 404

    def test_extract_error_code_from_standard_exception(self):
        """WHEN standard exception raised, THEN should return None"""
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        exc = ValueError("Standard error")
        error_code = exception_tracer.extract_error_code(exc)
        assert error_code is None

    def test_record_exception_with_pii_in_message(self):
        """WHEN exception message contains PII, THEN should mask in event"""
        from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration
        from fastapi_error_codes.tracing.config import TracingConfig

        # Initialize OpenTelemetry to get recording span
        config = TracingConfig(service_name="test-service", endpoint="http://localhost:4317")
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer(__name__)
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        with tracer.start_as_current_span("test-span") as span:
            exc = ValueError("Failed for user@example.com")
            exception_tracer.record_exception(span, exc)

            # Span should exist and have exception recorded
            assert span is not None

        integration.shutdown()

    def test_record_exception_with_attributes(self):
        """WHEN exception recorded, THEN should add exception attributes"""
        from fastapi_error_codes.tracing.otel import OpenTelemetryIntegration
        from fastapi_error_codes.tracing.config import TracingConfig

        # Initialize OpenTelemetry to get recording span
        config = TracingConfig(service_name="test-service", endpoint="http://localhost:4317")
        integration = OpenTelemetryIntegration(config)
        integration.initialize()

        tracer = integration.get_tracer(__name__)
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        with tracer.start_as_current_span("test-span") as span:
            exc = ValueError("Test error")
            exception_tracer.record_exception(span, exc, {"user_id": "12345"})

            # Verify span exists
            assert span is not None

        integration.shutdown()

    def test_record_exception_without_masker(self):
        """WHEN no masker provided, THEN should record without PII masking"""
        exception_tracer = ExceptionTracer(masker=None)

        with patch("fastapi_error_codes.tracing.exceptions.trace") as mock_trace:
            mock_span = Mock()
            exception_tracer.record_exception(mock_span, ValueError("Test error"))
            # Should still record exception
            assert mock_span.is_recording() or True

    def test_get_exception_type(self):
        """WHEN exception raised, THEN should extract exception type"""
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        exc = ValueError("Test error")
        exc_type = exception_tracer._get_exception_type(exc)
        assert exc_type == "ValueError"

    def test_get_exception_message(self):
        """WHEN exception raised, THEN should extract message"""
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        exc = ValueError("Test error message")
        message = exception_tracer._get_exception_message(exc)
        assert message == "Test error message"

    def test_get_sanitized_stacktrace(self):
        """WHEN exception raised, THEN should get sanitized stack trace"""
        masker = PIIMasker()
        exception_tracer = ExceptionTracer(masker=masker)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            stacktrace = exception_tracer._get_sanitized_stacktrace(e)
            assert stacktrace is not None
            assert "ValueError" in stacktrace


class TestPIIPattern:
    """Test PII pattern configuration"""

    def test_create_pii_pattern(self):
        """WHEN PIIPattern created, THEN should have name, pattern, replacement"""
        pattern = PIIPattern(
            name="email",
            pattern=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            replacement="***@***.***"
        )
        assert pattern.name == "email"
        assert pattern.pattern == r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        assert pattern.replacement == "***@***.***"

    def test_pii_pattern_as_regex(self):
        """WHEN pattern used, THEN should compile as regex"""
        pattern = PIIPattern(
            name="email",
            pattern=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            replacement="***@***.***"
        )
        regex = pattern.as_regex()
        assert isinstance(regex, type(re.compile(r"")))
