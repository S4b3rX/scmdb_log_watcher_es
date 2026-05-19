from __future__ import annotations

import unittest
from pathlib import Path

from scmdb_watcher.gui_settings import build_settings_defaults, build_settings_save_result


class GuiSettingsTests(unittest.TestCase):
    def test_build_settings_defaults(self) -> None:
        defaults = build_settings_defaults(
            {"game_install_dir": "C:/Games/SC", "channel": "hotfix", "run_startup_tests": True},
            current_language="EN",
            auto_start=True,
        )
        self.assertEqual(defaults.game_dir, "C:/Games/SC")
        self.assertEqual(defaults.channel, "LIVE")
        self.assertEqual(defaults.language, "en-en")
        self.assertTrue(defaults.auto_start)
        self.assertTrue(defaults.run_startup_tests)

    def test_build_settings_save_result_ok(self) -> None:
        result = build_settings_save_result(
            game_dir_raw=" C:/Games/SC ",
            channel_raw="live",
            language_raw="ES",
            auto_start=False,
            run_startup_tests=True,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.error_key, "")
        self.assertEqual(result.game_dir, "C:/Games/SC")
        self.assertEqual(result.channel, "LIVE")
        self.assertEqual(result.language, "es-es")
        self.assertFalse(result.auto_start)
        self.assertTrue(result.run_startup_tests)
        self.assertTrue(result.log_path.endswith("LIVE\\Game.log") or result.log_path.endswith("LIVE/Game.log"))

    def test_build_settings_save_result_hotfix_dir_is_normalized_to_live_root(self) -> None:
        result = build_settings_save_result(
            game_dir_raw=" D:/RSI/StarCitizen/HOTFIX ",
            channel_raw="hotfix",
            language_raw="ES",
            auto_start=False,
            run_startup_tests=False,
        )
        self.assertTrue(result.ok)
        self.assertEqual(Path(result.game_dir), Path("D:/RSI/StarCitizen"))
        self.assertEqual(result.channel, "LIVE")
        self.assertTrue(result.log_path.endswith("LIVE\\Game.log") or result.log_path.endswith("LIVE/Game.log"))

    def test_build_settings_save_result_missing_path(self) -> None:
        result = build_settings_save_result(
            game_dir_raw="   ",
            channel_raw="live",
            language_raw="es",
            auto_start=True,
            run_startup_tests=False,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error_key, "missing_cfg")



if __name__ == "__main__":
    unittest.main()
