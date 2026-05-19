"""Settings workflow helpers for Watcher GUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scmdb_watcher.validators import build_log_path, normalize_channel, normalize_language, validate_game_install_dir


TRACKED_CHANNEL = "LIVE"


@dataclass(frozen=True)
class SettingsDefaults:
    game_dir: str
    channel: str
    language: str
    auto_start: bool
    run_startup_tests: bool


@dataclass(frozen=True)
class SettingsSaveResult:
    ok: bool
    error_key: str
    game_dir: str
    channel: str
    language: str
    auto_start: bool
    run_startup_tests: bool
    log_path: str


def build_settings_defaults(config_data: dict, current_language: str, auto_start: bool) -> SettingsDefaults:
    return SettingsDefaults(
        game_dir=str(config_data.get("game_install_dir", "")),
        channel=TRACKED_CHANNEL,
        language=normalize_language(current_language),
        auto_start=bool(auto_start),
        run_startup_tests=bool(config_data.get("run_startup_tests", False)),
    )


def build_settings_save_result(
    *,
    game_dir_raw: str,
    channel_raw: str,
    language_raw: str,
    auto_start: bool,
    run_startup_tests: bool,
) -> SettingsSaveResult:
    valid, game_dir_or_reason = validate_game_install_dir(game_dir_raw)
    if not valid:
        return SettingsSaveResult(
            ok=False,
            error_key="missing_cfg",
            game_dir="",
            channel="",
            language="",
            auto_start=False,
            run_startup_tests=False,
            log_path="",
        )

    game_dir = game_dir_or_reason
    channel = TRACKED_CHANNEL
    language = normalize_language(language_raw)
    game_dir_path = Path(game_dir)
    if game_dir_path.name.upper() == "HOTFIX":
        game_dir = str(game_dir_path.parent)
    return SettingsSaveResult(
        ok=True,
        error_key="",
        game_dir=game_dir,
        channel=channel,
        language=language,
        auto_start=bool(auto_start),
        run_startup_tests=bool(run_startup_tests),
        log_path=build_log_path(game_dir, channel),
    )
