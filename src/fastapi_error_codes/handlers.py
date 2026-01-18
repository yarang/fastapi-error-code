"""
Exception handlers for fastapi-error-codes package.

This module provides the setup_exception_handler function for integrating
error handling with FastAPI applications.
"""

import contextlib
import logging
import traceback
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from opentelemetry import trace

from fastapi_error_codes.base import BaseAppException
from fastapi_error_codes.config import ErrorHandlerConfig
from fastapi_error_codes.i18n import MessageProvider
from fastapi_error_codes.models import ErrorResponse

# Metrics integration (optional)
try:
    from fastapi_error_codes.metrics.collector import ErrorMetricsCollector
    from fastapi_error_codes.metrics.config import MetricsConfig
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


logger = logging.getLogger(__name__)


def _parse_accept_language(header: str) -> List[str]:
    """
    Parse Accept-Language header and return ordered list of locales.

    Args:
        header: Accept-Language header value (e.g., "ko-KR,ko;q=0.9,en;q=0.8")

    Returns:
        List of locale codes in order of preference

    Example:
        ```python
        locales = _parse_accept_language("ko-KR,ko;q=0.9,en;q=0.8")
        # Returns: ["ko-KR", "ko", "en"]
        ```
    """
    if not header:
        return []

    locales = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue

        # Extract locale code (before ; or end of string)
        locale = part.split(";")[0].strip()
        if locale:
            locales.append(locale)

    return locales


def _resolve_message(
    message: str,
    provider: MessageProvider,
    accept_locales: List[str],
    detail: Optional[Any]
) -> str:
    """
    Resolve error message with i18n support.

    Args:
        message: Original message or message key
        provider: MessageProvider instance
        accept_locales: Ordered list of accepted locales from Accept-Language header
        detail: Optional detail dict with formatting parameters

    Returns:
        Resolved message string
    """
    # Try to resolve as message key (dot notation)
    # If message contains dots, it might be a nested key
    if "." in message:
        # Try each locale in the Accept-Language header
        for locale in accept_locales:
            resolved = provider.get_message(
                message,
                locale=locale,
                **(detail if isinstance(detail, dict) else {})
            )
            # If message was resolved (not same as key), use it
            if resolved != message:
                return resolved

        # Fallback to default locale
        resolved = provider.get_message(
            message,
            locale=provider.default_locale,
            **(detail if isinstance(detail, dict) else {})
        )
        if resolved != message:
            return resolved

    # If not a key or not found, format with detail parameters if provided
    if isinstance(detail, dict) and detail:
        try:
            # Use provider's partial formatting
            return provider._format_message_partial(message, **detail)
        except Exception:
            pass

    return message


async def _exception_handler(
    request: Request,
    exc: Exception,
    config: ErrorHandlerConfig,
    provider: MessageProvider,
    metrics_collector: Optional["ErrorMetricsCollector"] = None,
) -> JSONResponse:
    """
    Handle exceptions and convert to ErrorResponse.

    Args:
        request: FastAPI request instance
        exc: The exception that was raised
        config: Error handler configuration
        provider: MessageProvider for i18n

    Returns:
        JSONResponse with error details
    """
    # Parse Accept-Language header
    accept_language = request.headers.get("accept-language", "")
    accept_locales = _parse_accept_language(accept_language)

    # Determine error code and status
    if isinstance(exc, BaseAppException):
        error_code = exc.error_code
        status_code = exc.status_code
        message = exc.message
        detail = exc.detail
        error_name = exc.error_name
        headers = exc.headers
    else:
        # Unknown exception
        error_code = 500
        status_code = 500
        message = str(exc)
        detail = None
        error_name = exc.__class__.__name__
        headers = None

    # Resolve message with i18n
    resolved_message = _resolve_message(message, provider, accept_locales, detail)

    # Create error response
    error_response = ErrorResponse(
        error_code=error_code,
        message=resolved_message,
        status_code=status_code,
        detail=detail if config.debug_mode else None,
        error_name=error_name if config.debug_mode else None
    )

    # Add traceback in debug mode if enabled
    if config.debug_mode and config.include_traceback:
        traceback_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        # Add traceback to detail
        if error_response.detail is None:
            error_response.detail = {}
        if isinstance(error_response.detail, dict):
            error_response.detail["traceback"] = traceback_str

    # Convert to dict for JSON response
    response_data = error_response.model_dump() if hasattr(error_response, 'model_dump') else error_response.dict()

    # Record metrics (non-blocking, never affects response)
    if metrics_collector and METRICS_AVAILABLE:
        with contextlib.suppress(Exception):
            metrics_collector.record(
                error_code=error_code,
                error_name=error_name,
                status_code=status_code,
                message=message,
                detail=detail if config.debug_mode else None,
                path=request.url.path,
                method=request.method,
            )

    # Get trace ID from OpenTelemetry context if available
    trace_id: Optional[str] = None
    try:
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            if span_context.is_valid:
                trace_id = format(span_context.trace_id, "032x")
    except Exception:
        # Silently ignore trace ID retrieval failures
        pass

    # Prepare response headers
    response_headers: Dict[str, Any] = {}
    if headers:
        response_headers.update(headers)

    # Add X-Trace-ID header if available
    if trace_id:
        response_headers["X-Trace-ID"] = trace_id

    # Create JSONResponse
    return JSONResponse(
        status_code=status_code,
        content=response_data,
        headers=response_headers
    )


def setup_exception_handler(
    app: FastAPI,
    config: Optional[ErrorHandlerConfig] = None,
    metrics_config: Optional["MetricsConfig"] = None,
) -> None:
    """
    Setup global exception handler for FastAPI application.

    This function registers exception handlers with the FastAPI app to
    convert exceptions to standardized ErrorResponse objects with i18n support.

    Args:
        app: FastAPI application instance
        config: Optional error handler configuration (uses default if None)
        metrics_config: Optional metrics configuration for error tracking (SPEC-MONITOR-002)

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_error_codes.config import ErrorHandlerConfig
        from fastapi_error_codes.handlers import setup_exception_handler

        app = FastAPI()

        # With default config
        setup_exception_handler(app)

        # With custom config
        config = ErrorHandlerConfig(
            default_locale="ko",
            debug_mode=True
        )
        setup_exception_handler(app, config)
        ```
    """
    if config is None:
        config = ErrorHandlerConfig()

    # Initialize metrics collector if metrics_config provided
    metrics_collector = None
    if metrics_config and METRICS_AVAILABLE and metrics_config.enabled:
        try:
            metrics_collector = ErrorMetricsCollector(metrics_config)
            # Store in app state for external access
            app.state.metrics_collector = metrics_collector
        except Exception:
            # Gracefully degrade if metrics initialization fails
            metrics_collector = None

    # Initialize message provider
    provider = MessageProvider(
        locale_dir=config.locale_dir,
        default_locale=config.default_locale,
        fallback_locales=config.fallback_locales
    )

    async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Wrapper exception handler."""
        return await _exception_handler(request, exc, config, provider, metrics_collector)

    # Register exception handler for all exceptions
    app.add_exception_handler(Exception, exception_handler)

    logger.info(
        f"Registered exception handler for FastAPI app "
        f"(locale={config.default_locale}, debug={config.debug_mode})"
    )
