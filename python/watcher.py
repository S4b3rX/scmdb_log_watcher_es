"""
SCMDB Game Log Watcher

Tailed Star Citizen's Game.log, parses mission and blueprint events,
broadcasts them to a connected SCMDB browser tab via Server-Sent Events.

See gamelog-watcher-concept.md for the full design.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Optional

from scmdb_watcher.domain import (
    WatcherState,
    process_line,
)
from scmdb_watcher.import_service import (
    build_export_payload,
    collect_log_files,
    dedupe_missions_by_guid,
    resolve_output_path,
    scan_file_for_export,
    write_payload,
)
from scmdb_watcher.live_runtime_service import (
    build_allowed_origins,
    register_shutdown_signals,
    start_live_runtime,
    stop_live_runtime,
)
from scmdb_watcher.paths import resolve_default_log_path
from scmdb_watcher.runtime_service import setup_session_logging
from scmdb_watcher.server import EventBus, build_app


__version__ = "0.1.2"

DEFAULT_PORT = 23456
RUNTIME_DIR_NAME = "runtime"
PROD_ORIGINS = frozenset({"https://scmdb.net", "https://www.scmdb.net"})
DEV_ORIGINS_DEFAULT = frozenset({"http://localhost:5173", "http://localhost:3000"})

TAIL_POLL_INTERVAL_SEC = 0.2

log = logging.getLogger("scmdb-watcher")


# ---------------------------------------------------------------------------
# File tailer with rotation detection
# ---------------------------------------------------------------------------


class LogTailer:
    def __init__(self, path: Path, state: WatcherState, bus: EventBus) -> None:
        self.path = path
        self.state = state
        self.bus = bus
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        fh: Optional[object] = None
        last_inode: Optional[int] = None
        last_size: int = 0
        buffer = bytearray()
        first_open = True

        while not self._stop.is_set():
            try:
                st = self.path.stat()
            except FileNotFoundError:
                if fh:
                    fh.close()
                    fh = None
                    last_inode = None
                    buffer.clear()
                    log.info("Game.log not found, waiting for it to appear...")
                self._stop.wait(1.0)
                continue
            except OSError as e:
                log.warning("stat failed: %s", e)
                self._stop.wait(1.0)
                continue

            rotated = (
                fh is None
                or (last_inode is not None and st.st_ino and st.st_ino != last_inode)
                or st.st_size < last_size
            )

            if rotated:
                if fh:
                    log.info("Log rotation detected — resetting state")
                    fh.close()
                    self.state.reset()
                    self.bus.broadcast({"type": "session_reset"})
                try:
                    fh = open(self.path, "rb")
                except OSError as e:
                    log.warning("open failed: %s — retrying", e)
                    fh = None
                    self._stop.wait(1.0)
                    continue
                last_inode = st.st_ino or None
                if first_open:
                    fh.seek(0, os.SEEK_END)
                    last_size = fh.tell()
                else:
                    last_size = 0
                buffer.clear()
                if first_open:
                    log.info("Opened %s (size=%d bytes) — starting from end of current log",
                             self.path, st.st_size)
                    first_open = False

            try:
                chunk = fh.read()
            except OSError as e:
                log.warning("read failed: %s", e)
                self._stop.wait(1.0)
                continue

            if chunk:
                buffer.extend(chunk)
                # Split at last newline; keep trailing fragment in buffer.
                nl = buffer.rfind(b"\n")
                if nl >= 0:
                    block = bytes(buffer[: nl + 1])
                    del buffer[: nl + 1]
                    for raw in block.splitlines():
                        if not raw:
                            continue
                        line = raw.decode("utf-8", errors="replace")
                        process_line(line, self.state, self.bus, log)
                last_size = st.st_size
            else:
                self._stop.wait(TAIL_POLL_INTERVAL_SEC)

        if fh:
            fh.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_live_args(argv: list[str]) -> argparse.Namespace:
    default_log_path = resolve_default_log_path(__file__)
    parser = argparse.ArgumentParser(
        prog="watcher",
        description="SCMDB Star Citizen Game.log watcher (live event push to scmdb.net)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("SCMDB_WATCHER_PORT", DEFAULT_PORT)),
        help=f"Port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=default_log_path,
        help=(
            "Path to Game.log "
            f"(default auto-detected: {default_log_path})"
        ),
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        default=bool(os.environ.get("SCMDB_WATCHER_DEV")),
        help="Allow localhost dev origins (5173, 3000) in CORS whitelist",
    )
    parser.add_argument(
        "--dev-origins",
        type=str,
        default=os.environ.get("SCMDB_WATCHER_DEV_ORIGINS", ""),
        help="Comma-separated list of extra origins to allow (implies --dev)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--parent-pid",
        type=int,
        default=None,
        help="Internal: parent GUI process PID; watcher exits if the parent disappears.",
    )
    return parser.parse_args(argv)


def _is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False

    if os.name == "nt":
        import ctypes

        synchronize = 0x00100000
        wait_timeout = 0x00000102
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(synchronize, False, pid)
        if not handle:
            return False
        try:
            return kernel32.WaitForSingleObject(handle, 0) == wait_timeout
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def start_parent_watchdog(
    parent_pid: int | None,
    request_shutdown,
    logger,
    *,
    poll_interval_sec: float = 1.0,
) -> threading.Event | None:
    if parent_pid is None:
        return None

    stop_event = threading.Event()

    def worker() -> None:
        while not stop_event.wait(poll_interval_sec):
            if _is_process_alive(parent_pid):
                continue
            logger.warning("Parent process %s exited; shutting down watcher", parent_pid)
            request_shutdown()
            return

    threading.Thread(target=worker, name="parent-watchdog", daemon=True).start()
    return stop_event


def parse_import_args(argv: list[str]) -> argparse.Namespace:
    default_log_path = resolve_default_log_path(__file__)
    parser = argparse.ArgumentParser(
        prog="watcher.py import",
        description="Scan Star Citizen logbackups and export completed missions + blueprints as JSON.",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=default_log_path,
        help="Path to Game.log; the logbackups directory is derived from its parent. "
             "Override only if you installed Star Citizen somewhere non-default.",
    )
    parser.add_argument(
        "--logbackups-dir",
        type=Path,
        default=None,
        help="Explicit path to a logbackups directory. Defaults to '<log-path parent>/logbackups'.",
    )
    parser.add_argument(
        "--include-current",
        action="store_true",
        help="Also scan the current Game.log in addition to the backups (default: off)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path. Defaults to 'scmdb-import/scmdb-import-<timestamp>.json' next to watcher.py.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


def run_live(argv: list[str]) -> int:
    args = parse_live_args(argv)

    script_dir = Path(__file__).resolve().parent
    log_file = setup_session_logging(args.verbose, script_dir, runtime_dir_name=RUNTIME_DIR_NAME)

    allowed = build_allowed_origins(PROD_ORIGINS, DEV_ORIGINS_DEFAULT, args.dev, args.dev_origins)

    log.info("SCMDB Log Watcher v%s starting", __version__)
    log.debug("CLI args (live): %s", argv)
    log.info("Session log file: %s", log_file)
    log.info("CORS whitelist: %s", sorted(allowed))
    log.info("Watching: %s", args.log_path)
    log.info("Requested port: %d", args.port)
    if args.parent_pid is not None:
        log.info("Parent watchdog enabled for PID %s", args.parent_pid)

    state = WatcherState()
    bus = EventBus()
    app = build_app(state, bus, frozenset(allowed), __version__)

    try:
        runtime = start_live_runtime(
            log_path=args.log_path,
            state=state,
            bus=bus,
            app=app,
            requested_port=args.port,
            logger=log,
            tailer_cls=LogTailer,
        )
    except OSError as e:
        log.error("Failed to bind watcher server near 127.0.0.1:%d - %s", args.port, e)
        return 2

    log.info("Listening on http://127.0.0.1:%d", runtime.bound_port)
    request_shutdown = register_shutdown_signals(runtime.server, log)
    parent_watchdog = start_parent_watchdog(args.parent_pid, request_shutdown, log)

    try:
        runtime.server.serve_forever()
    except KeyboardInterrupt:
        request_shutdown()
    finally:
        if parent_watchdog is not None:
            parent_watchdog.set()
        stop_live_runtime(runtime, log)

    return 0


def run_import(argv: list[str]) -> int:
    args = parse_import_args(argv)

    script_dir = Path(__file__).resolve().parent
    log_file = setup_session_logging(args.verbose, script_dir, runtime_dir_name=RUNTIME_DIR_NAME)
    log.info("SCMDB Log Watcher v%s — import mode", __version__)
    log.info("Session log file: %s", log_file)
    log.debug("CLI args (import): %s", argv)

    logbackups = args.logbackups_dir or args.log_path.parent / "logbackups"
    if not logbackups.is_dir():
        print(f"[ERROR] logbackups directory not found: {logbackups}", file=sys.stderr)
        print(
            "Pass --log-path pointing at your Star Citizen Game.log, "
            "or --logbackups-dir directly.",
            file=sys.stderr,
        )
        return 1

    files_to_scan = collect_log_files(logbackups, args.log_path, args.include_current)

    if not files_to_scan:
        print(f"[ERROR] No log files found in {logbackups}", file=sys.stderr)
        return 1

    print(f"SCMDB Log Watcher v{__version__} — import mode")
    print(f"Scanning {len(files_to_scan)} log file(s) from: {logbackups}")
    print()

    all_missions: list[dict] = []
    all_blueprints: list[dict] = []
    source_logs: list[str] = []

    for i, path in enumerate(files_to_scan, 1):
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  [{i:>3}/{len(files_to_scan)}] {path.name}  ({size_mb:.2f} MB)")
        m, b = scan_file_for_export(path, log)
        if m or b:
            print(f"           -> {len(m)} mission(s), {len(b)} blueprint(s)")
        all_missions.extend(m)
        all_blueprints.extend(b)
        source_logs.append(path.name)

    deduped_missions, dropped = dedupe_missions_by_guid(all_missions)
    output = resolve_output_path(args.output, __file__, runtime_dir_name=RUNTIME_DIR_NAME)
    payload = build_export_payload(__version__, source_logs, deduped_missions, all_blueprints)
    write_payload(output, payload)

    print()
    print(f"Done. {len(deduped_missions)} mission(s), {len(all_blueprints)} blueprint(s).")
    if dropped:
        print(f"  ({dropped} duplicate mission GUID(s) merged.)")
    print(f"Output written to:")
    print(f"  {output}")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] == "import":
        return run_import(argv[1:])
    return run_live(argv)


if __name__ == "__main__":
    sys.exit(main())
