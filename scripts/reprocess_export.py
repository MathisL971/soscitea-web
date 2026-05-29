#!/usr/bin/env python3
"""Re-apply date/location/time enrichment to an existing export file."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scraper.filters import _enrich_row_dates, _enrich_row_details

DEFAULT_PATH = ROOT / "data" / "upcoming_events.json"


def main(argv: list[str] | None = None) -> int:
    path = Path(argv[0]) if argv else DEFAULT_PATH
    if not path.exists():
        print(f"Missing export: {path}", file=sys.stderr)
        return 1

    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("events", [])
    payload["events"] = [
        _enrich_row_details(_enrich_row_dates(dict(event))) for event in events
    ]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with_location = sum(1 for event in payload["events"] if event.get("location"))
    print(f"Reprocessed {len(payload['events'])} events ({with_location} with location) -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
