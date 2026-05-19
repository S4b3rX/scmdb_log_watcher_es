"""First-run installation wizard for SCMDB Log Watcher."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from scmdb_watcher.config import resolve_base_dir, resolve_config_path
from scmdb_watcher.gui_i18n import get_available_language_codes
from scmdb_watcher.validators import (
    LANGUAGE_OPTIONS,
    VALID_CHANNELS,
    normalize_channel,
    normalize_language,
    validate_game_install_dir,
)


class InstallerWizard(QDialog):
    def __init__(self) -> None:
        app = QApplication.instance()
        self._owns_app = app is None
        self.app = app or QApplication(sys.argv)
        super().__init__()
        self.setWindowTitle("SCMDB Watcher - Instalacion")
        self.setModal(True)
        self.setFixedSize(700, 420)

        self.base_dir = resolve_base_dir(__file__)
        self.config_path = resolve_config_path(__file__)
        self.exit_code = 1

        self._build_ui()
        self._apply_theme()
        self._center_on_screen()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        hero = QFrame(self)
        hero.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(18, 18, 18, 18)
        hero_layout.setSpacing(6)

        self.lbl_chip = QLabel("INITIAL LINK")
        self.lbl_chip.setObjectName("chip")
        hero_layout.addWidget(self.lbl_chip, 0, Qt.AlignmentFlag.AlignLeft)

        self.lbl_title = QLabel("Asistente de instalacion")
        self.lbl_title.setObjectName("title")
        hero_layout.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel(
            "Define las opciones iniciales del watcher. Luego podras cambiarlas desde la interfaz principal."
        )
        self.lbl_subtitle.setWordWrap(True)
        self.lbl_subtitle.setObjectName("subtitle")
        hero_layout.addWidget(self.lbl_subtitle)
        root.addWidget(hero)

        form_card = QFrame(self)
        form_card.setObjectName("panelCard")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)
        form_layout.setColumnStretch(1, 1)

        self.lbl_game_dir = QLabel("Carpeta StarCitizen")
        form_layout.addWidget(self.lbl_game_dir, 0, 0)
        self.ent_game_dir = QLineEdit()
        self.ent_game_dir.setPlaceholderText("C:/Program Files/Roberts Space Industries/StarCitizen")
        form_layout.addWidget(self.ent_game_dir, 0, 1)
        self.btn_browse = QPushButton("Seleccionar...")
        self.btn_browse.clicked.connect(self._browse_folder)
        self.btn_browse.setFixedWidth(120)
        form_layout.addWidget(self.btn_browse, 0, 2)

        self.lbl_channel = QLabel("Canal")
        form_layout.addWidget(self.lbl_channel, 1, 0)
            self.lbl_language = QLabel("Idioma interfaz")
            form_layout.addWidget(self.lbl_language, 1, 0)
            self.cmb_language = QComboBox()
            self.cmb_language.addItems(list(get_available_language_codes(__file__) or LANGUAGE_OPTIONS))
            self.cmb_language.setCurrentText("es-es")
            self.cmb_language.setFixedWidth(150)
            form_layout.addWidget(self.cmb_language, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        form_layout.addWidget(self.lbl_language, 2, 0)
        self.cmb_language = QComboBox()
                "Puedes seleccionar la carpeta base de StarCitizen o directamente la carpeta LIVE. El watcher solo trabaja con LIVE."
        self.cmb_language.setCurrentText("es-es")
        self.cmb_language.setFixedWidth(150)
        form_layout.addWidget(self.cmb_language, 2, 1, alignment=Qt.AlignmentFlag.AlignLeft)
            form_layout.addWidget(self.lbl_note, 2, 0, 1, 3)
        self.lbl_note = QLabel(
            "Puedes seleccionar la carpeta base de StarCitizen o directamente la carpeta LIVE/HOTFIX."
        )
        self.lbl_note.setWordWrap(True)
        self.lbl_note.setObjectName("note")
        form_layout.addWidget(self.lbl_note, 3, 0, 1, 3)
        root.addWidget(form_card)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self._cancel)
        actions.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Guardar y continuar")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(self._save)
        actions.addWidget(self.btn_save)
        root.addLayout(actions)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #07131c, stop:0.45 #0b1d2a, stop:1 #10283a);
                color: #d8ecf5;
                font-family: Segoe UI;
            }
            QFrame#heroCard, QFrame#panelCard {
                background-color: rgba(7, 19, 28, 0.86);
                border: 1px solid rgba(116, 212, 255, 0.22);
                border-radius: 18px;
            }
            QLabel#chip {
                color: #0a141a;
                background-color: #78e6ff;
                border-radius: 10px;
                padding: 4px 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#title {
                font-size: 20pt;
                font-weight: 700;
                color: #f3fbff;
            }
            QLabel#subtitle {
                color: #8fb8c9;
                font-size: 10.5pt;
            }
            QLabel#note {
                color: #7ca2b2;
            }
            QLabel {
                color: #d8ecf5;
            }
            QLineEdit, QComboBox {
                background-color: rgba(6, 14, 20, 0.88);
                border: 1px solid rgba(116, 212, 255, 0.22);
                border-radius: 10px;
                padding: 8px 10px;
                color: #f3fbff;
                selection-background-color: #1497c9;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid rgba(120, 230, 255, 0.72);
            }
            QPushButton {
                background-color: rgba(10, 26, 36, 0.92);
                border: 1px solid rgba(116, 212, 255, 0.26);
                border-radius: 12px;
                color: #d8ecf5;
                padding: 9px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                border: 1px solid rgba(120, 230, 255, 0.74);
                background-color: rgba(13, 36, 49, 0.96);
            }
            QPushButton#primaryButton {
                background-color: #78e6ff;
                color: #07202b;
                border: 1px solid #9af0ff;
            }
            QPushButton#primaryButton:hover {
                background-color: #9df0ff;
            }
            """
        )

    def _center_on_screen(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        frame = self.frameGeometry()
        frame.moveCenter(screen.availableGeometry().center())
        self.move(frame.topLeft())

    def _browse_folder(self) -> None:
        try:
            selected = QFileDialog.getExistingDirectory(
                self,
                "Selecciona carpeta StarCitizen o carpeta LIVE/HOTFIX",
                str(self.base_dir),
            )
            if not selected:
                return
            selected_path = Path(selected)
            folder_name = selected_path.name.upper()
            if folder_name in VALID_CHANNELS:
                if folder_name == "LIVE":
                    self.ent_game_dir.setText(str(selected_path))
                else:
                    self.ent_game_dir.setText(str(selected_path.parent))
            else:
                self.ent_game_dir.setText(str(selected_path))
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Error al seleccionar carpeta: {exc}")

    def _save(self) -> None:
        valid, game_dir_or_reason = validate_game_install_dir(self.ent_game_dir.text().strip())
        if not valid:
            QMessageBox.critical(self, "Falta ruta", "Selecciona la carpeta de instalacion de StarCitizen.")
            return
        game_dir = game_dir_or_reason

        channel = "LIVE"
        language = normalize_language(self.cmb_language.currentText())

        payload = {
            "game_install_dir": game_dir,
            "channel": "LIVE",
            "language": language,
        }
        self.config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.exit_code = 0
        self.accept()

    def _cancel(self) -> None:
        self.reject()


def main() -> int:
    wizard = InstallerWizard()
    wizard.show()
    wizard.app.exec()
    return wizard.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
