"""
Sentry error tracking integration example.

This example demonstrates how to integrate Sentry error tracking
with automatic PII masking for production environments.

Note: This example requires a Sentry DSN. Set the SENTRY_DSN environment
variable or replace the placeholder below with your actual Sentry DSN.
"""

import os
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi_error_codes import (
    BaseAppException,
    setup_exception_handler,
    ErrorHandlerConfig,
    MetricsConfig,
    MetricsPreset,
)

# Get Sentry DSN from environment or use placeholder
SENTRY_DSN = os.environ.get(
    "SENTRY_DSN",
    "https://examplePublicKey@o0.ingest.sentry.io/0",
)

# Create FastAPI app
app = FastAPI(title="Sentry Integration Example")

# Setup error handler with Sentry integration
error_config = ErrorHandlerConfig(
    default_locale="en",
    debug_mode=False,
)

# Production preset with Sentry
# In production, always provide a real Sentry DSN
metrics_config = MetricsPreset.production(
    sentry_dsn=SENTRY_DSN,
)

# Customize PII patterns for masking
# This will automatically mask fields containing these patterns
from dataclasses import replace

metrics_config = replace(
    metrics_config,
    pii_patterns=[
        "email",
        "password",
        "ssn",
        "credit_card",
        "api_key",
        "token",
        "secret",
        "phone",
        "address",  # Custom: also mask address fields
    ],
)

setup_exception_handler(
    app,
    config=error_config,
    metrics_config=metrics_config,
)


# Define custom exceptions
class AuthenticationError(BaseAppException):
    def __init__(self, email: str):
        # Email will be automatically masked before sending to Sentry
        super().__init__(
            error_code=201,
            message="Authentication failed",
            status_code=401,
            detail={
                "email": email,  # Will be masked: ***@***.***
                "reason": "Invalid credentials",
            },
        )


class PaymentError(BaseAppException):
    def __init__(self, user_id: int, card_last_four: str):
        # Credit card info will be masked
        super().__init__(
            error_code=501,
            message="Payment processing failed",
            status_code=402,
            detail={
                "user_id": user_id,
                "credit_card": f"****-****-****-{card_last_four}",
                "amount": 99.99,
            },
        )


class UserProfileError(BaseAppException):
    def __init__(self, user_data: Dict[str, Any]):
        # Multiple PII fields will be masked
        super().__init__(
            error_code=502,
            message="User profile update failed",
            status_code=422,
            detail=user_data,
        )


# API endpoints
@app.get("/")
async def root():
    """Root endpoint with usage information."""
    return {
        "message": "Sentry Integration Example",
        "status": "Sentry enabled" if SENTRY_DSN else "Sentry disabled (no DSN)",
        "endpoints": {
            "auth_error": "/auth/fail",
            "payment_error": "/payment/fail",
            "profile_error": "/profile/fail",
            "dashboard": "/api/metrics/summary",
        },
        "features": [
            "Automatic PII masking (email, password, credit card, etc.)",
            "Non-blocking error transmission",
            "Graceful degradation if Sentry is unavailable",
            "Breadcrumbs for error context",
        ],
    }


@app.get("/auth/fail")
async def trigger_auth_error():
    """
    Trigger authentication error with email.

    The email in the detail will be automatically masked
    before sending to Sentry: user@example.com -> ***@***.***
    """
    raise AuthenticationError(email="user@example.com")


@app.get("/payment/fail")
async def trigger_payment_error():
    """
    Trigger payment error with credit card information.

    Credit card information will be partially masked.
    """
    raise PaymentError(
        user_id=12345,
        card_last_four="1234",
    )


@app.get("/profile/fail")
async def trigger_profile_error():
    """
    Trigger profile error with multiple PII fields.

    All PII fields will be automatically masked before
    sending to Sentry.
    """
    raise UserProfileError(
        user_data={
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "address": "123 Main St, City, Country",
            "password": "supersecret123",  # Will be masked: ***
        }
    )


@app.get("/test/breadcrumb")
async def test_breadcrumb():
    """
    Add breadcrumbs and trigger error.

    Breadcrumbs provide context leading up to an error.
    """
    from fastapi_error_codes import SentryIntegration

    # Access Sentry integration from app state
    if hasattr(app.state, "metrics_sentry"):
        sentry = app.state.metrics_sentry

        # Add breadcrumbs for context
        sentry.add_breadcrumb(
            category="auth",
            message="User login attempt",
            level="info",
            data={"user_id": "123"},  # Will be masked if needed
        )

        sentry.add_breadcrumb(
            category="auth",
            message="Authentication failed",
            level="warning",
        )

    # Trigger error - Sentry will include breadcrumbs
    raise AuthenticationError(email="test@example.com")


@app.get("/sentry/health")
async def check_sentry_health():
    """Check if Sentry integration is working."""
    if hasattr(app.state, "metrics_sentry"):
        sentry = app.state.metrics_sentry
        return {
            "sentry_enabled": sentry.enabled,
            "sentry_dsn_provided": bool(sentry.dsn),
            "pii_patterns": sentry.pii_patterns,
        }
    return {"sentry_enabled": False}


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Sentry Integration Example")
    print("=" * 60)

    if SENTRY_DSN == "https://examplePublicKey@o0.ingest.sentry.io/0":
        print("\nWARNING: Using placeholder Sentry DSN!")
        print("Set SENTRY_DSN environment variable for actual error tracking:")
        print("  export SENTRY_DSN='https://key@sentry.io/project'")
        print("\nSentry integration will be initialized but events won't be sent.")
    else:
        print(f"\nSentry DSN: {SENTRY_DSN}")
        print("Sentry integration is enabled and events will be sent.")

    print("\nEndpoints:")
    print("  GET /                   : Usage information")
    print("  GET /auth/fail          : Trigger auth error (email masked)")
    print("  GET /payment/fail       : Trigger payment error (card masked)")
    print("  GET /profile/fail       : Trigger profile error (multi PII masked)")
    print("  GET /test/breadcrumb    : Test breadcrumbs with context")
    print("  GET /sentry/health      : Check Sentry integration status")
    print("\nFeatures:")
    print("  - Automatic PII masking")
    print("  - Non-blocking error transmission")
    print("  - Graceful degradation")
    print("  - Breadcrumbs for context")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
