"""Probe Batch B source HTML structure."""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from scraper.http import fetch_text

URLS = [
    ("GRIPP", "https://grippmontreal.org/fr/"),
    ("GRIPP events", "https://grippmontreal.org/fr/evenements/"),
    ("UdeM calendrier", "https://calendrier.umontreal.ca/"),
    ("IRPP policyoptions", "https://policyoptions.irpp.org/events/"),
    ("IRPP main", "https://irpp.org/irpp-event/"),
    ("SQSP congres", "https://sqsp.uqam.ca/congres/"),
    ("Conference Montreal", "https://www.conferenceofmontreal.com/"),
    ("SHIFT", "https://www.concordia.ca/artsci/research/shift/"),
    ("McGill polisci cal", "https://www.mcgill.ca/politicalscience/events/calendar"),
]


def main() -> None:
    with httpx.Client(follow_redirects=True, timeout=45) as client:
        for name, url in URLS:
            print(f"\n=== {name} ===")
            try:
                browser = "mcgill" in url
                html = fetch_text(client, url, browser_fallback=browser)
                soup = BeautifulSoup(html, "lxml")
                print(f"bytes={len(html)}")
                for sel in (
                    "article",
                    ".tribe-events",
                    ".views-row",
                    "h2",
                    "h3",
                    ".event",
                    ".card",
                ):
                    n = len(soup.select(sel))
                    if n:
                        print(f"  {sel}: {n}")
                for h in soup.find_all(["h2", "h3"])[:5]:
                    t = h.get_text(" ", strip=True)
                    if len(t) > 12:
                        print(f"  H: {t[:100]}")
            except Exception as exc:
                print(f"FAILED: {exc}")


if __name__ == "__main__":
    main()
