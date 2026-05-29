#!/usr/bin/env python3
"""Copy scraper export into the web app's public events feed."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "upcoming_events.json"
TARGET = ROOT / "web" / "public" / "events.json"


def main() -> int:
    if not SOURCE.exists():
        print(f"Missing scraper export: {SOURCE}", file=sys.stderr)
        print("Run: python run.py", file=sys.stderr)
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    print(f"Synced {SOURCE} -> {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
