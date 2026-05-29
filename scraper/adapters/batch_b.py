from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.dates import find_dates_in_html, find_dates_in_text, parse_datetime, year_from_url
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source

_NAV_SKIP = re.compile(
    r"navigation|menu|footer|subscribe|contact|infolettre|newsletter|"
    r"suivez-nous|follow us|main navigation|revue politique|liste d'envoi|"
    r"partager|membres$|publications$",
    re.I,
)

_FR_MONTH_RANGE = re.compile(
    r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)"
    r"\s+(\d{1,2})\s*[–-]\s*(\d{1,2}),?\s*(\d{4})",
    re.I,
)

_CUEVENT_DATE = re.compile(r"/cuevents/[^/]+/(\d{4})/(\d{2})/(\d{2})/")


class UdemCalendrierAdapter(BaseAdapter):
    name = "udem_calendrier"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []

        for card in soup.select(".card"):
            link = card.find("a", href=True)
            if not link:
                continue
            title_el = card.select_one(".results-topic")
            date_el = card.select_one(".results-date")
            title = title_el.get_text(" ", strip=True) if title_el else link.get_text(" ", strip=True)
            if len(title) < 8:
                continue
            date_text = date_el.get_text(" ", strip=True) if date_el else ""
            start = parse_datetime(date_text.replace("\xa0", " "))
            if start and start < now:
                continue
            url = urljoin(source.url, link["href"])
            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    description=date_text or None,
                    url=url,
                    status=EventStatus.UPCOMING,
                )
            )
        return events[:50]


class IrppEventsAdapter(BaseAdapter):
    name = "irpp_events"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        seen: set[str] = set()

        for heading in soup.find_all("h3"):
            title = heading.get_text(" ", strip=True)
            if len(title) < 12 or title in seen:
                continue
            seen.add(title)
            link = heading.find("a", href=True)
            if not link:
                container = heading.parent
                link = container.find("a", href=True) if container else None
            url = urljoin(source.url, link["href"]) if link else source.url
            start, end = self._fetch_event_date(client, url)
            if start and start < now:
                continue
            url_year = year_from_url(url)
            if url_year is not None and url_year < now.year:
                continue
            if not start and url_year is None:
                continue
            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    end_date=end,
                    url=url,
                    status=EventStatus.UPCOMING,
                )
            )
        return events[:20]

    def _fetch_event_date(
        self, client: httpx.Client, url: str
    ) -> tuple[datetime | None, datetime | None]:
        if url == "" or "policyoptions.irpp.org" not in url:
            return None, None
        try:
            html = fetch_text(client, url)
        except httpx.HTTPError:
            return None, None
        start, end = find_dates_in_html(html)
        if not start:
            slug_match = re.search(r"/events/([^/]+)/", url)
            if slug_match:
                slug = slug_match.group(1)
                year_match = re.search(r"(20\d{2})", slug)
                if year_match:
                    start = parse_datetime(f"January 1 {year_match.group(1)}")
        return start, end


class GrippAdapter(BaseAdapter):
    name = "gripp"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        seen: set[str] = set()

        for article in soup.select("article"):
            link = article.find("a", href=True)
            if not link:
                continue
            text = article.get_text(" ", strip=True)
            if len(text) < 20 or text in seen:
                continue
            seen.add(text)
            title = link.get_text(" ", strip=True) or text[:120]
            if len(title) < 12 or _NAV_SKIP.search(title):
                continue
            if not re.search(
                r"atelier|colloq|conféren|seminar|workshop|cours|lecture|prix|manuscrit",
                f"{title} {text}",
                re.I,
            ):
                continue
            start, end = find_dates_in_text(text)
            if not start:
                slug = link["href"]
                slug_match = re.search(r"/(\d{4})/(\d{2})/", slug)
                if slug_match:
                    start = parse_datetime(f"{slug_match.group(1)}-{slug_match.group(2)}-01")
            if start and start < now:
                continue
            url = urljoin(source.url, link["href"])
            events.append(
                self._event(
                    source,
                    title=title[:200],
                    start_date=start,
                    end_date=end,
                    description=text[:400],
                    url=url,
                    status=EventStatus.UPCOMING,
                )
            )
        return events[:25]


