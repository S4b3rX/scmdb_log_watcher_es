from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from scmdb_watcher.test_groups_service import TestGroup, run_test_groups


class TestGroupsServiceTests(unittest.TestCase):
    @patch("scmdb_watcher.test_groups_service.subprocess.run")
    def test_run_test_groups_ok(self, run_mock) -> None:
        run_mock.return_value = CompletedProcess(
            args=["python"],
            returncode=0,
            stdout="GROUP_RESULT:12:0:0\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            results = run_test_groups(
                script_dir=Path(tmp),
                groups=(TestGroup("g1", ("test_a.py",)),),
            )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].ok)
        self.assertEqual(results[0].tests_run, 12)
        self.assertEqual(results[0].failures, 0)
        self.assertEqual(results[0].errors, 0)

    @patch("scmdb_watcher.test_groups_service.subprocess.run")
    def test_run_test_groups_fail_and_callbacks(self, run_mock) -> None:
        run_mock.return_value = CompletedProcess(
            args=["python"],
            returncode=1,
            stdout="GROUP_RESULT:8:1:0\n",
            stderr="trace",
        )
        started: list[str] = []
        done: list[str] = []

        with tempfile.TemporaryDirectory() as tmp:
            run_test_groups(
                script_dir=Path(tmp),
                groups=(TestGroup("g2", ("test_b.py",)),),
                on_group_start=lambda g: started.append(g.key),
                on_group_done=lambda r: done.append(r.key),
            )

        self.assertEqual(started, ["g2"])
        self.assertEqual(done, ["g2"])


if __name__ == "__main__":
    unittest.main()
