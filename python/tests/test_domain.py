from __future__ import annotations

import logging
import unittest

from scmdb_watcher.domain import WatcherState, process_line


class _FakeBus:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def broadcast(self, event: dict) -> None:
        self.events.append(event)


class DomainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = WatcherState()
        self.bus = _FakeBus()
        self.logger = logging.getLogger("test-domain")

    def test_marker_then_accept_emits_mission_start(self) -> None:
        process_line(
            '<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-1] generator name [gen-a] contract [Contract A]',
            self.state,
            self.bus,
            self.logger,
        )
        process_line(
            '<2026-05-17T12:00:02.000Z> Added notification "Contract Accepted: foo MissionId: [guid-1]"',
            self.state,
            self.bus,
            self.logger,
        )

        self.assertTrue(any(evt.get("type") == "mission_start" for evt in self.bus.events))

    def test_complete_emits_mission_complete(self) -> None:
        process_line(
            '<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-2] generator name [gen-b] contract [Contract B]',
            self.state,
            self.bus,
            self.logger,
        )
        process_line(
            '<2026-05-17T12:00:01.000Z> Added notification "Contract Accepted: bar MissionId: [guid-2]"',
            self.state,
            self.bus,
            self.logger,
        )
        process_line(
            '<2026-05-17T12:00:05.000Z> <EndMission> MissionId[guid-2] CompletionType[Complete] Reason[Complete]',
            self.state,
            self.bus,
            self.logger,
        )

        self.assertTrue(any(evt.get("type") == "mission_complete" for evt in self.bus.events))

    def test_blueprint_correlates_to_recent_lifecycle_event(self) -> None:
        process_line(
            '<2026-05-17T12:00:00.000Z> CreateMarker missionId [guid-3] generator name [gen-c] contract [Contract C]',
            self.state,
            self.bus,
            self.logger,
        )
        process_line(
            '<2026-05-17T12:00:01.000Z> Added notification "Contract Accepted: baz MissionId: [guid-3]"',
            self.state,
            self.bus,
            self.logger,
        )
        process_line(
            '<2026-05-17T12:00:02.000Z> Added notification "Received Blueprint: Product X:"',
            self.state,
            self.bus,
            self.logger,
        )

        bp_events = [evt for evt in self.bus.events if evt.get("type") == "blueprint_received"]
        self.assertEqual(len(bp_events), 1)
        self.assertEqual(bp_events[0].get("missionGuid"), "guid-3")


if __name__ == "__main__":
    unittest.main()
