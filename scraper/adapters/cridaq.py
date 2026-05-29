from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from scraper.adapters.base import BaseAdapter
from scraper.http import fetch_text
from scraper.models import Event, EventStatus, Source


class CridaqAdapter(BaseAdapter):
    name = "cridaq"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        html = fetch_text(client, source.url)
        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        now = datetime.now(timezone.utc)

        for heading in soup.find_all(["h2", "h3"]):
            title = heading.get_text(" ", strip=True)
            if len(title) < 8:
                continue
            if any(skip in title.lower() for skip in ("abécédaire", "balado", "infolettre", "ressources", "filtre")):
                continue

            sibling = heading.find_next_sibling(["p", "div"])
            description = sibling.get_text(" ", strip=True) if sibling else None
            link = heading.find("a", href=True) or (sibling.find("a", href=True) if sibling else None)
            url = urljoin(source.url, link["href"]) if link else source.url

            combined = f"{title} {description or ''}"
            if re.search(r"inscription|sur invitation|réservé", combined, re.I):
                pass

            events.append(
                self._event(
                    source,
                    title=title,
                    description=description,
                    url=url,
                    status=EventStatus.UPCOMING,
                )
            )

        return events[:40]
