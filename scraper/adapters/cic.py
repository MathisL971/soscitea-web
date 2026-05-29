from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.dates import find_dates_in_text, parse_datetime
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source

_MONTREAL_HINT = re.compile(
    r"montreal|montréal|tio.?tia.?ke|westmount|outremont|en ligne|online|virtual|zoom",
    re.I,
)
_OTHER_CITY = re.compile(
    r"\b(calgary|edmonton|saskatoon|vancouver|toronto|ottawa|winnipeg|halifax|victoria|"
    r"waterloo|yukon|regina|hamilton|quebec city|ville de qu[eé]bec)\b",
    re.I,
)


class CicAdapter(BaseAdapter):
    name = "cic"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url, browser_fallback=True)
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        now = datetime.now(timezone.utc)
        seen: set[str] = set()

        selectors = (
            "article.tribe-events-calendar-list__event, article.tec_events, "
            "article.type-tribe_events, article.tribe-events-calendar-month__calendar-event"
        )
        for article in soup.select(selectors):
            event = self._parse_article(article, source, now, seen)
            if event:
                events.append(event)

        if not events:
            events = self._parse_list_view(soup, source, now, seen)

        return events

    def _parse_article(
        self,
        article: BeautifulSoup,
        source: Source,
        now: datetime,
        seen: set[str],
    ) -> Event | None:
        title_el = article.select_one(
            ".tribe-events-calendar-list__event-title, "
            ".tribe-events-calendar-month__calendar-event-title-link, h3, h2, a"
        )
        if not title_el:
            return None
        title = title_el.get_text(" ", strip=True)
        if len(title) < 8 or title in seen:
            return None
        seen.add(title)

        start = None
        time_el = article.select_one(
            ".tribe-events-calendar-month__calendar-event-tooltip time[datetime], "
            "time[datetime][datetime*='-'], .tribe-event-date-start"
        )
        if time_el:
            raw = time_el.get("datetime") or ""
            if re.match(r"\d{4}-\d{2}-\d{2}", raw):
                start = parse_datetime(raw)
            else:
                start = parse_datetime(time_el.get_text(" ", strip=True))

        if not start:
            text = article.get_text(" ", strip=True)
            start = find_dates_in_text(text)[0]

        desc_el = article.select_one(".tribe-events-calendar-list__event-description, p")
        description = desc_el.get_text(" ", strip=True) if desc_el else None

        link = article.find("a", href=True)
        url = urljoin(source.url, link["href"]) if link else source.url

        if not self._is_montreal_relevant(title, description, url):
            return None

        status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
        return self._event(
            source,
            title=title,
            start_date=start,
            description=description,
            url=url,
            status=status,
        )

    def _is_montreal_relevant(self, title: str, description: str | None, url: str) -> bool:
        blob = f"{title} {description or ''} {url}"
        if _MONTREAL_HINT.search(blob):
            return True
        if _OTHER_CITY.search(blob):
            return False
        return False

    def _parse_list_view(
        self,
        soup: BeautifulSoup,
        source: Source,
        now: datetime,
        seen: set[str],
    ) -> list[Event]:
        events: list[Event] = []
        for h3 in soup.find_all("h3"):
            title = h3.get_text(" ", strip=True)
            if len(title) < 6 or title in seen:
                continue
            if "event" in title.lower() and len(title) < 20:
                continue
            seen.add(title)

            container = h3.find_parent(["article", "div"]) or h3.parent
            text = container.get_text(" ", strip=True) if container else ""
            start = find_dates_in_text(text)[0]
            link = h3.find("a", href=True) or (container.find("a", href=True) if container else None)
            url = urljoin(source.url, link["href"]) if link else source.url
            if not self._is_montreal_relevant(title, text, url):
                continue
            status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
            events.append(
                self._event(source, title=title, start_date=start, url=url, status=status)
            )
        return events
