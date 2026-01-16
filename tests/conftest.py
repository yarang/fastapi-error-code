"""Pytest configuration and fixtures for fastapi-error-codes tests."""

import pytest


@pytest.fixture
def clean_registry():
    """Clear the exception registry before each test."""
    from fastapi_error_codes.registry import _registry

    # Store original state
    original_codes = _registry.get_all_codes().copy()

    yield

    # Clear registry after test
    for code in _registry.get_all_codes():
        if code not in original_codes:
            _registry._exceptions.pop(code, None)
            _registry._messages.pop(code, None)
            _registry._metadata.pop(code, None)
