"""I18N catalog and translation helper for Watcher GUI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from scmdb_watcher.config import resolve_base_dir
from scmdb_watcher.validators import normalize_language

DEFAULT_LANGUAGE = "es-es"
DEFAULT_STRINGS = {
    "window_title": "SCMDB Log Watcher",
    "btn_start": "Iniciar",
    "btn_stop": "Desconectar",
}


def _language_dirs(anchor_file: str | Path | None = None) -> list[Path]:
    base_dir = resolve_base_dir(anchor_file or __file__)
    candidates: list[Path] = []
    seen: set[Path] = set()
    for parent in (base_dir, *base_dir.parents):
        lang_dir = parent / "lang"
        if lang_dir in seen:
            continue
        seen.add(lang_dir)
        if lang_dir.is_dir():
            candidates.append(lang_dir)
    return candidates


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[dict[str, dict], dict[str, str]]:
    catalog: dict[str, dict] = {}
    aliases: dict[str, str] = {}

    for lang_dir in reversed(_language_dirs()):
        for file_path in sorted(lang_dir.glob("*.json")):
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            code = normalize_language(str(payload.get("code", file_path.stem)))
            strings = payload.get("strings", {})
            if not isinstance(strings, dict):
                strings = {}
            catalog[code] = {
                "code": code,
                "display_name": str(payload.get("display_name", code)),
                "native_name": str(payload.get("native_name", code)),
                "strings": {str(key): str(value) for key, value in strings.items()},
            }
            aliases[code] = code
            for alias in payload.get("aliases", []):
                aliases[str(alias).strip().lower().replace("_", "-")] = code

    aliases.setdefault(DEFAULT_LANGUAGE, DEFAULT_LANGUAGE)
    return catalog, aliases


def get_available_language_codes(anchor_file: str | Path | None = None) -> tuple[str, ...]:
    if anchor_file is None:
        catalog, _aliases = _load_catalog()
        if catalog:
            return tuple(sorted(catalog))
        return (DEFAULT_LANGUAGE,)

    codes: list[str] = []
    seen: set[str] = set()
    for lang_dir in _language_dirs(anchor_file):
        for file_path in sorted(lang_dir.glob("*.json")):
            code = normalize_language(file_path.stem)
            if code in seen:
                continue
            seen.add(code)
            codes.append(code)
    return tuple(codes) or (DEFAULT_LANGUAGE,)


def tr(language: str, key: str, **kwargs) -> str:
    catalog, aliases = _load_catalog()
    normalized_language = normalize_language(aliases.get(language.strip().lower().replace("_", "-"), language))
    selected = catalog.get(normalized_language)
    fallback = catalog.get(DEFAULT_LANGUAGE, {"strings": DEFAULT_STRINGS})
    template = (
        (selected or {}).get("strings", {}).get(key)
        or fallback.get("strings", {}).get(key)
        or DEFAULT_STRINGS.get(key)
        or key
    )
    return template.format(**kwargs)
