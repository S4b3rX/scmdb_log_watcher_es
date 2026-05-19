from __future__ import annotations

import unittest

from scmdb_watcher.gui_status import decide_poll_status


class GuiStatusTests(unittest.TestCase):
    def test_running_and_ping_ok(self) -> None:
        decision = decide_poll_status(running=True, ping_ok=True, auto_start=True, game_running=True)
        self.assertEqual(decision.status_key, "status_ok")
        self.assertEqual(decision.color, "#2e7d32")
        self.assertTrue(decision.running)
        self.assertFalse(decision.should_start)

    def test_running_waiting_connection(self) -> None:
        decision = decide_poll_status(running=True, ping_ok=False, auto_start=True, game_running=True)
        self.assertEqual(decision.status_key, "status_wait_conn")
        self.assertEqual(decision.color, "#ef6c00")
        self.assertTrue(decision.running)
        self.assertFalse(decision.should_start)

    def test_not_running_with_autostart_and_game(self) -> None:
        decision = decide_poll_status(running=False, ping_ok=False, auto_start=True, game_running=True)
        self.assertEqual(decision.status_key, "status_wait_sc")
        self.assertFalse(decision.running)
        self.assertTrue(decision.should_start)

    def test_not_running_autostart_off(self) -> None:
        decision = decide_poll_status(running=False, ping_ok=False, auto_start=False, game_running=False)
        self.assertEqual(decision.status_key, "status_stopped")
        self.assertEqual(decision.color, "#c62828")
        self.assertFalse(decision.running)
        self.assertFalse(decision.should_start)


if __name__ == "__main__":
    unittest.main()
