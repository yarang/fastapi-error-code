"""
Exception tracing and PII masking for distributed tracing

Provides exception recording in spans with PII masking:
- ExceptionTracer: Automatic exception event recording
- PIIMasker: Sensitive data masking in span attributes
- Stack trace sanitization
- Integration with BaseAppException
"""

import re
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Pattern

from opentelemetry import trace
from opentelemetry.trace import Span
from opentelemetry.sdk.trace import Status, StatusCode

from fastapi_error_codes.base import BaseAppException


@dataclass
class PIIPattern:
    """
    Configuration for a PII detection pattern.

    Attributes:
        name: Pattern name for identification
        pattern: Regex pattern to match PII
        replacement: Replacement string for matched PII
    """
    name: str
    pattern: str
    replacement: str

    def as_regex(self) -> Pattern:
        """Compile pattern as regex."""
        return re.compile(self.pattern)


class PIIMasker:
    """
    PII masking utility for sanitizing sensitive data.

    Masks common PII types:
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - SSN/Tax IDs
    - Custom patterns
    """

    # Default PII patterns
    DEFAULT_PATTERNS = [
        PIIPattern(
            name="email",
            pattern=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            replacement="***@***.***"
        ),
        PIIPattern(
            name="phone",
            pattern=r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
            replacement="***-***-****"
        ),
        PIIPattern(
            name="credit_card",
            pattern=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            replacement="****-****-****-****"
        ),
        PIIPattern(
            name="ssn",
            pattern=r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
            replacement="***-**-****"
        ),
    ]

    def __init__(self, custom_patterns: Optional[List[PIIPattern]] = None):
        """
        Initialize PII masker.

        Args:
            custom_patterns: Optional custom PII patterns
        """
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)

        # Compile all patterns
        self.compiled_patterns = [p.as_regex() for p in self.patterns]

    def mask_email(self, email: str) -> str:
        """
        Mask email address showing first char and domain.

        Args:
            email: Email address to mask

        Returns:
            Masked email address
        """
        if "@" not in email:
            return email

        username, domain = email.split("@", 1)
        if len(username) > 0:
            masked_username = username[0] + "***"
        else:
            masked_username = "***"

        return f"{masked_username}@{domain}"

    def mask_phone(self, phone: str) -> str:
        """
        Mask phone number showing last 4 digits.

        Args:
            phone: Phone number to mask

        Returns:
            Masked phone number
        """
        # Extract digits
        digits = re.sub(r"\D", "", phone)

        if len(digits) >= 4:
            last_four = digits[-4:]
            return f"***-***-{last_four}"
        return phone

    def mask_credit_card(self, card: str) -> str:
        """
        Mask credit card showing last 4 digits.

        Args:
            card: Credit card number to mask

        Returns:
            Masked credit card number
        """
        # Extract digits
        digits = re.sub(r"\D", "", card)

        if len(digits) >= 4:
            last_four = digits[-4:]
            return f"****-****-****-{last_four}"
        return card

    def mask_ssn(self, ssn: str) -> str:
        """
        Mask SSN showing last 4 digits.

        Args:
            ssn: SSN to mask

        Returns:
            Masked SSN
        """
        # Extract digits
        digits = re.sub(r"\D", "", ssn)

        if len(digits) >= 4:
            last_four = digits[-4:]
            return f"***-**-{last_four}"
        return ssn

    def mask_value(self, value: str) -> str:
        """
        Mask PII in string value using all patterns.

        Args:
            value: String value to mask

        Returns:
            String with PII masked
        """
        result = value
        # First apply specific patterns from DEFAULT_PATTERNS
        result = self._mask_email_in_string(result)
        result = self._mask_phone_in_string(result)
        result = self._mask_credit_card_in_string(result)
        result = self._mask_ssn_in_string(result)

        # Then apply custom patterns
        for i, pattern in enumerate(self.compiled_patterns):
            if i >= len(self.DEFAULT_PATTERNS):  # Custom patterns only
                result = pattern.sub(self.patterns[i].replacement, result)

        return result

    def _mask_email_in_string(self, value: str) -> str:
        """Mask email addresses in string."""
        return re.sub(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            lambda m: self.mask_email(m.group(0)),
            value
        )

    def _mask_phone_in_string(self, value: str) -> str:
        """Mask phone numbers in string."""
        return re.sub(
            r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
            lambda m: self.mask_phone(m.group(0)),
            value
        )

    def _mask_credit_card_in_string(self, value: str) -> str:
        """Mask credit cards in string."""
        return re.sub(
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            lambda m: self.mask_credit_card(m.group(0)),
            value
        )

    def _mask_ssn_in_string(self, value: str) -> str:
        """Mask SSNs in string."""
        return re.sub(
            r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
            lambda m: self.mask_ssn(m.group(0)),
            value
        )

    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask PII in dictionary values.

        Args:
            data: Dictionary to mask

        Returns:
            Dictionary with PII masked
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Check if key suggests PII type
                if "email" in key.lower():
                    result[key] = self.mask_email(value)
                elif "phone" in key.lower():
                    result[key] = self.mask_phone(value)
                elif "card" in key.lower() or "credit" in key.lower():
                    result[key] = self.mask_credit_card(value)
                elif "ssn" in key.lower() or "tax" in key.lower():
                    result[key] = self.mask_ssn(value)
                else:
                    result[key] = self.mask_value(value)
            elif isinstance(value, dict):
                result[key] = self.mask_dict(value)
            elif isinstance(value, list):
                result[key] = self.mask_list(value)
            else:
                result[key] = value
        return result

    def mask_list(self, data: List[Any]) -> List[Any]:
        """
        Recursively mask PII in list values.

        Args:
            data: List to mask

        Returns:
            List with PII masked
        """
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(self.mask_value(item))
            elif isinstance(item, dict):
                result.append(self.mask_dict(item))
            elif isinstance(item, list):
                result.append(self.mask_list(item))
            else:
                result.append(item)
        return result


