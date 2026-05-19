"""Live runtime orchestration helpers for watcher server lifecycle."""

from __future__ import annotations

import signal
import threading
from dataclasses import dataclass
from pathlib import Path

from scmdb_watcher.runtime_service import create_server_with_fallback


@dataclass
class LiveRuntimeContext:
    tailer: object
    tail_thread: threading.Thread
    server: object
    bound_port: int


def build_allowed_origins(
    prod_origins: frozenset[str],
    dev_origins_default: frozenset[str],
    dev_flag: bool,
    dev_origins_raw: str,
) -> set[str]:
    allowed = set(prod_origins)
    if dev_flag or dev_origins_raw:
        allowed |= set(dev_origins_default)
    if dev_origins_raw:
        allowed |= {origin.strip() for origin in dev_origins_raw.split(",") if origin.strip()}
    return allowed


def start_live_runtime(
    log_path: Path,
    state,
    bus,
    app,
    requested_port: int,
    logger,
    tailer_cls,
) -> LiveRuntimeContext:
    tailer = tailer_cls(log_path, state, bus)
    tail_thread = threading.Thread(target=tailer.run, name="log-tail", daemon=True)
    tail_thread.start()

    server, bound_port = create_server_with_fallback(app, "127.0.0.1", requested_port, logger, max_attempts=1)
    return LiveRuntimeContext(
        tailer=tailer,
        tail_thread=tail_thread,
        server=server,
        bound_port=bound_port,
    )


def register_shutdown_signals(server, logger):
    def request_shutdown(*_args):  # type: ignore[no-untyped-def]
        logger.info("Shutdown requested")
        threading.Thread(target=server.shutdown, daemon=True).start()

    for sig_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            signal.signal(sig, request_shutdown)
        except (OSError, ValueError):
            continue

    return request_shutdown


def stop_live_runtime(runtime: LiveRuntimeContext, logger) -> None:
    runtime.server.server_close()
    runtime.tailer.stop()
    runtime.tail_thread.join(timeout=2.0)
    logger.info("Watcher stopped")
