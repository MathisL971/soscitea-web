import json
import sqlite3
from collections import Counter
from pathlib import Path

payload = json.loads(Path("data/upcoming_events.json").read_text(encoding="utf-8"))
events = payload["events"]
print(f"Upcoming: {payload['event_count']}")
print(f"Sources ok/failed: {payload['sources_ok']}/{payload['sources_failed']}")
print("By discipline:", dict(Counter(e["discipline"] for e in events)))
print("By source (top 10):", Counter(e["source_name"] for e in events).most_common(10))
dated = sum(1 for e in events if e.get("start_date"))
print(f"With date: {dated}, TBD/no date: {len(events)-dated}")
print("\nSample upcoming (with dates):")
for e in [x for x in events if x.get("start_date")][:8]:
    print(f"  {e['start_date'][:16]} | {e['title'][:55]} | {e['source_name']}")

conn = sqlite3.connect("data/events.db")
print("\nScrape errors:")
for row in conn.execute(
    "SELECT source_name, error FROM scrape_errors WHERE run_id = (SELECT MAX(id) FROM scrape_runs)"
):
    print(f"  {row[0]}: {row[1][:100]}")
