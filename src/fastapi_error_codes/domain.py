"""
Domain management for fastapi-error-codes package.

This module provides the ErrorDomain class for managing error code ranges
and domains. Each domain represents a category of errors with a specific
code range.
"""

from typing import Dict, List, Optional, Tuple


class ErrorDomain:
    """
    Represents an error domain with a specific code range.

    Error domains categorize errors into logical groups with contiguous
    code ranges. This helps organize error codes and validate that codes
    fall within expected ranges.

    Attributes:
        name: The domain name (e.g., "AUTH", "RESOURCE")
        code_range: Tuple of (start_code, end_code) for this domain

    Example:
        ```python
        domain = ErrorDomain("AUTH", (200, 299))
        assert 201 in domain
        assert domain.is_valid(250)
        ```
    """

    # Class-level registry for predefined domains
    _domains: Dict[str, "ErrorDomain"] = {}

    def __init__(self, name: str, code_range: Tuple[int, int]) -> None:
        """
        Initialize an ErrorDomain.

        Args:
            name: The domain name
            code_range: Tuple of (start_code, end_code)

        Raises:
            ValueError: If code_range is invalid (start > end)
        """
        if code_range[0] > code_range[1]:
            raise ValueError(f"Invalid code range: {code_range}. Start must be <= end.")

        self.name = name
        self._code_range = code_range

    @property
    def code_range(self) -> Tuple[int, int]:
        """Get the code range tuple."""
        return self._code_range

    def __contains__(self, code: int) -> bool:
        """
        Check if a code is within this domain's range.

        Args:
            code: The error code to check

        Returns:
            True if the code is within the domain range, False otherwise
        """
        return self._code_range[0] <= code <= self._code_range[1]

    def is_valid(self, code: int) -> bool:
        """
        Check if a code is valid for this domain.

        Args:
            code: The error code to validate

        Returns:
            True if the code is within the domain range, False otherwise
        """
        return code in self

    @classmethod
    def register_domain(cls, name: str, code_range: Tuple[int, int]) -> "ErrorDomain":
        """
        Register a new error domain.

        Args:
            name: The domain name
            code_range: Tuple of (start_code, end_code)

        Raises:
            ValueError: If domain already exists or code_range is invalid

        Returns:
            The newly created ErrorDomain instance
        """
        if name in cls._domains:
            raise ValueError(f"Domain '{name}' is already registered.")

        if code_range[0] > code_range[1]:
            raise ValueError(f"Invalid code range: {code_range}. Start must be <= end.")

        domain = cls(name, code_range)
        cls._domains[name] = domain
        return domain

    @classmethod
    def get_domain(cls, name: str) -> Optional["ErrorDomain"]:
        """
        Get a registered domain by name.

        Args:
            name: The domain name to retrieve

        Returns:
            The ErrorDomain if found, None otherwise
        """
        return cls._domains.get(name)

    @classmethod
    def is_valid_code(cls, code: int, domain_name: str) -> bool:
        """
        Check if a code is valid for a specific domain.

        Args:
            code: The error code to validate
            domain_name: The domain name to check against

        Returns:
            True if the code is within the domain range, False otherwise
        """
        domain = cls.get_domain(domain_name)
        if domain is None:
            return False
        return code in domain

    @classmethod
    def get_domain_for_code(cls, code: int) -> Optional["ErrorDomain"]:
        """
        Find the domain that contains a given code.

        Args:
            code: The error code to look up

        Returns:
            The ErrorDomain containing the code, or None if not found
        """
        for domain in cls._domains.values():
            if code in domain:
                return domain
        return None

    @classmethod
    def list_domains(cls) -> List[str]:
        """
        List all registered domain names.

        Returns:
            List of domain names
        """
        return list(cls._domains.keys())


# Initialize predefined domains
def _initialize_predefined_domains() -> None:
    """Initialize all predefined error domains."""
    ErrorDomain.register_domain("AUTH", (200, 299))
    ErrorDomain.register_domain("RESOURCE", (300, 399))
    ErrorDomain.register_domain("VALIDATION", (400, 499))
    ErrorDomain.register_domain("SERVER", (500, 599))
    ErrorDomain.register_domain("CUSTOM", (900, 999))


# Auto-initialize predefined domains on module import
_initialize_predefined_domains()
