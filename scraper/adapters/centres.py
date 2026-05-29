from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.adapters.cridaq import CridaqAdapter
from scraper.dates import find_dates_in_text, parse_datetime
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source

_NAV_SKIP = re.compile(
    r"navigation|menu|footer|subscribe|contact|infolettre|newsletter|"
    r"suivez-nous|follow us|main navigation|department and university",
    re.I,
)

_FR_DATE_TITLE = re.compile(
    r"(\d{1,2}\s+"
    r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)"
    r"\s+\d{4})\s+(.+?)(?=\d{1,2}\s+(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)|\Z)",
    re.I | re.S,
)


class WordpressHeadingsAdapter(CridaqAdapter):
    """WordPress research-centre pages with h2/h3 event blocks (CRIDAQ-style)."""

    name = "wordpress_headings"

    _SKIP_TITLES = re.compile(
        r"archives et bilans|navigation|infolettre|abécédaire|balado|"
        r"colloque international crises$|perspectives et dialogue|"
        r"^appel à candidatures|^bourses gripp|^prix annuel",
        re.I,
    )

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        events = self._parse_headings(soup, source)
        if events:
            return events
        return self._parse_articles(soup, source)

    def _parse_headings(self, soup: BeautifulSoup, source: Source) -> list[Event]:
        now = datetime.now(timezone.utc)
        events: list[Event] = []

        for heading in soup.find_all(["h2", "h3"]):
            title = heading.get_text(" ", strip=True)
            if len(title) < 8 or self._SKIP_TITLES.search(title):
                continue
            if any(skip in title.lower() for skip in ("abécédaire", "balado", "infolettre", "ressources", "filtre")):
                continue
            if "ceim" in source.url.lower() and re.search(
                r"^appel à communication|^a propos de la résolution|^la découvrabilité|"
                r"^félicitations|^bourse fulbright|^l'afrique|^l[\u2019']afrique",
                title,
                re.I,
            ):
                continue

            sibling = heading.find_next_sibling(["p", "div"])
            description = sibling.get_text(" ", strip=True) if sibling else None
            link = heading.find("a", href=True) or (sibling.find("a", href=True) if sibling else None)
            url = urljoin(source.url, link["href"]) if link else source.url
            start, end = find_dates_in_text(f"{title} {description or ''}")

            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    end_date=end,
                    description=description,
                    url=url,
                    status=EventStatus.PAST if start and start < now else EventStatus.UPCOMING,
                )
            )

        return events[:40]

    def _parse_articles(self, soup: BeautifulSoup, source: Source) -> list[Event]:
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        seen: set[str] = set()

        for article in soup.select("article"):
            text = article.get_text(" ", strip=True)
            if len(text) < 30 or text in seen:
                continue
            if not re.search(
                r"colloq|conféren|conférence|table ronde|séminaire|seminar|atelier|webinaire|"
                r"workshop|lecture|symposium|événement|event",
                text,
                re.I,
            ):
                continue
            seen.add(text)
            start, end = find_dates_in_text(text)
            if start and start < now:
                continue
            link = article.find("a", href=True)
            url = urljoin(source.url, link["href"]) if link else source.url
            title = text[:120] if len(text) > 120 else text
            if link:
                link_text = link.get_text(" ", strip=True)
                if len(link_text) >= 12:
                    title = link_text
            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    end_date=end,
                    description=text[:500],
                    url=url,
                    status=EventStatus.UPCOMING if not start or start >= now else EventStatus.PAST,
                )
            )
        return events[:40]


class CreAdapter(BaseAdapter):
    name = "cre"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url, browser_fallback=True)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []

        for row in soup.select(".cre-event-row"):
            title_el = row.select_one(".cre-event-row__title")
            if not title_el:
                continue
            title = title_el.get_text(" ", strip=True)
            if len(title) < 8:
                continue

            date_el = row.select_one(".cre-event-row__date")
            date_text = date_el.get_text(" ", strip=True) if date_el else ""
            start, _ = find_dates_in_text(date_text)
            if not start:
                start = parse_datetime(date_text)

            loc_el = row.select_one(".cre-event-row__location")
            location = loc_el.get_text(" ", strip=True) if loc_el else None
            excerpt_el = row.select_one(".cre-event-row__excerpt")
            description = excerpt_el.get_text(" ", strip=True) if excerpt_el else None

            link = row.select_one("a[href]") or title_el.find("a", href=True)
            url = urljoin(source.url, link["href"]) if link else source.url
            status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
            events.append(
                self._event(
                    source,
                    title=title,
                    start_date=start,
                    description=description,
                    location=location,
                    url=url,
                    status=status,
                )
            )
        return events


