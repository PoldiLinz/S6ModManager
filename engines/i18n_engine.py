"""
Siedler 6 Mod Manager - Internationalization (i18n) Engine
Centralized multi-language dictionary and translation manager.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple


class I18nEngine:
    """Manages translation dictionaries and text resolution."""

    _instance: Optional['I18nEngine'] = None

    SUPPORTED_LANGUAGES: List[Tuple[str, str]] = [
        ("en", "English"),
        ("de", "Deutsch")
    ]

    def __init__(self, language: str = "en", locales_dir: Optional[str] = None):
        self.language = language
        if locales_dir:
            self.locales_dir = locales_dir
        else:
            self.locales_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "locales")
            )
        self.translations: Dict[str, Any] = {}
        self.load_translations()
        I18nEngine._instance = self

    @classmethod
    def get_instance(cls, default_lang: str = "en") -> 'I18nEngine':
        if cls._instance is None:
            cls._instance = I18nEngine(language=default_lang)
        return cls._instance

    def load_translations(self):
        """Loads translations from dictionary.json."""
        dict_file = os.path.join(self.locales_dir, "dictionary.json")
        if os.path.exists(dict_file):
            try:
                with open(dict_file, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
            except Exception as e:
                print(f"[I18nEngine] Error loading dictionary: {e}")
                self.translations = {}
        else:
            print(f"[I18nEngine] Warning: Dictionary file not found at {dict_file}")
            self.translations = {}

    def set_language(self, language: str):
        """Sets the current language code (e.g. 'en', 'de')."""
        if language in self.translations or any(lang[0] == language for lang in self.SUPPORTED_LANGUAGES):
            self.language = language

    def get_language(self) -> str:
        """Returns the active language code."""
        return self.language

    def translate(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """
        Translates a key using dot notation (e.g. 'app.title').
        Falls back to English if key is missing in active language.
        Supports keyword formatting: tr('msg', count=5) -> 'Found {count}' -> 'Found 5'.
        """
        # 1. Look up in active language
        val = self._resolve_nested(self.translations.get(self.language, {}), key)

        # 2. Fallback to English
        if val is None and self.language != "en":
            val = self._resolve_nested(self.translations.get("en", {}), key)

        # 3. Fallback to provided default or key itself
        if val is None:
            val = default if default is not None else key

        if kwargs and isinstance(val, str):
            try:
                return val.format(**kwargs)
            except Exception:
                return val
        return str(val)

    def _resolve_nested(self, data: Dict[str, Any], key: str) -> Optional[Any]:
        cur = data
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur


def tr(key: str, default: Optional[str] = None, **kwargs) -> str:
    """Convenience shortcut to translate a key."""
    return I18nEngine.get_instance().translate(key, default, **kwargs)


# Alias t for fast typing
t = tr
