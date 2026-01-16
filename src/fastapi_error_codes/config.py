"""
Configuration management for fastapi-error-codes package.

This module provides the ErrorHandlerConfig class for managing
error handler configuration with development and production presets.
"""

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ErrorHandlerConfig:
    """
    Configuration for error handler behavior.

    This dataclass defines configuration options for the error handler
    including locale settings, debug mode, and traceback inclusion.

    Attributes:
        default_locale: Default locale code for messages (default: "en")
        fallback_locales: Ordered list of fallback locales to try before default
        debug_mode: Enable debug mode for detailed error messages (default: False)
        include_traceback: Include stack trace in error responses (default: False)
        locale_dir: Directory containing locale JSON files (default: "locales")
        _validate: Whether to validate locale directory exists (default: False, internal use)

    Example:
        ```python
        config = ErrorHandlerConfig(
            default_locale="ko",
            debug_mode=True,
            include_traceback=True
        )
        ```
    """

    default_locale: str = "en"
    fallback_locales: List[str] = field(default_factory=list)
    debug_mode: bool = False
    include_traceback: bool = False
    locale_dir: str = "locales"
    _validate: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate locale directory if validation is enabled
        if self._validate:
            locale_path = Path(self.locale_dir)
            if not locale_path.exists() or not locale_path.is_dir():
                raise ValueError(f"Locale directory does not exist: {self.locale_dir}")

    @classmethod
    def development(
        cls,
        default_locale: str = "en",
        fallback_locales: Optional[List[str]] = None,
        locale_dir: str = "locales"
    ) -> "ErrorHandlerConfig":
        """
        Create configuration for development environment.

        Development preset enables debug mode and traceback inclusion
        for easier debugging during development.

        Args:
            default_locale: Default locale code (default: "en")
            fallback_locales: Optional list of fallback locales
            locale_dir: Directory containing locale files (default: "locales")

        Returns:
            ErrorHandlerConfig instance with development settings

        Example:
            ```python
            config = ErrorHandlerConfig.development()
            # debug_mode=True, include_traceback=True
            ```
        """
        return cls(
            default_locale=default_locale,
            fallback_locales=fallback_locales or [],
            debug_mode=True,
            include_traceback=True,
            locale_dir=locale_dir
        )

    @classmethod
    def production(
        cls,
        default_locale: str = "en",
        fallback_locales: Optional[List[str]] = None,
        locale_dir: str = "locales"
    ) -> "ErrorHandlerConfig":
        """
        Create configuration for production environment.

        Production preset disables debug mode and traceback inclusion
        for security and cleaner error responses in production.

        Args:
            default_locale: Default locale code (default: "en")
            fallback_locales: Optional list of fallback locales
            locale_dir: Directory containing locale files (default: "locales")

        Returns:
            ErrorHandlerConfig instance with production settings

        Example:
            ```python
            config = ErrorHandlerConfig.production()
            # debug_mode=False, include_traceback=False
            ```
        """
        return cls(
            default_locale=default_locale,
            fallback_locales=fallback_locales or [],
            debug_mode=False,
            include_traceback=False,
            locale_dir=locale_dir
        )

    def copy(self) -> "ErrorHandlerConfig":
        """
        Create a copy of this configuration.

        Since the dataclass is frozen, this returns the same instance.
        Use update() to create modified copies.

        Returns:
            Copy of the configuration (same instance due to frozen dataclass)
        """
        return self

    def update(self, **kwargs: Any) -> "ErrorHandlerConfig":
        """
        Create a new configuration with updated values.

        Args:
            **kwargs: Field names and new values

        Returns:
            New ErrorHandlerConfig instance with updated values

        Example:
            ```python
            original = ErrorHandlerConfig(default_locale="en")
            updated = original.update(default_locale="ko", debug_mode=True)
            ```
        """
        return replace(self, **kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration

        Example:
            ```python
            config = ErrorHandlerConfig(default_locale="ko")
            data = config.to_dict()
            # {'default_locale': 'ko', 'fallback_locales': [], ...}
            ```
        """
        return {
            "default_locale": self.default_locale,
            "fallback_locales": self.fallback_locales,
            "debug_mode": self.debug_mode,
            "include_traceback": self.include_traceback,
            "locale_dir": self.locale_dir
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorHandlerConfig":
        """
        Create configuration from dictionary.

        Args:
            data: Dictionary containing configuration values

        Returns:
            New ErrorHandlerConfig instance

        Example:
            ```python
            data = {"default_locale": "ko", "debug_mode": True}
            config = ErrorHandlerConfig.from_dict(data)
            ```
        """
        return cls(
            default_locale=data.get("default_locale", "en"),
            fallback_locales=data.get("fallback_locales", []),
            debug_mode=data.get("debug_mode", False),
            include_traceback=data.get("include_traceback", False),
            locale_dir=data.get("locale_dir", "locales")
        )

    @classmethod
    def from_environment(cls) -> "ErrorHandlerConfig":
        """
        Create configuration from environment variables.

        Environment variables:
        - ERROR_LOCALE: Default locale (default: "en")
        - ERROR_DEBUG: Debug mode "true"/"false" (default: "false")
        - ERROR_TRACEBACK: Include traceback "true"/"false" (default: "false")
        - ERROR_LOCALE_DIR: Locale directory (default: "locales")
        - ERROR_FALLBACK_LOCALES: Comma-separated fallback locales

        Returns:
            New ErrorHandlerConfig instance from environment

        Example:
            ```python
            # Set environment variables
            os.environ["ERROR_LOCALE"] = "ko"
            os.environ["ERROR_DEBUG"] = "true"

            config = ErrorHandlerConfig.from_environment()
            ```
        """
        def parse_bool(value: Optional[str]) -> bool:
            """Parse boolean from string."""
            if not value:
                return False
            return value.lower() in ("true", "1", "yes", "on")

        def parse_list(value: Optional[str]) -> List[str]:
            """Parse comma-separated list from string."""
            if not value:
                return []
            return [item.strip() for item in value.split(",") if item.strip()]

        return cls(
            default_locale=os.environ.get("ERROR_LOCALE", "en"),
            fallback_locales=parse_list(os.environ.get("ERROR_FALLBACK_LOCALES")),
            debug_mode=parse_bool(os.environ.get("ERROR_DEBUG")),
            include_traceback=parse_bool(os.environ.get("ERROR_TRACEBACK")),
            locale_dir=os.environ.get("ERROR_LOCALE_DIR", "locales")
        )
