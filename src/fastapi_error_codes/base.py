"""
Base exception class for fastapi-error-codes package.

This module provides BaseAppException, the foundational exception class
for all custom application exceptions with error code support.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """
    Base exception class for all custom exceptions with error_code support.

    This class provides a structured way to define application-specific exceptions
    with custom error codes, internationalized messages, and HTTP status codes.

    Attributes:
        error_code: Custom application error code (0-9999)
        message: Error message (supports i18n)
        status_code: HTTP status code for the response
        detail: Additional error details (can be dict, list, str, or any type)
        headers: Custom HTTP headers to include in the response
        timestamp: ISO format timestamp of when the exception was created

    Example:
        ```python
        class UserNotFoundException(BaseAppException):
            def __init__(self, user_id: int):
                super().__init__(
                    error_code=404,
                    message=f'User {user_id} not found',
                    status_code=404,
                    detail={'user_id': user_id}
                )

        # Usage
        raise UserNotFoundException(user_id=123)
        ```

    Example with custom headers:
        ```python
        exception = BaseAppException(
            error_code=429,
            message='Rate limit exceeded',
            status_code=429,
            detail={'retry_after': 60},
            headers={'Retry-After': '60'}
        )
        ```
    """

    def __init__(
        self,
        error_code: int,
        message: str,
        status_code: int = 400,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize BaseAppException with error details.

        Args:
            error_code: Custom application error code (0-9999)
            message: Error message description
            status_code: HTTP status code (default: 400)
            detail: Additional error details (optional)
            headers: Custom HTTP headers (optional)
        """
        self.error_code: int = error_code
        self.message: str = message
        self.status_code: int = status_code
        self.detail: Any = detail
        self.headers: Optional[Dict[str, str]] = headers
        self._timestamp: str = datetime.utcnow().isoformat() + "Z"

        # Initialize parent Exception with the message
        super().__init__(self.message)

    @property
    def timestamp(self) -> str:
        """Get the ISO format timestamp when the exception was created."""
        return self._timestamp

    @property
    def error_name(self) -> str:
        """Get the exception class name for logging purposes."""
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary for JSON serialization.

        This is useful for creating consistent API error responses.

        Returns:
            Dictionary containing error_code, message, detail, timestamp, and error_name

        Example:
            ```python
            exc = BaseAppException(error_code=201, message='Auth required')
            response_dict = exc.to_dict()
            # {
            #     'error_code': 201,
            #     'message': 'Auth required',
            #     'detail': None,
            #     'timestamp': '2025-01-16T10:30:00Z',
            #     'error_name': 'BaseAppException'
            # }
            ```
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "error_name": self.error_name,
        }

    def add_detail(self, key: str, value: Any) -> None:
        """
        Add or update a detail information to the exception.

        If detail is None, initializes it as a dict.
        If detail is already a dict, adds/updates the key-value pair.
        If detail is another type, converts it to a dict with previous detail as 'previous' key.

        Args:
            key: The detail key
            value: The detail value

        Example:
            ```python
            exc = BaseAppException(error_code=400, message='Validation failed')
            exc.add_detail('field', 'email')
            exc.add_detail('reason', 'invalid format')
            # exc.detail is now {'field': 'email', 'reason': 'invalid format'}
            ```
        """
        if self.detail is None:
            self.detail = {key: value}
        elif isinstance(self.detail, dict):
            self.detail[key] = value
        else:
            # Preserve previous detail if it exists
            self.detail = {"previous": self.detail, key: value}

    def __str__(self) -> str:
        """
        Return a readable string representation of the exception.

        Returns:
            Formatted error message string

        Example:
            ```python
            exc = BaseAppException(error_code=201, message='Auth required')
            print(exc)  # "[Error 201] Auth required"
            ```
        """
        return f"[Error {self.error_code}] {self.message}"

    def __repr__(self) -> str:
        """
        Return a detailed representation of the exception for debugging.

        Returns:
            Detailed string representation including all attributes

        Example:
            ```python
            exc = BaseAppException(error_code=201, message='Auth required', status_code=401)
            repr(exc)  # "BaseAppException(error_code=201, message='Auth required', status_code=401, ...)"
            ```
        """
        return (
            f"{self.__class__.__name__}("
            f"error_code={self.error_code}, "
            f"message='{self.message}', "
            f"status_code={self.status_code}, "
            f"detail={repr(self.detail)}, "
            f"headers={repr(self.headers)}, "
            f"timestamp='{self.timestamp}'"
            f")"
        )
