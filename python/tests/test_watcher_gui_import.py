from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from watcher_gui import WatcherGui, _invoke_later


class WatcherGuiImportTests(unittest.TestCase):
    def _build_gui(self) -> WatcherGui:
        gui = WatcherGui.__new__(WatcherGui)
        messages = {
            "import_ok_title": "Importar",
            "import_ok_msg": "Importacion completada correctamente.",
            "import_open_prompt": "Importacion completada. Quieres abrir la carpeta del archivo exportado?",
        }
        gui.tr = lambda key, **kwargs: messages[key]
        gui.window = object()
        return gui

    @patch("watcher_gui.subprocess.Popen")
    @patch("watcher_gui.messagebox.askyesno", return_value=False)
    @patch("watcher_gui.messagebox.showinfo")
    def test_handle_successful_import_uses_single_prompt_when_output_exists(self, showinfo, askyesno, popen) -> None:
        gui = self._build_gui()

        gui._handle_successful_import("C:/tmp/out.json")

        showinfo.assert_not_called()
        askyesno.assert_called_once()
        self.assertIn("C:/tmp/out.json", askyesno.call_args.args[1])
        self.assertIs(askyesno.call_args.kwargs["parent"], gui)
        popen.assert_not_called()

    @patch("watcher_gui.subprocess.Popen")
    @patch("watcher_gui.messagebox.askyesno", return_value=True)
    @patch("watcher_gui.messagebox.showinfo")
    def test_handle_successful_import_opens_parent_when_target_missing(self, showinfo, askyesno, popen) -> None:
        gui = self._build_gui()
        missing_output = str(Path("C:/tmp/out.json"))

        gui._handle_successful_import(missing_output)

        showinfo.assert_not_called()
        askyesno.assert_called_once()
        popen.assert_called_once_with(["explorer", str(Path(missing_output).parent)])

    @patch("watcher_gui.subprocess.Popen")
    @patch("watcher_gui.messagebox.askyesno")
    @patch("watcher_gui.messagebox.showinfo")
    def test_handle_successful_import_shows_single_info_when_output_missing(self, showinfo, askyesno, popen) -> None:
        gui = self._build_gui()

        gui._handle_successful_import("")

        showinfo.assert_called_once_with("Importar", "Importacion completada correctamente.", parent=gui)
        askyesno.assert_not_called()
        popen.assert_not_called()

    @patch("watcher_gui.subprocess.Popen")
    @patch("watcher_gui.messagebox.askyesno", return_value=True)
    @patch("watcher_gui.messagebox.showinfo")
    def test_handle_successful_import_selects_existing_output(self, showinfo, askyesno, popen) -> None:
        gui = self._build_gui()

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.json"
            output.write_text("{}", encoding="utf-8")

            gui._handle_successful_import(str(output))

        showinfo.assert_not_called()
        askyesno.assert_called_once()
        popen.assert_called_once_with(["explorer", "/select,", str(output)])

    @patch("watcher_gui.QApplication.instance", return_value=None)
    def test_invoke_later_runs_inline_without_qt_app(self, _instance) -> None:
        called: list[str] = []

        _invoke_later(lambda: called.append("ok"))

        self.assertEqual(called, ["ok"])

    @patch("watcher_gui._get_main_thread_invoker")
    @patch("watcher_gui.QApplication.instance")
    def test_invoke_later_queues_on_main_thread_invoker(self, instance, get_invoker) -> None:
        app = object()
        emitted: list[object] = []

        instance.return_value = app
        get_invoker.return_value = SimpleNamespace(
            invoke=SimpleNamespace(emit=lambda callback: emitted.append(callback))
        )

        callback = lambda: None
        _invoke_later(callback)

        instance.assert_called_once_with()
        get_invoker.assert_called_once_with(app)
        self.assertEqual(emitted, [callback])


if __name__ == "__main__":
    unittest.main()
