# fastapi-error-codes

Structured exception handling with error codes and internationalization support for FastAPI applications.

## Features

- **Custom Error Codes**: Define application-specific error codes (0-9999) for better tracking
- **i18n Support**: Multi-language error messages with automatic fallback chain
- **Domain Organization**: Organize errors by domain (AUTH, RESOURCE, VALIDATION, SERVER, CUSTOM)
- **FastAPI Integration**: Seamless integration with `setup_exception_handler()`
- **Accept-Language Parsing**: Automatic locale detection from HTTP headers
- **Pydantic Compatibility**: Full Pydantic v1/v2 support for response models
- **Type Safe**: Complete type hints with strict mypy configuration
- **Production Ready**: Development and production configuration presets

### Monitoring & Metrics (SPEC-MONITOR-002)

- **Error Metrics Collection**: Thread-safe metrics collection with < 50μs performance
- **Prometheus Integration**: Built-in `/metrics` endpoint for Prometheus monitoring
- **Sentry Integration**: Automatic error tracking to Sentry with PII masking
- **Dashboard API**: JSON API endpoints (`/api/metrics/*`) for real-time statistics
- **Time-based Bucketing**: Automatic data aggregation and cleanup
- **Non-blocking Collection**: Zero impact on request processing performance

### Distributed Tracing (SPEC-TRACING-003)

- **OpenTelemetry Integration**: Standard-based distributed tracing with OpenTelemetry SDK
- **Multiple Exporters**: Jaeger and OTLP (OpenTelemetry Protocol) support
- **Exception Tracing**: Automatic exception event recording in spans
- **PII Masking**: Sensitive data masking (email, phone, credit card, SSN) in traces
- **Trace Context Propagation**: W3C Trace Context support for cross-service tracing
- **Trace ID Correlation**: Automatic trace ID in error responses and metrics
- **Performance**: < 100μs overhead per request, < 1% total impact

## Installation

```bash
# Basic installation
pip install fastapi-error-codes

# With monitoring support (Prometheus + Sentry)
pip install fastapi-error-codes[monitoring]

# With distributed tracing support (OpenTelemetry + Jaeger + OTLP)
pip install fastapi-error-codes[tracing]

# With all optional features
pip install fastapi-error-codes[monitoring,tracing]
```

## Quick Start

```python
from fastapi import FastAPI
from fastapi_error_codes import (
    BaseAppException,
    setup_exception_handler,
    ErrorHandlerConfig,
    register_exception
)

# Define your exceptions
@register_exception(error_code=201, message='Authentication required')
class AuthRequiredException(BaseAppException):
    pass

# Create FastAPI app
app = FastAPI()

# Setup exception handler with configuration
config = ErrorHandlerConfig(
    default_locale="en",
    locale_dir="locales",
    debug_mode=True
)
setup_exception_handler(app, config)

# Use in endpoints
@app.get('/protected')
def protected():
    raise AuthRequiredException()
```

Response:
```json
{
    "error_code": 201,
    "message": "Authentication required",
    "status_code": 401,
    "detail": null,
    "timestamp": "2026-01-16T10:00:00Z",
    "error_name": "AuthRequiredException"
}
```

## Error Domains

Error codes are organized by predefined domains:

| Domain   | Code Range | Description                   |
|----------|------------|-------------------------------|
| AUTH     | 200-299    | Authentication/Authorization   |
| RESOURCE | 300-399    | Resource-related errors       |
| VALIDATION | 400-499  | Validation errors             |
| SERVER   | 500-599    | Server errors                 |
| CUSTOM   | 900-999    | Custom business logic errors  |

## Usage Examples

### Basic Exception Handling

```python
from fastapi_error_codes import BaseAppException

class UserNotFoundException(BaseAppException):
    def __init__(self, user_id: int):
        super().__init__(
            error_code=301,
            message="User not found",
            status_code=404,
            detail={"user_id": user_id}
        )
```

### Using ErrorDomain

```python
from fastapi_error_codes import ErrorDomain

# Check if code is in domain
domain = ErrorDomain.get_domain("AUTH")
if 201 in domain:
    print("Code 201 is an AUTH error")

# Validate code for domain
is_valid = ErrorDomain.is_valid_code(301, "RESOURCE")  # True

# Get domain for code
domain = ErrorDomain.get_domain_for_code(401)
print(domain.name)  # "AUTH"
```

### Internationalization (i18n)

