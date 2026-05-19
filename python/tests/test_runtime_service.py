from __future__ import annotations

import logging
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scmdb_watcher.runtime_service import choose_available_port, create_server_with_fallback, prune_old_log_files


class RuntimeServiceTests(unittest.TestCase):
    def test_choose_available_port_falls_forward_when_preferred_is_busy(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy_sock:
            busy_sock.bind(("127.0.0.1", 0))
            busy_sock.listen(1)
            busy_port = busy_sock.getsockname()[1]

            selected = choose_available_port("127.0.0.1", busy_port, search_span=5)
            self.assertNotEqual(selected, busy_port)
            self.assertGreaterEqual(selected, busy_port)

    def test_prune_old_log_files_keeps_latest_five(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            for idx in range(7):
                path = log_dir / f"watcher-2026-05-17_00-00-0{idx}.log"
                path.write_text(f"log {idx}", encoding="utf-8")

            deleted = prune_old_log_files(log_dir, keep=5)
            self.assertEqual(deleted, 2)

            remaining = sorted(p.name for p in log_dir.glob("watcher-*.log"))
            self.assertEqual(len(remaining), 5)
            self.assertEqual(
                remaining,
                [
                    "watcher-2026-05-17_00-00-02.log",
                    "watcher-2026-05-17_00-00-03.log",
                    "watcher-2026-05-17_00-00-04.log",
                    "watcher-2026-05-17_00-00-05.log",
                    "watcher-2026-05-17_00-00-06.log",
                ],
            )

    def test_create_server_with_fallback_does_not_retry_when_max_attempts_is_one(self) -> None:
        logger = logging.getLogger("test-runtime-service")

        with patch("werkzeug.serving.make_server", side_effect=OSError(10048, "Only one usage of each socket address")) as make_server:
            with self.assertRaises(OSError):
                create_server_with_fallback(object(), "127.0.0.1", 23456, logger, max_attempts=1)

        self.assertEqual(make_server.call_count, 1)
        self.assertEqual(make_server.call_args_list[0].args[1], 23456)

    def test_create_server_with_fallback_retries_next_port_when_attempts_allow_it(self) -> None:
        logger = logging.getLogger("test-runtime-service")
        server = object()

        with patch(
            "werkzeug.serving.make_server",
            side_effect=[OSError(10048, "Only one usage of each socket address"), server],
        ) as make_server:
            created_server, port = create_server_with_fallback(object(), "127.0.0.1", 23456, logger, max_attempts=2)

        self.assertIs(created_server, server)
        self.assertEqual(port, 23457)
        self.assertEqual(make_server.call_count, 2)
        self.assertEqual(make_server.call_args_list[0].args[1], 23456)
        self.assertEqual(make_server.call_args_list[1].args[1], 23457)


if __name__ == "__main__":
    unittest.main()
