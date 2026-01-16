"""
Sentry error tracking integration with PII masking.

This module provides SentryIntegration for sending error events
to Sentry with PII masking and graceful degradation.
"""

import copy
import re
import threading
from typing import Any, Dict, List, Optional, Union

from fastapi_error_codes.metrics.config import MetricsConfig


def mask_pii(data: Any, patterns: List[str]) -> Any:
    """
    Mask PII (Personally Identifiable Information) in data.

    Recursively masks fields matching PII patterns in dictionaries
    and lists. Preserves the original data structure.

    Args:
        data: Data to mask (dict, list, or primitive)
        patterns: List of field patterns to mask

    Returns:
        Masked copy of the data

    Example:
        ```python
        data = {"email": "user@example.com", "name": "John"}
        masked = mask_pii(data, ["email"])
        # {"email": "***@***.***", "name": "John"}
        ```
    """
    if not patterns:
        return data

    if data is None:
        return None

    if isinstance(data, dict):
        return _mask_dict(data, patterns)
    elif isinstance(data, list):
        return [_mask_item(item, patterns) for item in data]
    else:
        return data


def _mask_dict(data: Dict[str, Any], patterns: List[str]) -> Dict[str, Any]:
    """Mask PII in dictionary."""
    masked = {}
    for key, value in data.items():
        if any(pattern in key.lower() for pattern in patterns):
            # Mask this field
            if value is None:
                masked[key] = None
            elif isinstance(value, str) and "@" in value:
                # Email masking
                masked[key] = "***@***.***"
            else:
                # General masking
                masked[key] = "***"
        else:
            # Recursively mask nested structures
            if isinstance(value, dict):
                masked[key] = _mask_dict(value, patterns)
            elif isinstance(value, list):
                masked[key] = [_mask_item(item, patterns) for item in value]
            else:
                masked[key] = value
    return masked


def _mask_item(item: Any, patterns: List[str]) -> Any:
    """Mask PII in a single item."""
    if item is None:
        return None
    if isinstance(item, dict):
        return _mask_dict(item, patterns)
    elif isinstance(item, list):
        return [_mask_item(sub_item, patterns) for sub_item in item]
    else:
        return item


