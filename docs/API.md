# API Reference

## Core Classes

### BaseAppException

The base exception class for all custom application exceptions.

```python
class BaseAppException(Exception):
    def __init__(
        self,
        error_code: int,
        message: str,
        status_code: int = 400,
        detail: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None
```

**Parameters:**
- `error_code` (int, required): Custom error code (0-9999)
- `message` (str, required): Error message description
- `status_code` (int, default=400): HTTP status code
- `detail` (Any, optional): Additional error details
- `headers` (Dict[str, str], optional): Custom HTTP headers

**Attributes:**
- `error_code` (int): The custom error code
- `message` (str): Error message
- `status_code` (int): HTTP status code
- `detail` (Any): Additional details
- `headers` (Dict[str, str] | None): Custom headers
- `timestamp` (str): ISO format timestamp (read-only)
- `error_name` (str): Exception class name (read-only)

**Methods:**

#### `to_dict() -> Dict[str, Any]`

Convert exception to dictionary for JSON serialization.

```python
exc = BaseAppException(error_code=201, message='Auth required')
response_dict = exc.to_dict()
# Returns: {
#     'error_code': 201,
#     'message': 'Auth required',
#     'detail': None,
#     'timestamp': '2026-01-16T10:00:00Z',
#     'error_name': 'BaseAppException'
# }
```

#### `add_detail(key: str, value: Any) -> None`

Add or update detail information.

```python
exc = BaseAppException(error_code=400, message='Validation failed')
exc.add_detail('field', 'email')
exc.add_detail('reason', 'invalid format')
```

---

### ErrorDomain

Represents an error domain with a specific code range.

```python
class ErrorDomain:
    def __init__(self, name: str, code_range: Tuple[int, int]) -> None
```

**Parameters:**
- `name` (str): The domain name (e.g., "AUTH", "RESOURCE")
- `code_range` (Tuple[int, int]): Tuple of (start_code, end_code)

**Attributes:**
- `name` (str): The domain name
- `code_range` (Tuple[int, int]): The code range tuple

**Class Methods:**

#### `register_domain(name: str, code_range: Tuple[int, int]) -> ErrorDomain`

Register a new error domain.

```python
ErrorDomain.register_domain("CUSTOM", (1000, 1999))
```

#### `get_domain(name: str) -> Optional[ErrorDomain]`

Get a registered domain by name.

```python
domain = ErrorDomain.get_domain("AUTH")
```

#### `is_valid_code(code: int, domain_name: str) -> bool`

Check if a code is valid for a specific domain.

```python
is_valid = ErrorDomain.is_valid_code(201, "AUTH")  # True
```

#### `get_domain_for_code(code: int) -> Optional[ErrorDomain]`

Find the domain that contains a given code.

```python
domain = ErrorDomain.get_domain_for_code(201)
```

#### `list_domains() -> List[str]`

List all registered domain names.

```python
domains = ErrorDomain.list_domains()
# Returns: ["AUTH", "RESOURCE", "VALIDATION", "SERVER", "CUSTOM"]
```

**Predefined Domains:**

| Domain  | Code Range | Description                  |
|---------|------------|------------------------------|
| AUTH    | 200-299    | Authentication/Authorization  |
| RESOURCE| 300-399    | Resource-related errors      |
| VALIDATION| 400-499  | Validation errors            |
| SERVER  | 500-599    | Server errors                |
| CUSTOM  | 900-999    | Custom business logic errors |

---

### MessageProvider

Provider for localized error messages with fallback chain support.

```python
class MessageProvider:
    def __init__(
        self,
        locale_dir: str,
        default_locale: str = "en",
        fallback_locales: Optional[List[str]] = None,
    ) -> None
```

**Parameters:**
- `locale_dir` (str): Directory containing locale JSON files (e.g., en.json, ko.json)
- `default_locale` (str, default="en"): Default locale code
- `fallback_locales` (List[str], optional): Ordered list of fallback locales

**Attributes:**
- `locale_dir` (str): The locale directory path
- `default_locale` (str): The default locale code

**Methods:**

#### `get_message(key: str, locale: Optional[str] = None, default: Optional[str] = None, **kwargs: Any) -> str`

Get localized message for a given key.

**Fallback chain:**
1. Requested locale
2. Fallback locales (in order)
3. Default locale
4. Original key (if not found anywhere)

```python
# Get message in Korean
msg = provider.get_message("errors.auth.required", locale="ko")

# Get message with parameters
msg = provider.get_message(
    "errors.user_not_found",
    locale="en",
    user_id=123
)
# Returns: "User 123 not found"
```

#### `reload_locale(locale: str) -> None`

Reload a locale from disk, updating the cache.

```python
provider.reload_locale("ko")
```

#### `clear_cache() -> None`

