"""
Tests for models.py module - Pydantic response models.

RED phase: Write failing tests first to define expected behavior.
"""

from datetime import datetime
from typing import List, Dict, Any

import pytest
from pydantic import ValidationError

from fastapi_error_codes.models import (
    ErrorResponse,
    ValidationErrorResponse,
    ErrorDetail,
    ErrorDetailItem,
)


class TestErrorDetail:
    """Test ErrorDetail model for single error information."""

    def test_create_error_detail(self):
        """Should create ErrorDetail with all fields."""
        detail = ErrorDetail(
            field="email",
            message="Invalid email format",
            code="INVALID_FORMAT"
        )
        assert detail.field == "email"
        assert detail.message == "Invalid email format"
        assert detail.code == "INVALID_FORMAT"

    def test_create_error_detail_without_code(self):
        """Should create ErrorDetail without optional code field."""
        detail = ErrorDetail(
            field="password",
            message="Password is required"
        )
        assert detail.field == "password"
        assert detail.message == "Password is required"
        assert detail.code is None

    def test_error_detail_serialization(self):
        """Should serialize to dict correctly."""
        detail = ErrorDetail(
            field="email",
            message="Invalid email",
            code="INVALID"
        )
        data = detail.model_dump() if hasattr(detail, 'model_dump') else detail.dict()
        assert data["field"] == "email"
        assert data["message"] == "Invalid email"
        assert data["code"] == "INVALID"

    def test_error_detail_from_dict(self):
        """Should create from dict using model_validate."""
        data = {
            "field": "username",
            "message": "Username already exists",
            "code": "DUPLICATE"
        }
        detail = ErrorDetail.model_validate(data)
        assert detail.field == "username"
        assert detail.message == "Username already exists"
        assert detail.code == "DUPLICATE"


class TestErrorDetailItem:
    """Test ErrorDetailItem for complex validation errors."""

    def test_create_error_detail_item_with_location(self):
        """Should create ErrorDetailItem with location information."""
        item = ErrorDetailItem(
            loc=["body", "users", 0, "email"],
            msg="field required",
            type="value_error.missing"
        )
        assert item.loc == ["body", "users", 0, "email"]
        assert item.msg == "field required"
        assert item.type == "value_error.missing"

    def test_create_error_detail_item_minimal(self):
        """Should create ErrorDetailItem with minimal fields."""
        item = ErrorDetailItem(
            loc=["query", "page"],
            msg="value is not a valid integer"
        )
        assert item.loc == ["query", "page"]
        assert item.msg == "value is not a valid integer"
        assert item.type is None

    def test_error_detail_item_serialization(self):
        """Should serialize to dict for JSON response."""
        item = ErrorDetailItem(
            loc=["body", "email"],
            msg="invalid email format",
            type="value_error.email"
        )
        data = item.model_dump() if hasattr(item, 'model_dump') else item.dict()
        assert data["loc"] == ["body", "email"]
        assert data["msg"] == "invalid email format"
        assert data["type"] == "value_error.email"


class TestErrorResponse:
    """Test ErrorResponse model for standard error responses."""

    def test_create_error_response_minimal(self):
        """Should create ErrorResponse with required fields only."""
        response = ErrorResponse(
            error_code=201,
            message="Authentication required"
        )
        assert response.error_code == 201
        assert response.message == "Authentication required"
        assert response.status_code is None
        assert response.detail is None
        assert response.timestamp is not None

    def test_create_error_response_full(self):
        """Should create ErrorResponse with all fields."""
        response = ErrorResponse(
            error_code=301,
            message="User not found",
            status_code=404,
            detail={"user_id": 123},
            error_name="UserNotFoundException"
        )
        assert response.error_code == 301
        assert response.message == "User not found"
        assert response.status_code == 404
        assert response.detail == {"user_id": 123}
        assert response.error_name == "UserNotFoundException"

    def test_error_response_timestamp_format(self):
        """Should include ISO 8601 UTC timestamp."""
        response = ErrorResponse(
            error_code=500,
            message="Internal error"
        )
        # Timestamp should be ISO format with 'Z' suffix for UTC
        assert response.timestamp.endswith("Z")
        # Should be parseable
        datetime.fromisoformat(response.timestamp.replace("Z", "+00:00"))

    def test_error_response_serialization(self):
        """Should serialize to dict for JSON response."""
        response = ErrorResponse(
            error_code=201,
            message="Auth required",
            status_code=401,
            detail={"token": "expired"}
        )
        data = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
        assert data["error_code"] == 201
        assert data["message"] == "Auth required"
        assert data["status_code"] == 401
        assert data["detail"] == {"token": "expired"}
        assert "timestamp" in data

    def test_error_response_from_exception(self):
        """Should create ErrorResponse from BaseAppException."""
        from fastapi_error_codes.base import BaseAppException

        exc = BaseAppException(
            error_code=401,
            message="Invalid credentials",
            status_code=401,
            detail={"attempts": 3}
        )
        response = ErrorResponse.from_exception(exc)
        assert response.error_code == 401
        assert response.message == "Invalid credentials"
        assert response.status_code == 401
        assert response.detail == {"attempts": 3}
        assert response.error_name == "BaseAppException"


