#!/usr/bin/env python3
"""Detect common UTF-8 mojibake signatures in tracked text files."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

# Common signatures produced when UTF-8 text is decoded/saved through cp1252/latin-1.
SUSPICIOUS_TOKENS = (
    "\u00c3",
    "\u00c2",
    "\u00e2",
    "\u00f0\u0178",
)

SKIP_SUFFIXES = {
    ".db",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".pyc",
    ".sqlite",
    ".woff",
    ".woff2",
    ".xls",
    ".xlsx",
    ".zip",
}


def tracked_files(root: Path) -> list[Path]:
    try:
        output = subprocess.check_output(
            ["git", "-c", "core.quotepath=false", "ls-files", "-z"],
            cwd=root,
            stderr=subprocess.DEVNULL,
        )
        return [root / chunk.decode("utf-8") for chunk in output.split(b"\0") if chunk]
    except (FileNotFoundError, subprocess.CalledProcessError):
        return [path for path in root.rglob("*") if path.is_file()]


def scan_repo(root: Path) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for path in tracked_files(root):
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(token in line for token in SUSPICIOUS_TOKENS):
                hits.append((path, line_no, line))
    return hits


def main() -> int:
    hits = scan_repo(ROOT)
    if not hits:
        print("[OK] no mojibake signatures found in tracked text files")
        return 0

    print("[FAIL] mojibake signatures detected:")
    for path, line_no, line in hits:
        rel_path = path.relative_to(ROOT)
        print(f" - {rel_path}:{line_no}: {line.strip()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