Clear all cached locale data.

```python
provider.clear_cache()
```

#### `get_available_locales() -> List[str]`

Get list of available locale files.

```python
locales = provider.get_available_locales()
# Returns: ["en", "ko", "ja"]
```

---

### ErrorHandlerConfig

Configuration for error handler behavior.

```python
@dataclass(frozen=True)
class ErrorHandlerConfig:
    default_locale: str = "en"
    fallback_locales: List[str] = field(default_factory=list)
    debug_mode: bool = False
    include_traceback: bool = False
    locale_dir: str = "locales"
```

**Attributes:**
- `default_locale` (str): Default locale code for messages (default: "en")
- `fallback_locales` (List[str]): Ordered list of fallback locales
- `debug_mode` (bool): Enable debug mode for detailed error messages (default: False)
- `include_traceback` (bool): Include stack trace in error responses (default: False)
- `locale_dir` (str): Directory containing locale JSON files (default: "locales")

**Class Methods:**

#### `development(...) -> ErrorHandlerConfig`

Create configuration for development environment.

```python
config = ErrorHandlerConfig.development()
# debug_mode=True, include_traceback=True
```

#### `production(...) -> ErrorHandlerConfig`

Create configuration for production environment.

```python
config = ErrorHandlerConfig.production()
# debug_mode=False, include_traceback=False
```

#### `from_environment() -> ErrorHandlerConfig`

Create configuration from environment variables.

```python
# Environment variables:
# ERROR_LOCALE: Default locale (default: "en")
# ERROR_DEBUG: Debug mode "true"/"false" (default: "false")
# ERROR_TRACEBACK: Include traceback "true"/"false" (default: "false")
# ERROR_LOCALE_DIR: Locale directory (default: "locales")
# ERROR_FALLBACK_LOCALES: Comma-separated fallback locales

config = ErrorHandlerConfig.from_environment()
```

**Methods:**

#### `update(**kwargs: Any) -> ErrorHandlerConfig`

Create a new configuration with updated values.

```python
original = ErrorHandlerConfig(default_locale="en")
updated = original.update(default_locale="ko", debug_mode=True)
```

#### `to_dict() -> Dict[str, Any]`

Convert configuration to dictionary.

```python
config = ErrorHandlerConfig(default_locale="ko")
data = config.to_dict()
# {'default_locale': 'ko', 'fallback_locales': [], ...}
```

---

### ErrorResponse

Standard error response model for API errors.

```python
class ErrorResponse(BaseModel):
    error_code: int
    message: str
    status_code: Optional[int] = None
    detail: Any = None
    timestamp: str = Field(default_factory=...)
    error_name: Optional[str] = None
```

**Attributes:**
- `error_code` (int): Application-specific error code (0-9999)
- `message` (str): Human-readable error message (supports i18n)
- `status_code` (Optional[int]): HTTP status code for the response
- `detail` (Any): Additional error details (can be dict, list, str, or any type)
- `timestamp` (str): ISO 8601 UTC timestamp when the error occurred
- `error_name` (Optional[str]): Exception class name for debugging

**Class Methods:**

#### `from_exception(exception: Any) -> ErrorResponse`

Create ErrorResponse from BaseAppException.

```python
try:
    raise UserNotFoundException(user_id=123)
except BaseAppException as exc:
    response = ErrorResponse.from_exception(exc)
```

---

### ValidationErrorResponse

Validation error response model with multiple error details.

```python
class ValidationErrorResponse(BaseModel):
    error_code: int
    message: str
    errors: List[ErrorDetail] = Field(default_factory=list)
    status_code: Optional[int] = 422
    timestamp: str = Field(default_factory=...)
```

**Attributes:**
- `error_code` (int): Application error code (typically in VALIDATION range 400-499)
- `message` (str): Overall error message
- `errors` (List[ErrorDetail]): List of individual error details
- `status_code` (Optional[int]): HTTP status code (default: 422)
- `timestamp` (str): ISO 8601 UTC timestamp

**Class Methods:**

#### `from_validation_details(error_code: int, message: str, details: List[Dict[str, Any]], status_code: Optional[int] = 422) -> ValidationErrorResponse`

Create ValidationErrorResponse from list of error detail dictionaries.

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

---

## Functions

### setup_exception_handler

Setup global exception handler for FastAPI application.

```python
def setup_exception_handler(
    app: FastAPI,
    config: Optional[ErrorHandlerConfig] = None
) -> None
```

**Parameters:**
- `app` (FastAPI): FastAPI application instance
- `config` (ErrorHandlerConfig, optional): Error handler configuration (uses default if None)

**Example:**

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

**Features:**
- Registers exception handler for all Exception types
- Initializes MessageProvider with specified configuration
- Enables Accept-Language header parsing for locale detection
- Resolves i18n messages with fallback chain
- Includes traceback in debug mode when enabled

