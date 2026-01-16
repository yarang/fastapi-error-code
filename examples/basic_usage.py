"""
Basic usage example for fastapi-error-codes.

This example demonstrates:
1. Creating custom exceptions with @register_exception
2. Raising exceptions in FastAPI endpoints
3. Receiving formatted error responses
"""

from fastapi import FastAPI
from fastapi_error_codes import BaseAppException, register_exception

# Define custom exceptions using the decorator
@register_exception(error_code=201, message='Authentication required', status_code=401)
class AuthRequiredException(BaseAppException):
    """Raised when authentication is required but not provided."""
    pass


@register_exception(error_code=301, message='User not found', status_code=404)
class UserNotFoundException(BaseAppException):
    """Raised when a requested user does not exist."""
    pass


@register_exception(error_code=401, message='Invalid email format', status_code=400)
class InvalidEmailException(BaseAppException):
    """Raised when email validation fails."""
    pass


# Create FastAPI app
app = FastAPI(title="Basic Usage Example")


# Endpoints that use custom exceptions
@app.get("/protected")
async def protected_route():
    """
    This endpoint requires authentication.
    Raises AuthRequiredException if accessed.
    """
    raise AuthRequiredException()


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    This endpoint returns a user.
    Raises UserNotFoundException if user doesn't exist.
    """
    # Simulate user lookup
    if user_id != 1:
        raise UserNotFoundException(
            detail={"user_id": user_id, "hint": "Try user_id=1"}
        )

    return {"user_id": 1, "name": "John Doe"}


@app.post("/users")
async def create_user(email: str):
    """
    This endpoint creates a new user.
    Raises InvalidEmailException if email is invalid.
    """
    # Simple email validation
    if "@" not in email:
        exc = InvalidEmailException()
        exc.add_detail("field", "email")
        exc.add_detail("provided_value", email)
        raise exc

    return {"email": email, "status": "created"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
