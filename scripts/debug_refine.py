"""Debug IRPP dates and near-duplicate events."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from scraper.dates import find_dates_in_text, parse_datetime
from scraper.filters import normalize_title
from scraper.http import fetch_text


def irpp_dates() -> None:
    urls = [
        "https://policyoptions.irpp.org/events/fall-lecture-2025/",
        "https://policyoptions.irpp.org/events/industrial-policy-conference-2025/",
    ]
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for url in urls:
            html = fetch_text(client, url)
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(" ", strip=True)
            print(url.split("/")[-2])
            print("  find_dates:", find_dates_in_text(text))
            for script in soup.find_all("script", type="application/ld+json"):
                if script.string and "startDate" in script.string:
                    print("  json-ld snippet:", script.string[:400])
            year = re.search(r"/events/[^/]*-(\d{4})/", url)
            if year:
                print("  year slug:", year.group(1))


def near_dupes() -> None:
    events = json.loads(Path("data/upcoming_events.json").read_text(encoding="utf-8"))["events"]

    def core_title(title: str) -> str:
        t = normalize_title(title)
        t = re.sub(r"^(cipss speaker series[^:]*:\s*)", "", t, flags=re.I)
        t = re.sub(r"\s*\([^)]{0,80}\)\s*", " ", t)
        t = re.sub(r'["""].*?["""]', "", t)
        return re.sub(r"\s+", " ", t).strip()[:70]

    by: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for event in events:
        by[core_title(event["title"])].append((event["title"][:55], event["source_name"]))

    near = [(k, v) for k, v in by.items() if len(v) > 1 and len(k) > 15]
    print("\nNear dupes:", len(near))
    for key, items in sorted(near, key=lambda x: -len(x[1]))[:8]:
        print(key)
        for title, source in items:
            print(f"  {source} | {title}")

    undated = Counter(e["source_name"] for e in events if not e.get("start_date"))
    print("\nUndated top:", undated.most_common(8))


if __name__ == "__main__":
    irpp_dates()
    near_dupes()
