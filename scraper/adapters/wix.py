from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.dates import parse_datetime
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source


class WixAdapter(BaseAdapter):
    name = "wix"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []

        upcoming = False
        for heading in soup.find_all(["h1", "h2"]):
            label = heading.get_text(" ", strip=True).lower()
            if "upcoming" in label or "à venir" in label:
                upcoming = True
            elif "past" in label or "passé" in label:
                upcoming = False

            if not upcoming and "past" in label:
                continue

        for h2 in soup.find_all("h2"):
            title = h2.get_text(" ", strip=True)
            if len(title) < 4:
                continue
            if title.lower() in {"upcoming events", "past events"}:
                continue

            block_text = ""
            for sib in h2.find_next_siblings():
                if sib.name in {"h1", "h2"}:
                    break
                block_text += sib.get_text(" ", strip=True) + " "

            date_match = re.search(r"DATE\s*(.+?)(?:LOCATION|$)", block_text, re.I)
            loc_match = re.search(r"LOCATION\s*(.+?)(?:It'|$)", block_text, re.I)
            date_text = date_match.group(1).strip() if date_match else ""
            location = loc_match.group(1).strip() if loc_match else None

            status = EventStatus.TBD if re.search(r"\bTBD\b|to be determined", date_text, re.I) else EventStatus.UPCOMING
            start = None if status == EventStatus.TBD else parse_datetime(date_text)

            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    location=location,
                    description=block_text.strip() or None,
                    status=status,
                )
            )

        return events