```python
from fastapi_error_codes import MessageProvider

# Create message provider
provider = MessageProvider(
    locale_dir="locales",
    default_locale="en",
    fallback_locales=["ko"]
)

# Get localized message
msg = provider.get_message("errors.auth.required", locale="ko")

# With parameters
msg = provider.get_message(
    "errors.user_not_found",
    locale="en",
    user_id=123
)
# Returns: "User 123 not found"
```

Locale file structure (`locales/en.json`):
```json
{
    "errors": {
        "auth": {
            "required": "Authentication required",
            "invalid_credentials": "Invalid credentials"
        },
        "user_not_found": "User {user_id} not found"
    }
}
```

### Configuration Presets

```python
from fastapi_error_codes import ErrorHandlerConfig

# Development config (debug mode enabled)
dev_config = ErrorHandlerConfig.development(
    default_locale="ko",
    locale_dir="locales"
)
# debug_mode=True, include_traceback=True

# Production config (debug mode disabled)
prod_config = ErrorHandlerConfig.production(
    default_locale="en",
    locale_dir="locales"
)
# debug_mode=False, include_traceback=False

# Custom config
custom_config = ErrorHandlerConfig(
    default_locale="ja",
    fallback_locales=["en", "ko"],
    debug_mode=False,
    include_traceback=False,
    locale_dir="locales"
)

# From environment variables
# ERROR_LOCALE, ERROR_DEBUG, ERROR_TRACEBACK, ERROR_LOCALE_DIR
env_config = ErrorHandlerConfig.from_environment()
```

### Error Monitoring

```python
from fastapi import FastAPI
from fastapi_error_codes import (
    setup_exception_handler,
    ErrorHandlerConfig,
    MetricsConfig,
    MetricsPreset,
)

app = FastAPI()

# Setup error handler with monitoring
error_config = ErrorHandlerConfig(
    default_locale="en",
    debug_mode=True
)
metrics_config = MetricsPreset.production(
    sentry_dsn="https://key@sentry.io/123"
)

setup_exception_handler(
    app,
    config=error_config,
    metrics_config=metrics_config  # Enable monitoring
)

# Available endpoints:
# - /metrics (Prometheus metrics)
# - /api/metrics/summary (Dashboard summary)
# - /api/metrics/recent (Recent errors)
# - /api/metrics/top-errors (Top error codes)
```

### Distributed Tracing

```python
from fastapi import FastAPI
from fastapi_error_codes import (
    setup_exception_handler,
    ErrorHandlerConfig,
)
from fastapi_error_codes.tracing import TracingConfig, setup_tracing

app = FastAPI()

# Setup error handler
error_config = ErrorHandlerConfig(default_locale="en")
setup_exception_handler(app, config=error_config)

# Setup distributed tracing
tracing_config = TracingConfig(
    service_name="my-service",
    endpoint="http://localhost:4317",  # OTLP endpoint
    sample_rate=0.1,  # Sample 10% of traces
)

setup_tracing(
    app,
    config=tracing_config,
    exporter_type="otlp",  # or "jaeger"
)

# Automatic features:
# - All HTTP requests are traced with spans
# - Exceptions are recorded as span events
# - Trace IDs added to error responses
# - PII automatically masked in spans
# - X-Trace-ID header added to responses
```

### Accept-Language Header Support

The error handler automatically parses the `Accept-Language` header:

```python
# Request with header:
# Accept-Language: ko-KR,ko;q=0.9,en;q=0.8

# The handler will try locales in order:
# 1. ko-KR
# 2. ko
# 3. en (default)
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [API Reference](docs/API.md) - Complete API documentation
- [Examples](examples/) - Usage examples
- [SPEC-001](.moai/specs/SPEC-001/spec.md) - Error handler implementation specification
- [SPEC-MONITOR-002](.moai/specs/SPEC-MONITOR-002/spec.md) - Monitoring system specification
- [SPEC-TRACING-003](.moai/specs/SPEC-TRACING-003/spec.md) - Distributed tracing specification

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=fastapi_error_codes --cov-report=html
```

Test Results:
- 104/104 tests passing
- 95%+ code coverage
- TRUST 5 framework compliance

## Project Status

- **Version**: 0.1.0
- **Tests**: 104/104 passing
- **Coverage**: 95%+
- **Status**: Production Ready

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [GitHub Repository](https://github.com/yarang/fastapi-error-codes)
- [Issue Tracker](https://github.com/yarang/fastapi-error-codes/issues)