---

## Decorators

### `@register_exception`

Decorator for automatic exception registration.

```python
def register_exception(
    error_code: int,
    message: Optional[str] = None,
    message_key: Optional[str] = None,
    status_code: int = 400,
    domain: Optional[str] = None,
    **metadata: Any,
) -> Callable
```

**Parameters:**
- `error_code` (int, required): Custom error code (0-9999)
- `message` (str, optional): Default message
- `message_key` (str, optional): i18n message key
- `status_code` (int, default=400): HTTP status code
- `domain` (str, optional): Error domain
- `**metadata`: Additional metadata

**Raises:**
- `TypeError`: If applied to non-class
- `ValueError`: If error_code invalid (< 0, > 9999, or non-int)
- `ValueError`: If status_code invalid (< 100, > 599, or non-int)
- `ValueError`: If error_code already registered

**Usage:**

```python
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
    domain='RESOURCE',
    status_code=404
)
class ResourceNotFoundException(BaseAppException):
    pass
```

---

## Registry Functions

### register_error_code

Register error code using global registry.

```python
def register_error_code(
    error_code: int,
    exception_class: Type[BaseAppException],
    message: str,
    **metadata: Any
) -> None
```

### get_error_code_info

Get complete error code information.

```python
def get_error_code_info(error_code: int) -> Optional[Dict[str, Any]]
```

**Example:**

```python
info = get_error_code_info(201)
if info:
    print(f"Class: {info['class'].__name__}")
    print(f"Message: {info['message']}")
```

### list_error_codes

List all registered error codes.

```python
def list_error_codes() -> List[int]
```

**Example:**

```python
codes = list_error_codes()
# Returns: [201, 202, 301, ...]
```

---

## ExceptionRegistry

Global registry for managing registered exceptions.

```python
class ExceptionRegistry:
    def __init__(self) -> None
```

**Methods:**

#### `register(error_code, exception_class, message, **metadata) -> None`

Register an exception with its error code.

```python
registry = ExceptionRegistry()
registry.register(
    201,
    AuthException,
    "Authentication required",
    domain="AUTH",
    status_code=401
)
```

#### `get_exception(error_code: int) -> Optional[Type[BaseAppException]]`

Get exception class by error code.

```python
exc_class = registry.get_exception(201)
```

#### `get_message(error_code: int) -> Optional[str]`

Get default message by error code.

```python
message = registry.get_message(201)
```

#### `get_metadata(error_code: int) -> Optional[Dict[str, Any]]`

Get metadata by error code.

```python
metadata = registry.get_metadata(201)
```

#### `is_registered(error_code: int) -> bool`

Check if error code is registered.

```python
if registry.is_registered(201):
    print("Code 201 is registered")
```

#### `get_all_codes() -> List[int]`

Get all registered error codes (sorted).

```python
codes = registry.get_all_codes()  # [201, 202, 301, ...]
```

#### `clear() -> None`

Clear all registrations.

```python
registry.clear()
```

#### `get_registry_info() -> Dict[int, Dict[str, Any]]`

Get complete registry information.

```python
info = registry.get_registry_info()
```

---

## Package Exports

```python
from fastapi_error_codes import (
    # Core exception handling
    BaseAppException,

    # Domain management
    ErrorDomain,

    # Configuration
    ErrorHandlerConfig,

    # i18n
    MessageProvider,

    # Response models
    ErrorResponse,
    ValidationErrorResponse,
    ErrorDetail,
    ErrorDetailItem,

    # Integration
    setup_exception_handler,

    # Registration
    register_exception,
    _registry,
    register_error_code,
    get_error_code_info,
    list_error_codes,
)
```

---

## Type Aliases

```python
from typing import Any, Dict, Optional, Type

ExceptionClass = Type[BaseAppException]
ErrorDetail = Any
HeadersDict = Optional[Dict[str, str]]
```

---

## Constants

### Error Code Ranges

- `AUTH_CODES`: 200-299
- `RESOURCE_CODES`: 300-399
- `VALIDATION_CODES`: 400-499
- `SERVER_CODES`: 500-599
- `CUSTOM_CODES`: 900-999

### Default Values

- `DEFAULT_STATUS_CODE`: 400
- `MIN_ERROR_CODE`: 0
- `MAX_ERROR_CODE`: 9999

---

## Response Models

### ErrorDetail

Model for individual error detail information.

```python
class ErrorDetail(BaseModel):
    field: str = Field(..., description="Field name that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Optional error code")
```

### ErrorDetailItem

Model for complex validation error items (Pydantic-style).

```python
class ErrorDetailItem(BaseModel):
    loc: List[Any] = Field(..., description="Location path of the error")
    msg: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type identifier")
```
