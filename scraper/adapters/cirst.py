from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from icalendar import Calendar

from scraper.adapters.base import BaseAdapter
from scraper.dates import find_dates_in_text
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source

MONTREAL = ZoneInfo("America/Montreal")
ICAL_URL = "https://framagenda.org/remote.php/dav/public-calendars/zQHSGsKNDxPwAFr6?export"


class CirstAdapter(BaseAdapter):
    """CIRST events via Framagenda iCal feed and cirst.uqam.ca HTML listings."""

    name = "cirst"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        if self._is_ical_source(source.url):
            return self._scrape_ical(client, source)
        if "cirst.uqam.ca" in source.url:
            return self._scrape_html(client, source)
        return self._scrape_ical(client, source)

    def _is_ical_source(self, url: str) -> bool:
        return "framagenda.org" in url or url.endswith(".ics") or "export" in url

    def _scrape_ical(self, client: httpx.Client, source: Source) -> list[Event]:
        feed_url = source.url if self._is_ical_source(source.url) else ICAL_URL
        response = client.get(feed_url)
        response.raise_for_status()
        cal = Calendar.from_ical(response.content)
        now = datetime.now(timezone.utc)
        events: list[Event] = []

        for comp in cal.walk():
            if comp.name != "VEVENT":
                continue

            title = str(comp.get("summary", "")).strip()
            if not title:
                continue

            start = self._to_aware_datetime(comp.get("dtstart"))
            end = self._to_aware_datetime(comp.get("dtend"))
            if not start or start < now - timedelta(hours=6):
                continue

            location = str(comp.get("location", "")).strip() or None
            description = self._unfold_ical_text(str(comp.get("description", "")))
            url = self._extract_url(description) or "https://cirst.uqam.ca/activites/"

            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    end_date=end,
                    description=description or None,
                    location=location,
                    url=url,
                    status=EventStatus.UPCOMING,
                )
            )

        return _dedupe(events)

    def _scrape_html(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []

        for h3 in soup.find_all("h3"):
            title = h3.get_text(" ", strip=True)
            if len(title) < 12:
                continue

            description_parts: list[str] = []
            start = end = None
            location = None

            for sib in h3.find_next_siblings():
                if sib.name == "h3":
                    break
                text = sib.get_text(" ", strip=True)
                if not text:
                    continue
                sib_start, sib_end = find_dates_in_text(text)
                if sib_start and not start:
                    start, end = sib_start, sib_end
                    continue
                if not location and re.search(
                    r"UQAM|Montréal|Montreal|En ligne|salle|Salle|Campus|Agora|Complexe",
                    text,
                    re.I,
                ):
                    location = text
                    continue
                description_parts.append(text)

            if not start:
                block = h3.find_parent(["article", "div", "section"]) or h3.parent
                block_text = block.get_text("\n", strip=True) if block else ""
                start, end = find_dates_in_text(block_text)

            if not start or start < now - timedelta(hours=6):
                continue

            link = h3.find("a", href=True)
            url = urljoin(source.url, link["href"]) if link else source.url

            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    end_date=end,
                    description=" ".join(description_parts)[:800] or None,
                    location=location,
                    url=url,
                    status=EventStatus.UPCOMING,
                )
            )

        return _dedupe(events)

    def _to_aware_datetime(self, prop) -> datetime | None:
        if prop is None:
            return None
        dt = prop.dt
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime.combine(dt, datetime.min.time(), tzinfo=MONTREAL)
        elif isinstance(dt, datetime) and dt.tzinfo is None:
            dt = dt.replace(tzinfo=MONTREAL)
        return dt.astimezone(timezone.utc)

    def _unfold_ical_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.replace("\\n", "\n").replace("\\,", ",")).strip()

    def _extract_url(self, text: str) -> str | None:
        match = re.search(r"https?://[^\s\\]+", text)
        if not match:
            return None
        return match.group(0).rstrip("/")


def _dedupe(events: list[Event]) -> list[Event]:
    seen: set[str] = set()
    out: list[Event] = []
    for event in events:
        key = event.fingerprint()
        if key not in seen:
            seen.add(key)
            out.append(event)
    return out
