from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.dates import parse_datetime
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source


class McGillEventsAdapter(BaseAdapter):
    name = "mcgill_events"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url, browser_fallback=True)
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        now = datetime.now(timezone.utc)

        for row in soup.select(".views-row, article.node--type-event, article.node, .event-teaser"):
            title_el = row.select_one(".field--name-title, .title, h2, h3, a")
            if not title_el:
                continue
            title = title_el.get_text(" ", strip=True)
            if len(title) < 6 or title.lower() in {"events", "upcoming events"}:
                continue

            date_el = row.select_one("time[datetime], .date-display-single, .field--name-field-event-date")
            start = None
            if date_el and date_el.get("datetime"):
                start = parse_datetime(date_el["datetime"])
            text = row.get_text(" ", strip=True)
            if not start:
                date_match = re.search(
                    r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|"
                    r"janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})",
                    text,
                    re.I,
                )
                start = parse_datetime(date_match.group(1)) if date_match else None

            loc_el = row.select_one(".field--name-field-event-location, .location")
            location = loc_el.get_text(" ", strip=True) if loc_el else None
            link = row.select_one("a[href*='/event'], a[href*='/events/'], h2 a, h3 a, .title a")
            if not link:
                link = row.find("a", href=True)
            url = urljoin(source.url, link["href"]) if link else source.url
            status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING

            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    location=location,
                    description=text[:400] if len(text) < 400 else text[:400] + "…",
                    url=url,
                    status=status,
                )
            )

        if not events:
            events = self._parse_headings(soup, source, now)
        if not events and "events/calendar" in source.url:
            events = self._parse_calendar(soup, source, now)

        if not events:
            return []

        return _dedupe(events)

    _SKIP_HEADINGS = re.compile(
        r"navigation|main navigation|department and university|mailing list|recorded events|"
        r"speaker series$|speaker line-up$|research groups|welcome to|join our|watch our|"
        r"register now|visit our|explore the|about the institute|news$|events$|"
        r"^location:|^register here|^deep \d{4} annual conference$",
        re.I,
    )

    _SERIES_HEADING = re.compile(
        r"lecture series|lectureship|annual lecture|memorial lecture|"
        r"distinguished lecture|conference$|^birks annual|^g\. campbell",
        re.I,
    )

    _DATE_LINE = re.compile(
        r"^(?:january|february|march|april|may|june|july|august|september|october|november|december|"
        r"location:|register here|\d{1,2}\s*(?:st|nd|rd|th)?\s*,?\s*\d{4})",
        re.I,
    )

    def _parse_headings(self, soup: BeautifulSoup, source: Source, now: datetime) -> list[Event]:
        events: list[Event] = []
        main = soup.select_one("#main-content, main, .region-content") or soup
        headings = main.find_all(["h2", "h3", "h4"])
        idx = 0

        while idx < len(headings):
            heading = headings[idx]
            title = heading.get_text(" ", strip=True)
            idx += 1

            if len(title) < 10 or self._SKIP_HEADINGS.search(title):
                continue
            if self._SERIES_HEADING.search(title):
                continue
            if self._DATE_LINE.match(title) or title.lower().startswith("location:"):
                continue

            parts = [title]
            while idx < len(headings):
                nxt = headings[idx].get_text(" ", strip=True)
                if self._DATE_LINE.match(nxt) or nxt.lower().startswith("location:"):
                    parts.append(nxt)
                    idx += 1
                    continue
                if len(nxt) >= 10 and not self._SKIP_HEADINGS.search(nxt):
                    break
                idx += 1

            text = " ".join(parts)
            start, end = self._dates_from_block(text)
            if start and start < now:
                continue
            if not start and not re.search(r"\b20\d{2}\b", text):
                continue

            link = heading.find("a", href=True)
            if not link:
                container = heading.find_parent(["div", "article", "li", "section"])
                link = container.find("a", href=True) if container else None
            url = urljoin(source.url, link["href"]) if link else source.url
            status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    end_date=end,
                    description=text[:400],
                    url=url,
                    status=status,
                )
            )

        for li in main.find_all("li"):
            text = li.get_text(" ", strip=True)
            if len(text) < 25:
                continue
            if not re.search(r"seminar|lecture|colloq|workshop|conféren|\d{1,2}:\d{2}", text, re.I):
                continue
            start, end = self._dates_from_block(text)
            if start and start < now:
                continue
            link = li.find("a", href=True)
            title = link.get_text(" ", strip=True) if link else text[:120]
            if len(title) < 10:
                continue
            url = urljoin(source.url, link["href"]) if link else source.url
            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    end_date=end,
                    description=text[:400],
                    url=url,
                    status=EventStatus.UPCOMING,
                )
            )
        return events

    def _parse_calendar(self, soup: BeautifulSoup, source: Source, now: datetime) -> list[Event]:
        events: list[Event] = []
        text = soup.get_text("\n", strip=True)
        seen: set[str] = set()

        for match in re.finditer(
            r"(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})\s+(.+?)(?=\n\d{1,2}:\d{2}\s*-|\Z)",
            text,
            re.S,
        ):
            title = match.group(2).strip()
            if len(title) < 10 or title in seen:
                continue
            if re.search(r"convocation|graduation|meeting only", title, re.I):
                continue
            seen.add(title)
            events.append(
                self._event(
                    source,
                    title=title[:200],
                    description=match.group(0)[:200],
                    url=source.url,
                    status=EventStatus.UPCOMING,
                )
            )

        for match in re.finditer(
            r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}:\d{2})\s+to\s+(\d{2}:\d{2})\s+(.+?)(?=\d{2}/\d{2}/\d{4}|\Z)",
            text,
            re.S,
        ):
            date_str = f"{match.group(1)} {match.group(2)}"
            title = match.group(4).strip()
            if len(title) < 10 or title in seen:
                continue
            seen.add(title)
            start = parse_datetime(date_str)
            if start and start < now:
                continue
            events.append(
                self._event(
                    source,
                    title=title[:200],
                    start_date=start,
                    url=source.url,
                    status=EventStatus.UPCOMING,
                )
            )
        return events

    def _dates_from_block(self, text: str) -> tuple[datetime | None, datetime | None]:
        from scraper.dates import find_dates_in_text

        start, end = find_dates_in_text(text)
        if start:
            return start, end
        return parse_datetime(text), None


