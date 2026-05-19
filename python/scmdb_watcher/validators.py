"""Shared config validation/normalization helpers."""

from __future__ import annotations

import re
from pathlib import Path


VALID_CHANNELS = ("LIVE", "HOTFIX")
LANGUAGE_OPTIONS = (
    "de-de",
    "en-en",
    "es-es",
    "fr-fr",
    "it-it",
    "ja-jp",
    "pt-pt",
    "ru-ru",
    "zh-cn",
)

LANGUAGE_ALIASES = {
    "de": "de-de",
    "de-de": "de-de",
    "en": "en-en",
    "en-en": "en-en",
    "es": "es-es",
    "es-es": "es-es",
    "fr": "fr-fr",
    "fr-fr": "fr-fr",
    "it": "it-it",
    "it-it": "it-it",
    "ja": "ja-jp",
    "ja-jp": "ja-jp",
    "pt": "pt-pt",
    "pt-pt": "pt-pt",
    "ru": "ru-ru",
    "ru-ru": "ru-ru",
    "zh": "zh-cn",
    "zh-cn": "zh-cn",
    "zh-hans": "zh-cn",
}

LANGUAGE_CODE_PATTERN = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,4})+$")


def normalize_channel(value: str, default: str = "LIVE") -> str:
    channel = value.strip().upper() or default
    return channel if channel in VALID_CHANNELS else default


def normalize_language(value: str, default: str = "es-es") -> str:
    fallback = LANGUAGE_ALIASES.get(default.strip().lower().replace("_", "-"), "es-es")
    language = value.strip().lower().replace("_", "-") or fallback
    if language in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[language]
    return language if LANGUAGE_CODE_PATTERN.match(language) else fallback


def validate_game_install_dir(game_dir: str) -> tuple[bool, str]:
    clean = game_dir.strip()
    if not clean:
        return False, "missing"
    return True, clean


def build_log_path(game_dir: str, channel: str) -> str:
    base_dir = Path(game_dir)
    if base_dir.name.upper() in VALID_CHANNELS:
        return str(base_dir / "Game.log")
    return str(base_dir / channel / "Game.log")
