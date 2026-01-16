"""
Pydantic response models for fastapi-error-codes package.

This module provides response models for error responses with full
Pydantic v1/v2 compatibility support.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Model for individual error detail information.

    This model represents a single validation error or field-specific error
    with field name, error message, and optional error code.

    Attributes:
        field: The field name that caused the error
        message: Human-readable error message
        code: Optional error code for programmatic handling

    Example:
        ```python
        detail = ErrorDetail(
            field="email",
            message="Invalid email format",
            code="INVALID_FORMAT"
        )
        ```
    """

    field: str = Field(..., description="Field name that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Optional error code")


class ErrorDetailItem(BaseModel):
    """
    Model for complex validation error items (Pydantic-style).

    This model represents validation errors in Pydantic's internal format,
    with location path, error message, and error type.

    Attributes:
        loc: Location path as a list (e.g., ["body", "users", 0, "email"])
        msg: Error message
        type: Optional error type identifier

    Example:
        ```python
        item = ErrorDetailItem(
            loc=["body", "users", 0, "email"],
            msg="field required",
            type="value_error.missing"
        )
        ```
    """

    loc: List[Any] = Field(..., description="Location path of the error")
    msg: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type identifier")


class ErrorResponse(BaseModel):
    """
    Standard error response model for API errors.

    This model provides a consistent structure for all error responses
    from the API, including error code, message, timestamp, and optional
    additional details.

    Attributes:
        error_code: Application-specific error code (0-9999)
        message: Human-readable error message (supports i18n)
        status_code: HTTP status code for the response
        detail: Additional error details (can be dict, list, str, or any type)
        timestamp: ISO 8601 UTC timestamp when the error occurred
        error_name: Exception class name for debugging

    Example:
        ```python
        response = ErrorResponse(
            error_code=201,
            message="Authentication required",
            status_code=401,
            detail={"token": "expired"},
            error_name="AuthException"
        )
        ```
    """

    error_code: int = Field(..., ge=0, le=9999, description="Application error code (0-9999)")
    message: str = Field(..., description="Error message")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    detail: Any = Field(None, description="Additional error details")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 UTC timestamp"
    )
    error_name: Optional[str] = Field(None, description="Exception class name")

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

    @classmethod
    def from_exception(cls, exception: Any) -> "ErrorResponse":
        """
        Create ErrorResponse from BaseAppException.

        Args:
            exception: BaseAppException instance

        Returns:
            ErrorResponse instance with data from exception

        Example:
            ```python
            try:
                raise UserNotFoundException(user_id=123)
            except BaseAppException as exc:
                response = ErrorResponse.from_exception(exc)
            ```
        """
        from fastapi_error_codes.base import BaseAppException

        if isinstance(exception, BaseAppException):
            return cls(
                error_code=exception.error_code,
                message=exception.message,
                status_code=exception.status_code,
                detail=exception.detail,
                timestamp=exception.timestamp,
                error_name=exception.error_name
            )
        else:
            # For regular exceptions
            return cls(
                error_code=500,
                message=str(exception),
                error_name=exception.__class__.__name__
            )


class ValidationErrorResponse(BaseModel):
    """
    Validation error response model with multiple error details.

    This model extends ErrorResponse to include multiple validation
    error details, useful for form validation or bulk data validation.

    Attributes:
        error_code: Application error code (typically in VALIDATION range 400-499)
        message: Overall error message
        errors: List of individual error details
        status_code: HTTP status code (default: 422)
        timestamp: ISO 8601 UTC timestamp

    Example:
        ```python
        response = ValidationErrorResponse(
            error_code=401,
            message="Validation failed",
            errors=[
                ErrorDetail(field="email", message="Invalid email"),
                ErrorDetail(field="password", message="Too short")
            ]
        )
        ```
    """

    error_code: int = Field(..., ge=0, le=9999, description="Application error code")
    message: str = Field(..., description="Overall error message")
    errors: List[ErrorDetail] = Field(default_factory=list, description="List of validation errors")
    status_code: Optional[int] = Field(422, description="HTTP status code")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 UTC timestamp"
    )

    @classmethod
    def from_validation_details(
        cls,
        error_code: int,
        message: str,
        details: List[Dict[str, Any]],
        status_code: Optional[int] = 422
    ) -> "ValidationErrorResponse":
        """
        Create ValidationErrorResponse from list of error detail dictionaries.

        Args:
            error_code: Application error code
            message: Overall error message
            details: List of error detail dictionaries
            status_code: HTTP status code (default: 422)

        Returns:
            ValidationErrorResponse instance

        Example:
            ```python
            error_dicts = [
                {"field": "email", "message": "Invalid", "code": "INVALID"},
                {"field": "password", "message": "Required", "code": "REQUIRED"}
            ]
            response = ValidationErrorResponse.from_validation_details(
                error_code=401,
                message="Validation failed",
                details=error_dicts
            )
            ```
        """
        errors = [ErrorDetail.model_validate(detail) for detail in details]
        return cls(
            error_code=error_code,
            message=message,
            errors=errors,
            status_code=status_code
        )
