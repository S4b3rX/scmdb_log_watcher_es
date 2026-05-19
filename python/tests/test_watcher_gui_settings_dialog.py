from __future__ import annotations

import unittest
from unittest.mock import Mock

from watcher_gui import WatcherGui


class _DialogStub:
    def __init__(self, exists: bool = True) -> None:
        self._exists = exists

    def winfo_exists(self) -> bool:
        return self._exists


class WatcherGuiSettingsDialogTests(unittest.TestCase):
    def test_poll_status_skips_health_check_while_settings_dialog_is_open(self) -> None:
        gui = WatcherGui.__new__(WatcherGui)
        gui.proc = None
        gui._settings_dialog = _DialogStub(True)
        gui._exiting = False
        gui._watcher_start_time = None
        gui._toggle_buttons = Mock()
        gui._ping_ok = Mock(return_value=(True, "0.1.2"))
        gui._set_status = Mock()
        gui.start_watcher = Mock()
        gui.after = Mock()
        gui.log = Mock()

        gui._poll_status()

        gui._ping_ok.assert_not_called()
        gui._toggle_buttons.assert_called_once_with(running=False)
        gui._set_status.assert_not_called()
        gui.start_watcher.assert_not_called()
        gui.after.assert_called_once_with(1500, gui._poll_status)


if __name__ == "__main__":
    unittest.main()
