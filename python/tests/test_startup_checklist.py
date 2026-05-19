from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from scmdb_watcher.config import IMPORTS_DIR_NAME
from scmdb_watcher.startup_checklist import run_startup_checklist


class StartupChecklistTests(unittest.TestCase):
    def test_checklist_creates_runtime_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            scripts = base / ".venv" / "Scripts"
            scripts.mkdir(parents=True, exist_ok=True)
            (scripts / "python.exe").write_text("", encoding="utf-8")
            (base / "watcher.py").write_text("print('ok')", encoding="utf-8")

            result = run_startup_checklist(
                runtime_dir=runtime,
                script_dir=base,
                config_data={"log_path": "C:/Games/SC/LIVE/Game.log"},
                frozen=False,
                run_tests=False,
            )
            self.assertTrue((runtime / "logs").is_dir())
            self.assertTrue((runtime / IMPORTS_DIR_NAME).is_dir())
            self.assertIn("runtime dirs: ok", result.details)

    @patch("scmdb_watcher.startup_checklist.subprocess.run")
    def test_checklist_tests_enabled_ok(self, run_mock) -> None:
        run_mock.return_value = CompletedProcess(args=["python"], returncode=0, stdout="ok", stderr="")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            scripts = base / ".venv" / "Scripts"
            scripts.mkdir(parents=True, exist_ok=True)
            (scripts / "python.exe").write_text("", encoding="utf-8")
            (base / "watcher.py").write_text("print('ok')", encoding="utf-8")
            result = run_startup_checklist(
                runtime_dir=runtime,
                script_dir=base,
                config_data={"log_path": "C:/Games/SC/LIVE/Game.log"},
                frozen=False,
                run_tests=True,
            )
            self.assertTrue(result.ok)
            self.assertIn("startup tests: ok", result.details)


if __name__ == "__main__":
    unittest.main()
