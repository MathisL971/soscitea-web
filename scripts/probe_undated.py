"""Probe CIC, DEEP, CEIM HTML for date patterns."""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from scraper.dates import find_dates_in_html, find_dates_in_text
from scraper.http import fetch_text

URLS = [
    ("CIC", "https://thecic.org/events/"),
    ("DEEP", "https://www.mcgill.ca/equity-ethics-policy/events-0"),
    ("CEIM", "https://www.ceim.uqam.ca/db/spip.php?rubrique27="),
]


def probe(name: str, url: str) -> None:
    print(f"\n=== {name} ===")
    html = fetch_text(httpx.Client(follow_redirects=True, timeout=45), url, browser_fallback="mcgill" in url)
    soup = BeautifulSoup(html, "lxml")
    if name == "CIC":
        articles = soup.select("article.tribe-events-calendar-list__event, article.tec_events")[:3]
        for art in articles:
            print("ART", art.get_text(" ", strip=True)[:200])
            time_el = art.select_one("time, .tribe-event-date-start")
            print("  time", time_el.get("datetime") if time_el else None, time_el.get_text(" ", strip=True) if time_el else None)
    elif name == "DEEP":
        for h in soup.find_all(["h2", "h3"])[:6]:
            t = h.get_text(" ", strip=True)
            if len(t) > 15:
                block = h.find_parent(["div", "article"]) or h.parent
                text = block.get_text(" ", strip=True) if block else t
                print("H", t[:90])
                print("  dates", find_dates_in_text(text))
    elif name == "CEIM":
        for h in soup.find_all("h3")[:5]:
            t = h.get_text(" ", strip=True)
            if len(t) > 20:
                sib = h.find_next_sibling("p")
                meta = sib.get_text(" ", strip=True) if sib else ""
                print("H3", t[:100])
                print("  meta", meta[:120])
                print("  dates", find_dates_in_text(f"{t} {meta}"))


if __name__ == "__main__":
    for n, u in URLS:
        probe(n, u)
