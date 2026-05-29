from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.dates import find_dates_in_text, parse_date_range
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source


class UdemActivitesAdapter(BaseAdapter):
    name = "udem_activites"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url, browser_fallback=True)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []

        main = soup.select_one("main, .view-content, #content") or soup
        current_section = EventStatus.UPCOMING

        for el in main.find_all(["h2", "h3", "p", "article", "div"]):
            if el.name == "h2":
                label = el.get_text(" ", strip=True).lower()
                if "termin" in label:
                    current_section = EventStatus.PAST
                elif "venir" in label:
                    current_section = EventStatus.UPCOMING
                continue

            if el.name == "h3":
                event = self._from_heading(el, source, current_section, now)
                if event:
                    events.append(event)

        if not events:
            events = self._parse_fallback(soup, source, now)

        return _dedupe(events)

    def _from_heading(self, h3, source: Source, section: EventStatus, now: datetime) -> Event | None:
        title = h3.get_text(" ", strip=True)
        if len(title) < 6:
            return None

        meta_text = ""
        for prev in h3.find_all_previous(["p", "span", "div"], limit=3):
            text = prev.get_text(" ", strip=True)
            if re.search(r"\d{4}|\b(jan|fév|mar|avr|mai|juin|juil|aoû|sep|oct|nov|déc|\d{1,2}\s+mai)", text, re.I):
                meta_text = text
                break

        start, end = find_dates_in_text(meta_text)
        location = None
        if " - " in meta_text:
            location = meta_text.split(" - ", 1)[-1].strip()

        nxt = h3.find_next_sibling("p")
        description = nxt.get_text(" ", strip=True) if nxt else meta_text or None
        if not start and description:
            start, end = find_dates_in_text(description)

        link = h3.find("a", href=True)
        url = link["href"] if link else source.url
        if url.startswith("/"):
            from urllib.parse import urljoin

            url = urljoin(source.url, url)

        status = section
        if re.search(r"\bTBD\b|à déterminer", title, re.I):
            status = EventStatus.TBD
        if start and start < now and status != EventStatus.TBD:
            if not (end and end > now):
                status = EventStatus.PAST

        if status == EventStatus.PAST:
            return None

        return self._event(
            source,
            title=title,
            start_date=start,
            end_date=end,
            description=description,
            location=location,
            url=url,
            status=status if start else EventStatus.TBD,
        )

    def _parse_fallback(self, soup: BeautifulSoup, source: Source, now: datetime) -> list[Event]:
        events: list[Event] = []
        for h3 in soup.find_all("h3"):
            event = self._from_heading(h3, source, EventStatus.UPCOMING, now)
            if event:
                events.append(event)
        return events


def _dedupe(events: list[Event]) -> list[Event]:
    seen: set[str] = set()
    out: list[Event] = []
    for event in events:
        key = event.fingerprint()
        if key not in seen:
            seen.add(key)
            out.append(event)
    return out
