"""Presentation helpers for Watcher GUI widgets."""

from __future__ import annotations


def _set_text(widget, text: str) -> None:
    if hasattr(widget, "configure"):
        widget.configure(text=text)
        return
    if hasattr(widget, "setText"):
        widget.setText(text)


def apply_language_to_widgets(gui) -> None:
    gui.title(gui.tr("window_title"))
    _set_text(gui.lbl_title, gui.tr("window_title"))
    _set_text(gui.lbl_subtitle, gui.tr("subtitle"))
    if hasattr(gui, "lbl_chip"):
        _set_text(gui.lbl_chip, gui.tr("hero_chip"))
    if hasattr(gui, "lbl_chip_status"):
        _set_text(gui.lbl_chip_status, gui.tr("hero_chip_status"))
    if hasattr(gui, "lbl_hero_hint"):
        _set_text(gui.lbl_hero_hint, gui.tr("hero_hint"))
    if hasattr(gui, "lbl_config_section"):
        _set_text(gui.lbl_config_section, gui.tr("config_section_title"))
    if hasattr(gui, "lbl_game_dir"):
        _set_text(gui.lbl_game_dir, gui.tr("settings_game_dir"))
    if hasattr(gui, "lbl_backup_count"):
        _set_text(gui.lbl_backup_count, gui.tr("settings_backup_count"))
    if hasattr(gui, "lbl_language"):
        _set_text(gui.lbl_language, gui.tr("settings_language"))
    if hasattr(gui, "chk_auto"):
        _set_text(gui.chk_auto, gui.tr("auto_start_label"))
    _set_text(gui.btn_start, gui.tr("btn_start"))
    _set_text(gui.btn_stop, gui.tr("btn_stop"))
    if hasattr(gui, "btn_reload"):
        _set_text(gui.btn_reload, gui.tr("btn_reload"))
    _set_text(gui.btn_import, gui.tr("btn_import"))
    if hasattr(gui, "btn_run_tests"):
        _set_text(gui.btn_run_tests, gui.tr("btn_run_tests"))
    _set_text(gui.btn_tray, gui.tr("btn_tray"))
    _set_text(gui.btn_settings, gui.tr("btn_settings"))
    if hasattr(gui, "btn_save_config"):
        _set_text(gui.btn_save_config, gui.tr("settings_save"))
    if hasattr(gui, "btn_open_runtime"):
        _set_text(gui.btn_open_runtime, gui.tr("btn_open_runtime"))
    if hasattr(gui, "btn_browse_game_dir"):
        _set_text(gui.btn_browse_game_dir, gui.tr("settings_browse"))
    if hasattr(gui, "txt_summary"):
        _set_text(gui.txt_summary, gui.tr("ui_summary"))
    if hasattr(gui, "lbl_status_hint"):
        _set_text(gui.lbl_status_hint, gui.tr("ui_summary"))
    if hasattr(gui, "frm_tests"):
        _set_text(gui.frm_tests, gui.tr("tests_groups_title"))
    if hasattr(gui, "btn_open_releases"):
        _set_text(gui.btn_open_releases, gui.tr("btn_open_releases"))
    if hasattr(gui, "lbl_help"):
        _set_text(gui.lbl_help, gui.tr("help"))
    gui._refresh_path_text()


def build_status_text(gui, status_key: str, version: str) -> str:
    if status_key == "status_ok":
        if not version:
            return gui.tr("status_ok_no_version")
        return gui.tr("status_ok", version=version)
    return gui.tr(status_key)
