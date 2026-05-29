"""Dump HTML snippets from Batch A sources for adapter development."""
from __future__ import annotations

import re
import sys

import httpx
from bs4 import BeautifulSoup

from scraper.http import fetch_text

SOURCES = {
    "cre": "https://www.lecre.umontreal.ca/calendrier/",
    "crises": "https://crises.uqam.ca/activites/evenements-a-venir/",
    "celat": "https://celat.ca/uqam/activites-uqam/",
    "bellesheures": "https://bellesheures.umontreal.ca/themes-activites/societe/",
    "enap": "https://enap.ca/evenements",
    "cirano": "https://cirano.qc.ca/index.php/fr/list/evenements",
    "ceim": "https://www.ceim.uqam.ca/db/spip.php?rubrique27=",
    "uqam": "https://evenements.uqam.ca/evenements",
}


def dump(name: str, url: str, client: httpx.Client) -> None:
    print(f"\n{'='*60}\n{name}: {url}\n{'='*60}")
    html = fetch_text(client, url, browser_fallback=name == "cireq")
    soup = BeautifulSoup(html, "lxml")
    # first few event-like blocks
    selectors = [
        "article.tribe-events-calendar-list__event",
        "article",
        ".views-row",
        ".event",
        ".card",
        "h2",
        "h3",
    ]
    for sel in selectors:
        items = soup.select(sel)
        if items and len(items) <= 30:
            print(f"\n--- {sel} ({len(items)}) ---")
            for item in items[:3]:
                print(item.get_text(" ", strip=True)[:300])
                print("---")
            break
    # script JSON hints for UQAM
    if name == "uqam":
        for script in soup.find_all("script"):
            if script.string and "evenement" in script.string.lower()[:5000]:
                m = re.search(r"https?://[^\"']+api[^\"']+", script.string)
                if m:
                    print("API hint:", m.group(0))


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else None
    with httpx.Client(follow_redirects=True, timeout=45) as client:
        for name, url in SOURCES.items():
            if target and name != target:
                continue
            try:
                dump(name, url, client)
            except Exception as exc:
                print(f"{name} FAILED: {exc}")


if __name__ == "__main__":
    main()
