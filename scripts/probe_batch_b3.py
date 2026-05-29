"""Probe remaining Batch B URLs."""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from scraper.http import fetch_text

CHECKS = [
    "https://www.forum-americas.org/all-events",
    "https://www.concordia.ca/about/shift.html",
    "https://calendrier.umontreal.ca/",
    "https://policyoptions.irpp.org/events/fall-lecture-2025/",
    "https://sqsp.uqam.ca/congres/congres-2026/",
]


def main() -> None:
    client = httpx.Client(follow_redirects=True, timeout=45)
    for url in CHECKS:
        print(f"\n=== {url} ===")
        try:
            html = fetch_text(client, url)
            soup = BeautifulSoup(html, "lxml")
            print("len", len(html))
            if "forum-americas" in url:
                for h in soup.find_all(["h2", "h3", "h4"]):
                    t = h.get_text(" ", strip=True)
                    if "montreal" in t.lower() or "2026" in t:
                        print(" ", t[:120])
            elif "shift" in url:
                for a in soup.find_all("a", href=True):
                    if "cuevents" in a["href"]:
                        print(" ", a.get_text(" ", strip=True)[:80], "->", a["href"][:90])
            elif "calendrier" in url:
                for c in soup.select(".card")[:4]:
                    print(" ", c.get_text(" ", strip=True)[:140])
            elif "policyoptions" in url and "events/" in url:
                print(" ", soup.get_text(" ", strip=True)[:400])
            elif "sqsp" in url:
                for h in soup.find_all(["h1", "h2", "h3", "p"])[:12]:
                    t = h.get_text(" ", strip=True)
                    if len(t) > 20:
                        print(" ", t[:120])
        except Exception as exc:
            print("FAIL", exc)


if __name__ == "__main__":
    main()
