"""Deep probe Batch B sources."""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from scraper.http import fetch_text

PROBES = [
    ("UdeM cards", "https://calendrier.umontreal.ca/", "article,.card,.event"),
    ("GRIPP ev", "https://grippmontreal.org/fr/evenements/", "article,h2,h3,a"),
    ("SQSP", "https://sqsp.uqam.ca/congres/", "article,.card,h2,h3,p"),
    ("IRPP", "https://policyoptions.irpp.org/events/", "article,h3,.event,.card"),
    ("McGill poli", "https://www.mcgill.ca/politicalscience/events/calendar", "h3,.views-row"),
    ("SHIFT1", "https://www.concordia.ca/artsci/research/shift", None),
    ("SHIFT2", "https://www.concordia.ca/research/shift", None),
    ("Conf1", "https://www.conference-montreal.com/", None),
    ("Conf2", "https://www.forum-americas.org/conference-of-montreal", None),
]


def dump(name: str, url: str, selector: str | None) -> None:
    print(f"\n=== {name}: {url} ===")
    try:
        html = fetch_text(
            httpx.Client(follow_redirects=True, timeout=45),
            url,
            browser_fallback="mcgill" in url or "irpp.org" in url,
        )
        soup = BeautifulSoup(html, "lxml")
        print("final url ok, len", len(html))
        if selector:
            for sel in selector.split(","):
                items = soup.select(sel.strip())
                if items:
                    print(f"--- {sel} ({len(items)}) ---")
                    for it in items[:4]:
                        print(it.get_text(" ", strip=True)[:180])
        else:
            print("title:", soup.title.get_text(strip=True) if soup.title else "?")
            for h in soup.find_all(["h1", "h2", "h3"])[:6]:
                t = h.get_text(" ", strip=True)
                if len(t) > 10:
                    print("H:", t[:120])
    except Exception as exc:
        print("FAIL:", exc)


if __name__ == "__main__":
    for args in PROBES:
        dump(*args)
