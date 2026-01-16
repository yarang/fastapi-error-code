"""
fastapi-error-codes: Structured exception handling for FastAPI

This package provides:
- Custom error codes for better API error tracking (0-9999)
- Multi-level fallback for internationalized error messages
- Automatic FastAPI integration with consistent JSON responses
- Domain-based error code organization
- Pydantic v1/v2 compatibility

Modules:
- base: BaseAppException for all custom exceptions
- domain: ErrorDomain for error code range management
- i18n: MessageProvider for internationalization
- models: Pydantic response models
- config: ErrorHandlerConfig with presets
- handlers: setup_exception_handler for FastAPI integration
- registry: Exception registration system
- decorators: @register_exception decorator

Basic Usage:
    from fastapi import FastAPI
    from fastapi_error_codes import BaseAppException, setup_exception_handler, ErrorHandlerConfig

    app = FastAPI()
    config = ErrorHandlerConfig(default_locale="en", locale_dir="locales")
    setup_exception_handler(app, config)

    @app.get('/users/{user_id}')
    def get_user(user_id: int):
        raise BaseAppException(
            error_code=301,
            message="User not found",
            status_code=404,
            detail={"user_id": user_id}
        )

For more examples, see: https://github.com/yarang/fastapi-error-codes/tree/main/examples
"""

from typing import TYPE_CHECKING

__version__ = "0.1.0"

# Import all main classes and functions
from .base import BaseAppException
from .config import ErrorHandlerConfig
from .decorators import register_exception
from .domain import ErrorDomain
from .handlers import setup_exception_handler
from .i18n import MessageProvider
from .models import ErrorResponse, ValidationErrorResponse, ErrorDetail, ErrorDetailItem
from .registry import _registry, register_error_code, get_error_code_info, list_error_codes

__all__ = [
    "__version__",
    # Core exception handling
    "BaseAppException",
    # Domain management
    "ErrorDomain",
    # Configuration
    "ErrorHandlerConfig",
    # i18n
    "MessageProvider",
    # Response models
    "ErrorResponse",
    "ValidationErrorResponse",
    "ErrorDetail",
    "ErrorDetailItem",
    # Integration
    "setup_exception_handler",
    # Registration
    "register_exception",
    "_registry",
    "register_error_code",
    "get_error_code_info",
    "list_error_codes",
]

# Type checking imports
if TYPE_CHECKING:
    from .base import BaseAppException
    from .config import ErrorHandlerConfig
    from .decorators import register_exception
    from .domain import ErrorDomain
    from .handlers import setup_exception_handler
    from .i18n import MessageProvider
    from .models import ErrorResponse, ValidationErrorResponse, ErrorDetail, ErrorDetailItem
    from .registry import ExceptionRegistry
