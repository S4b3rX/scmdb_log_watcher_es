"""Domain state and line parser for SCMDB watcher."""

from __future__ import annotations

import logging
import re
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional, Protocol

BLUEPRINT_CORRELATION_WINDOW_SEC = 5.0

PATTERN_TIMESTAMP = re.compile(r"^<([0-9T:\-.Z]+)>")
PATTERN_MARKER = re.compile(
    r"CreateMarker.*missionId \[([^\]]+)\].*generator name \[([^\]]+)\].*contract \[([^\]]+)\]"
)
PATTERN_ACCEPTED = re.compile(r'Added notification "Contract Accepted:.*?MissionId: \[([^\]]+)\]')
PATTERN_END_MISSION = re.compile(
    r"<EndMission>.*MissionId\[([^\]]+)\].*CompletionType\[(\w+)\].*Reason\[([^\]]+)\]"
)
PATTERN_BLUEPRINT = re.compile(r'Added notification "Received Blueprint: ([^:]+):')

COMPLETION_LABELS = {
    "Complete": "Mission complete",
    "Abandon": "Mission abandoned",
    "Fail": "Mission failed",
    "Disconnect": "Mission disconnected",
    "Deactivate": "Mission deactivated",
}


class EventBroadcaster(Protocol):
    def broadcast(self, event: dict) -> None:
        ...


def parse_log_timestamp(line: str) -> Optional[float]:
    m = PATTERN_TIMESTAMP.match(line)
    if not m:
        return None
    raw = m.group(1).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).timestamp()
    except ValueError:
        return None


@dataclass
class MissionEntry:
    debug_name: str
    generator: str


@dataclass
class ActiveMission:
    guid: str
    debug_name: str
    generator: str
    start_ts: float


@dataclass
class MissionLifecycleEvent:
    trigger: str
    guid: str
    debug_name: str
    ts: float


class WatcherState:
    """Holds parsed mission state. Thread-safe via a single lock."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.guid_map: dict[str, MissionEntry] = {}
        self.active: dict[str, ActiveMission] = {}
        self.recent_lifecycle: deque[MissionLifecycleEvent] = deque(maxlen=32)

    def reset(self) -> None:
        with self._lock:
            self.guid_map.clear()
            self.active.clear()
            self.recent_lifecycle.clear()

    def record_marker(self, guid: str, generator: str, contract: str) -> None:
        with self._lock:
            if guid not in self.guid_map:
                self.guid_map[guid] = MissionEntry(debug_name=contract, generator=generator)

    def record_accepted(self, guid: str, ts: float) -> Optional[ActiveMission]:
        with self._lock:
            entry = self.guid_map.get(guid)
            if not entry:
                return None
            active = ActiveMission(
                guid=guid,
                debug_name=entry.debug_name,
                generator=entry.generator,
                start_ts=ts,
            )
            self.active[guid] = active
            self.recent_lifecycle.append(
                MissionLifecycleEvent(trigger="accept", guid=guid, debug_name=entry.debug_name, ts=ts)
            )
            return active

    def record_end(self, guid: str, completion: str, ts: float) -> Optional[ActiveMission]:
        with self._lock:
            active = self.active.pop(guid, None)
            entry = self.guid_map.get(guid)
            if completion == "Complete":
                debug_name = (active.debug_name if active else (entry.debug_name if entry else "?"))
                self.recent_lifecycle.append(
                    MissionLifecycleEvent(trigger="complete", guid=guid, debug_name=debug_name, ts=ts)
                )
            return active

    def correlate_blueprint(self, ts: float) -> Optional[MissionLifecycleEvent]:
        with self._lock:
            best: Optional[MissionLifecycleEvent] = None
            best_delta = BLUEPRINT_CORRELATION_WINDOW_SEC + 1.0
            for event in self.recent_lifecycle:
                delta = ts - event.ts
                if 0.0 <= delta <= BLUEPRINT_CORRELATION_WINDOW_SEC and delta < best_delta:
                    best = event
                    best_delta = delta
            return best

    def snapshot_active(self) -> list[dict]:
        with self._lock:
            return [asdict(mission) for mission in self.active.values()]


def process_line(
    line: str,
    state: WatcherState,
    bus: EventBroadcaster,
    logger: logging.Logger,
) -> None:
    ts = parse_log_timestamp(line) or time.time()

    if m := PATTERN_MARKER.search(line):
        state.record_marker(m.group(1), m.group(2), m.group(3))
        return

    if m := PATTERN_ACCEPTED.search(line):
        active = state.record_accepted(m.group(1), ts)
        if active is None:
            logger.debug("Contract Accepted without prior CreateMarker for %s", m.group(1))
            return
        logger.info("Mission started: %s (%s)", active.debug_name, active.guid)
        bus.broadcast(
            {
                "type": "mission_start",
                "guid": active.guid,
                "debugName": active.debug_name,
                "generator": active.generator,
                "startTs": active.start_ts,
            }
        )
        return

    if m := PATTERN_END_MISSION.search(line):
        guid, completion, reason = m.group(1), m.group(2), m.group(3)
        active = state.record_end(guid, completion, ts)
        entry = state.guid_map.get(guid)
        debug_name = active.debug_name if active else (entry.debug_name if entry else None)
        generator = active.generator if active else (entry.generator if entry else None)
        event_type = "mission_complete" if completion == "Complete" else "mission_ended"
        label = COMPLETION_LABELS.get(completion, f"Mission ended ({completion})")
        logger.info("%s: %s (%s) [%s]", label, debug_name or "?", guid, reason)
        bus.broadcast(
            {
                "type": event_type,
                "guid": guid,
                "debugName": debug_name,
                "generator": generator,
                "completion": completion,
                "reason": reason,
                "endTs": ts,
            }
        )
        return

    if m := PATTERN_BLUEPRINT.search(line):
        product_name = m.group(1).strip()
        corr = state.correlate_blueprint(ts)
        if corr:
            logger.info("Blueprint received: %s (from %s on %s)", product_name, corr.debug_name, corr.trigger)
        else:
            logger.info("Blueprint received: %s (no recent mission to correlate)", product_name)
        bus.broadcast(
            {
                "type": "blueprint_received",
                "productName": product_name,
                "missionGuid": corr.guid if corr else None,
                "missionDebugName": corr.debug_name if corr else None,
                "missionTrigger": corr.trigger if corr else None,
                "ts": ts,
            }
        )
