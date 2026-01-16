"""
Tests for domain.py module - ErrorDomain class.

RED phase: Write failing tests first to define expected behavior.
"""

import pytest

from fastapi_error_codes.domain import ErrorDomain


@pytest.fixture(autouse=True)
def reset_domains():
    """
    Reset domain registry before each test to ensure test isolation.

    This fixture automatically runs before every test in this module,
    ensuring that custom domains registered in one test don't affect
    subsequent tests.
    """
    # Store original domains
    original_domains = ErrorDomain._domains.copy()

    yield

    # Restore original domains
    ErrorDomain._domains.clear()
    ErrorDomain._domains.update(original_domains)


class TestErrorDomainPredefinedDomains:
    """Test predefined error domains."""

    def test_auth_domain_exists(self):
        """AUTH domain should be predefined with codes 200-299."""
        domain = ErrorDomain.get_domain("AUTH")
        assert domain is not None
        assert domain.name == "AUTH"
        assert domain.code_range == (200, 299)

    def test_resource_domain_exists(self):
        """RESOURCE domain should be predefined with codes 300-399."""
        domain = ErrorDomain.get_domain("RESOURCE")
        assert domain is not None
        assert domain.name == "RESOURCE"
        assert domain.code_range == (300, 399)

    def test_validation_domain_exists(self):
        """VALIDATION domain should be predefined with codes 400-499."""
        domain = ErrorDomain.get_domain("VALIDATION")
        assert domain is not None
        assert domain.name == "VALIDATION"
        assert domain.code_range == (400, 499)

    def test_server_domain_exists(self):
        """SERVER domain should be predefined with codes 500-599."""
        domain = ErrorDomain.get_domain("SERVER")
        assert domain is not None
        assert domain.name == "SERVER"
        assert domain.code_range == (500, 599)

    def test_custom_domain_exists(self):
        """CUSTOM domain should be predefined with codes 900-999."""
        domain = ErrorDomain.get_domain("CUSTOM")
        assert domain is not None
        assert domain.name == "CUSTOM"
        assert domain.code_range == (900, 999)


class TestErrorDomainCustomRegistration:
    """Test custom domain registration."""

    def test_register_custom_domain(self):
        """Should be able to register a custom domain."""
        ErrorDomain.register_domain("BUSINESS", (1000, 1999))
        domain = ErrorDomain.get_domain("BUSINESS")
        assert domain is not None
        assert domain.name == "BUSINESS"
        assert domain.code_range == (1000, 1999)

    def test_register_duplicate_domain_raises_error(self):
        """Registering duplicate domain should raise ValueError."""
        with pytest.raises(ValueError, match="already registered"):
            ErrorDomain.register_domain("AUTH", (200, 299))

    def test_register_invalid_code_range_raises_error(self):
        """Registering with invalid range (start > end) should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid code range"):
            ErrorDomain.register_domain("INVALID", (500, 400))


class TestErrorDomainCodeValidation:
    """Test error code validation within domains."""

    def test_is_valid_code_true_for_auth_domain(self):
        """Should return True for valid AUTH domain codes."""
        assert ErrorDomain.is_valid_code(201, "AUTH") is True
        assert ErrorDomain.is_valid_code(250, "AUTH") is True
        assert ErrorDomain.is_valid_code(299, "AUTH") is True

    def test_is_valid_code_false_for_out_of_range(self):
        """Should return False for codes outside domain range."""
        assert ErrorDomain.is_valid_code(199, "AUTH") is False
        assert ErrorDomain.is_valid_code(300, "AUTH") is False

    def test_is_valid_code_nonexistent_domain(self):
        """Should return False for non-existent domain."""
        assert ErrorDomain.is_valid_code(100, "NONEXISTENT") is False

    def test_get_domain_for_code(self):
        """Should return correct domain for a given code."""
        domain = ErrorDomain.get_domain_for_code(201)
        assert domain is not None
        assert domain.name == "AUTH"

    def test_get_domain_for_code_outside_ranges(self):
        """Should return None for codes outside any domain range."""
        domain = ErrorDomain.get_domain_for_code(1000)
        assert domain is None  # Assuming no domain covers 1000


class TestErrorDomainProperties:
    """Test ErrorDomain class properties."""

    def test_domain_properties(self):
        """Domain should expose name and code_range as properties."""
        domain = ErrorDomain("TEST", (600, 699))
        assert domain.name == "TEST"
        assert domain.code_range == (600, 699)

    def test_domain_contains_code(self):
        """Domain should check if it contains a specific code."""
        domain = ErrorDomain("TEST", (600, 699))
        assert 600 in domain
        assert 650 in domain
        assert 699 in domain
        assert 599 not in domain
        assert 700 not in domain


class TestErrorDomainListAll:
    """Test listing all registered domains."""

    def test_list_all_domains(self):
        """Should return list of all registered domain names."""
        domains = ErrorDomain.list_domains()
        assert "AUTH" in domains
        assert "RESOURCE" in domains
        assert "VALIDATION" in domains
        assert "SERVER" in domains
        assert "CUSTOM" in domains

    def test_list_domains_includes_custom(self):
        """Custom registered domains should appear in list."""
        ErrorDomain.register_domain("TEMPORARY", (800, 899))
        domains = ErrorDomain.list_domains()
        assert "TEMPORARY" in domains
