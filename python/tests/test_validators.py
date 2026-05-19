from __future__ import annotations

import unittest

from scmdb_watcher.validators import (
    build_log_path,
    normalize_channel,
    normalize_language,
    validate_game_install_dir,
)


class ValidatorsTests(unittest.TestCase):
    def test_normalize_channel(self) -> None:
        self.assertEqual(normalize_channel("live"), "LIVE")
        self.assertEqual(normalize_channel("hotfix"), "HOTFIX")
        self.assertEqual(normalize_channel("unknown"), "LIVE")

    def test_normalize_language(self) -> None:
        self.assertEqual(normalize_language("EN"), "en-en")
        self.assertEqual(normalize_language("es"), "es-es")
        self.assertEqual(normalize_language("fr"), "fr-fr")
        self.assertEqual(normalize_language("zh-hans"), "zh-cn")
        self.assertEqual(normalize_language("unknown"), "es-es")

    def test_validate_game_install_dir(self) -> None:
        ok, value = validate_game_install_dir(" C:/Games/SC ")
        self.assertTrue(ok)
        self.assertEqual(value, "C:/Games/SC")

        ok2, reason = validate_game_install_dir("   ")
        self.assertFalse(ok2)
        self.assertEqual(reason, "missing")

    def test_build_log_path(self) -> None:
        self.assertTrue(build_log_path("C:/Games/SC", "LIVE").endswith("LIVE\\Game.log") or build_log_path("C:/Games/SC", "LIVE").endswith("LIVE/Game.log"))

    def test_build_log_path_when_game_dir_already_points_to_channel(self) -> None:
        path = build_log_path("D:/RSI/StarCitizen/LIVE", "LIVE")
        self.assertFalse("LIVE/LIVE/Game.log" in path.replace("\\", "/"))
        self.assertTrue(path.replace("\\", "/").endswith("LIVE/Game.log"))


if __name__ == "__main__":
    unittest.main()
