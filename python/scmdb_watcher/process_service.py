"""Process/runtime helpers for watcher GUI orchestration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def resolve_watcher_launch_command(script_dir: Path, frozen: bool) -> tuple[list[str] | None, str | None]:
    if frozen:
        watcher_exe = script_dir / "SCMDB-Watcher.exe"
        if watcher_exe.exists():
            return [str(watcher_exe), "core"], None
        return None, "missing_core"

    python_exe = script_dir / ".venv" / "Scripts" / "pythonw.exe"
    if not python_exe.exists():
        python_exe = script_dir / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        return None, "missing_env"
    return [str(python_exe), "launcher.py", "core"], None


def resolve_import_command(script_dir: Path, frozen: bool) -> tuple[list[str] | None, str | None]:
    if frozen:
        watcher_exe = script_dir / "SCMDB-Watcher.exe"
        if watcher_exe.exists():
            return [str(watcher_exe), "import"], None
        return None, "missing_core"

    python_exe = script_dir / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        return None, "missing_env"
    return [str(python_exe), "launcher.py", "import"], None


def force_cleanup_orphan_watchers() -> None:
    ps_cmd = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { "
        "( $_.Name -match '^pythonw?\\.exe$' -and ($_.CommandLine -match 'launcher\\.py(\\s|$)' -or $_.CommandLine -match 'watcher\\.py(\\s|$)') ) -or "
        "( $_.Name -eq 'SCMDB-Watcher.exe' -and $_.CommandLine -match '\\s(core|import)(\\s|$)' ) "
        "} | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-Command",
            ps_cmd,
        ],
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def ping_ok(port: int) -> tuple[bool, str]:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/ping", timeout=1.2) as res:
            data = json.loads(res.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False, ""
    return data.get("status") == "ok", str(data.get("version", ""))


def is_game_running() -> bool:
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq StarCitizen.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    out = (result.stdout or "").strip().lower()
    return "starcitizen.exe" in out and "no tasks are running" not in out
