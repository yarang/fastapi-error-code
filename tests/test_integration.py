"""
Integration tests for fastapi-error-codes package.

Tests the complete integration of all modules: domain, i18n, models, config, and handlers.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_error_codes.base import BaseAppException
from fastapi_error_codes.config import ErrorHandlerConfig
from fastapi_error_codes.domain import ErrorDomain
from fastapi_error_codes.handlers import setup_exception_handler
from fastapi_error_codes.i18n import MessageProvider
from fastapi_error_codes.models import ErrorResponse, ValidationErrorResponse


class TestFullStackIntegration:
    """Test complete integration of all modules."""

    def test_end_to_end_error_handling(self):
        """Test complete error handling flow from exception to response."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise BaseAppException(
                error_code=201,
                message="errors.auth.required",
                status_code=401
            )

        config = ErrorHandlerConfig(
            default_locale="en",
            locale_dir="locales"
        )
        setup_exception_handler(app, config)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error", headers={"Accept-Language": "en"})

        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == 201
        assert "message" in data
        assert "timestamp" in data

    def test_domain_validation_integration(self):
        """Test ErrorDomain integration with error codes."""
        # Verify predefined domains exist
        auth_domain = ErrorDomain.get_domain("AUTH")
        assert auth_domain is not None
        assert 201 in auth_domain
        assert 299 in auth_domain

        resource_domain = ErrorDomain.get_domain("RESOURCE")
        assert resource_domain is not None
        assert 301 in resource_domain

    def test_i18n_with_fallback_chain(self):
        """Test i18n with complete fallback chain."""
        provider = MessageProvider(
            locale_dir="locales",
            default_locale="en"
        )

        # Test message retrieval with fallback
        message = provider.get_message("errors.auth.required", locale="en")
        assert message == "Authentication required"

        # Test with Korean locale
        message_ko = provider.get_message("errors.auth.required", locale="ko")
        assert "인증" in message_ko or "Authentication" in message_ko

    def test_validation_error_response(self):
        """Test ValidationErrorResponse integration."""
        errors = [
            {"field": "email", "message": "Invalid email", "code": "INVALID_EMAIL"},
            {"field": "password", "message": "Too short", "code": "TOO_SHORT"}
        ]

        response = ValidationErrorResponse.from_validation_details(
            error_code=401,
            message="Validation failed",
            details=errors
        )

        assert len(response.errors) == 2
        assert response.errors[0].field == "email"
        assert response.error_code == 401

    def test_config_presets_integration(self):
        """Test ErrorHandlerConfig presets with handlers."""
        app = FastAPI()

        @app.get("/debug-error")
        async def debug_error():
            raise ValueError("Debug test error")

        @app.get("/prod-error")
        async def prod_error():
            raise ValueError("Production test error")

        # Development config with debug enabled
        dev_config = ErrorHandlerConfig.development()
        setup_exception_handler(app, dev_config)

        client = TestClient(app, raise_server_exceptions=False)

        # Test debug endpoint
        response = client.get("/debug-error")
        assert response.status_code == 500
        data = response.json()
        assert "error_code" in data

    def test_environment_variable_config(self):
        """Test configuration from environment variables."""
        import os

        # Save original values
        original_locale = os.environ.get("ERROR_LOCALE")
        original_debug = os.environ.get("ERROR_DEBUG")

        try:
            os.environ["ERROR_LOCALE"] = "ko"
            os.environ["ERROR_DEBUG"] = "true"

            config = ErrorHandlerConfig.from_environment()
            assert config.default_locale == "ko"
            assert config.debug_mode is True
        finally:
            # Restore original values
            if original_locale is None:
                os.environ.pop("ERROR_LOCALE", None)
            else:
                os.environ["ERROR_LOCALE"] = original_locale

            if original_debug is None:
                os.environ.pop("ERROR_DEBUG", None)
            else:
                os.environ["ERROR_DEBUG"] = original_debug

    def test_accept_language_parsing_integration(self):
        """Test Accept-Language header parsing in real scenario."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise BaseAppException(
                error_code=201,
                message="errors.auth.required",
                status_code=401
            )

        config = ErrorHandlerConfig(
            default_locale="en",
            locale_dir="locales"
        )
        setup_exception_handler(app, config)

        client = TestClient(app, raise_server_exceptions=False)

        # Test with multiple locales in Accept-Language
        response = client.get(
            "/error",
            headers={"Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "message" in data

    def test_error_response_serialization(self):
        """Test complete error response serialization."""
        exc = BaseAppException(
            error_code=301,
            message="User not found",
            status_code=404,
            detail={"user_id": 123}
        )

        response = ErrorResponse.from_exception(exc)

        # Test dict conversion
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
        assert response_dict["error_code"] == 301
        assert response_dict["message"] == "User not found"
        assert response_dict["status_code"] == 404
        assert response_dict["detail"] == {"user_id": 123}

    def test_custom_domain_registration(self):
        """Test custom domain registration and validation."""
        # Register custom domain
        ErrorDomain.register_domain("BUSINESS", (1000, 1999))

        # Verify it's registered
        domain = ErrorDomain.get_domain("BUSINESS")
        assert domain is not None
        assert domain.name == "BUSINESS"
        assert 1000 in domain
        assert 1999 in domain

        # Verify code validation
        assert ErrorDomain.is_valid_code(1500, "BUSINESS")
        assert not ErrorDomain.is_valid_code(500, "BUSINESS")

    def test_message_provider_caching(self):
        """Test MessageProvider caching across multiple requests."""
        provider = MessageProvider(
            locale_dir="locales",
            default_locale="en"
        )

        # First call loads from file
        msg1 = provider.get_message("errors.auth.required")

        # Second call uses cache
        msg2 = provider.get_message("errors.auth.required")

        assert msg1 == msg2

        # Verify locale is cached
        assert "en" in provider._cache

    def test_multiple_exception_types(self):
        """Test handling of different exception types."""
        app = FastAPI()

        @app.get("/base-exception")
        async def base_exception():
            raise BaseAppException(
                error_code=201,
                message="Auth required",
                status_code=401
            )

        @app.get("/unknown-exception")
        async def unknown_exception():
            raise ValueError("Unknown error")

        setup_exception_handler(app)

        client = TestClient(app, raise_server_exceptions=False)

        # Test BaseAppException
        response1 = client.get("/base-exception")
        assert response1.status_code == 401
        data1 = response1.json()
        assert data1["error_code"] == 201

        # Test unknown exception
        response2 = client.get("/unknown-exception")
        assert response2.status_code == 500
        data2 = response2.json()
        assert data2["error_code"] == 500


class TestEARSRequirements:
    """Test compliance with EARS format requirements from SPEC-001."""

    def test_uq_001_error_code_validation(self):
        """UQ-001: error_code 0-9999 validation."""
        # Valid error codes
        response1 = ErrorResponse(error_code=0, message="Test")
        assert response1.error_code == 0

        response2 = ErrorResponse(error_code=9999, message="Test")
        assert response2.error_code == 9999

        # Pydantic will reject invalid codes
        with pytest.raises(Exception):  # ValidationError
            ErrorResponse(error_code=10000, message="Test")

    def test_uq_002_iso_8601_timestamp(self):
        """UQ-002: ISO 8601 UTC timestamp."""
        response = ErrorResponse(error_code=500, message="Test")
        assert response.timestamp.endswith("Z")

        # Verify it's valid ISO format
        from datetime import datetime
        parsed = datetime.fromisoformat(response.timestamp.replace("Z", "+00:00"))
        assert parsed is not None

    def test_uq_004_fallback_to_default_message(self):
        """UQ-004: Fallback to default message."""
        provider = MessageProvider(
            locale_dir="locales",
            default_locale="en"
        )

        # Request non-existent locale
        message = provider.get_message("errors.auth.required", locale="fr")
        # Should fallback to English
        assert "Authentication" in message or "required" in message

    def test_ed_001_exception_to_status_code(self):
        """ED-001: BaseAppException -> HTTP status code."""
        exc = BaseAppException(
            error_code=301,
            message="Not found",
            status_code=404
        )

        response = ErrorResponse.from_exception(exc)
        assert response.status_code == 404

    def test_ed_002_accept_language_to_localized_messages(self):
        """ED-002: Accept-Language -> localized messages."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise BaseAppException(
                error_code=201,
                message="errors.auth.required",
                status_code=401
            )

        config = ErrorHandlerConfig(
            default_locale="en",
            locale_dir="locales"
        )
        setup_exception_handler(app, config)

        client = TestClient(app, raise_server_exceptions=False)

        # Request Korean
        response_ko = client.get("/error", headers={"Accept-Language": "ko"})
        data_ko = response_ko.json()
        assert "message" in data_ko

        # Request English
        response_en = client.get("/error", headers={"Accept-Language": "en"})
        data_en = response_en.json()
        assert "message" in data_en

    def test_ed_003_missing_locale_fallback(self):
        """ED-003: Missing locale -> en.json fallback."""
        provider = MessageProvider(
            locale_dir="locales",
            default_locale="en"
        )

        # Non-existent locale should fallback to default
        message = provider.get_message("errors.auth.required", locale="xyz")
        assert "Authentication" in message or "required" in message

    def test_ed_005_exception_handler_registration(self):
        """ED-005: setup_exception_handler() registration."""
        app = FastAPI()

        # Before registration
        initial_handlers = len(app.exception_handlers)

        setup_exception_handler(app)

        # After registration
        assert len(app.exception_handlers) > initial_handlers
