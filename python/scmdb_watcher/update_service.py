"""Version and release-feed helpers."""

from __future__ import annotations

import re
from xml.etree import ElementTree


def version_tuple(text: str) -> tuple[int, ...]:
    normalized = text.strip().lower().lstrip("v")
    parts = [p for p in normalized.split(".") if p]
    nums: list[int] = []
    for part in parts:
        m = re.match(r"(\d+)", part)
        nums.append(int(m.group(1)) if m else 0)
    return tuple(nums or [0])


def parse_latest_version_from_feed(feed_xml: str) -> str:
    root = ElementTree.fromstring(feed_xml)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        if not title:
            continue
        m = re.search(r"v?\d+(?:\.\d+){1,3}", title)
        if m:
            return m.group(0).lstrip("v")
    return ""


def has_update(latest: str, current: str) -> bool:
    if not latest:
        return False
    return version_tuple(latest) > version_tuple(current)
