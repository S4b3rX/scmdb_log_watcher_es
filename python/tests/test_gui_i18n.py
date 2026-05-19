from __future__ import annotations

import unittest

from scmdb_watcher.gui_i18n import tr


class GuiI18nTests(unittest.TestCase):
    def test_tr_known_key_es(self) -> None:
        self.assertEqual(tr("es-es", "btn_start"), "Iniciar")

    def test_tr_known_key_en(self) -> None:
        self.assertEqual(tr("en-en", "btn_start"), "Start")

    def test_tr_known_key_fr_with_alias(self) -> None:
        self.assertEqual(tr("fr", "btn_stop"), "Deconnecter")

    def test_tr_fallback_language(self) -> None:
        self.assertEqual(tr("xx-yy", "btn_stop"), "Desconectar")

    def test_tr_with_kwargs(self) -> None:
        self.assertEqual(tr("en-en", "status_ok", version="1.2.3"), "Status: connected and running (v1.2.3)")


if __name__ == "__main__":
    unittest.main()
