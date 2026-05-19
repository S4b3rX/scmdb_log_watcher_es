"""Controller helpers to keep WatcherGui focused on presentation."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from scmdb_watcher.process_service import ping_ok, resolve_watcher_launch_command


@dataclass(frozen=True)
class ImportExecutionResult:
    ok: bool
    output_path: str
    error_text: str


def resolve_start_command(
    script_dir: Path,
    config_data: dict,
    *,
    default_port: int,
    frozen: bool,
    log_path: str,
    parent_pid: int | None = None,
) -> tuple[list[str] | None, str | None, int | None]:
    base_cmd, error = resolve_watcher_launch_command(script_dir, frozen)
    if not base_cmd:
        return None, error, None

    requested_port = int(config_data.get("port", default_port))

    cmd = [
        *base_cmd,
        "--log-path",
        log_path,
        "--port",
        str(requested_port),
    ]
    if parent_pid is not None and parent_pid > 0:
        cmd.extend(["--parent-pid", str(parent_pid)])
    return cmd, None, requested_port


def launch_watcher_process(cmd: list[str], script_dir: Path) -> subprocess.Popen:
    return subprocess.Popen(
        cmd,
        cwd=str(script_dir),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def terminate_watcher_process(proc: subprocess.Popen, timeout: float = 3.0) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()


def check_watcher_health(config_data: dict, default_port: int) -> tuple[bool, str]:
    port = int(config_data.get("port", default_port))
    return ping_ok(port)


def extract_output_path(stdout_text: str) -> str:
    output_lines = [ln.strip() for ln in stdout_text.splitlines() if ln.strip()]
    for idx, line in enumerate(output_lines):
        if line.lower().startswith("output written to") and idx + 1 < len(output_lines):
            return output_lines[idx + 1]
    return ""


def run_import_process(
    base_cmd: list[str],
    script_dir: Path,
    log_path: str,
    *,
    output_path: Path | None = None,
) -> ImportExecutionResult:
    cmd = [*base_cmd, "--log-path", log_path]
    if output_path is not None:
        cmd.extend(["--output", str(output_path)])

    result = subprocess.run(
        cmd,
        cwd=str(script_dir),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        resolved_output_path = extract_output_path(result.stdout)
        if not resolved_output_path and output_path is not None:
            resolved_output_path = str(output_path)
        return ImportExecutionResult(ok=True, output_path=resolved_output_path, error_text="")

    err = (result.stderr or result.stdout).strip() or "Unknown error"
    return ImportExecutionResult(ok=False, output_path="", error_text=err)
