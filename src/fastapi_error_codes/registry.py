"""
Exception Registry for fastapi-error-codes package.

This module provides a global registry to manage registered exceptions
and prevent duplicate error codes.
"""

import logging
import threading
from types import TracebackType
from typing import Any, Dict, List, Optional, Type

from fastapi_error_codes.base import BaseAppException


# Configure logger for this module
logger = logging.getLogger(__name__)


class ExceptionRegistry:
    """
    Global registry to manage registered exceptions and prevent duplicate error codes.

    The registry maintains a mapping of error codes to exception classes,
    default messages, and metadata. It ensures that each error code is
    registered only once and provides thread-safe operations.

    Attributes:
        _exceptions: Dict mapping error codes to exception classes
        _messages: Dict mapping error codes to default messages
        _metadata: Dict mapping error codes to additional metadata
        _lock: Threading lock for thread-safe operations

    Example:
        ```python
        from fastapi_error_codes.registry import _registry

        # Register an exception
        _registry.register(201, AuthException, "Auth required", domain="AUTH")

        # Check if registered
        if _registry.is_registered(201):
            exc_class = _registry.get_exception(201)
            message = _registry.get_message(201)

        # Get all registered codes
        codes = _registry.get_all_codes()
        ```
    """

    def __init__(self) -> None:
        """Initialize an empty exception registry."""
        self._exceptions: Dict[int, Type[BaseAppException]] = {}
        self._messages: Dict[int, str] = {}
        self._metadata: Dict[int, Dict[str, Any]] = {}
        self._lock: threading.Lock = threading.Lock()

    def register(
        self,
        error_code: int,
        exception_class: Type[BaseAppException],
        message: str,
        **metadata: Any,
    ) -> None:
        """
        Register an exception with its error code.

        This method is thread-safe and will raise ValueError if the error code
        is already registered.

        Args:
            error_code: The error code to register (0-9999)
            exception_class: The exception class to associate with the error code
            message: Default error message for this error code
            **metadata: Additional metadata to store with the registration

        Raises:
            ValueError: If the error code is already registered

        Example:
            ```python
            registry = ExceptionRegistry()

            class AuthException(BaseAppException):
                pass

            registry.register(
                201,
                AuthException,
                "Authentication required",
                domain="AUTH",
                status_code=401
            )
            ```
        """
        with self._lock:
            if error_code in self._exceptions:
                existing_class = self._exceptions[error_code]
                existing_name = existing_class.__name__
                new_name = exception_class.__name__
                raise ValueError(
                    f"Error code {error_code} is already registered by {existing_name}. "
                    f"Cannot re-register with {new_name}."
                )

            self._exceptions[error_code] = exception_class
            self._messages[error_code] = message
            self._metadata[error_code] = metadata

            logger.info(
                f"Registered error code {error_code}: {exception_class.__name__} - '{message}'"
            )

            if metadata:
                logger.debug(f"  Metadata: {metadata}")

    def get_exception(self, error_code: int) -> Optional[Type[BaseAppException]]:
        """
        Retrieve exception class by error code.

        Args:
            error_code: The error code to look up

        Returns:
            The exception class if found, None otherwise

        Example:
            ```python
            exc_class = registry.get_exception(201)
            if exc_class:
                # Can instantiate the exception
                raise exc_class()
            ```
        """
        return self._exceptions.get(error_code)

    def get_message(self, error_code: int) -> Optional[str]:
        """
        Retrieve default message by error code.

        Args:
            error_code: The error code to look up

        Returns:
            The default message if found, None otherwise

        Example:
            ```python
            message = registry.get_message(201)
            # Returns: "Authentication required"
            ```
        """
        return self._messages.get(error_code)

    def get_metadata(self, error_code: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata by error code.

        Args:
            error_code: The error code to look up

        Returns:
            The metadata dict if found, None otherwise

        Example:
            ```python
            metadata = registry.get_metadata(201)
            # Returns: {'domain': 'AUTH', 'status_code': 401}
            ```
        """
        return self._metadata.get(error_code)

    def is_registered(self, error_code: int) -> bool:
        """
        Check if an error code is already registered.

        Args:
            error_code: The error code to check

        Returns:
            True if the error code is registered, False otherwise

        Example:
            ```python
            if registry.is_registered(201):
                print("Error code 201 is already in use")
            ```
        """
        return error_code in self._exceptions

    def get_all_codes(self) -> List[int]:
        """
        Return a list of all registered error codes.

        The returned list is sorted for consistent ordering.

        Returns:
            Sorted list of registered error codes

        Example:
            ```python
            codes = registry.get_all_codes()
            # Returns: [201, 202, 301, 401]
            ```
        """
        return sorted(self._exceptions.keys())

    def clear(self) -> None:
        """
        Clear all registrations from the registry.

        This is primarily useful for testing purposes.

        Example:
            ```python
            # In test setup
            registry.clear()  # Start with a clean slate
            ```
        """
        with self._lock:
            count = len(self._exceptions)
            self._exceptions.clear()
            self._messages.clear()
            self._metadata.clear()
            logger.debug(f"Cleared {count} error code(s) from registry")

    def get_registry_info(self) -> Dict[int, Dict[str, Any]]:
        """
        Return complete registry information for all registered codes.

        This is useful for debugging and documentation generation.

        Returns:
            Dictionary mapping error codes to their complete info:
            {error_code: {'class': exception_class, 'message': message, 'metadata': dict}}

        Example:
            ```python
            info = registry.get_registry_info()
            # Returns:
            # {
            #     201: {
            #         'class': AuthException,
            #         'message': 'Authentication required',
            #         'metadata': {'domain': 'AUTH'}
            #     },
            #     301: {...}
            # }
            ```
        """
        with self._lock:
            return {
                code: {
                    "class": self._exceptions[code],
                    "message": self._messages[code],
                    "metadata": self._metadata[code],
                }
                for code in self._exceptions
            }


# Module-level singleton instance
_registry = ExceptionRegistry()


# Module-level convenience functions
def register_error_code(
    error_code: int,
    exception_class: Type[BaseAppException],
    message: str,
    **metadata: Any,
) -> None:
    """
    Register an error code with its exception class.

    This is a convenience function that uses the global registry instance.

    Args:
        error_code: The error code to register (0-9999)
        exception_class: The exception class to associate with the error code
        message: Default error message for this error code
        **metadata: Additional metadata to store with the registration

    Raises:
        ValueError: If the error code is already registered

    Example:
        ```python
        from fastapi_error_codes.registry import register_error_code

        register_error_code(
            201,
            AuthException,
            "Authentication required",
            domain="AUTH"
        )
        ```
    """
    _registry.register(error_code, exception_class, message, **metadata)


def get_error_code_info(error_code: int) -> Optional[Dict[str, Any]]:
    """
    Get complete information about an error code.

    This is a convenience function that uses the global registry instance.

    Args:
        error_code: The error code to look up

    Returns:
        Dict with 'class', 'message', and 'metadata' keys, or None if not found

    Example:
        ```python
        from fastapi_error_codes.registry import get_error_code_info

        info = get_error_code_info(201)
        if info:
            print(f"Class: {info['class'].__name__}")
            print(f"Message: {info['message']}")
        ```
    """
    if not _registry.is_registered(error_code):
        return None

    return {
        "class": _registry.get_exception(error_code),
        "message": _registry.get_message(error_code),
        "metadata": _registry.get_metadata(error_code),
    }


def list_error_codes() -> List[int]:
    """
    List all registered error codes.

    This is a convenience function that uses the global registry instance.

    Returns:
        Sorted list of registered error codes

    Example:
        ```python
        from fastapi_error_codes.registry import list_error_codes

        codes = list_error_codes()
        print(f"Registered codes: {codes}")
        ```
    """
    return _registry.get_all_codes()
