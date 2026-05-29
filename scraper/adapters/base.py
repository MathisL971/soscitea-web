from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from scraper.models import Event, Source


class BaseAdapter(ABC):
    name: str = "base"

    @abstractmethod
    def scrape(self, client: httpx.Client, source: Source) -> list[Event]:
        raise NotImplementedError

    def _event(
        self,
        source: Source,
        *,
        title: str,
        start_date=None,
        end_date=None,
        description: str | None = None,
        location: str | None = None,
        url: str | None = None,
        status=None,
    ) -> Event:
        from scraper.models import EventStatus

        return Event(
            title=title.strip(),
            source_url=source.url,
            source_name=source.name,
            discipline=source.discipline,
            start_date=start_date,
            end_date=end_date,
            description=description,
            location=location,
            url=url or source.url,
            status=status or EventStatus.UPCOMING,
        )
