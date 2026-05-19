from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from scmdb_watcher.config import IMPORTS_DIR_NAME
from scmdb_watcher.import_service import (
    build_export_payload,
    collect_log_files,
    dedupe_missions_by_guid,
    resolve_output_path,
    scan_file_for_export,
)


class ImportServiceTests(unittest.TestCase):
    def test_collect_log_files_and_include_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logbackups = root / "logbackups"
            logbackups.mkdir(parents=True, exist_ok=True)
            (logbackups / "Game Build(1).log").write_text("", encoding="utf-8")
            (logbackups / "Game Build(2).log").write_text("", encoding="utf-8")
            current = root / "Game.log"
            current.write_text("", encoding="utf-8")

            files = collect_log_files(logbackups, current, include_current=True)
            self.assertEqual(len(files), 3)
            self.assertEqual(files[-1], current)

    def test_dedupe_missions_by_guid(self) -> None:
        missions = [
            {"guid": "a", "x": 1},
            {"guid": "b", "x": 2},
            {"guid": "a", "x": 3},
        ]
        deduped, dropped = dedupe_missions_by_guid(missions)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(dropped, 1)

    def test_resolve_output_path_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            anchor = Path(tmp) / "watcher.py"
            anchor.write_text("# anchor", encoding="utf-8")
            output = resolve_output_path(None, anchor)
            self.assertEqual(output.parent.name, IMPORTS_DIR_NAME)
            self.assertTrue(output.name.startswith("scmdb-import-"))

    def test_scan_file_for_export_minimal_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.log"
            path.write_text(
                "\n".join(
                    [
                        "<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-1] generator name [gen] contract [Contract A]",
                        '<2026-05-17T12:00:01.000Z> Added notification "Contract Accepted: test MissionId: [guid-1]"',
                        "<2026-05-17T12:00:05.000Z> <EndMission> MissionId[guid-1] CompletionType[Complete] Reason[Complete]",
                        '<2026-05-17T12:00:06.000Z> Added notification "Received Blueprint: Product X:"',
                    ]
                ),
                encoding="utf-8",
            )
            logger = logging.getLogger("test-import")
            missions, blueprints = scan_file_for_export(path, logger)
            self.assertEqual(len(missions), 1)
            self.assertEqual(len(blueprints), 1)
            self.assertEqual(missions[0]["guid"], "guid-1")

    def test_build_export_payload(self) -> None:
        payload = build_export_payload("0.1.2", ["a.log"], [{"guid": "x"}], [{"productName": "p"}])
        self.assertEqual(payload["watcherVersion"], "0.1.2")
        self.assertEqual(payload["sourceLogs"], ["a.log"])


if __name__ == "__main__":
    unittest.main()
