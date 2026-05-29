from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.dates import parse_datetime
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source


class ConcordiaEventsAdapter(BaseAdapter):
    name = "concordia_events"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        now = datetime.now(timezone.utc)

        for block in soup.select("div.c-event, article, .event-item"):
            event = self._parse_block(block, source, now)
            if event:
                events.append(event)

        if not events:
            events = self._parse_heading_blocks(soup, source, now)

        return events

    def _parse_block(self, block, source: Source, now: datetime) -> Event | None:
        title_el = block.find(["h2", "h3", "h4"])
        if not title_el:
            return None
        title = title_el.get_text(" ", strip=True)
        if len(title) < 4:
            return None

        text = block.get_text("\n", strip=True)
        when = _field(text, "When")
        where = _field(text, "Where")
        start = parse_datetime(when) if when else None
        end = None
        if when and "–" in when:
            parts = re.split(r"\s*[–-]\s*", when, maxsplit=1)
            if len(parts) == 2:
                start = parse_datetime(parts[0]) or start
                end = parse_datetime(parts[1])

        link = block.find("a", href=True)
        url = link["href"] if link else source.url

        status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
        return self._event(
            source,
            title=title,
            start_date=start,
            end_date=end,
            location=where,
            url=url,
            status=status,
        )

    def _parse_heading_blocks(self, soup: BeautifulSoup, source: Source, now: datetime) -> list[Event]:
        events: list[Event] = []
        for h3 in soup.find_all("h3"):
            title = h3.get_text(" ", strip=True)
            if len(title) < 4 or title.lower() in {"events", "today's events"}:
                continue
            container = h3.parent
            if not container:
                continue
            text = container.get_text("\n", strip=True)
            when = _field(text, "When")
            where = _field(text, "Where")
            start = parse_datetime(when) if when else None
            status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    location=where,
                    status=status,
                )
            )
        return events


class ConcordiaDepartmentAdapter(BaseAdapter):
    name = "concordia_department"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        now = datetime.now(timezone.utc)

        no_events = soup.find(string=re.compile(r"no upcoming events|aucun événement", re.I))
        if no_events:
            return []

        for h2 in soup.find_all(["h2", "h3"]):
            title = h2.get_text(" ", strip=True)
            if len(title) < 6:
                continue
            if any(
                skip in title.lower()
                for skip in (
                    "newsletter",
                    "latest stories",
                    "news & events",
                    "henry habib lecture series",
                    "about the colloquium",
                    "about the series",
                )
            ):
                continue
            sibling = h2.find_next_sibling(["p", "div", "time"])
            meta = sibling.get_text(" ", strip=True) if sibling else ""
            start = parse_datetime(meta) if meta else None
            if not start and not re.search(r"lecture|colloq|conf|seminar|séminaire|workshop", title, re.I):
                continue
            status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
            events.append(
                self._event(source, title=title, start_date=start, description=meta or None, status=status)
            )

        return events


def _field(text: str, label: str) -> str | None:
    pattern = rf"{label}\s*\n?\s*(.+?)(?:\n(?:When|Where|Speaker|SGW|LOY|$))"
    match = re.search(pattern, text, re.I | re.S)
    if match:
        return match.group(1).strip()
    pattern2 = rf"{label}\s*\n?\s*(.+)"
    match2 = re.search(pattern2, text, re.I)
    return match2.group(1).strip() if match2 else None