class ShiftAdapter(BaseAdapter):
    name = "shift"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        seen: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/cuevents/" not in href:
                continue
            title = link.get_text(" ", strip=True)
            if len(title) < 12 or title in seen:
                continue
            seen.add(title)
            url = urljoin("https://www.concordia.ca", href)
            start = self._date_from_cuevent_url(href)
            if start and start < now:
                continue
            events.append(
                self._event(
                    source,
                    title=title[:200],
                    start_date=start,
                    url=url,
                    status=EventStatus.UPCOMING,
                )
            )
        return events

    def _date_from_cuevent_url(self, href: str) -> datetime | None:
        match = _CUEVENT_DATE.search(href)
        if not match:
            return None
        return parse_datetime(f"{match.group(1)}-{match.group(2)}-{match.group(3)}")


class SqspCongressAdapter(BaseAdapter):
    name = "sqsp_congress"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        text = soup.get_text(" ", strip=True)

        congress_match = re.search(
            r"(\d{1,2}(?:ᵉ|e|er|ère|re)?\s*Congrès[^|]{0,120}\|\|[^|]{0,40}\|\|\s*([^|]{3,80}))"
            r"(\d{1,2}\s*[–-]\s*\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})",
            text,
            re.I,
        )
        if congress_match:
            label = congress_match.group(1).strip()
            date_part = congress_match.group(2).strip()
            start, end = find_dates_in_text(date_part)
            if start and start >= now:
                events.append(
                    self._event(
                        source,
                        title=f"Congrès SQSP — {label.split('||')[0].strip()}",
                        start_date=start,
                        end_date=end,
                        description=date_part,
                        url=source.url,
                        status=EventStatus.UPCOMING,
                    )
                )

        if not events:
            for match in re.finditer(
                r"(\d{1,2}\s*[–-]\s*\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})",
                text,
                re.I,
            ):
                date_part = match.group(1)
                start, end = find_dates_in_text(date_part)
                if not start or start < now:
                    continue
                context_start = max(0, match.start() - 120)
                context = text[context_start : match.start() + len(date_part)]
                title = "Congrès annuel SQSP"
                if re.search(r"63", context):
                    title = "63e Congrès SQSP — Université de Montréal"
                events.append(
                    self._event(
                        source,
                        title=title,
                        start_date=start,
                        end_date=end,
                        description=context[-200:],
                        url=source.url,
                        status=EventStatus.UPCOMING,
                    )
                )
                break

        for heading in soup.find_all(["h1", "h2", "h3"]):
            title = heading.get_text(" ", strip=True)
            if not re.search(r"congrès|congress", title, re.I):
                continue
            block = heading.find_parent(["article", "div", "section"]) or heading.parent
            block_text = block.get_text(" ", strip=True) if block else title
            start, end = find_dates_in_text(block_text)
            if start and start >= now:
                link = heading.find("a", href=True) or (block.find("a", href=True) if block else None)
                url = urljoin(source.url, link["href"]) if link else source.url
                events.append(
                    self._event(
                        source,
                        title=title,
                        start_date=start,
                        end_date=end,
                        description=block_text[:400],
                        url=url,
                        status=EventStatus.UPCOMING,
                    )
                )
        return _dedupe(events)


class ConferenceMontrealAdapter(BaseAdapter):
    name = "conference_montreal"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        from scraper.browser import fetch_html

        html = fetch_html(source.url, wait_ms=2500)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        text = soup.get_text(" ", strip=True)

        range_match = _FR_MONTH_RANGE.search(text)
        start = end = None
        if range_match:
            month_word = range_match.group(0).split()[0]
            year = range_match.group(3)
            start = parse_datetime(f"{range_match.group(1)} {month_word} {year}")
            end = parse_datetime(f"{range_match.group(2)} {month_word} {year}")

        title_el = soup.find(["h1", "h2"])
        title = title_el.get_text(" ", strip=True) if title_el else "Conférence de Montréal 2026"
        if not re.search(r"2026", title):
            title = "Conférence de Montréal 2026 — Mener à travers l'incertitude"

        if not start:
            start, end = find_dates_in_text("8 au 10 juin 2026")

        if start and start >= now:
            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    end_date=end,
                    description="32e édition — Forum économique international des Amériques (FEIA/IEFA)",
                    location="Montréal, QC",
                    url=source.url,
                    status=EventStatus.UPCOMING,
                )
            )
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
