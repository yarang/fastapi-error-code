"""
Example using fastapi-error-codes with FastAPI exception handler.

This example demonstrates:
1. Setting up a global exception handler for BaseAppException
2. Consistent error response format across all endpoints
3. Integration with FastAPI's exception handling system

Note: This example requires the handler implementation which is planned for future releases.
For now, it shows how the system will work once handlers are implemented.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_error_codes import BaseAppException, register_exception


# Define exceptions
@register_exception(error_code=201, message='Authentication required', status_code=401)
class AuthRequiredException(BaseAppException):
    pass


@register_exception(error_code=301, message='Resource not found', status_code=404)
class ResourceNotFoundException(BaseAppException):
    pass


# Create FastAPI app
app = FastAPI(title="With Handler Example")


# Custom exception handler
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """
    Global exception handler for BaseAppException.

    This handler catches all BaseAppException subclasses and returns
    a consistent JSON response format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=exc.headers or {},
    )


# Endpoints
@app.get("/protected")
async def protected():
    """Endpoint that requires authentication."""
    raise AuthRequiredException(
        detail={"redirect_url": "/login"}
    )


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Endpoint that returns an item or raises not found."""
    if item_id < 1 or item_id > 100:
        raise ResourceNotFoundException(
            detail={
                "resource_type": "Item",
                "resource_id": item_id,
                "valid_range": "1-100"
            }
        )

    return {"item_id": item_id, "name": f"Item {item_id}"}


@app.get("/health")
async def health_check():
    """Health check endpoint that never raises exceptions."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
