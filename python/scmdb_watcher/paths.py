"""Path discovery and defaults for Star Citizen Game.log."""

from __future__ import annotations

import os
import string
from pathlib import Path
from typing import Mapping, Optional, Sequence

from scmdb_watcher.config import load_config

DEFAULT_LOG_PATH_FALLBACK = Path(
    r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\Game.log"
)
TRACKED_CHANNEL = "LIVE"
PREFERRED_STAR_CITIZEN_ROOTS = (
    Path(r"D:\RSI\StarCitizen"),
)
STAR_CITIZEN_CHANNELS = ("LIVE", "HOTFIX")


def load_user_config(anchor_file: str | Path) -> dict:
    return load_config(anchor_file)


def resolve_log_path_from_config(config: dict) -> Optional[Path]:
    raw_game_install_dir = config.get("game_install_dir")
    install_dir = Path(raw_game_install_dir.strip()) if isinstance(raw_game_install_dir, str) and raw_game_install_dir.strip() else None

    if install_dir is not None:
        if install_dir.name.upper() == TRACKED_CHANNEL:
            return install_dir / "Game.log"
        if install_dir.name.upper() in STAR_CITIZEN_CHANNELS:
            return install_dir.parent / TRACKED_CHANNEL / "Game.log"
        return install_dir / TRACKED_CHANNEL / "Game.log"

    raw_log_path = config.get("log_path")
    if isinstance(raw_log_path, str) and raw_log_path.strip():
        return Path(raw_log_path.strip())

    return None


def _unique_paths(paths: Sequence[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def resolve_default_log_path(
    anchor_file: str | Path,
    *,
    env: Mapping[str, str] | None = None,
    scan_all_drives: bool = True,
    preferred_roots: Sequence[Path] = PREFERRED_STAR_CITIZEN_ROOTS,
) -> Path:
    effective_env = env if env is not None else os.environ

    env_value = effective_env.get("SCMDB_WATCHER_LOG_PATH")
    if env_value:
        return Path(env_value)

    configured = resolve_log_path_from_config(load_user_config(anchor_file))
    if configured is not None:
        return configured

    base_dirs: list[Path] = list(preferred_roots)

    for env_key in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
        env_dir = effective_env.get(env_key)
        if env_dir:
            base_dirs.append(Path(env_dir) / "Roberts Space Industries" / "StarCitizen")

    if scan_all_drives:
        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:\\")
            if not drive.exists():
                continue
            base_dirs.extend(
                [
                    drive / "Roberts Space Industries" / "StarCitizen",
                    drive / "Program Files" / "Roberts Space Industries" / "StarCitizen",
                    drive / "Program Files (x86)" / "Roberts Space Industries" / "StarCitizen",
                ]
            )

    first_existing_channel_dir: Optional[Path] = None
    for base in _unique_paths(base_dirs):
        for channel in STAR_CITIZEN_CHANNELS:
            candidate = base / channel / "Game.log"
            if candidate.is_file():
                return candidate
            if first_existing_channel_dir is None and candidate.parent.is_dir():
                first_existing_channel_dir = candidate

    if first_existing_channel_dir is not None:
        return first_existing_channel_dir

    return DEFAULT_LOG_PATH_FALLBACK