def sanitize_stacktrace(stacktrace: str) -> str:
    """
    Sanitize stack trace by removing sensitive file paths.

    Args:
        stacktrace: Raw stack trace string

    Returns:
        Sanitized stack trace with paths removed
    """
    lines = stacktrace.split("\n")
    sanitized_lines = []

    for line in lines:
        # Remove file paths but keep filenames
        sanitized = re.sub(r'File "[^"]*/([^"/]+)",', r'File "\1",', line)
        sanitized = re.sub(r"File '[^']*/([^'/]+)',", r"File '\1',", sanitized)
        sanitized_lines.append(sanitized)

    return "\n".join(sanitized_lines)


class ExceptionTracer:
    """
    Exception tracer for recording exceptions in spans.

    Automatically records exceptions as span events with:
    - Exception type and message
    - Sanitized stack trace
    - Error code (from BaseAppException if available)
    - PII masking in attributes
    """

    def __init__(self, masker: Optional[PIIMasker] = None):
        """
        Initialize exception tracer.

        Args:
            masker: Optional PII masker for sanitizing exception data
        """
        self.masker = masker or PIIMasker()

    def record_exception(
        self,
        span: Span,
        exception: Exception,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record exception in span as event.

        Args:
            span: Span to record exception in
            exception: Exception to record
            attributes: Optional additional attributes
        """
        if not span.is_recording():
            return

        # Extract exception information
        exc_type = self._get_exception_type(exception)
        exc_message = self._get_exception_message(exception)
        exc_stacktrace = self._get_sanitized_stacktrace(exception)

        # Mask PII in message and attributes
        masked_message = self.masker.mask_value(exc_message)

        # Create event attributes
        event_attributes = {
            "exception.type": exc_type,
            "exception.message": masked_message,
            "exception.stacktrace": exc_stacktrace,
        }

        # Add error code if available
        error_code = self.extract_error_code(exception)
        if error_code is not None:
            event_attributes["exception.error_code"] = str(error_code)

        # Mask and add custom attributes
        if attributes:
            masked_attrs = self.masker.mask_dict(attributes)
            event_attributes.update(masked_attrs)

        # Record exception as span event
        span.add_event(
            name="exception",
            attributes=event_attributes
        )

        # Set span status to error
        span.set_status(
            Status(StatusCode.ERROR, masked_message)
        )

    def extract_error_code(self, exception: Exception) -> Optional[int]:
        """
        Extract error code from BaseAppException.

        Args:
            exception: Exception to extract error code from

        Returns:
            Error code if available, None otherwise
        """
        if isinstance(exception, BaseAppException):
            return exception.error_code
        return None

    def _get_exception_type(self, exception: Exception) -> str:
        """Get exception type name."""
        return type(exception).__name__

    def _get_exception_message(self, exception: Exception) -> str:
        """Get exception message."""
        return str(exception)

    def _get_sanitized_stacktrace(self, exception: Exception) -> str:
        """Get sanitized stack trace from exception."""
        stacktrace = "".join(traceback.format_tb(exception.__traceback__))
        return sanitize_stacktrace(stacktrace)
