"""Runtime/config path helpers shared across watcher and GUI tools."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CONFIG_FILE_NAME = "watcher-config.json"
RUNTIME_DIR_NAME = "runtime"
IMPORTS_DIR_NAME = "scmdb-import"
APP_DATA_DIR_NAME = "SCMDB Log Watcher"


def resolve_base_dir(anchor_file: str | Path) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(anchor_file).resolve().parent


def resolve_data_dir(anchor_file: str | Path) -> Path:
    if getattr(sys, "frozen", False):
        local_appdata = os.environ.get("LOCALAPPDATA", "").strip()
        if local_appdata:
            data_dir = Path(local_appdata) / APP_DATA_DIR_NAME
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir
    return resolve_base_dir(anchor_file)


def resolve_runtime_dir(anchor_file: str | Path) -> Path:
    runtime_dir = resolve_data_dir(anchor_file) / RUNTIME_DIR_NAME
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def resolve_config_path(anchor_file: str | Path) -> Path:
    return resolve_runtime_dir(anchor_file) / CONFIG_FILE_NAME


def load_config(anchor_file: str | Path) -> dict:
    config_path = resolve_config_path(anchor_file)
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_config(anchor_file: str | Path, payload: dict) -> None:
    config_path = resolve_config_path(anchor_file)
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
