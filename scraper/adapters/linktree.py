from __future__ import annotations

import logging

import httpx

from scraper.adapters.base import BaseAdapter
from scraper.http import fetch_text
from scraper.models import Event, Source

logger = logging.getLogger(__name__)


class LinktreeAdapter(BaseAdapter):
    """Linktree pages are hubs, not event listings — discover links only (no events emitted)."""

    name = "linktree"

    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        try:
            fetch_text(client, source.url)
        except httpx.HTTPError:
            raise
        logger.debug("Linktree hub reachable (no events extracted): %s", source.name)
        return []
