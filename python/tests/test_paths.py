from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scmdb_watcher.paths import DEFAULT_LOG_PATH_FALLBACK, resolve_default_log_path, resolve_log_path_from_config


class PathsTests(unittest.TestCase):
    def test_resolve_log_path_from_config_explicit(self) -> None:
        cfg = {"log_path": r"C:\Games\StarCitizen\LIVE\Game.log"}
        self.assertEqual(resolve_log_path_from_config(cfg), Path(r"C:\Games\StarCitizen\LIVE\Game.log"))

    def test_resolve_log_path_from_config_from_install_dir(self) -> None:
        cfg = {"game_install_dir": r"C:\Games\StarCitizen", "channel": "HOTFIX"}
        self.assertEqual(
            resolve_log_path_from_config(cfg),
            Path(r"C:\Games\StarCitizen") / "LIVE" / "Game.log",
        )

    def test_resolve_log_path_from_config_relative_log_path_uses_install_root(self) -> None:
        cfg = {
            "game_install_dir": r"D:\RSI\StarCitizen\LIVE",
            "channel": "LIVE",
            "log_path": r"LIVE\Game.log",
        }
        self.assertEqual(
            resolve_log_path_from_config(cfg),
            Path(r"D:\RSI\StarCitizen\LIVE\Game.log"),
        )

    def test_resolve_log_path_from_config_relative_filename_uses_channel_dir(self) -> None:
        cfg = {
            "game_install_dir": r"D:\RSI\StarCitizen",
            "channel": "HOTFIX",
            "log_path": "Game.log",
        }
        self.assertEqual(
            resolve_log_path_from_config(cfg),
            Path(r"D:\RSI\StarCitizen\LIVE\Game.log"),
        )

    def test_resolve_log_path_from_config_hotfix_dir_is_redirected_to_live(self) -> None:
        cfg = {"game_install_dir": r"D:\RSI\StarCitizen\HOTFIX", "channel": "HOTFIX"}
        self.assertEqual(
            resolve_log_path_from_config(cfg),
            Path(r"D:\RSI\StarCitizen\LIVE\Game.log"),
        )

    def test_resolve_log_path_from_config_prefers_install_dir_over_explicit_log_path(self) -> None:
        cfg = {
            "game_install_dir": r"D:\RSI\StarCitizen\LIVE",
            "channel": "LIVE",
            "log_path": r"Z:\Wrong\Game.log",
        }
        self.assertEqual(
            resolve_log_path_from_config(cfg),
            Path(r"D:\RSI\StarCitizen\LIVE\Game.log"),
        )

    def test_resolve_default_log_path_uses_env_override(self) -> None:
        resolved = resolve_default_log_path(
            __file__,
            env={"SCMDB_WATCHER_LOG_PATH": r"E:\SC\LIVE\Game.log"},
            scan_all_drives=False,
            preferred_roots=(),
        )
        self.assertEqual(resolved, Path(r"E:\SC\LIVE\Game.log"))

    def test_resolve_default_log_path_uses_runtime_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_file = root / "anchor.py"
            script_file.write_text("# anchor", encoding="utf-8")
            runtime = root / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            cfg_path = runtime / "watcher-config.json"
            cfg_path.write_text(json.dumps({"log_path": r"D:\RSI\StarCitizen\LIVE\Game.log"}), encoding="utf-8")

            resolved = resolve_default_log_path(
                script_file,
                env={},
                scan_all_drives=False,
                preferred_roots=(),
            )
            self.assertEqual(resolved, Path(r"D:\RSI\StarCitizen\LIVE\Game.log"))

    def test_resolve_default_log_path_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script_file = Path(tmp) / "anchor.py"
            script_file.write_text("# anchor", encoding="utf-8")
            resolved = resolve_default_log_path(
                script_file,
                env={},
                scan_all_drives=False,
                preferred_roots=(),
            )
            self.assertEqual(resolved, DEFAULT_LOG_PATH_FALLBACK)


if __name__ == "__main__":
    unittest.main()
