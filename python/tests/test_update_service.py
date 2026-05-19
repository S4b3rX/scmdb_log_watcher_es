from __future__ import annotations

import unittest

from scmdb_watcher.update_service import has_update, parse_latest_version_from_feed, version_tuple


class UpdateServiceTests(unittest.TestCase):
    def test_version_tuple_parses_prefixed_versions(self) -> None:
        self.assertEqual(version_tuple("v1.2.3"), (1, 2, 3))

    def test_parse_latest_version_from_feed(self) -> None:
        feed = """
<feed xmlns=\"http://www.w3.org/2005/Atom\">
  <entry><title>Release v0.1.2</title></entry>
  <entry><title>Release v0.1.1</title></entry>
</feed>
"""
        self.assertEqual(parse_latest_version_from_feed(feed), "0.1.2")

    def test_has_update(self) -> None:
        self.assertTrue(has_update("0.2.0", "0.1.9"))
        self.assertFalse(has_update("0.1.0", "0.1.0"))
        self.assertFalse(has_update("", "0.1.0"))


if __name__ == "__main__":
    unittest.main()
