"""Probe CIRANO API and CEIM articles."""
from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from scraper.browser import fetch_html
from scraper.http import fetch_text


def cirano_browser() -> None:
    html = fetch_html("https://cirano.qc.ca/index.php/fr/list/evenements", wait_ms=4000)
    soup = BeautifulSoup(html, "lxml")
    for el in soup.select(".feed-activity-list li, .event, [class*='event']"):
        text = el.get_text(" ", strip=True)
        if len(text) > 30:
            print("ITEM", text[:200])
    # API hints
    for script in soup.find_all("script"):
        if script.string and "event" in (script.string or "").lower():
            for m in re.finditer(r"/api/[^\"']+", script.string):
                print("API", m.group(0))


def cirano_api() -> None:
    client = httpx.Client(follow_redirects=True, timeout=30)
    for url in (
        "https://cirano.qc.ca/api/events",
        "https://cirano.qc.ca/index.php/fr/api/events",
        "https://cirano.qc.ca/index.php/api/events",
    ):
        try:
            r = client.get(url)
            print(url, r.status_code, r.text[:300])
        except Exception as exc:
            print(url, exc)


def ceim() -> None:
    html = fetch_text(
        httpx.Client(follow_redirects=True, timeout=30),
        "https://www.ceim.uqam.ca/db/spip.php?rubrique27=",
    )
    soup = BeautifulSoup(html, "lxml")
    count = 0
    for art in soup.select("article"):
        text = art.get_text(" ", strip=True)
        if len(text) < 40:
            continue
        link = art.find("a", href=True)
        if not link:
            continue
        count += 1
        if count <= 8:
            print("CEIM", text[:160])
            print(" ", link["href"][:90])


if __name__ == "__main__":
    print("=== CEIM ===")
    ceim()
    print("\n=== CIRANO API ===")
    cirano_api()
    print("\n=== CIRANO browser ===")
    cirano_browser()