class SentryIntegration:
    """
    Sentry error tracking integration with PII masking.

    Provides integration with Sentry SDK for error tracking with:
    - Automatic PII masking before sending to Sentry
    - Graceful degradation when Sentry is unavailable
    - Async/batch sending support
    - Custom breadcrumb and scope management

    Example:
        ```python
        config = MetricsConfig(
            sentry_enabled=True,
            sentry_dsn="https://key@sentry.io/123",
            pii_patterns=["email", "password"]
        )
        integration = SentryIntegration(config)
        integration.initialize()

        # Capture error
        integration.capture_event(
            error_code=404,
            error_name="NotFound",
            message="Resource not found",
            detail={"email": "user@example.com"}  # Will be masked
        )
        ```
    """

    def __init__(self, config: MetricsConfig) -> None:
        """
        Initialize Sentry integration.

        Args:
            config: Metrics configuration with Sentry settings
        """
        self.config = config
        self.enabled = config.sentry_enabled
        self.dsn = config.sentry_dsn
        self.pii_patterns = config.pii_patterns
        self._lock = threading.Lock()
        self._initialized = False
        self._sentry_sdk = None

        # Try to import sentry_sdk
        try:
            import sentry_sdk
            self._sentry_sdk = sentry_sdk
        except ImportError:
            pass

    def initialize(self) -> None:
        """
        Initialize Sentry SDK.

        Should be called once at application startup.
        Gracefully degrades if Sentry is unavailable.

        Example:
            ```python
            integration = SentryIntegration(config)
            integration.initialize()
            ```
        """
        if not self.enabled or not self.dsn:
            return

        if self._sentry_sdk is None:
            return

        with self._lock:
            if self._initialized:
                return

            try:
                self._sentry_sdk.init(
                    dsn=self.dsn,
                    traces_sample_rate=0.1,  # Sample 10% of transactions
                    # Disable some default integrations that might capture PII
                    send_default_pii=False,
                )
                self._initialized = True
            except Exception:
                # Graceful degradation - don't crash if Sentry init fails
                pass

    def capture_event(
        self,
        error_code: int,
        error_name: str,
        message: str,
        detail: Any = None,
        level: str = "error",
    ) -> Optional[str]:
        """
        Capture an error event and send to Sentry.

        PII is masked from detail before sending.

        Args:
            error_code: Application error code
            error_name: Exception class name
            message: Error message
            detail: Additional error details (will be masked)
            level: Event level (error, warning, info)

        Returns:
            Sentry event ID if sent, None otherwise

        Example:
            ```python
            event_id = integration.capture_event(
                error_code=404,
                error_name="NotFound",
                message="Resource not found",
                detail={"email": "user@example.com"}
            )
            ```
        """
        if not self.enabled or self._sentry_sdk is None:
            return None

        try:
            # Mask PII from detail
            masked_detail = mask_pii(detail, self.pii_patterns) if detail else None

            # Create Sentry event
            event = {
                "level": level,
                "message": f"[{error_name}] {message}",
                "extra": {
                    "error_code": error_code,
                    "error_name": error_name,
                    "detail": masked_detail,
                },
                "tags": {
                    "error_code": str(error_code),
                    "error_name": error_name,
                },
            }

            return self._sentry_sdk.capture_event(event)
        except Exception:
            # Graceful degradation - don't crash on Sentry errors
            return None

    def capture_exception(
        self,
        exception: Exception,
        detail: Any = None,
    ) -> Optional[str]:
        """
        Capture a Python exception and send to Sentry.

        PII is masked from detail before sending.

        Args:
            exception: Python exception to capture
            detail: Additional context (will be masked)

        Returns:
            Sentry event ID if sent, None otherwise

        Example:
            ```python
            try:
                risky_operation()
            except Exception as e:
                integration.capture_exception(e, detail={"email": "user@example.com"})
            ```
        """
        if not self.enabled or self._sentry_sdk is None:
            return None

        try:
            # Mask PII from detail
            masked_detail = mask_pii(detail, self.pii_patterns) if detail else None

            # Add masked detail to scope
            self._sentry_sdk.configure_scope(
                lambda scope: scope.set_context("detail", {"masked_detail": masked_detail})
            )

            return self._sentry_sdk.capture_exception(exception)
        except Exception:
            # Graceful degradation
            return None

    def add_breadcrumb(
        self,
        category: str,
        message: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a breadcrumb for error context.

        Breadcrumbs provide context leading up to an error.

        Args:
            category: Breadcrumb category
            message: Breadcrumb message
            level: Breadcrumb level
            data: Additional data (will be masked)

        Example:
            ```python
            integration.add_breadcrumb(
                category="auth",
                message="User login failed",
                level="warning",
                data={"user_id": "123"}
            )
            ```
        """
        if not self.enabled or self._sentry_sdk is None:
            return

        try:
            # Mask PII from data
            masked_data = mask_pii(data, self.pii_patterns) if data else None

            self._sentry_sdk.add_breadcrumb(
                category=category,
                message=message,
                level=level,
                data=masked_data,
            )
        except Exception:
            # Graceful degradation
            pass

    def configure_scope(self, data: Dict[str, Any]) -> None:
        """
        Configure Sentry scope with custom data.

        Args:
            data: Scope data (will be masked)

        Example:
            ```python
            integration.configure_scope({
                "user_id": "123",
                "request_id": "abc"
            })
            ```
        """
        if not self.enabled or self._sentry_sdk is None:
            return

        try:
            # Mask PII from data
            masked_data = mask_pii(data, self.pii_patterns)

            def set_scope(scope):
                for key, value in masked_data.items():
                    scope.set_tag(key, str(value))

            self._sentry_sdk.configure_scope(set_scope)
        except Exception:
            # Graceful degradation
            pass

    def flush(self, timeout: float = 2.0) -> bool:
        """
        Flush pending events to Sentry.

        Args:
            timeout: Flush timeout in seconds

        Returns:
            True if flush succeeded, False otherwise

        Example:
            ```python
            # Before shutdown
            integration.flush(timeout=5.0)
            ```
        """
        if not self.enabled or self._sentry_sdk is None:
            return False

        try:
            return self._sentry_sdk.flush(timeout)
        except Exception:
            return False

    def _mask_event_data(self, data: Any) -> Any:
        """
        Mask PII in event data using configured patterns.

        Args:
            data: Data to mask

        Returns:
            Masked data
        """
        return mask_pii(data, self.pii_patterns)
