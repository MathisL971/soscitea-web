from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.dates import parse_datetime
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source


class ForumAmericasAdapter(BaseAdapter):
    name = "forum_americas"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        now = datetime.now(timezone.utc)
        section = "upcoming"

        for heading in soup.find_all(["h2", "h3", "h4"]):
            label = heading.get_text(" ", strip=True).lower()
            if "next events" in label or "upcoming" in label:
                section = "upcoming"
                continue
            if "past events" in label:
                section = "past"
                continue

            title = heading.get_text(" ", strip=True)
            if len(title) < 10:
                continue
            if re.match(r"^\d+[A-Z]{2}\s+EDITION", title, re.I):
                sibling = heading.find_next_sibling()
                date_text = sibling.get_text(" ", strip=True) if sibling else ""
                start = parse_datetime(date_text)
                status = EventStatus.PAST if section == "past" else EventStatus.UPCOMING
                if start and start < now:
                    status = EventStatus.PAST
                if status == EventStatus.UPCOMING:
                    events.append(
                        self._event(source, title=title, start_date=start, status=status)
                    )

        return events
