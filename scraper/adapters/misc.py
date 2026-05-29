from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.adapters.udem_activites import _dedupe
from scraper.dates import find_dates_in_text
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source

logger = logging.getLogger(__name__)


class GenericAdapter(BaseAdapter):
    name = "generic"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        try:
            fetch_text(client, source.url)
        except httpx.HTTPError as exc:
            logger.warning("Generic fetch failed for %s: %s", source.url, exc)
            raise
        logger.info("No parser for %s (%s) — skipped", source.name, source.adapter)
        return []


class SkipAdapter(BaseAdapter):
    name = "skip"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        logger.info("Skipped source %s: %s", source.name, source.notes or source.adapter)
        return []


class EventbriteAdapter(BaseAdapter):
    name = "eventbrite"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        if soup.find(string=lambda t: t and "nothing planned" in t.lower()):
            return []
        logger.info("Eventbrite page reachable but no API parser yet: %s", source.name)
        return []


class WordpressArchiveAdapter(BaseAdapter):
    name = "wordpress_archive"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        now = datetime.now(timezone.utc)
        current_year = now.year

        for h2 in soup.find_all("h2"):
            section = h2.get_text(" ", strip=True)
            year_match = re.search(r"(20\d{2})", section)
            if not year_match:
                continue
            section_year = int(year_match.group(1))
            if section_year < current_year:
                continue

            for sib in h2.find_next_siblings():
                if sib.name == "h2":
                    break
                text = sib.get_text(" ", strip=True)
                if len(text) < 40:
                    continue
                if re.search(r"annulée|cancelled|covid", text, re.I):
                    continue

                start, end = find_dates_in_text(text)
                if not start or start < now - timedelta(days=1):
                    continue

                parts = re.split(
                    r"\d{1,2}\s+(?:jan|fév|mar|avr|mai|juin|juil|aoû|sep|oct|nov|déc|january|)",
                    text,
                    maxsplit=1,
                    flags=re.I,
                )
                title = parts[1].split(",")[0].strip()[:120] if len(parts) > 1 else text[:120]
                if len(title) < 15:
                    continue

                events.append(
                    self._event(
                        source,
                        title=title,
                        start_date=start,
                        end_date=end,
                        description=text[:800],
                        status=EventStatus.UPCOMING,
                    )
                )

        return _dedupe(events)
