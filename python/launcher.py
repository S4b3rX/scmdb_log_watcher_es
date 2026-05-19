"""Single entry point for SCMDB Watcher.

Default launch opens the GUI. Subcommands route to live or import mode.
"""

from __future__ import annotations

import ctypes
import sys


def _detach_console_if_gui() -> None:
    if sys.argv[1:] and sys.argv[1] not in {"gui"}:
        return
    try:
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])

    if not args or args[0] == "gui":
        _detach_console_if_gui()
        from watcher_gui import main as gui_main

        return gui_main()

    if args[0] == "import":
        from watcher import main as watcher_main

        return watcher_main(["import", *args[1:]])

    if args[0] == "core":
        from watcher import main as watcher_main

        return watcher_main(args[1:])

    from watcher import main as watcher_main

    return watcher_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
