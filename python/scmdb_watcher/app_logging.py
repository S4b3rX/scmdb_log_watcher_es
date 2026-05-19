"""Application logging helpers for GUI/runtime diagnostics."""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path


MAX_APP_LOG_FILES = 5


def prune_named_log_files(log_dir: Path, prefix: str, keep: int = MAX_APP_LOG_FILES) -> int:
    files = sorted(log_dir.glob(f"{prefix}-*.log"), key=lambda p: p.stat().st_mtime)
    if len(files) <= keep:
        return 0

    deleted = 0
    for path in files[: len(files) - keep]:
        try:
            path.unlink()
            deleted += 1
        except OSError:
            continue
    return deleted


def setup_app_file_logger(runtime_dir: Path, prefix: str = "gui", level: int = logging.INFO) -> tuple[logging.Logger, Path]:
    log_dir = runtime_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{prefix}.log"

    logger = logging.getLogger(f"scmdb-{prefix}")
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    fmt = "%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d %(funcName)s - %(message)s"
    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="w")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

    return logger, log_file


def install_global_exception_hooks(logger: logging.Logger) -> None:
    prev_excepthook = sys.excepthook

    def _handle_exception(exc_type, exc_value, exc_traceback) -> None:
        logger.exception("Unhandled exception in main thread", exc_info=(exc_type, exc_value, exc_traceback))
        try:
            prev_excepthook(exc_type, exc_value, exc_traceback)
        except Exception:
            # Avoid recursion if previous hook also fails.
            pass

    sys.excepthook = _handle_exception

    if hasattr(threading, "excepthook"):
        prev_thread_hook = threading.excepthook

        def _handle_thread_exception(args) -> None:
            logger.exception(
                "Unhandled exception in thread '%s'",
                args.thread.name if args.thread else "unknown",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )
            try:
                prev_thread_hook(args)
            except Exception:
                pass

        threading.excepthook = _handle_thread_exception
