"""
Decorator for registering exception classes with error codes.

This module provides the @register_exception decorator that automatically
registers exception classes with the global exception registry.
"""

import logging
import re
from typing import Any, Callable, Dict, Optional, Type

from fastapi_error_codes.base import BaseAppException
from fastapi_error_codes.registry import _registry

# Configure logger for this module
logger = logging.getLogger(__name__)


def register_exception(
    error_code: int,
    message: Optional[str] = None,
    message_key: Optional[str] = None,
    status_code: int = 400,
    domain: Optional[str] = None,
    **metadata: Any,
) -> Callable[[Type[BaseAppException]], Type[BaseAppException]]:
    """
    Decorator to automatically register exception classes with error codes.

    This decorator validates parameters, generates auto-messages if needed,
    registers the exception in the global registry, and sets class attributes.

    Args:
        error_code: Custom error code (0-9999)
        message: Default error message (optional, auto-generated if not provided)
        message_key: i18n message key for localization (optional)
        status_code: HTTP status code (default: 400)
        domain: Error domain for organization (optional)
        **metadata: Additional metadata to store with registration

    Returns:
        Decorator function that wraps the exception class

    Raises:
        TypeError: If applied to a non-class
        ValueError: If error_code is invalid (< 0, > 9999, or non-int)
        ValueError: If status_code is invalid
        ValueError: If error_code is already registered

    Example:
        ```python
        from fastapi_error_codes import BaseAppException, register_exception

        # Basic usage
        @register_exception(error_code=201, message='Authentication required')
        class AuthRequiredException(BaseAppException):
            pass

        # With i18n support
        @register_exception(
            error_code=202,
            message='Invalid credentials',
            message_key='auth.invalid_credentials',
            status_code=401
        )
        class InvalidCredentialsException(BaseAppException):
            pass

        # With domain
        @register_exception(
            error_code=301,
            message='Resource not found',
            domain='resource',
            status_code=404
        )
        class ResourceNotFoundException(BaseAppException):
            pass

        # Minimal (auto-generated message with warning)
        @register_exception(error_code=203)
        class PaymentFailedException(BaseAppException):
            pass
        # Warning: No message provided for error_code 203,
        # using auto-generated: "Payment Failed Exception"
        ```

    Note:
        The decorator creates a wrapper class that provides default values
        from the registered parameters while preserving the original class behavior.
    """

    def decorator(original_cls: Type[BaseAppException]) -> Type[BaseAppException]:
        # Validate that we're decorating a class
        if not isinstance(original_cls, type):
            raise TypeError(
                f"@register_exception can only be applied to classes, "
                f"got {type(original_cls).__name__}"
            )

        # Validate error_code
        if not isinstance(error_code, int):
            raise ValueError(
                f"error_code must be an integer, got {type(error_code).__name__}"
            )
        if error_code < 0 or error_code > 9999:
            raise ValueError(
                f"error_code must be between 0 and 9999, got {error_code}"
            )

        # Validate status_code
        if not isinstance(status_code, int):
            raise ValueError(
                f"status_code must be an integer, got {type(status_code).__name__}"
            )
        if status_code < 100 or status_code > 599:
            raise ValueError(
                f"status_code must be a valid HTTP status code (100-599), got {status_code}"
            )

        # Generate default message if not provided
        final_message = message
        if final_message is None:
            final_message = _class_name_to_message(original_cls.__name__)
            logger.warning(
                f"No message provided for error_code {error_code}, "
                f"using auto-generated: '{final_message}'"
            )

        # Prepare metadata for registration
        registration_metadata = {
            "status_code": status_code,
            "domain": domain,
            "message_key": message_key,
            **metadata,
        }

        # Register in global registry (will raise ValueError if duplicate)
        _registry.register(error_code, original_cls, final_message, **registration_metadata)

        # Capture defaults for use in wrapper
        default_error_code = error_code
        default_message = final_message
        default_status_code = status_code

        # Create a wrapper class that provides default values
        class WrappedException(original_cls):
            """
            Wrapped exception class with default values from decorator.

            This class inherits from the original exception class and provides
            default values for error_code, message, and status_code based on
            the decorator parameters.
            """

            def __init__(
                self,
                error_code: Optional[int] = None,
                message: Optional[str] = None,
                status_code: Optional[int] = None,
                detail: Any = None,
                headers: Optional[Dict[str, str]] = None,
            ) -> None:
                """
                Initialize the wrapped exception with default values.

                Args:
                    error_code: Override error code (uses registered value if None)
                    message: Override message (uses registered value if None)
                    status_code: Override status code (uses registered value if None)
                    detail: Additional error details
                    headers: Custom HTTP headers
                """
                super().__init__(
                    error_code=error_code if error_code is not None else default_error_code,
                    message=message if message is not None else default_message,
                    status_code=status_code if status_code is not None else default_status_code,
                    detail=detail,
                    headers=headers,
                )

        # Preserve original class metadata
        WrappedException.__name__ = original_cls.__name__
        WrappedException.__qualname__ = original_cls.__qualname__
        WrappedException.__module__ = original_cls.__module__
        WrappedException.__doc__ = original_cls.__doc__

        # Set class attributes for metadata access
        WrappedException._error_code = error_code  # type: ignore[attr-defined]
        WrappedException._default_message = final_message  # type: ignore[attr-defined]
        WrappedException._message_key = message_key  # type: ignore[attr-defined]
        WrappedException._status_code = status_code  # type: ignore[attr-defined]
        WrappedException._domain = domain  # type: ignore[attr-defined]

        logger.info(
            f"Registered exception class '{original_cls.__name__}' "
            f"with error_code={error_code}, status_code={status_code}"
        )

        return WrappedException

    return decorator


def _class_name_to_message(class_name: str) -> str:
    """
    Convert exception class name to readable message.

    Converts CamelCase to spaces and removes trailing "Exception".

    Args:
        class_name: The exception class name (e.g., "UserNotFoundException")

    Returns:
        Readable message (e.g., "User Not Found")

    Example:
        ```python
        _class_name_to_message("UserNotFoundException")
        # Returns: "User Not Found"

        _class_name_to_message("AuthRequiredException")
        # Returns: "Auth Required"

        _class_name_to_message("HTTPException")
        # Returns: "HTTP Exception"
        ```
    """
    # Insert space before uppercase letters that follow lowercase letters
    # Handle consecutive uppercase letters (like HTTP) as a single word
    message = re.sub(r"([a-z])([A-Z])", r"\1 \2", class_name)
    # Insert space before uppercase letters that follow other uppercase letters
    # but only when followed by lowercase (to handle HTTPException correctly)
    message = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", message)

    # Remove trailing "Exception" if present
    if message.endswith("Exception"):
        message = message[:-10].strip()  # Remove "Exception" and trim

    return message


# Re-export register_exception as the primary public API
__all__ = ["register_exception"]
