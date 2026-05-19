from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import watcher


class _ImmediateThread:
    def __init__(self, target, name: str, daemon: bool) -> None:
        self._target = target
        self.name = name
        self.daemon = daemon

    def start(self) -> None:
        self._target()


class WatcherParentWatchdogTests(unittest.TestCase):
    def test_start_parent_watchdog_returns_none_without_parent_pid(self) -> None:
        self.assertIsNone(watcher.start_parent_watchdog(None, Mock(), Mock()))

    @patch("watcher.threading.Thread", side_effect=_ImmediateThread)
    @patch("watcher._is_process_alive", return_value=False)
    def test_start_parent_watchdog_requests_shutdown_when_parent_is_gone(self, alive_mock, thread_mock) -> None:
        request_shutdown = Mock()
        logger = Mock()

        stop_event = watcher.start_parent_watchdog(4321, request_shutdown, logger, poll_interval_sec=0)

        self.assertIsNotNone(stop_event)
        alive_mock.assert_called_once_with(4321)
        request_shutdown.assert_called_once_with()
        logger.warning.assert_called_once()
        thread_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
