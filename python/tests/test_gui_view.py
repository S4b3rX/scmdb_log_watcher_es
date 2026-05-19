from __future__ import annotations

import unittest

from scmdb_watcher.gui_view import apply_language_to_widgets, build_status_text


class _DummyWidget:
    def __init__(self) -> None:
        self.text = ""

    def configure(self, **kwargs) -> None:
        self.text = kwargs.get("text", self.text)


class _DummyGui:
    def __init__(self) -> None:
        self._title = ""
        self.lbl_title = _DummyWidget()
        self.lbl_subtitle = _DummyWidget()
        self.lbl_game_dir = _DummyWidget()
        self.lbl_backup_count = _DummyWidget()
        self.lbl_language = _DummyWidget()
        self.chk_auto = _DummyWidget()
        self.btn_start = _DummyWidget()
        self.btn_stop = _DummyWidget()
        self.btn_reload = _DummyWidget()
        self.btn_import = _DummyWidget()
        self.btn_tray = _DummyWidget()
        self.btn_settings = _DummyWidget()
        self.btn_save_config = _DummyWidget()
        self.btn_open_runtime = _DummyWidget()
        self.btn_browse_game_dir = _DummyWidget()
        self.txt_summary = _DummyWidget()
        self.btn_open_releases = _DummyWidget()
        self.lbl_help = _DummyWidget()
        self.refreshed = False

    def tr(self, key: str, **kwargs) -> str:
        if key == "status_ok":
            return f"ok {kwargs.get('version', '')}"
        if key == "status_ok_no_version":
            return "ok no version"
        return key

    def title(self, text: str) -> None:
        self._title = text

    def _refresh_path_text(self) -> None:
        self.refreshed = True


class GuiViewTests(unittest.TestCase):
    def test_apply_language_to_widgets(self) -> None:
        gui = _DummyGui()
        apply_language_to_widgets(gui)
        self.assertEqual(gui._title, "window_title")
        self.assertEqual(gui.lbl_title.text, "window_title")
        self.assertEqual(gui.btn_start.text, "btn_start")
        self.assertTrue(gui.refreshed)

    def test_build_status_text_ok(self) -> None:
        gui = _DummyGui()
        self.assertEqual(build_status_text(gui, "status_ok", "9.9.9"), "ok 9.9.9")

    def test_build_status_text_non_ok(self) -> None:
        gui = _DummyGui()
        self.assertEqual(build_status_text(gui, "status_wait_conn", "unused"), "status_wait_conn")

    def test_build_status_text_ok_without_version(self) -> None:
        gui = _DummyGui()
        self.assertEqual(build_status_text(gui, "status_ok", ""), "ok no version")


if __name__ == "__main__":
    unittest.main()
