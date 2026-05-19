"""Pure status transition helpers for Watcher GUI polling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PollDecision:
    status_key: str
    color: str
    running: bool
    should_start: bool


def decide_poll_status(
    *,
    running: bool,
    ping_ok: bool,
    auto_start: bool,
    game_running: bool,
) -> PollDecision:
    if running and ping_ok:
        return PollDecision(status_key="status_ok", color="#2e7d32", running=True, should_start=False)

    if running:
        return PollDecision(status_key="status_wait_conn", color="#ef6c00", running=True, should_start=False)

    if auto_start and game_running:
        return PollDecision(status_key="status_wait_sc", color="#ef6c00", running=False, should_start=True)

    if auto_start:
        return PollDecision(status_key="status_wait_sc", color="#ef6c00", running=False, should_start=False)

    return PollDecision(status_key="status_stopped", color="#c62828", running=False, should_start=False)
