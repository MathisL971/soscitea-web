"""Second probe for Batch A adapter development."""
from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from scraper.http import fetch_text


def cirano() -> None:
    html = fetch_text(httpx.Client(follow_redirects=True, timeout=30), "https://cirano.qc.ca/index.php/fr/list/evenements")
    soup = BeautifulSoup(html, "lxml")
    for el in soup.select("[class*=event], [class*=feed], [class*=activity]"):
        cls = " ".join(el.get("class", []))
        text = el.get_text(" ", strip=True)
        if 20 < len(text) < 400:
            print("CIRANO", cls[:50], text[:150])


def crises_colloque() -> None:
    url = "https://crises.uqam.ca/activites/colloque-international-crises/"
    html = fetch_text(httpx.Client(follow_redirects=True, timeout=30), url)
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["h1", "h2", "h3", "p"])[:15]:
        text = tag.get_text(" ", strip=True)
        if len(text) > 15:
            print("CRISES", tag.name, text[:120])


def ceim() -> None:
    html = fetch_text(
        httpx.Client(follow_redirects=True, timeout=30),
        "https://www.ceim.uqam.ca/db/spip.php?rubrique27=",
    )
    soup = BeautifulSoup(html, "lxml")
    for art in soup.select("article")[:10]:
        text = art.get_text(" ", strip=True)
        if re.search(r"20\d{2}", text):
            link = art.find("a", href=True)
            print("CEIM", text[:140])
            if link:
                print(" ", link["href"][:80])


def irms() -> None:
    client = httpx.Client(follow_redirects=True, timeout=20)
    for path in (
        "/artsci/research/irms/news.html",
        "/artsci/research/irms/events.html",
        "/artsci/research/irms/news-and-events.html",
    ):
        url = f"https://www.concordia.ca{path}"
        try:
            r = client.get(url)
            print(path, r.status_code, len(r.text))
        except Exception as exc:
            print(path, exc)


def cipss() -> None:
    html = fetch_text(
        httpx.Client(follow_redirects=True, timeout=30),
        "https://www.mcgill.ca/peace-security/speaker-series",
        browser_fallback=True,
    )
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("#main-content, main, .region-content") or soup
    for li in main.find_all("li")[:20]:
        text = li.get_text(" ", strip=True)
        if len(text) > 25:
            print("CIPSS", text[:120])


if __name__ == "__main__":
    cirano()
    print()
    crises_colloque()
    print()
    ceim()
    print()
    irms()
    print()
    cipss()
