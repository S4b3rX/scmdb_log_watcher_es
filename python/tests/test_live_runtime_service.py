from __future__ import annotations

import unittest

from scmdb_watcher.live_runtime_service import build_allowed_origins


class LiveRuntimeServiceTests(unittest.TestCase):
    def test_build_allowed_origins_prod_only(self) -> None:
        prod = frozenset({"https://scmdb.net"})
        dev_defaults = frozenset({"http://localhost:3000"})
        allowed = build_allowed_origins(prod, dev_defaults, dev_flag=False, dev_origins_raw="")
        self.assertEqual(allowed, {"https://scmdb.net"})

    def test_build_allowed_origins_with_dev_and_extra(self) -> None:
        prod = frozenset({"https://scmdb.net"})
        dev_defaults = frozenset({"http://localhost:3000"})
        allowed = build_allowed_origins(
            prod,
            dev_defaults,
            dev_flag=True,
            dev_origins_raw="http://localhost:5173, https://preview.scmdb.net",
        )
        self.assertIn("https://scmdb.net", allowed)
        self.assertIn("http://localhost:3000", allowed)
        self.assertIn("http://localhost:5173", allowed)
        self.assertIn("https://preview.scmdb.net", allowed)


if __name__ == "__main__":
    unittest.main()
