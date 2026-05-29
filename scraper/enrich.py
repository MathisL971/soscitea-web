from __future__ import annotations

from datetime import datetime, timezone

from scraper.dates import date_from_url, find_dates_in_text, year_from_url
from scraper.extract import enrich_text_fields
from scraper.models import Event, EventStatus


def enrich_event_dates(event: Event) -> Event:
    """Fill missing start/end dates from description or title text."""
    if event.start_date:
        return event

    for blob in (event.description, event.title, event.location):
        if not blob:
            continue
        start, end = find_dates_in_text(blob)
        if start:
            event.start_date = start
            event.end_date = end or event.end_date
            break

    if not event.start_date and event.url:
        start = date_from_url(event.url)
        if start:
            event.start_date = start

    return event


def enrich_event_details(event: Event) -> Event:
    """Fill missing location and refine midnight-only timestamps from text."""
    location, start_date = enrich_text_fields(
        title=event.title,
        description=event.description,
        location=event.location,
        start_date=event.start_date,
    )
    event.location = location
    event.start_date = start_date
    return event


def finalize_status(event: Event, *, now: datetime | None = None) -> Event:
    from datetime import timedelta

    now = now or datetime.now(timezone.utc)
    event = enrich_event_dates(event)
    event = enrich_event_details(event)

    if event.status == EventStatus.TBD and not event.start_date:
        return event

    ref = event.end_date or event.start_date
    if ref:
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        if ref < now - timedelta(hours=6):
            event.status = EventStatus.PAST
        else:
            event.status = EventStatus.UPCOMING
    elif event.url:
        url_year = year_from_url(event.url)
        if url_year is not None and url_year < now.year:
            event.status = EventStatus.PAST
        elif event.status != EventStatus.TBD:
            event.status = EventStatus.TBD
    elif event.start_date is None and event.status != EventStatus.TBD:
        event.status = EventStatus.TBD
    return event
