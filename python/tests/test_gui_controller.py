from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from subprocess import CompletedProcess

from scmdb_watcher.gui_controller import extract_output_path, resolve_start_command, run_import_process


class GuiControllerTests(unittest.TestCase):
    def test_resolve_start_command_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "SCMDB-Watcher.exe").write_text("", encoding="utf-8")
            cmd, err, port = resolve_start_command(
                script_dir=base,
                config_data={"port": 23456},
                default_port=23456,
                frozen=True,
                log_path="C:/Games/SC/LIVE/Game.log",
                parent_pid=4321,
            )
            self.assertIsNone(err)
            self.assertIsNotNone(cmd)
            self.assertIsNotNone(port)
            self.assertIn("--log-path", cmd)
            self.assertIn("--port", cmd)
            self.assertEqual(cmd[-2:], ["--parent-pid", "4321"])

    def test_resolve_start_command_missing_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cmd, err, port = resolve_start_command(
                script_dir=base,
                config_data={"port": 23456},
                default_port=23456,
                frozen=False,
                log_path="C:/Games/SC/LIVE/Game.log",
            )
            self.assertIsNone(cmd)
            self.assertEqual(err, "missing_env")
            self.assertIsNone(port)

    def test_extract_output_path(self) -> None:
        sample = "line a\nOutput written to\nC:/tmp/out.json\nline c\n"
        self.assertEqual(extract_output_path(sample), "C:/tmp/out.json")

    @patch("scmdb_watcher.gui_controller.subprocess.run")
    def test_run_import_process_success(self, run_mock) -> None:
        run_mock.return_value = CompletedProcess(
            args=["watcher", "import"],
            returncode=0,
            stdout="Output written to\nC:/tmp/out.json\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_import_process(["watcher", "import"], Path(tmp), "C:/Games/SC/LIVE/Game.log")
        self.assertTrue(result.ok)
        self.assertEqual(result.output_path, "C:/tmp/out.json")
        self.assertEqual(result.error_text, "")

    @patch("scmdb_watcher.gui_controller.subprocess.run")
    def test_run_import_process_success_uses_explicit_output_when_stdout_is_empty(self, run_mock) -> None:
        run_mock.return_value = CompletedProcess(
            args=["watcher", "import"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.json"
            result = run_import_process(
                ["watcher", "import"],
                Path(tmp),
                "C:/Games/SC/LIVE/Game.log",
                output_path=output,
            )
        self.assertTrue(result.ok)
        self.assertEqual(result.output_path, str(output))
        self.assertEqual(result.error_text, "")

    @patch("scmdb_watcher.gui_controller.subprocess.run")
    def test_run_import_process_failure(self, run_mock) -> None:
        run_mock.return_value = CompletedProcess(
            args=["watcher", "import"],
            returncode=1,
            stdout="",
            stderr="boom",
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_import_process(["watcher", "import"], Path(tmp), "C:/Games/SC/LIVE/Game.log")
        self.assertFalse(result.ok)
        self.assertEqual(result.output_path, "")
        self.assertEqual(result.error_text, "boom")


if __name__ == "__main__":
    unittest.main()
