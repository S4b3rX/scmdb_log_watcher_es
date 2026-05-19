"""Grouped unittest execution helpers for GUI-driven test runs."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class TestGroup:
    key: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class TestGroupResult:
    key: str
    ok: bool
    tests_run: int
    failures: int
    errors: int
    output: str


DEFAULT_TEST_GROUPS: tuple[TestGroup, ...] = (
    TestGroup("tests_group_core", ("test_domain.py", "test_paths.py", "test_validators.py")),
    TestGroup(
        "tests_group_runtime",
        ("test_runtime_service.py", "test_process_service.py", "test_live_runtime_service.py", "test_startup_checklist.py"),
    ),
    TestGroup("tests_group_import", ("test_import_service.py",)),
    TestGroup(
        "tests_group_gui",
        ("test_gui_controller.py", "test_gui_i18n.py", "test_gui_settings.py", "test_gui_status.py", "test_gui_view.py", "test_app_logging.py"),
    ),
    TestGroup("tests_group_updates", ("test_update_service.py",)),
)


def _build_group_runner_code() -> str:
    return (
        "import json,sys,unittest\n"
        "patterns=json.loads(sys.argv[1])\n"
        "loader=unittest.defaultTestLoader\n"
        "suite=unittest.TestSuite()\n"
        "for pattern in patterns:\n"
        "    suite.addTests(loader.discover('tests', pattern=pattern))\n"
        "result=unittest.TextTestRunner(verbosity=0).run(suite)\n"
        "print(f'GROUP_RESULT:{result.testsRun}:{len(result.failures)}:{len(result.errors)}')\n"
        "sys.exit(0 if result.wasSuccessful() else 1)\n"
    )


def _parse_group_result(stdout: str) -> tuple[int, int, int]:
    tests_run = 0
    failures = 0
    errors = 0
    for line in (stdout or "").splitlines():
        if line.startswith("GROUP_RESULT:"):
            _prefix, a, b, c = line.split(":", 3)
            tests_run = int(a)
            failures = int(b)
            errors = int(c)
            break
    return tests_run, failures, errors


def run_test_groups(
    *,
    script_dir: Path,
    python_executable: str | None = None,
    groups: tuple[TestGroup, ...] = DEFAULT_TEST_GROUPS,
    on_group_start: Callable[[TestGroup], None] | None = None,
    on_group_done: Callable[[TestGroupResult], None] | None = None,
) -> list[TestGroupResult]:
    python_cmd = python_executable or sys.executable
    runner_code = _build_group_runner_code()
    results: list[TestGroupResult] = []

    for group in groups:
        if on_group_start:
            on_group_start(group)
        cmd = [python_cmd, "-c", runner_code, json.dumps(list(group.files))]
        proc = subprocess.run(cmd, cwd=str(script_dir), capture_output=True, text=True)
        merged_output = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part).strip()
        tests_run, failures, errors = _parse_group_result(proc.stdout or "")
        result = TestGroupResult(
            key=group.key,
            ok=(proc.returncode == 0),
            tests_run=tests_run,
            failures=failures,
            errors=errors,
            output=merged_output,
        )
        results.append(result)
        if on_group_done:
            on_group_done(result)

    return results
