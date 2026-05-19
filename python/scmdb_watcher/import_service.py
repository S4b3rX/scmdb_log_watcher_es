"""Batch import helpers for historical Star Citizen logs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from scmdb_watcher.config import IMPORTS_DIR_NAME, resolve_runtime_dir

from scmdb_watcher.domain import (
    PATTERN_ACCEPTED,
    PATTERN_BLUEPRINT,
    PATTERN_END_MISSION,
    PATTERN_MARKER,
    WatcherState,
    parse_log_timestamp,
)


def scan_file_for_export(path: Path, logger: logging.Logger) -> tuple[list[dict], list[dict]]:
    """Scan one log file and return (missions, blueprints)."""
    state = WatcherState()
    missions: list[dict] = []
    blueprints: list[dict] = []

    try:
        f = open(path, "rb")
    except OSError as error:
        logger.warning("Skipping %s: %s", path.name, error)
        return missions, blueprints

    with f:
        for raw in f:
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                continue
            ts = parse_log_timestamp(line) or 0.0

            if m := PATTERN_MARKER.search(line):
                state.record_marker(m.group(1), m.group(2), m.group(3))
            elif m := PATTERN_ACCEPTED.search(line):
                state.record_accepted(m.group(1), ts)
            elif m := PATTERN_END_MISSION.search(line):
                guid, completion, reason = m.group(1), m.group(2), m.group(3)
                active = state.record_end(guid, completion, ts)
                if completion == "Complete" and active is not None:
                    missions.append(
                        {
                            "guid": guid,
                            "debugName": active.debug_name,
                            "generator": active.generator,
                            "startTs": active.start_ts,
                            "endTs": ts,
                            "durationSec": round(ts - active.start_ts, 3),
                            "reason": reason,
                        }
                    )
            elif m := PATTERN_BLUEPRINT.search(line):
                product_name = m.group(1).strip()
                corr = state.correlate_blueprint(ts)
                if corr is not None:
                    blueprints.append(
                        {
                            "productName": product_name,
                            "ts": ts,
                            "missionGuid": corr.guid,
                            "missionDebugName": corr.debug_name,
                            "missionTrigger": corr.trigger,
                        }
                    )

    return missions, blueprints


def collect_log_files(logbackups_dir: Path, log_path: Path, include_current: bool) -> list[Path]:
    files = sorted(logbackups_dir.glob("Game Build(*).log"))
    if include_current and log_path.is_file():
        files.append(log_path)
    return files


def dedupe_missions_by_guid(missions: list[dict]) -> tuple[list[dict], int]:
    seen_guids: set[str] = set()
    deduped: list[dict] = []
    for mission in missions:
        guid = mission.get("guid")
        if isinstance(guid, str) and guid in seen_guids:
            continue
        if isinstance(guid, str):
            seen_guids.add(guid)
        deduped.append(mission)
    dropped = len(missions) - len(deduped)
    return deduped, dropped


def resolve_output_path(output_arg: Path | None, anchor_file: str | Path, runtime_dir_name: str = "runtime") -> Path:
    if output_arg:
        output_arg.parent.mkdir(parents=True, exist_ok=True)
        return output_arg

    runtime_dir = resolve_runtime_dir(anchor_file)
    out_dir = runtime_dir / IMPORTS_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"scmdb-import-{datetime.now():%Y-%m-%d_%H-%M-%S}.json"


def build_export_payload(
    watcher_version: str,
    source_logs: list[str],
    missions: list[dict],
    blueprints: list[dict],
) -> dict:
    return {
        "exportSchemaVersion": 1,
        "watcherVersion": watcher_version,
        "exportedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sourceLogs": source_logs,
        "missions": missions,
        "blueprints": blueprints,
    }


def write_payload(output_path: Path, payload: dict) -> None:
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
