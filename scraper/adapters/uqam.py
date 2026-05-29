from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx

from scraper.adapters.base import BaseAdapter
from scraper.dates import parse_datetime
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source


class UqamCalendarAdapter(BaseAdapter):
    """UQAM event portal — tries embedded JSON/API before HTML fallback."""

    name = "uqam_calendar"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        org_id = source.org_id
        if org_id is None:
            match = re.search(r"organizations=(\d+)", source.url)
            org_id = int(match.group(1)) if match else None

        events: list[Event] = []
        if org_id is not None:
            api_base = source.url.split("/evenements")[0]
            events = self._scrape_api(client, source, org_id, f"{api_base}/api/evenements")
        if not events:
            events = self._scrape_html(client, source)
        return events

    def _scrape_api(
        self,
        client: httpx.Client,
        source: Source,
        org_id: int,
        api_url: str,
    ) -> list[Event]:
        params = {"organizations": org_id, "limit": 100}
        try:
            response = client.get(api_url, params=params)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            return []

        items = data if isinstance(data, list) else data.get("results") or data.get("data") or []
        now = datetime.now(timezone.utc)
        events: list[Event] = []

        for item in items:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("nom") or item.get("name")
            if not title:
                continue
            start_raw = item.get("start") or item.get("dateDebut") or item.get("start_date")
            end_raw = item.get("end") or item.get("dateFin") or item.get("end_date")
            start = parse_datetime(str(start_raw)) if start_raw else None
            end = parse_datetime(str(end_raw)) if end_raw else None
            location = item.get("location") or item.get("lieu")
            slug = item.get("slug") or item.get("id")
            url = item.get("url") or item.get("link")
            if not url and slug:
                url = f"https://evenements.uqam.ca/evenements/{slug}"
            status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
            events.append(
                self._event(
                    source,
                    title=str(title),
                    start_date=start,
                    end_date=end,
                    location=str(location) if location else None,
                    description=item.get("description") or item.get("resume"),
                    url=url,
                    status=status,
                )
            )
        return events

    def _scrape_html(self, client: httpx.Client, source: Source) -> list[Event]:
        from bs4 import BeautifulSoup

        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        now = datetime.now(timezone.utc)
        events: list[Event] = []
        seen: set[str] = set()

        for article in soup.select("article"):
            text = article.get_text(" ", strip=True)
            if len(text) < 15 or text in seen:
                continue
            seen.add(text)

            link = article.find("a", href=True)
            href = link["href"] if link else ""
            url = urljoin("https://evenements.uqam.ca", href) if href.startswith("/") else href or source.url

            start = None
            date_match = re.search(r"date=(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})", href)
            if date_match:
                iso = f"{date_match.group(1)}T{date_match.group(2)}:{date_match.group(3)}:{date_match.group(4)}"
                start = parse_datetime(iso)

            time_match = re.match(r"^(\d{1,2}h\d{2})\s+(.+)$", text)
            title = text
            location = None
            if time_match:
                if not start:
                    start = parse_datetime(time_match.group(1))
                remainder = time_match.group(2)
                parts = remainder.rsplit(" ", 1)
                if len(parts) == 2 and parts[1] in {
                    "Cours",
                    "Conférence",
                    "Atelier",
                    "Colloque",
                    "Séminaire",
                    "Formation",
                    "Exposition",
                }:
                    title = parts[0]
                else:
                    title = remainder

            status = EventStatus.PAST if start and start < now else EventStatus.UPCOMING
            events.append(
                self._event(
                    source,
                    title=title[:200],
                    start_date=start,
                    location=location,
                    description=text[:300],
                    url=url,
                    status=status,
                )
            )

        if events:
            return events[:80]

        for script in soup.find_all("script"):
            if not script.string or "event" not in script.string.lower():
                continue
            for match in re.finditer(r"\{[^{}]*\"title\"[^{}]*\}", script.string):
                try:
                    item = json.loads(match.group(0))
                except json.JSONDecodeError:
                    continue
                title = item.get("title")
                if title:
                    events.append(self._event(source, title=str(title)))

        return events
