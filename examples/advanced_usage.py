"""
Advanced usage example for fastapi-error-codes.

This example demonstrates:
1. Custom exception classes with additional logic
2. Using detail field for structured error information
3. Custom headers in error responses
4. Dynamic message generation
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, Header
from fastapi_error_codes import BaseAppException, register_exception


# Custom exception with additional methods
@register_exception(
    error_code=202,
    message='Invalid credentials provided',
    status_code=401,
    domain='auth'
)
class InvalidCredentialsException(BaseAppException):
    """Raised when login credentials are invalid."""

    def __init__(
        self,
        attempts_remaining: int = 3,
        lockout_minutes: Optional[int] = None,
    ):
        super().__init__(
            error_code=202,
            message='Invalid credentials provided',
            detail={
                'attempts_remaining': attempts_remaining,
                'lockout_minutes': lockout_minutes,
            }
        )


# Exception with custom headers
@register_exception(
    error_code=429,
    message='Rate limit exceeded',
    status_code=429,
    domain='rate_limit'
)
class RateLimitException(BaseAppException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        retry_after: int,
    ):
        super().__init__(
            error_code=429,
            message=f'Rate limit exceeded: {limit} requests per {window_seconds} seconds',
            detail={
                'limit': limit,
                'window_seconds': window_seconds,
            },
            headers={'Retry-After': str(retry_after)}
        )


# Exception with dynamic message
@register_exception(
    error_code=302,
    message='Resource conflict detected',
    status_code=409,
    domain='resource'
)
class ResourceConflictException(BaseAppException):
    """Raised when a resource conflict is detected."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        conflicting_field: str,
        conflicting_value: str,
    ):
        super().__init__(
            error_code=302,
            message=f'{resource_type} conflict: {conflicting_field}={conflicting_value} already exists',
            detail={
                'resource_type': resource_type,
                'resource_id': resource_id,
                'conflicting_field': conflicting_field,
                'conflicting_value': conflicting_value,
            }
        )


# Validation exception with field-level errors
@register_exception(
    error_code=402,
    message='Validation failed',
    status_code=400,
    domain='validation'
)
class ValidationException(BaseAppException):
    """Raised when input validation fails."""

    def __init__(self, field_errors: Dict[str, List[str]]):
        """
        Args:
            field_errors: Dictionary mapping field names to list of error messages
        """
        super().__init__(
            error_code=402,
            message='Validation failed',
            detail={'field_errors': field_errors}
        )


# Create FastAPI app
app = FastAPI(title="Advanced Usage Example")


# Simulated in-memory database
users_db: Dict[str, Dict] = {
    "john@example.com": {"id": 1, "name": "John Doe"}
}


@app.post("/auth/login")
async def login(email: str, password: str):
    """Login endpoint that raises InvalidCredentialsException."""
    if email not in users_db or password != "password123":
        raise InvalidCredentialsException(
            attempts_remaining=2,
            lockout_minutes=15
        )

    return {"access_token": "abc123", "token_type": "bearer"}


@app.post("/users")
async def create_user(email: str, name: str):
    """Create user endpoint that raises ResourceConflictException."""
    if email in users_db:
        raise ResourceConflictException(
            resource_type='User',
            resource_id=email,
            conflicting_field='email',
            conflicting_value=email
        )

    users_db[email] = {"id": len(users_db) + 1, "name": name}
    return {"email": email, "id": users_db[email]["id"]}


@app.post("/users/validate")
async def validate_user_data(email: Optional[str] = None, name: Optional[str] = None):
    """Validation endpoint that raises ValidationException."""
    field_errors = {}

    if email:
        if "@" not in email:
            field_errors["email"] = field_errors.get("email", []) + ["Invalid email format"]
        if len(email) > 100:
            field_errors["email"] = field_errors.get("email", []) + ["Email too long (max 100 chars)"]

    if name:
        if len(name) < 2:
            field_errors["name"] = field_errors.get("name", []) + ["Name too short (min 2 chars)"]
        if len(name) > 50:
            field_errors["name"] = field_errors.get("name", []) + ["Name too long (max 50 chars)"]

    if field_errors:
        raise ValidationException(field_errors=field_errors)

    return {"valid": True}


# Simulated rate limiter
_request_count: Dict[str, int] = {}


@app.get("/api/data")
async def get_data(x_client_id: str = Header(...)):
    """Endpoint with rate limiting."""
    count = _request_count.get(x_client_id, 0)

    if count >= 10:
        raise RateLimitException(
            limit=10,
            window_seconds=60,
            retry_after=60
        )

    _request_count[x_client_id] = count + 1
    return {"data": "example data", "requests_remaining": 10 - count - 1}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
