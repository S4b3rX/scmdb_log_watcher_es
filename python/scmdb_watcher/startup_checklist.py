"""Startup checklist for packaged/source GUI execution."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from scmdb_watcher.config import IMPORTS_DIR_NAME
from scmdb_watcher.paths import resolve_log_path_from_config
from scmdb_watcher.process_service import resolve_watcher_launch_command


@dataclass(frozen=True)
class StartupChecklistResult:
    ok: bool
    details: list[str]


def _check_runtime_dirs(runtime_dir: Path) -> list[str]:
    details: list[str] = []
    (runtime_dir / "logs").mkdir(parents=True, exist_ok=True)
    (runtime_dir / IMPORTS_DIR_NAME).mkdir(parents=True, exist_ok=True)
    details.append("runtime dirs: ok")
    return details


def _check_launcher(script_dir: Path, frozen: bool) -> list[str]:
    details: list[str] = []
    cmd, err = resolve_watcher_launch_command(script_dir, frozen)
    if cmd:
        details.append("watcher runtime: ok")
    else:
        details.append(f"watcher runtime: missing ({err or 'unknown'})")
    return details


def _check_log_path(config_data: dict) -> list[str]:
    details: list[str] = []
    log_path = resolve_log_path_from_config(config_data)
    if log_path is None:
        details.append("log path: missing")
        return details
    if log_path.exists():
        details.append("log path: found")
    else:
        details.append(f"log path: {log_path}")
    return details


def _run_unittest_suite(script_dir: Path) -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    result = subprocess.run(cmd, cwd=str(script_dir), capture_output=True, text=True, timeout=120)
    return result.returncode == 0, (result.stdout or result.stderr or "").strip()


def run_startup_checklist(
    *,
    runtime_dir: Path,
    script_dir: Path,
    config_data: dict,
    frozen: bool,
    run_tests: bool,
) -> StartupChecklistResult:
    details: list[str] = []
    details.extend(_check_runtime_dirs(runtime_dir))
    details.extend(_check_launcher(script_dir, frozen))
    details.extend(_check_log_path(config_data))

    tests_ok = True
    if run_tests and not frozen:
        ok, _out = _run_unittest_suite(script_dir)
        tests_ok = ok
        details.append("startup tests: ok" if ok else "startup tests: failed")
    elif run_tests and frozen:
        details.append("startup tests: skipped (frozen)")
    else:
        details.append("startup tests: disabled")

    has_missing_runtime = any(line.startswith("watcher runtime: missing") for line in details)
    ok = (not has_missing_runtime) and tests_ok
    return StartupChecklistResult(ok=ok, details=details)
