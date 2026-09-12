#!/usr/bin/env python3
"""Verify every local reference in the site resolves to a file on disk.

Covers the "Network panel: zero 404s" item on the README checklist without
needing a browser. Stdlib only.

    python3 check-links.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ["*.html", "*.webmanifest"]

# href/src/content values, plus every candidate inside a srcset list.
ATTR = re.compile(r'(?:href|src|content)\s*=\s*"([^"]+)"')
SRCSET = re.compile(r'srcset\s*=\s*"([^"]+)"')
MANIFEST_SRC = re.compile(r'"src"\s*:\s*"([^"]+)"')


def candidates(text: str):
    for value in ATTR.findall(text):
        yield value
    for value in MANIFEST_SRC.findall(text):
        yield value
    for value in SRCSET.findall(text):
        for entry in value.split(","):
            part = entry.strip().split(" ")[0]
            if part:
                yield part


# Long enough for .webmanifest; short enough that prose ending in a word
# after a period doesn't qualify.
FILEISH = re.compile(r"\.[A-Za-z0-9]{2,12}$")


def is_local(ref: str) -> bool:
    """A path we can look up on disk — not a URL, anchor, or meta value.

    `content="..."` attributes carry both og:image paths and prose, so a
    reference only counts when it is root-relative, explicitly relative, or
    ends in a file extension, and never when it contains whitespace.
    """
    if not ref or ref.startswith(("#", "mailto:", "tel:", "data:", "//")):
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", ref):  # http:, https:, etc.
        return False
    if any(ch.isspace() for ch in ref):
        return False
    return ref.startswith(("/", "./", "../")) or bool(FILEISH.search(ref))


def main() -> int:
    missing: list[tuple[str, str]] = []
    checked = 0

    files = sorted(p for pattern in SOURCES for p in ROOT.glob(pattern))
    for source in files:
        text = source.read_text(encoding="utf-8")
        seen: set[str] = set()
        for ref in candidates(text):
            if not is_local(ref) or ref in seen:
                continue
            seen.add(ref)
            checked += 1
            target = ROOT / ref.lstrip("/").split("?")[0].split("#")[0]
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                missing.append((source.name, ref))

    print(f"checked {checked} local references across {len(files)} files")
    if missing:
        print(f"\n{len(missing)} missing:")
        for source, ref in missing:
            print(f"  {source}: {ref}")
        return 1
    print("all resolve ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
