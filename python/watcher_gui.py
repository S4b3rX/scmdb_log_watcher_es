"""SCMDB Watcher GUI launcher with PySide6 tray, settings and language selector."""

from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QCloseEvent, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from scmdb_watcher.app_logging import install_global_exception_hooks, setup_app_file_logger
from scmdb_watcher.config import IMPORTS_DIR_NAME, load_config, resolve_base_dir, resolve_runtime_dir, save_config
from scmdb_watcher.gui_controller import (
    check_watcher_health,
    launch_watcher_process,
    resolve_start_command,
    run_import_process,
    terminate_watcher_process,
)
from scmdb_watcher.gui_i18n import get_available_language_codes, tr as tr_text
from scmdb_watcher.paths import resolve_log_path_from_config
from scmdb_watcher.gui_settings import build_settings_save_result
from scmdb_watcher.gui_status import decide_poll_status
from scmdb_watcher.gui_view import apply_language_to_widgets, build_status_text
from scmdb_watcher.process_service import force_cleanup_orphan_watchers, is_game_running, resolve_import_command
from scmdb_watcher.startup_checklist import run_startup_checklist
from scmdb_watcher.test_groups_service import DEFAULT_TEST_GROUPS, run_test_groups
from scmdb_watcher.validators import normalize_language

DEFAULT_PORT = 23456


