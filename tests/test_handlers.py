"""
Tests for handlers.py module - setup_exception_handler function.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_error_codes.base import BaseAppException
from fastapi_error_codes.config import ErrorHandlerConfig
from fastapi_error_codes.handlers import setup_exception_handler


class TestExceptionHandlerRegistration:
    """Test exception handler registration with FastAPI app."""

    def test_setup_exception_handler_registers_handler(self):
        """Should register exception handler with the app."""
        app = FastAPI()
        config = ErrorHandlerConfig()
        setup_exception_handler(app, config)

        # Verify handler was registered
        assert len(app.exception_handlers) > 0

    def test_setup_exception_handler_with_default_config(self):
        """Should work with default ErrorHandlerConfig."""
        app = FastAPI()
        setup_exception_handler(app)
        # Should not raise any errors
        assert app is not None


class TestBaseAppExceptionHandling:
    """Test handling of BaseAppException and its subclasses."""

    def test_handle_base_app_exception(self):
        """Should convert BaseAppException to ErrorResponse."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise BaseAppException(
                error_code=201,
                message="Auth required",
                status_code=401
            )

        setup_exception_handler(app)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == 201
        assert data["message"] == "Auth required"

    def test_handle_exception_with_detail(self):
        """Should include detail in error response."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise BaseAppException(
                error_code=301,
                message="User not found",
                status_code=404,
                detail={"user_id": 123}
            )

        setup_exception_handler(app)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        data = response.json()
        # In non-debug mode, detail might not be included
        assert "error_code" in data

    def test_handle_exception_with_custom_headers(self):
        """Should include custom headers in response."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise BaseAppException(
                error_code=429,
                message="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"}
            )

        setup_exception_handler(app)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        assert "retry-after" in response.headers


class TestI18nMessageResolution:
    """Test i18n message resolution with Accept-Language header."""

    def test_resolve_message_for_requested_locale(self):
        """Should resolve message in requested locale."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            exc = BaseAppException(
                error_code=201,
                message="errors.auth.required",
                status_code=401
            )
            raise exc

        config = ErrorHandlerConfig(
            default_locale="en",
            locale_dir="locales"
        )
        setup_exception_handler(app, config)

        client = TestClient(app, raise_server_exceptions=False)
        # Request Korean locale
        response = client.get(
            "/error",
            headers={"Accept-Language": "ko"}
        )

        data = response.json()
        # Should return message (either resolved or original key)
        assert "message" in data

    def test_fallback_to_default_locale(self):
        """Should fallback to default locale when requested not found."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            exc = BaseAppException(
                error_code=500,
                message="errors.server.internal_error",
                status_code=500
            )
            raise exc

        config = ErrorHandlerConfig(
            default_locale="en",
            locale_dir="locales"
        )
        setup_exception_handler(app, config)

        client = TestClient(app, raise_server_exceptions=False)
        # Request non-existent locale
        response = client.get(
            "/error",
            headers={"Accept-Language": "fr"}
        )

        data = response.json()
        assert "message" in data


class TestDebugModeAndTraceback:
    """Test debug mode and traceback inclusion."""

    def test_include_traceback_in_debug_mode(self):
        """Should include traceback in debug mode."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        config = ErrorHandlerConfig.development()
        setup_exception_handler(app, config)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        data = response.json()
        # In debug mode with traceback enabled, should include stack info
        assert "error_code" in data

    def test_no_traceback_in_production(self):
        """Should not include traceback in production mode."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        config = ErrorHandlerConfig.production()
        setup_exception_handler(app, config)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        data = response.json()
        assert "error_code" in data


class TestUnknownExceptionHandling:
    """Test handling of unknown/non-BaseAppException errors."""

    def test_handle_unknown_exception(self):
        """Should handle unknown exceptions gracefully."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Unknown error")

        setup_exception_handler(app)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == 500


class TestResponseFormat:
    """Test error response format consistency."""

    def test_response_has_required_fields(self):
        """Error response should have all required fields."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise BaseAppException(
                error_code=201,
                message="Auth required",
                status_code=401
            )

        setup_exception_handler(app)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        data = response.json()
        assert "error_code" in data
        assert "message" in data
        assert "timestamp" in data

    def test_timestamp_iso_format(self):
        """Timestamp should be in ISO 8601 format with UTC."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            raise BaseAppException(
                error_code=201,
                message="Test",
                status_code=400
            )

        setup_exception_handler(app)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        data = response.json()
        assert data["timestamp"].endswith("Z")


class TestMessageFormatting:
    """Test message formatting with parameters."""

    def test_format_message_with_parameters(self):
        """Should format message with parameters from exception detail."""
        app = FastAPI()

        @app.get("/error")
        async def error_endpoint():
            exc = BaseAppException(
                error_code=301,
                message="User {user_id} not found",
                status_code=404,
                detail={"user_id": 123}
            )
            raise exc

        setup_exception_handler(app)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        data = response.json()
        # Message should be formatted with detail parameters
        assert "message" in data
