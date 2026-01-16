"""
Internationalization (i18n) support for fastapi-error-codes package.

This module provides the MessageProvider class for loading and managing
localized error messages with fallback chain support.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class MessageProvider:
    """
    Provider for localized error messages with fallback chain support.

    This class loads locale files from a directory and provides methods
    to retrieve messages using dot notation for nested keys. It supports
    a fallback chain: requested locale -> fallback locales -> default locale.

    Attributes:
        locale_dir: Directory containing locale JSON files
        default_locale: The default locale to use as fallback
        fallback_locales: Ordered list of locales to try before default

    Example:
        ```python
        provider = MessageProvider(
            locale_dir="locales",
            default_locale="en",
            fallback_locales=["ko"]
        )
        message = provider.get_message("errors.auth.required", locale="ko")
        ```
    """

    def __init__(
        self,
        locale_dir: str,
        default_locale: str = "en",
        fallback_locales: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize MessageProvider.

        Args:
            locale_dir: Directory containing locale JSON files (e.g., en.json, ko.json)
            default_locale: Default locale code (default: "en")
            fallback_locales: Ordered list of fallback locales to try before default

        Raises:
            ValueError: If locale_dir doesn't exist or default_locale file not found
        """
        locale_path = Path(locale_dir)
        if not locale_path.exists() or not locale_path.is_dir():
            raise ValueError(f"Locale directory does not exist: {locale_dir}")

        self._locale_dir = locale_path
        self._default_locale = default_locale
        self._fallback_locales = fallback_locales or []

        # Verify default locale file exists
        default_file = self._locale_dir / f"{default_locale}.json"
        if not default_file.exists():
            raise ValueError(f"Default locale file not found: {default_file}")

        # Cache for loaded locale messages
        self._cache: Dict[str, Dict[str, Any]] = {}

        # Load default locale into cache
        self._load_locale(default_locale)

    @property
    def locale_dir(self) -> str:
        """Get the locale directory path."""
        return str(self._locale_dir)

    @property
    def default_locale(self) -> str:
        """Get the default locale code."""
        return self._default_locale

    def _load_locale(self, locale: str) -> Dict[str, Any]:
        """
        Load locale file from disk.

        Args:
            locale: Locale code to load

        Returns:
            Dictionary containing locale messages

        Raises:
            FileNotFoundError: If locale file doesn't exist
        """
        locale_file = self._locale_dir / f"{locale}.json"

        if not locale_file.exists():
            raise FileNotFoundError(f"Locale file not found: {locale_file}")

        with open(locale_file, "r", encoding="utf-8") as f:
            messages = json.load(f)

        # Cache the loaded messages
        self._cache[locale] = messages
        logger.debug(f"Loaded locale: {locale} from {locale_file}")

        return messages

    def _get_cached_locale(self, locale: str) -> Optional[Dict[str, Any]]:
        """
        Get locale messages from cache, loading if necessary.

        Args:
            locale: Locale code to retrieve

        Returns:
            Dictionary of messages or None if locale doesn't exist
        """
        if locale not in self._cache:
            try:
                self._load_locale(locale)
            except FileNotFoundError:
                logger.warning(f"Locale file not found: {locale}")
                return None

        return self._cache.get(locale)

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """
        Get value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            key: Dot-separated key path (e.g., "errors.auth.required")

        Returns:
            Value at the key path, or key itself if not found
        """
        if not key:
            return key

        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                # Key not found, return original key
                return key

        return current

    def _format_message_partial(self, message: str, **kwargs: Any) -> str:
        """
        Format message with partial parameter support.

        This method formats only the parameters that are provided,
        leaving missing placeholders intact.

        Args:
            message: Message template with {placeholders}
            **kwargs: Parameters for formatting

        Returns:
            Formatted message with available parameters replaced

        Example:
            ```python
            _format_message_partial("User {user_id} not found in {resource}", user_id=123)
            # Returns: "User 123 not found in {resource}"
            ```
        """
        if not kwargs:
            return message

        result = message
        for key, value in kwargs.items():
            # Use regex to replace only the specific placeholder
            pattern = r'\{' + re.escape(key) + r'\}'
            result = re.sub(pattern, str(value), result)

        return result

    def get_message(
        self,
        key: str,
        locale: Optional[str] = None,
        default: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Get localized message for a given key.

        Fallback chain:
        1. Requested locale
        2. Fallback locales (in order)
        3. Default locale
        4. Original key (if not found anywhere)

        Args:
            key: Message key (supports dot notation for nested keys)
            locale: Requested locale code (uses default if None)
            default: Custom default message if key not found
            **kwargs: Parameters for string formatting

        Returns:
            Localized message string

        Example:
            ```python
            # Get message in Korean
            msg = provider.get_message("errors.auth.required", locale="ko")

            # Get message with parameters
            msg = provider.get_message(
                "errors.user_not_found",
                locale="en",
                user_id=123
            )
            # Returns: "User 123 not found"
            ```
        """
        if locale is None:
            locale = self._default_locale

        # Build fallback chain
        locales_to_try: List[str] = []
        if locale != self._default_locale:
            locales_to_try.append(locale)
        locales_to_try.extend(self._fallback_locales)
        if self._default_locale not in locales_to_try:
            locales_to_try.append(self._default_locale)

        # Try each locale in the fallback chain
        for current_locale in locales_to_try:
            messages = self._get_cached_locale(current_locale)
            if messages is None:
                continue

            value = self._get_nested_value(messages, key)

            # If value is different from key, we found the message
            if value != key:
                message = str(value)

                # Apply formatting if kwargs provided
                if kwargs:
                    message = self._format_message_partial(message, **kwargs)

                return message

        # If custom default provided, use it
        if default is not None:
            return default

        # Return original key as last resort
        return key

    def reload_locale(self, locale: str) -> None:
        """
        Reload a locale from disk, updating the cache.

        This is useful for testing or when locale files are updated
        at runtime.

        Args:
            locale: Locale code to reload

        Raises:
            FileNotFoundError: If locale file doesn't exist
        """
        # Remove from cache if exists
        self._cache.pop(locale, None)

        # Reload from disk
        self._load_locale(locale)

        logger.info(f"Reloaded locale: {locale}")

    def clear_cache(self) -> None:
        """
        Clear all cached locale data.

        This forces all locales to be reloaded from disk on next access.
        """
        self._cache.clear()
        logger.debug("Cleared locale cache")

    def get_available_locales(self) -> List[str]:
        """
        Get list of available locale files.

        Returns:
            List of locale codes (e.g., ["en", "ko", "ja"])
        """
        locales = []
        for file in self._locale_dir.glob("*.json"):
            locales.append(file.stem)

        return sorted(locales)