class EnapAdapter(BaseAdapter):
    name = "enap"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        seen: set[str] = set()

        for article in soup.select("article, .views-row"):
            text = article.get_text(" ", strip=True)
            if len(text) < 25 or text in seen:
                continue
            if not re.search(r"20\d{2}|colloq|conf|école|school|midi|séminaire|seminar|atelier", text, re.I):
                continue
            seen.add(text)
            start, end = find_dates_in_text(text)
            if start and start < now:
                continue
            link = article.find("a", href=True)
            url = urljoin(source.url, link["href"]) if link else source.url
            title = link.get_text(" ", strip=True) if link and len(link.get_text(strip=True)) >= 10 else text[:120]
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
        return events[:30]


_FR_DATE_PREFIX = re.compile(
    r"^(\d{1,2}\s+"
    r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)"
    r"\s+\d{4})\s+(.+)$",
    re.I | re.S,
)


class CiranoAdapter(BaseAdapter):
    name = "cirano"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        from scraper.browser import fetch_html

        html = fetch_html(source.url, wait_ms=3500)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        seen: set[str] = set()

        feed_rows = soup.select(".events-feed-element")
        if feed_rows:
            for row in feed_rows:
                link = row.find("a", href=lambda h: h and "/evenements/" in h)
                if not link:
                    continue
                text = row.get_text(" ", strip=True)
                match = _FR_DATE_PREFIX.match(text)
                if not match:
                    continue
                date_part, title = match.group(1), match.group(2).strip()
                if len(title) < 10 or title in seen or _NAV_SKIP.search(title):
                    continue
                seen.add(title)
                start = parse_datetime(date_part)
                if start and start < now:
                    continue
                events.append(
                    self._event(
                        source,
                        title=title[:200],
                        start_date=start,
                        url=urljoin(source.url, link["href"]),
                        status=EventStatus.UPCOMING,
                    )
                )
            return events[:40]

        text = soup.get_text("\n", strip=True)
        for match in _FR_DATE_TITLE.finditer(text):
            date_part = match.group(1)
            title = match.group(2).strip()
            if len(title) < 10 or title in seen:
                continue
            if _NAV_SKIP.search(title):
                continue
            seen.add(title)
            start = parse_datetime(date_part)
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
        return events[:40]


class CireqAdapter(BaseAdapter):
    name = "cireq"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        from scraper.browser import fetch_html

        html = fetch_html(source.url, wait_ms=2500)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        seen: set[str] = set()

        for block in soup.select(".swiper-slide, .activities .activity, .activity-card"):
            text = block.get_text(" ", strip=True)
            if len(text) < 20 or text in seen:
                continue
            if not re.search(
                r"conference|colloq|workshop|seminar|webinar|conféren|conférence|atelier|symposium|memorial",
                text,
                re.I,
            ):
                continue
            seen.add(text)
            start, end = find_dates_in_text(text)
            if start and start < now:
                continue
            link = block.find("a", href=True)
            url = urljoin(source.url, link["href"]) if link else source.url
            title = text.split("REGISTER")[0].split("Register")[0].strip()
            title = re.sub(r"\s+", " ", title)[:200]
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
        return events[:30]


class BellesHeuresAdapter(BaseAdapter):
    name = "belles_heures"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []

        for card in soup.select(".conference, .event, article, .card, .activite"):
            text = card.get_text(" ", strip=True)
            if len(text) < 20:
                continue
            start, end = find_dates_in_text(text)
            if start and start < now:
                continue
            title_el = card.find(["h2", "h3", "h4"])
            title = title_el.get_text(" ", strip=True) if title_el else text[:100]
            if len(title) < 10 or _NAV_SKIP.search(title):
                continue
            if re.search(r"sera publiée|will be published|infolettre|subscribe", title, re.I):
                continue
            link = card.find("a", href=True)
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

        if not events:
            for heading in soup.find_all(["h2", "h3"]):
                title = heading.get_text(" ", strip=True)
                if len(title) < 12 or _NAV_SKIP.search(title):
                    continue
                block = heading.find_parent(["div", "article", "section"]) or heading.parent
                text = block.get_text(" ", strip=True) if block else title
                start, end = find_dates_in_text(text)
                if start and start < now:
                    continue
                if not start and not re.search(r"conféren|lecture|colloq", title, re.I):
                    continue
                link = heading.find("a", href=True) or (block.find("a", href=True) if block else None)
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
        return events[:20]
