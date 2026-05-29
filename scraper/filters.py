from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from scraper.dates import date_from_url, find_dates_in_html, find_dates_in_text, latest_year_in_text, year_from_url
from scraper.extract import enrich_text_fields

MONTREAL_TZ = timezone(timedelta(hours=-4))  # America/Montreal (EDT; close enough for filtering)

_NOISE_TITLE = re.compile(
    r"^(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)"
    r"\.?\s*\d{0,2}$",
    re.I,
)

_EXCLUDE_TITLE = re.compile(
    r"campus tour|guided tour|open house|future students|admissions|"
    r"last day to apply|registration deadline|drop deadline|"
    r"^\[link\]|^linktree|^subscribe|^contact|^follow us|"
    r"^\*\s|advising for|^\*\s*libraries|^\*\s*minerva|student services|"
    r"annulée|cancelled|covid-19|^\d{1,2}[h:]\d{2}|"
    r"lecture series|lectureship|annual lecture series|about the colloquium",
    re.I,
)

_EXCLUDE_URL = re.compile(
    r"/undergrad/|/library|/minerva|/it/|/maps/|/contact|/about/faculty|/people/",
    re.I,
)

_SOCIAL_SCIENCE_HINT = re.compile(
    r"politic|philos|écon|econ|socio|anthrop|psych|histoir|history|relig|"
    r"conféren|colloq|seminar|séminaire|lecture|workshop|atelier|symposium|"
    r"debate|débat|panel|talk|discussion|research|science|policy|citoyen|"
    r"démocr|migration|justice|gender|femin|public|international|diplom",
    re.I,
)

_GENERAL_SOURCE_MARKERS = (
    "concordia all events",
    "concordia.ca/events.html",
    "uqam all events",
    "evenements.uqam.ca/evenements",
    "mcgill faculty of arts",
    "mcgill.ca/arts/events/calendar",
    "calendrier.umontreal.ca",
    "udem institutional calendar",
)


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def normalize_event_title(title: str) -> str:
    """Strip series prefixes and quotes for cross-source deduplication."""
    t = normalize_title(title)
    t = re.sub(
        r"^(cipss speaker series[^:]*:|gripp colloquium:|seminar:|lecture:|"
        r"colloque:|conférence:|conference:|workshop:|atelier:)\s*",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"[\"\"].*?[\"\"]", "", t)
    t = re.sub(r"\s*\([^)]{0,80}\)\s*", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def is_stale_event(row: dict[str, Any], *, now: datetime | None = None) -> bool:
    """Drop events whose title/URL clearly refer to a past year (e.g. Fall 2025 in mid-2026)."""
    now = now or datetime.now(MONTREAL_TZ)
    current_year = now.year
    parts = [row.get("title") or "", row.get("description") or "", row.get("url") or ""]
    blob = " ".join(parts)

    url_year = year_from_url(row.get("url") or "")
    if url_year is not None and url_year < current_year:
        return True

    text_year = latest_year_in_text(blob)
    if text_year is not None and text_year < current_year:
        return True

    if re.search(rf"\b(fall|automne|hiver|winter|spring|printemps)\s+{current_year - 1}\b", blob, re.I):
        return True
    return False


def row_quality(row: dict[str, Any]) -> int:
    score = 0
    if row.get("start_date"):
        score += 20
    if row.get("end_date"):
        score += 5
    if row.get("location"):
        score += 3
    url = row.get("url") or ""
    if re.search(r"/events/|/event/|/evenements/|/cuevents/", url, re.I):
        score += 8
    if len(url) > 40:
        score += 2
    if row.get("description") and len(str(row["description"])) > 80:
        score += 1
    return score


def is_noise(row: dict[str, Any]) -> bool:
    title = (row.get("title") or "").strip()
    url = row.get("url") or ""
    if len(title) < 10:
        return True
    if _NOISE_TITLE.match(title):
        return True
    if _EXCLUDE_TITLE.search(title):
        return True
    if _EXCLUDE_URL.search(url):
        return True
    if title.lower() in {"events", "upcoming events", "past events", "today's events"}:
        return True
    # Undated entries must look like real events
    if not row.get("start_date"):
        blob = f"{title} {row.get('description') or ''}"
        if not _SOCIAL_SCIENCE_HINT.search(blob) and len(title) < 25:
            return True
    return False


def is_from_general_feed(row: dict[str, Any]) -> bool:
    name = (row.get("source_name") or "").lower()
    url = (row.get("source_url") or "").lower()
    return any(m in name or m in url for m in _GENERAL_SOURCE_MARKERS)


def is_social_science_relevant(row: dict[str, Any]) -> bool:
    if not is_from_general_feed(row):
        return True
    blob = " ".join(
        filter(
            None,
            [
                row.get("title"),
                row.get("description"),
                row.get("location"),
            ],
        )
    )
    return bool(_SOCIAL_SCIENCE_HINT.search(blob))


def parse_row_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=MONTREAL_TZ)
        return dt
    except ValueError:
        return None


def is_upcoming(row: dict[str, Any], *, now: datetime | None = None) -> bool:
    now = now or datetime.now(MONTREAL_TZ)
    status = (row.get("status") or "").lower()
    if status == "past":
        return False

    start = parse_row_date(row.get("start_date"))
    end = parse_row_date(row.get("end_date"))

    if end and end < now - timedelta(hours=6):
        return False
    if start and start < now - timedelta(hours=6):
        if status != "tbd":
            return False

    if not start and not end:
        if is_stale_event(row, now=now):
            return False

    return True


def export_fingerprint(row: dict[str, Any]) -> str:
    title = normalize_event_title(row.get("title") or "")
    start = (row.get("start_date") or "")[:10]
    if start:
        return f"{title}|{start}"
    return f"{title}|nodate"


def _enrich_row_dates(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("start_date"):
        return row
    for field in ("description", "title", "location", "url"):
        text = row.get(field)
        if not text:
            continue
        if field == "url":
            start = date_from_url(str(text))
            if start:
                row = dict(row)
                row["start_date"] = start.isoformat()
                return row
            continue
        start, end = find_dates_in_text(str(text))
        if start:
            row = dict(row)
            row["start_date"] = start.isoformat()
            if end:
                row["end_date"] = end.isoformat()
            break
    if not row.get("start_date"):
        url_start = date_from_url(row.get("url") or "")
        if url_start:
            row = dict(row)
            row["start_date"] = url_start.isoformat()
    return row


def _enrich_row_details(row: dict[str, Any]) -> dict[str, Any]:
    start = parse_row_date(row.get("start_date"))
    location, start = enrich_text_fields(
        title=row.get("title"),
        description=row.get("description"),
        location=row.get("location"),
        start_date=start,
    )

    row = dict(row)
    if location:
        row["location"] = location
    if start:
        row["start_date"] = start.isoformat()
    return row


def filter_upcoming_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}

    for row in rows:
        row = _enrich_row_dates(row)
        row = _enrich_row_details(row)
        if is_noise(row):
            continue
        if not is_social_science_relevant(row):
            continue
        if not is_upcoming(row):
            continue
        if is_stale_event(row):
            continue

        fp = export_fingerprint(row)
        existing = best.get(fp)
        if existing is None or row_quality(row) > row_quality(existing):
            best[fp] = row

    out = list(best.values())
    out.sort(
        key=lambda r: (
            r.get("start_date") is None,
            r.get("start_date") or "9999",
            r.get("title") or "",
        )
    )
    return out
