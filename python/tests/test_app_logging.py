from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from scmdb_watcher.app_logging import prune_named_log_files, setup_app_file_logger


class AppLoggingTests(unittest.TestCase):
    def test_setup_app_file_logger_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            logger, log_file = setup_app_file_logger(runtime_dir, prefix="gui-test", level=logging.INFO)
            logger.info("hello")
            for handler in list(logger.handlers):
                handler.flush()
                handler.close()
                logger.removeHandler(handler)
            self.assertTrue(log_file.exists())
            content = log_file.read_text(encoding="utf-8")
            self.assertIn("hello", content)

    def test_prune_named_log_files_keeps_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            for idx in range(7):
                path = log_dir / f"gui-{idx}.log"
                path.write_text(str(idx), encoding="utf-8")

            deleted = prune_named_log_files(log_dir, prefix="gui", keep=5)
            self.assertEqual(deleted, 2)
            remaining = sorted(p.name for p in log_dir.glob("gui-*.log"))
            self.assertEqual(len(remaining), 5)


if __name__ == "__main__":
    unittest.main()
