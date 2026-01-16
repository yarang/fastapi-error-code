# fastapi-error-codes

Structured exception handling with error codes and internationalization support for FastAPI applications.

## Features

- 🔢 **Custom Error Codes**: Define application-specific error codes for better tracking
- 🌍 **i18n Support**: Multi-language error messages with automatic fallback
- 📝 **Domain Organization**: Organize errors by domain (auth, validation, business, etc.)
- 🎯 **FastAPI Integration**: Seamless integration with automatic handler setup
- 📚 **OpenAPI Documentation**: Automatic Swagger/OpenAPI documentation
- 🔒 **Type Safe**: Full type hints support

## Installation

```bash
pip install fastapi-error-codes
```

## Quick Start

```python
from fastapi import FastAPI
from fastapi_error_codes import BaseAppException, register_exception, setup_exception_handler

# Define your exceptions
@register_exception(error_code=201, message='Authentication required')
class AuthRequiredException(BaseAppException):
    pass

# Create FastAPI app
app = FastAPI()
setup_exception_handler(app)

# Use in endpoints
@app.get('/protected')
def protected():
    raise AuthRequiredException()
```

## Documentation

Coming soon...

## License

MIT License - see [LICENSE](LICENSE) file for details.