class McGillSeminarsAdapter(McGillEventsAdapter):
    name = "mcgill_seminars"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url, browser_fallback=True)
        soup = BeautifulSoup(html, "lxml")
        main = soup.select_one("#main-content, main, .region-content, article") or soup
        events: list[Event] = []
        now = datetime.now(timezone.utc)

        for heading in main.find_all(["h2", "h3"]):
            title = heading.get_text(" ", strip=True)
            if len(title) < 12 or title.startswith("*"):
                continue
            if not re.search(r"seminar|séminaire|lecture|colloq|workshop|conféren", title, re.I):
                continue
            block = heading.find_parent(["div", "section", "article"]) or heading.parent
            text = block.get_text(" ", strip=True) if block else title
            start = parse_datetime(text)
            link = heading.find("a", href=True)
            url = urljoin(source.url, link["href"]) if link else source.url
            if not start:
                continue
            status = EventStatus.PAST if start < now else EventStatus.UPCOMING
            if status == EventStatus.UPCOMING:
                events.append(
                    self._event(
                        source,
                        title=title,
                        start_date=start,
                        description=text[:500],
                        url=url,
                        status=status,
                    )
                )
        return _dedupe(events)


def _dedupe(events: list[Event]) -> list[Event]:
    seen: set[str] = set()
    out: list[Event] = []
    for event in events:
        key = event.fingerprint()
        if key not in seen:
            seen.add(key)
            out.append(event)
    return out
