"""Runtime helpers: logging setup/retention and port selection/binding."""

from __future__ import annotations

import logging
import socket
from pathlib import Path

from scmdb_watcher.config import resolve_runtime_dir


MAX_LOG_FILES = 5


def _is_address_in_use(error: OSError) -> bool:
    err_no = getattr(error, "errno", None)
    if err_no in {48, 98, 10048}:
        return True
    msg = str(error).lower()
    return "address already in use" in msg or "only one usage" in msg


def choose_available_port(host: str, preferred_port: int, search_span: int = 20) -> int:
    for offset in range(max(1, search_span + 1)):
        candidate = preferred_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, candidate))
            except OSError:
                continue
            return candidate
    return preferred_port


def create_server_with_fallback(app, host: str, preferred_port: int, logger: logging.Logger, max_attempts: int = 20):
    from werkzeug.serving import make_server

    last_err: OSError | None = None

    attempts = max(1, max_attempts)

    for offset in range(attempts):
        candidate = preferred_port + offset
        try:
            server = make_server(host, candidate, app, threaded=True)
            if candidate != preferred_port:
                logger.warning(
                    "Preferred port %d is in use. Using fallback port %d.",
                    preferred_port,
                    candidate,
                )
            else:
                logger.debug("Using preferred port %d.", preferred_port)
            return server, candidate
        except OSError as error:
            if not _is_address_in_use(error):
                raise
            last_err = error

    if last_err is not None:
        raise last_err
    raise OSError("Unable to bind watcher server")


def prune_old_log_files(log_dir: Path, keep: int = MAX_LOG_FILES) -> int:
    files = sorted(log_dir.glob("watcher-*.log"), key=lambda p: p.stat().st_mtime)
    if len(files) <= keep:
        return 0

    to_delete = files[: len(files) - keep]
    deleted = 0
    for path in to_delete:
        try:
            path.unlink()
            deleted += 1
        except OSError:
            continue
    return deleted


def setup_session_logging(verbose: bool, script_dir: Path, runtime_dir_name: str = "runtime") -> Path:
    runtime_dir = resolve_runtime_dir(script_dir)
    log_dir = runtime_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "watcher.log"

    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(message)s"

    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(fmt, datefmt="%H:%M:%S"))
    console.setLevel(level)
    root.addHandler(console)

    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="w")
    file_handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    file_handler.setLevel(level)
    root.addHandler(file_handler)

    return log_file
