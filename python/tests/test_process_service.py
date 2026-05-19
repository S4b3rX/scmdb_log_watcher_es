from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scmdb_watcher.process_service import resolve_import_command, resolve_watcher_launch_command


class ProcessServiceTests(unittest.TestCase):
    def test_resolve_watcher_launch_command_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "SCMDB-Watcher.exe").write_text("", encoding="utf-8")
            cmd, err = resolve_watcher_launch_command(base, frozen=True)
            self.assertIsNotNone(cmd)
            self.assertIsNone(err)
            self.assertTrue(str(base / "SCMDB-Watcher.exe") in cmd[0])

    def test_resolve_watcher_launch_command_missing_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cmd, err = resolve_watcher_launch_command(base, frozen=False)
            self.assertIsNone(cmd)
            self.assertEqual(err, "missing_env")

    def test_resolve_import_command_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "SCMDB-Watcher.exe").write_text("", encoding="utf-8")
            cmd, err = resolve_import_command(base, frozen=True)
            self.assertIsNotNone(cmd)
            self.assertIsNone(err)
            self.assertEqual(cmd[1], "import")

    def test_resolve_import_command_missing_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cmd, err = resolve_import_command(base, frozen=False)
            self.assertIsNone(cmd)
            self.assertEqual(err, "missing_env")


if __name__ == "__main__":
    unittest.main()