class _MainThreadInvoker(QObject):
    invoke = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.invoke.connect(self._run, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def _run(self, callback) -> None:
        callback()


def _qt_parent(parent):
    if parent is None:
        return None
    if hasattr(parent, "window"):
        return parent.window
    return parent


def _get_main_thread_invoker(app: QObject) -> _MainThreadInvoker:
    invoker = getattr(app, "_main_thread_invoker", None)
    if invoker is None:
        invoker = _MainThreadInvoker(app)
        setattr(app, "_main_thread_invoker", invoker)
    return invoker


def _invoke_later(callback) -> None:
    app = QApplication.instance()
    if app is None:
        callback()
        return
    _get_main_thread_invoker(app).invoke.emit(callback)


def _set_enabled(widget, enabled: bool) -> None:
    if hasattr(widget, "setEnabled"):
        widget.setEnabled(enabled)
        return
    if hasattr(widget, "configure"):
        widget.configure(state="normal" if enabled else "disabled")


def _set_label_color(widget, color: str) -> None:
    if hasattr(widget, "setStyleSheet"):
        widget.setStyleSheet(f"color: {color};")
        return
    if hasattr(widget, "configure"):
        widget.configure(foreground=color)


class messagebox:
    @staticmethod
    def showinfo(title: str, text: str, parent=None) -> None:
        QMessageBox.information(_qt_parent(parent), title, text)

    @staticmethod
    def showerror(title: str, text: str, parent=None) -> None:
        QMessageBox.critical(_qt_parent(parent), title, text)

    @staticmethod
    def askyesno(title: str, text: str, parent=None) -> bool:
        result = QMessageBox.question(
            _qt_parent(parent),
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes


class filedialog:
    @staticmethod
    def askopenfilename(*, title: str, initialdir: str, filetypes=None, parent=None) -> str:
        selected, _ = QFileDialog.getOpenFileName(_qt_parent(parent), title, initialdir)
        return selected

    @staticmethod
    def askdirectory(*, title: str, initialdir: str, parent=None) -> str:
        return QFileDialog.getExistingDirectory(_qt_parent(parent), title, initialdir)


class SingleInstanceLock:
    ERROR_ALREADY_EXISTS = 183

    def __init__(self, mutex_name: str) -> None:
        self.mutex_name = mutex_name
        self._handle = None

    def acquire(self) -> bool:
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        handle = kernel32.CreateMutexW(None, False, self.mutex_name)
        if not handle:
            return False
        self._handle = handle
        return kernel32.GetLastError() != self.ERROR_ALREADY_EXISTS

    def release(self) -> None:
        if self._handle:
            ctypes.windll.kernel32.CloseHandle(self._handle)
            self._handle = None


class _StatusDot(QWidget):
    def __init__(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(QSize(18, 18))

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(QColor("#202020"))
        painter.drawEllipse(2, 2, 14, 14)


class _MainWindow(QMainWindow):
    def __init__(self, owner) -> None:
        super().__init__()
        self._owner = owner
        self._drag_offset: QPoint | None = None
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._owner.on_close():
            event.accept()
            return
        event.ignore()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = None
            event.accept()
            return
        super().mouseReleaseEvent(event)


class _SettingsDialog(QDialog):
    def __init__(self, owner, force: bool) -> None:
        super().__init__(owner.window)
        self._force = force

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._force:
            event.ignore()
            return
        super().closeEvent(event)


class WatcherGui:
    def __init__(self) -> None:
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        _get_main_thread_invoker(self.app)

        self.script_dir = resolve_base_dir(__file__)
        self.runtime_dir = resolve_runtime_dir(__file__)
        self.log, self.log_file = setup_app_file_logger(self.runtime_dir, prefix="gui", level=logging.INFO)
        install_global_exception_hooks(self.log)

        self.config_data = self._load_config()
        self.proc: subprocess.Popen | None = None
        self._tray_icon: QSystemTrayIcon | None = None
        self._tray_available = False
        self._close_hint_shown = False
        self._exiting = False
        self._tests_running = False
        self._watcher_start_time: float | None = None
        self._test_window: QDialog | None = None
        self._settings_dialog: QDialog | None = None
        self._test_status_widgets: dict[str, QLabel] = {}
        self._test_mark_widgets: dict[str, QLabel] = {}
        self._test_summary_label: QLabel | None = None
        self._group_status: dict[str, str] = {group.key: "idle" for group in DEFAULT_TEST_GROUPS}

        self.language = self._normalized_language(str(self.config_data.get("language", "es-es")))
        self.status_text = self.tr("status_stopped")
        self.path_text = ""

        self.window = _MainWindow(self)
        self.window.setWindowTitle(self.tr("window_title"))

        self.log.info("GUI started. script_dir=%s runtime_dir=%s", self.script_dir, self.runtime_dir)
        self.log.info("GUI log file: %s", self.log_file)

        self._build_ui()
        self._apply_theme()
        self._apply_config_to_inputs()
        self._fit_main_window()
        self._center_window(self.window)
        self._ensure_configured_on_first_run()
        self._refresh_path_text()
        self._setup_tray_if_available()
        self._set_status(self.tr("status_stopped"), "#c62828")

        self.after(1200, self._poll_status)
        self.after(300, self._run_startup_checklist_async)

    def title(self, text: str) -> None:
        self.window.setWindowTitle(text)

    def after(self, ms: int, callback) -> None:
        QTimer.singleShot(ms, callback)

    def destroy(self) -> None:
        self.window.close()

    def show(self) -> None:
        self.window.show()

    def mainloop(self) -> int:
        return self.app.exec()

    def tr(self, key: str, **kwargs) -> str:
        return tr_text(self.language, key, **kwargs)

    def _normalized_language(self, value: str) -> str:
        return normalize_language(value)

    def _build_ui(self) -> None:
        central = QWidget(self.window)
        self.window.setCentralWidget(central)
        self.window.setObjectName("watcherWindow")

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        hero_card = QFrame(self.window)
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(18, 18, 18, 18)
        hero_layout.setSpacing(8)

        hero_top = QHBoxLayout()
        hero_top.setSpacing(10)

        self.lbl_chip = QLabel(self.tr("hero_chip"))
        self.lbl_chip.setObjectName("chip")
        hero_top.addWidget(self.lbl_chip, 0, Qt.AlignmentFlag.AlignLeft)

        self.lbl_chip_status = QLabel(self.tr("hero_chip_status"))
        self.lbl_chip_status.setObjectName("chipGhost")
        hero_top.addWidget(self.lbl_chip_status, 0, Qt.AlignmentFlag.AlignLeft)
        hero_top.addStretch(1)

        self.btn_minimize = QPushButton("_")
        self.btn_minimize.setObjectName("windowButton")
        self.btn_minimize.setFixedSize(34, 30)
        self.btn_minimize.clicked.connect(self.window.showMinimized)
        hero_top.addWidget(self.btn_minimize, 0, Qt.AlignmentFlag.AlignRight)

        self.btn_close_window = QPushButton("X")
        self.btn_close_window.setObjectName("windowCloseButton")
        self.btn_close_window.setFixedSize(34, 30)
        self.btn_close_window.clicked.connect(self.window.close)
        hero_top.addWidget(self.btn_close_window, 0, Qt.AlignmentFlag.AlignRight)
        hero_layout.addLayout(hero_top)

        self.lbl_title = QLabel(self.tr("window_title"))
        self.lbl_title.setObjectName("heroTitle")
        hero_layout.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel(self.tr("subtitle"))
        self.lbl_subtitle.setWordWrap(True)
        self.lbl_subtitle.setObjectName("heroSubtitle")
        hero_layout.addWidget(self.lbl_subtitle)

        self.lbl_hero_hint = QLabel(self.tr("hero_hint"))
        self.lbl_hero_hint.setObjectName("heroHint")
        self.lbl_hero_hint.setWordWrap(True)
        hero_layout.addWidget(self.lbl_hero_hint)
        root.addWidget(hero_card)

        status_card = QFrame(self.window)
        status_card.setObjectName("statusCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(16, 14, 16, 14)
        status_layout.setSpacing(10)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        self.indicator = _StatusDot("#c62828", self.window)
        self.lbl_status = QLabel(self.status_text)
        self.lbl_status.setObjectName("statusLabel")
        status_row.addWidget(self.indicator, 0, Qt.AlignmentFlag.AlignLeft)
        status_row.addWidget(self.lbl_status, 1)
        self.lbl_status_hint = QLabel(self.tr("ui_summary"))
        self.lbl_status_hint.setObjectName("statusHint")
        self.lbl_status_hint.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        status_row.addWidget(self.lbl_status_hint, 0)
        status_layout.addLayout(status_row)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.btn_start = QPushButton(self.tr("btn_start"))
        self.btn_start.setObjectName("primaryAction")
        self.btn_start.clicked.connect(self.start_watcher)
        self.btn_start.setFixedWidth(100)
        actions.addWidget(self.btn_start)

        self.btn_stop = QPushButton(self.tr("btn_stop"))
        self.btn_stop.setObjectName("dangerAction")
        self.btn_stop.clicked.connect(self.stop_watcher)
        self.btn_stop.setFixedWidth(100)
        actions.addWidget(self.btn_stop)

        self.btn_reload = QPushButton(self.tr("btn_reload"))
        self.btn_reload.clicked.connect(self._reload_inline_config)
        self.btn_reload.setFixedWidth(100)
        actions.addWidget(self.btn_reload)

        self.btn_settings = QPushButton(self.tr("btn_settings"))
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_settings.setFixedWidth(40)
        actions.addWidget(self.btn_settings)
        status_layout.addLayout(actions)
        root.addWidget(status_card)

        config_card = QFrame(self.window)
        config_card.setObjectName("panelCard")
        config_root = QVBoxLayout(config_card)
        config_root.setContentsMargins(18, 16, 18, 16)
        config_root.setSpacing(10)

        self.lbl_config_section = QLabel(self.tr("config_section_title"))
        self.lbl_config_section.setObjectName("sectionLabel")
        config_root.addWidget(self.lbl_config_section)

        form = QGridLayout()
        form.setColumnStretch(1, 1)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self.lbl_game_dir = QLabel(self.tr("settings_game_dir"))
        form.addWidget(self.lbl_game_dir, 0, 0)
        self.ent_game_dir = QLineEdit()
        self.ent_game_dir.setPlaceholderText("C:/Program Files/Roberts Space Industries/StarCitizen")
        form.addWidget(self.ent_game_dir, 0, 1)
        self.btn_browse_game_dir = QPushButton(self.tr("settings_browse"))
        self.btn_browse_game_dir.clicked.connect(lambda: self._browse_game_folder(self.ent_game_dir))
        self.btn_browse_game_dir.setFixedWidth(110)
        form.addWidget(self.btn_browse_game_dir, 0, 2)

        self.lbl_backup_count = QLabel(self.tr("settings_backup_count"))
        form.addWidget(self.lbl_backup_count, 1, 0)
        self.lbl_backup_count_value = QLabel("0")
        self.lbl_backup_count_value.setObjectName("chipGhost")
        form.addWidget(self.lbl_backup_count_value, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)

        self.lbl_language = QLabel(self.tr("settings_language"))
        form.addWidget(self.lbl_language, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        self.cmb_language = QComboBox()
        self.cmb_language.addItems(list(get_available_language_codes(__file__)))
        self.cmb_language.setFixedWidth(120)
        form.addWidget(self.cmb_language, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)
        config_root.addLayout(form)
        root.addWidget(config_card)

        footer_card = QFrame(self.window)
        footer_card.setObjectName("footerCard")
        footer = QHBoxLayout(footer_card)
        footer.setContentsMargins(16, 14, 16, 14)
        footer.setSpacing(10)
        self.btn_open_runtime = QPushButton(self.tr("btn_open_runtime"))
        self.btn_open_runtime.clicked.connect(self._open_runtime_dir)
        footer.addWidget(self.btn_open_runtime)
        footer.addStretch(1)

        if not bool(getattr(sys, "frozen", False)):
            self.btn_run_tests = QPushButton(self.tr("btn_run_tests"))
            self.btn_run_tests.clicked.connect(self._on_run_tests_clicked)
            footer.addWidget(self.btn_run_tests)

        self.btn_tray = QPushButton(self.tr("btn_tray"))
        self.btn_tray.clicked.connect(self._hide_to_tray)
        footer.addWidget(self.btn_tray)

        self.btn_import = QPushButton(self.tr("btn_import"))
        self.btn_import.clicked.connect(self.run_import)
        footer.addWidget(self.btn_import)

        self.btn_save_config = QPushButton(self.tr("settings_save"))
        self.btn_save_config.setObjectName("primaryAction")
        self.btn_save_config.clicked.connect(self._save_inline_config)
        footer.addWidget(self.btn_save_config)
        root.addWidget(footer_card)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(separator)

        self.lbl_path = QLabel("")
        self.lbl_path.setWordWrap(True)
        root.addWidget(self.lbl_path)

        self.txt_summary = QLabel(self.tr("ui_summary"))
        self.txt_summary.setWordWrap(True)
        self.txt_summary.setObjectName("summaryLabel")
        self.txt_summary.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        root.addWidget(self.txt_summary)

    def _apply_theme(self) -> None:
        self.window.setStyleSheet(
            """
            QMainWindow#watcherWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #050c12, stop:0.42 #0b1a24, stop:1 #102838);
                color: #dceef7;
                font-family: Segoe UI;
            }
            QFrame#heroCard, QFrame#statusCard, QFrame#panelCard, QFrame#footerCard {
                background-color: rgba(7, 19, 28, 0.84);
                border: 1px solid rgba(116, 212, 255, 0.22);
                border-radius: 18px;
            }
            QFrame#heroCard {
                background-color: rgba(8, 23, 34, 0.92);
                border: 1px solid rgba(120, 230, 255, 0.34);
            }
            QLabel#chip {
                color: #08202a;
                background-color: #78e6ff;
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 9pt;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#chipGhost {
                color: #8fc9d9;
                background-color: rgba(14, 37, 49, 0.85);
                border: 1px solid rgba(116, 212, 255, 0.18);
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 9pt;
                font-weight: 600;
                letter-spacing: 1px;
            }
            QLabel#heroTitle {
                color: #f5fbff;
                font-size: 20pt;
                font-weight: 700;
            }
            QLabel#heroSubtitle {
                color: #89b6c8;
                font-size: 10.5pt;
            }
            QLabel#heroHint {
                color: #b5d9e7;
                background-color: rgba(9, 28, 39, 0.72);
                border-left: 3px solid rgba(120, 230, 255, 0.72);
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 9.6pt;
            }
            QLabel#statusLabel {
                color: #f2fbff;
                font-size: 12pt;
                font-weight: 700;
            }
            QLabel#statusHint, QLabel#summaryLabel {
                color: #7ea7b7;
            }
            QLabel#sectionLabel {
                color: #78e6ff;
                font-size: 9pt;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel {
                color: #dceef7;
            }
            QLineEdit, QComboBox {
                background-color: rgba(5, 13, 19, 0.92);
                border: 1px solid rgba(116, 212, 255, 0.24);
                border-radius: 11px;
                padding: 8px 10px;
                color: #f4fbff;
                selection-background-color: #1f8fb7;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid rgba(120, 230, 255, 0.76);
            }
            QPushButton {
                background-color: rgba(10, 24, 33, 0.94);
                border: 1px solid rgba(116, 212, 255, 0.22);
                border-radius: 12px;
                color: #dceef7;
                padding: 9px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(14, 37, 49, 0.98);
                border: 1px solid rgba(120, 230, 255, 0.8);
            }
            QPushButton:pressed {
                padding-top: 10px;
                padding-bottom: 8px;
            }
            QPushButton#primaryAction {
                background-color: #78e6ff;
                color: #07212d;
                border: 1px solid #a0f2ff;
            }
            QPushButton#primaryAction:hover {
                background-color: #9ef1ff;
            }
            QPushButton#windowButton, QPushButton#windowCloseButton {
                background-color: rgba(10, 24, 33, 0.86);
                border: 1px solid rgba(116, 212, 255, 0.18);
                border-radius: 10px;
                color: #dceef7;
                padding: 0px;
                font-size: 11pt;
                font-weight: 700;
            }
            QPushButton#windowButton:hover {
                background-color: rgba(14, 37, 49, 0.98);
                border: 1px solid rgba(120, 230, 255, 0.8);
            }
            QPushButton#windowCloseButton:hover {
                background-color: rgba(95, 18, 27, 0.95);
                border: 1px solid rgba(255, 165, 175, 0.74);
                color: #ffd8de;
            }
            QPushButton#dangerAction {
                background-color: rgba(73, 12, 18, 0.92);
                border: 1px solid rgba(255, 132, 145, 0.36);
                color: #ffd8de;
            }
            QPushButton#dangerAction:hover {
                background-color: rgba(95, 18, 27, 0.95);
                border: 1px solid rgba(255, 165, 175, 0.74);
            }
            QFrame[frameShape="4"] {
                color: rgba(116, 212, 255, 0.16);
            }
            """
        )

    def _fit_main_window(self) -> None:
        self.window.adjustSize()
        size = self.window.sizeHint()
        width = max(780, size.width())
        height = size.height() + 10
        self.window.setFixedSize(width, height)

    def _center_window(self, window) -> None:
        screen = window.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        frame = window.frameGeometry()
        frame.moveCenter(geometry.center())
        window.move(frame.topLeft())

    def _apply_language_to_ui(self) -> None:
        apply_language_to_widgets(self)
        self._refresh_test_group_labels()
        self._fit_main_window()
        self._center_window(self.window)

    def _load_config(self) -> dict:
        return load_config(__file__)

    def _save_config(self) -> None:
        self.config_data["language"] = self.language
        self.config_data["auto_start_with_sc"] = False
        save_config(__file__, self.config_data)
        self.log.info("Configuration saved")

    def _close_action(self) -> str:
        action = str(self.config_data.get("close_action", "tray")).strip().lower()
        return action if action in {"tray", "exit"} else "tray"

    def _close_action_options(self) -> dict[str, str]:
        return {
            self.tr("close_action_tray"): "tray",
            self.tr("close_action_exit"): "exit",
        }

    def _current_game_dir(self) -> str:
        return self.ent_game_dir.text().strip()

    def _current_language(self) -> str:
        return self._normalized_language(self.cmb_language.currentText())

    def _configured_log_path(self) -> Path:
        resolved = resolve_log_path_from_config(self.config_data)
        if resolved is not None:
            return resolved

        base = Path(str(self.config_data.get("game_install_dir", "")).strip())
        if base.name.upper() == "HOTFIX":
            return base.parent / "LIVE" / "Game.log"
        if base.name.upper() == "LIVE":
            return base / "Game.log"
        return base / "LIVE" / "Game.log"

    def _count_available_backups(self) -> int:
        log_path = self._configured_log_path()
        logbackups_dir = log_path.parent / "logbackups"
        try:
            return sum(1 for _ in logbackups_dir.glob("Game Build(*).log"))
        except OSError:
            return 0

    def _refresh_path_text(self) -> None:
        self.path_text = self.tr("path_prefix", path=self._configured_log_path())
        self.lbl_path.setText(self.path_text)
        self.lbl_backup_count_value.setText(str(self._count_available_backups()))

    def _set_combo_value(self, combo: QComboBox, value: str) -> None:
        idx = combo.findText(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)
            return
        combo.addItem(value)
        combo.setCurrentIndex(combo.count() - 1)

    def _apply_config_to_inputs(self) -> None:
        self.ent_game_dir.setText(str(self.config_data.get("game_install_dir", "")).strip())
        self._set_combo_value(self.cmb_language, self._normalized_language(str(self.config_data.get("language", self.language))))

    def _save_inline_config(self) -> bool:
        result = build_settings_save_result(
            game_dir_raw=self._current_game_dir(),
            channel_raw="LIVE",
            language_raw=self._current_language(),
            auto_start=False,
            run_startup_tests=bool(self.config_data.get("run_startup_tests", False)),
        )
        if not result.ok:
            messagebox.showerror(self.tr("missing_cfg_title"), self.tr("missing_cfg_msg"), parent=self)
            return False

        self.language = result.language
        self.config_data["game_install_dir"] = result.game_dir
        self.config_data["channel"] = "LIVE"
        self.config_data["language"] = result.language
        self.config_data.pop("log_path", None)
        self._save_config()
        self._apply_config_to_inputs()
        self._apply_language_to_ui()
        self._refresh_path_text()
        self.log.info(
            "Inline settings saved: game_dir=%s channel=%s language=%s",
            result.game_dir,
            "LIVE",
            result.language,
        )
        return True

    def _reload_inline_config(self) -> None:
        self.config_data = self._load_config()
        self.language = self._normalized_language(str(self.config_data.get("language", "es-es")))
        self._apply_config_to_inputs()
        self._apply_language_to_ui()
        self._refresh_path_text()

    def _open_runtime_dir(self) -> None:
        subprocess.Popen(["explorer", str(self.runtime_dir)])

    def _ensure_configured_on_first_run(self) -> None:
        if str(self.config_data.get("game_install_dir", "")).strip():
            return
        messagebox.showinfo(self.tr("first_run_title"), self.tr("first_run_msg"), parent=self)
        self.open_settings(force=True)

    def _run_startup_checklist_async(self) -> None:
        def worker() -> None:
            try:
                result = run_startup_checklist(
                    runtime_dir=self.runtime_dir,
                    script_dir=self.script_dir,
                    config_data=self.config_data,
                    frozen=bool(getattr(sys, "frozen", False)),
                    run_tests=False,
                )
            except Exception:
                self.log.exception("Startup checklist failed")
                result = None

            def apply_result() -> None:
                if result is None:
                    self.log.warning("Startup checklist returned no result")
                    return
                details = " | ".join(result.details)
                if result.ok:
                    self.log.info("Startup checklist OK: %s", details)
                else:
                    self.log.warning("Startup checklist warnings: %s", details)

            _invoke_later(apply_result)

        threading.Thread(target=worker, daemon=True, name="startup-checklist").start()

    def _refresh_test_group_labels(self) -> None:
        for group in DEFAULT_TEST_GROUPS:
            status = self._group_status.get(group.key, "idle")
            if status == "running":
                text_status = self.tr("tests_status_running")
                color = "#ef6c00"
                mark = "..."
            elif status == "ok":
                text_status = self.tr("tests_status_ok")
                color = "#2e7d32"
                mark = "OK"
            elif status == "fail":
                text_status = self.tr("tests_status_fail")
                color = "#c62828"
                mark = "X"
            else:
                text_status = self.tr("tests_status_idle")
                color = "#777777"
                mark = "."

            if group.key in self._test_status_widgets:
                self._test_status_widgets[group.key].setText(f"{self.tr(group.key)}: {text_status}")
                _set_label_color(self._test_status_widgets[group.key], color)
            if group.key in self._test_mark_widgets:
                self._test_mark_widgets[group.key].setText(mark)
                _set_label_color(self._test_mark_widgets[group.key], color)

    def _set_test_status(self, group_key: str, status: str) -> None:
        self._group_status[group_key] = status
        self._refresh_test_group_labels()

    def _open_test_progress_window(self) -> None:
        if self._test_window is not None and self._test_window.isVisible():
            self._test_window.raise_()
            self._test_window.activateWindow()
            return

        window = QDialog(self.window)
        window.setModal(True)
        window.setWindowTitle(self.tr("tests_groups_title"))
        layout = QVBoxLayout(window)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel(self.tr("tests_report_title"))
        title.setStyleSheet("font-size: 14pt; font-weight: 700;")
        layout.addWidget(title)

        intro = QLabel(self.tr("tests_step_msg"))
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #555555;")
        layout.addWidget(intro)

        self._test_status_widgets = {}
        self._test_mark_widgets = {}
        for group in DEFAULT_TEST_GROUPS:
            row = QHBoxLayout()
            mark_lbl = QLabel(".")
            mark_lbl.setFixedWidth(24)
            status_lbl = QLabel(f"{self.tr(group.key)}: {self.tr('tests_status_idle')}")
            row.addWidget(mark_lbl)
            row.addWidget(status_lbl, 1)
            layout.addLayout(row)
            self._test_mark_widgets[group.key] = mark_lbl
            self._test_status_widgets[group.key] = status_lbl

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

        self._test_summary_label = QLabel("")
        self._test_summary_label.setWordWrap(True)
        self._test_summary_label.setStyleSheet("color: #444444;")
        layout.addWidget(self._test_summary_label)

        close_btn = QPushButton(self.tr("settings_close"))
        close_btn.clicked.connect(window.close)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

        def on_finished(_result: int) -> None:
            self._test_window = None

        window.finished.connect(on_finished)
        self._test_window = window
        window.adjustSize()
        window.setFixedSize(max(420, window.width()), window.height())
        self._center_window(window)
        self._refresh_test_group_labels()
        window.show()

    def _update_test_summary(self, text: str) -> None:
        if self._test_summary_label is not None:
            self._test_summary_label.setText(text)

    def _on_run_tests_clicked(self) -> None:
        self._open_test_progress_window()
        self._run_grouped_tests_async(from_startup=False)

    def _run_grouped_tests_async(self, from_startup: bool) -> None:
        if self._tests_running:
            return

        if bool(getattr(sys, "frozen", False)):
            self._update_test_summary(self.tr("tests_skipped_frozen"))
            self.log.info("Grouped tests skipped in frozen mode")
            return

        self._tests_running = True
        _set_enabled(self.btn_run_tests, False)
        self._update_test_summary(self.tr("tests_window_running"))
        for group in DEFAULT_TEST_GROUPS:
            self._set_test_status(group.key, "idle")

        def on_group_done(result) -> None:
            _invoke_later(lambda: self._set_test_status(result.key, "ok" if result.ok else "fail"))

        def on_group_start(group) -> None:
            _invoke_later(lambda key=group.key: self._set_test_status(key, "running"))

        def worker() -> None:
            try:
                results = run_test_groups(
                    script_dir=self.script_dir,
                    on_group_start=on_group_start,
                    on_group_done=on_group_done,
                )
            except Exception:
                self.log.exception("Grouped tests execution failed")
                results = []

            def apply_done() -> None:
                total = len(DEFAULT_TEST_GROUPS)
                passed = len([result for result in results if result.ok])
                failed = total - passed
                if results and passed == total:
                    self._update_test_summary(self.tr("tests_window_done_ok", passed=passed, total=total))
                elif results:
                    self._update_test_summary(self.tr("tests_window_done_fail", passed=passed, failed=failed, total=total))
                else:
                    self._update_test_summary(self.tr("tests_window_done_fail", passed=0, failed=total, total=total))
                self.log.info(
                    "Grouped tests finished (%s): %d/%d",
                    "startup" if from_startup else "manual",
                    passed,
                    total,
                )
                _set_enabled(self.btn_run_tests, True)
                self._tests_running = False

            _invoke_later(apply_done)

        threading.Thread(target=worker, daemon=True, name="grouped-tests").start()

    def _browse_game_folder(self, target_widget: QLineEdit) -> None:
        selected = filedialog.askdirectory(
            title=self.tr("settings_game_dir"),
            initialdir=str(self.script_dir),
            parent=self,
        )
        if selected:
            target_widget.setText(selected)

    def _dialog_is_open(self, dialog) -> bool:
        if dialog is None:
            return False
        if hasattr(dialog, "winfo_exists"):
            return bool(dialog.winfo_exists())
        if hasattr(dialog, "isVisible"):
            return bool(dialog.isVisible())
        return False

    def _is_settings_dialog_open(self) -> bool:
        return self._dialog_is_open(self._settings_dialog)

    def open_settings(self, force: bool = False) -> None:
        if self._is_settings_dialog_open():
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return

        dialog = _SettingsDialog(self, force)
        self._settings_dialog = dialog
        dialog.setWindowTitle(self.tr("settings_title"))
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        intro = QLabel(self.tr("settings_advanced_intro"))
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #555555;")
        layout.addWidget(intro)

        layout.addWidget(QLabel(self.tr("settings_close_behavior")))
        close_action_options = self._close_action_options()
        close_combo = QComboBox()
        close_combo.addItems(list(close_action_options.keys()))
        self._set_combo_value(
            close_combo,
            next(
                (label for label, value in close_action_options.items() if value == self._close_action()),
                self.tr("close_action_tray"),
            ),
        )
        close_combo.setFixedWidth(220)
        layout.addWidget(close_combo, 0, Qt.AlignmentFlag.AlignLeft)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

        button_box = QDialogButtonBox()
        save_btn = button_box.addButton(self.tr("settings_save"), QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = button_box.addButton(self.tr("settings_cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(button_box)

        def save_and_close() -> None:
            self.config_data["close_action"] = close_action_options[close_combo.currentText()]
            self._save_config()
            self.log.info(
                "Advanced settings updated: close_action=%s",
                close_action_options[close_combo.currentText()],
            )
            self._settings_dialog = None
            dialog.accept()

        def close_dialog() -> None:
            self._settings_dialog = None
            dialog.reject()

        save_btn.clicked.connect(save_and_close)
        cancel_btn.clicked.connect(close_dialog)
        dialog.finished.connect(lambda _result: setattr(self, "_settings_dialog", None))
        dialog.adjustSize()
        dialog.setFixedSize(max(520, dialog.width()), dialog.height())
        self._center_window(dialog)
        dialog.show()

    def _resolve_watcher_launch_command(self) -> list[str] | None:
        cmd, _error, _port = resolve_start_command(
            script_dir=self.script_dir,
            config_data=self.config_data,
            default_port=DEFAULT_PORT,
            frozen=bool(getattr(sys, "frozen", False)),
            log_path=str(self._configured_log_path()),
        )
        return cmd

    def _resolve_import_command(self) -> list[str] | None:
        cmd, _ = resolve_import_command(self.script_dir, bool(getattr(sys, "frozen", False)))
        return cmd

    def start_watcher(self) -> None:
        if not self._save_inline_config():
            return

        if self.proc and self.proc.poll() is None:
            self.log.info("start_watcher ignored: process already running")
            return

        force_cleanup_orphan_watchers()
        self.log.info("Requested watcher start")

        game_install_dir = str(self.config_data.get("game_install_dir", "")).strip()
        if not game_install_dir:
            self.log.warning("Cannot start watcher: missing game_install_dir")
            messagebox.showerror(self.tr("missing_cfg_title"), self.tr("missing_cfg_msg"), parent=self)
            return

        cmd, error, _selected_port = resolve_start_command(
            script_dir=self.script_dir,
            config_data=self.config_data,
            default_port=DEFAULT_PORT,
            frozen=bool(getattr(sys, "frozen", False)),
            log_path=str(self._configured_log_path()),
            parent_pid=os.getpid(),
        )
        if not cmd:
            self.log.error("Cannot start watcher: missing runtime (%s)", error or "unknown")
            if getattr(sys, "frozen", False):
                messagebox.showerror(self.tr("missing_core_title"), self.tr("missing_core_msg"), parent=self)
            else:
                messagebox.showerror(self.tr("missing_env_title"), self.tr("missing_env_msg"), parent=self)
            return

        self.proc = launch_watcher_process(cmd, self.script_dir)
        self.log.info("Watcher process launched: cmd=%s", cmd)
        self._watcher_start_time = time.monotonic()
        self._set_status(self.tr("status_starting"), "#ef6c00")
        self._toggle_buttons(running=True)

    def stop_watcher(self) -> None:
        if not self.proc or self.proc.poll() is not None:
            self.log.info("stop_watcher called but process is not running")
            self._set_status(self.tr("status_stopped"), "#c62828")
            self._toggle_buttons(running=False)
            return

        terminate_watcher_process(self.proc)
        self.log.info("Watcher process terminated")
        self._watcher_start_time = None
        self._set_status(self.tr("status_stopped"), "#c62828")
        self._toggle_buttons(running=False)

    def _toggle_buttons(self, running: bool) -> None:
        _set_enabled(self.btn_start, not running)
        _set_enabled(self.btn_stop, running)

    def _ping_ok(self) -> tuple[bool, str]:
        return check_watcher_health(self.config_data, DEFAULT_PORT)

    def _is_game_running(self) -> bool:
        return is_game_running()

    def _poll_status(self) -> None:
        try:
            running = self.proc is not None and self.proc.poll() is None
            if self._is_settings_dialog_open():
                self._toggle_buttons(running=running)
                return

            ok, version = self._ping_ok()
            starting_grace = self._watcher_start_time is not None and (time.monotonic() - self._watcher_start_time) < 3.0

            if not running:
                self._watcher_start_time = None

            if running and not ok and starting_grace:
                decision = None
            else:
                decision = decide_poll_status(
                    running=running,
                    ping_ok=ok,
                    auto_start=False,
                    game_running=False,
                )

            if decision is None:
                self._set_status(self.tr("status_starting"), "#ef6c00")
                self._toggle_buttons(running=running)
            elif decision.should_start:
                self.start_watcher()
                self._toggle_buttons(running=decision.running)
            else:
                self._set_status(build_status_text(self, decision.status_key, version), decision.color)
                self._toggle_buttons(running=decision.running)
        except Exception:
            self.log.exception("Status polling failed")
        finally:
            if not self._exiting:
                self.after(1500, self._poll_status)

    def run_import(self) -> None:
        if not self._save_inline_config():
            return

        _set_enabled(self.btn_import, False)
        self.log.info("Manual import requested")

        def worker() -> None:
            base_cmd = self._resolve_import_command()
            if not base_cmd:
                self.log.error("Import cannot start: missing runtime")
                if getattr(sys, "frozen", False):
                    _invoke_later(lambda: messagebox.showerror(self.tr("missing_core_title"), self.tr("missing_core_msg"), parent=self))
                else:
                    _invoke_later(lambda: messagebox.showerror(self.tr("missing_env_title"), self.tr("missing_env_msg"), parent=self))
                _invoke_later(lambda: _set_enabled(self.btn_import, True))
                return

            try:
                import_dir = self.runtime_dir / IMPORTS_DIR_NAME
                import_dir.mkdir(parents=True, exist_ok=True)
                output_path = import_dir / f"scmdb-import-{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                exec_result = run_import_process(
                    base_cmd,
                    self.script_dir,
                    str(self._configured_log_path()),
                    output_path=output_path,
                )
            except Exception:
                self.log.exception("Import process failed with unhandled exception")
                _invoke_later(
                    lambda: messagebox.showerror(
                        self.tr("import_ok_title"),
                        f"{self.tr('import_fail_msg')}\n\ninternal error",
                        parent=self,
                    )
                )
                _invoke_later(lambda: _set_enabled(self.btn_import, True))
                return

            if exec_result.ok:
                self.log.info("Import completed successfully. output=%s", exec_result.output_path)
                _invoke_later(lambda: self._handle_successful_import(exec_result.output_path))
            else:
                self.log.error("Import failed: %s", exec_result.error_text)
                _invoke_later(
                    lambda: messagebox.showerror(
                        self.tr("import_ok_title"),
                        f"{self.tr('import_fail_msg')}\n\n{exec_result.error_text}",
                        parent=self,
                    )
                )

            _invoke_later(lambda: _set_enabled(self.btn_import, True))

        threading.Thread(target=worker, daemon=True, name="import-runner").start()

    def _handle_successful_import(self, output_path: str) -> None:
        title = self.tr("import_ok_title")
        if not output_path:
            messagebox.showinfo(title, self.tr("import_ok_msg"), parent=self)
            return

        prompt = f"{self.tr('import_open_prompt')}\n\n{output_path}"
        open_now = messagebox.askyesno(title, prompt, parent=self)
        if not open_now:
            return

        target = Path(output_path)
        if target.exists():
            subprocess.Popen(["explorer", "/select,", str(target)])
        else:
            subprocess.Popen(["explorer", str(target.parent)])

    def _build_tray_icon(self, color: str) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(QColor("#202020"))
        painter.drawEllipse(8, 8, 48, 48)
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(22, 18, 8, 8)
        painter.end()
        return QIcon(pixmap)

    def _setup_tray_if_available(self) -> None:
        self._tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        if not self._tray_available:
            return

        menu = QMenu(self.window)
        show_action = QAction("Show", menu)
        show_action.triggered.connect(self._show_from_tray)
        menu.addAction(show_action)

        disconnect_action = QAction("Disconnect", menu)
        disconnect_action.triggered.connect(self.stop_watcher)
        menu.addAction(disconnect_action)

        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self._quit_application)
        menu.addAction(exit_action)

        self._tray_icon = QSystemTrayIcon(self._build_tray_icon("#c62828"), self.window)
        self._tray_icon.setContextMenu(menu)
        self._tray_icon.setToolTip("SCMDB Watcher")
        self._tray_icon.activated.connect(lambda reason: self._show_from_tray() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self._tray_icon.show()

    def _update_tray(self, color: str, tooltip: str) -> None:
        if self._tray_icon and self._tray_available:
            self._tray_icon.setIcon(self._build_tray_icon(color))
            self._tray_icon.setToolTip(tooltip)

    def _set_status(self, text: str, color: str) -> None:
        self.status_text = text
        if hasattr(self, "lbl_status"):
            self.lbl_status.setText(text)
        if hasattr(self, "indicator"):
            self.indicator.set_color(color)
        self._update_tray(color, text)

    def _hide_to_tray(self) -> None:
        if not self._tray_available:
            messagebox.showinfo(self.tr("tray_unavailable_title"), self.tr("tray_unavailable_msg"), parent=self)
            return
        self.window.hide()
        if not self._close_hint_shown:
            self._close_hint_shown = True
            messagebox.showinfo(self.tr("tray_hint_title"), self.tr("tray_hint_msg"), parent=self)

    def _show_from_tray(self) -> None:
        self.window.showNormal()
        self.window.activateWindow()
        self.window.raise_()

    def on_close(self) -> bool:
        if self._exiting:
            return True
        if self._close_action() == "tray" and self._tray_available:
            self._hide_to_tray()
            return False
        self._quit_application()
        return False

    def _quit_application(self) -> None:
        if self._exiting:
            return
        self._exiting = True
        self.log.info("GUI shutdown requested")
        self.stop_watcher()
        if self._tray_icon:
            self._tray_icon.hide()
        self.window.close()


def main() -> int:
    lock = SingleInstanceLock("Local\\SCMDB_LOG_WATCHER_GUI_SINGLE_INSTANCE")
    if not lock.acquire():
        return 0

    try:
        app = WatcherGui()
        app.show()
        return app.mainloop()
    finally:
        lock.release()


if __name__ == "__main__":
    raise SystemExit(main())