class TestValidationErrorResponse:
    """Test ValidationErrorResponse for validation errors."""

    def test_create_validation_error_response_minimal(self):
        """Should create ValidationErrorResponse with required fields."""
        response = ValidationErrorResponse(
            error_code=401,
            message="Validation failed",
            errors=[]
        )
        assert response.error_code == 401
        assert response.message == "Validation failed"
        assert response.errors == []

    def test_create_validation_error_response_with_errors(self):
        """Should create ValidationErrorResponse with error details."""
        errors = [
            ErrorDetail(field="email", message="Invalid email", code="INVALID_EMAIL"),
            ErrorDetail(field="password", message="Too short", code="TOO_SHORT")
        ]
        response = ValidationErrorResponse(
            error_code=401,
            message="Validation failed",
            errors=errors
        )
        assert len(response.errors) == 2
        assert response.errors[0].field == "email"
        assert response.errors[1].field == "password"

    def test_validation_error_response_serialization(self):
        """Should serialize to dict with nested errors."""
        errors = [
            ErrorDetail(field="email", message="Invalid", code="INVALID"),
            ErrorDetail(field="age", message="Must be positive", code="INVALID_RANGE")
        ]
        response = ValidationErrorResponse(
            error_code=401,
            message="Validation errors",
            errors=errors
        )
        data = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
        assert data["error_code"] == 401
        assert data["message"] == "Validation errors"
        assert len(data["errors"]) == 2
        assert data["errors"][0]["field"] == "email"

    def test_validation_error_response_from_details(self):
        """Should create ValidationErrorResponse from list of error details."""
        error_dicts = [
            {"field": "email", "message": "Invalid", "code": "INVALID"},
            {"field": "password", "message": "Required", "code": "REQUIRED"}
        ]
        response = ValidationErrorResponse.from_validation_details(
            error_code=401,
            message="Validation failed",
            details=error_dicts
        )
        assert len(response.errors) == 2
        assert response.errors[0].field == "email"
        assert response.errors[1].field == "password"


class TestPydanticCompatibility:
    """Test Pydantic v1/v2 compatibility layer."""

    def test_model_dump_method_exists(self):
        """Should support model_dump() for Pydantic v2."""
        response = ErrorResponse(
            error_code=201,
            message="Test"
        )
        # Pydantic v2 uses model_dump()
        assert hasattr(response, 'model_dump')
        data = response.model_dump()
        assert "error_code" in data

    def test_model_validate_method_exists(self):
        """Should support model_validate() for Pydantic v2."""
        data = {"error_code": 201, "message": "Test"}
        # Pydantic v2 uses model_validate()
        response = ErrorResponse.model_validate(data)
        assert response.error_code == 201

    def test_json_serialization(self):
        """Should support JSON serialization."""
        response = ErrorResponse(
            error_code=201,
            message="Test message"
        )
        # Should be able to serialize to JSON
        json_str = response.model_dump_json() if hasattr(response, 'model_dump_json') else response.json()
        assert "201" in json_str
        assert "Test message" in json_str

    def test_schema_generation(self):
        """Should generate JSON schema for models."""
        schema = ErrorResponse.model_json_schema() if hasattr(ErrorResponse, 'model_json_schema') else ErrorResponse.schema()
        assert "properties" in schema or "definitions" in schema
        assert "error_code" in str(schema)

    def test_validation_error_on_invalid_data(self):
        """Should raise ValidationError on invalid data."""
        with pytest.raises(ValidationError):
            ErrorResponse(
                error_code="invalid",  # Should be int
                message="Test"
            )
