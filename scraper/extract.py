from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from scraper.dates import parse_datetime

MONTREAL = ZoneInfo("America/Montreal")

_LOCATION_LABEL = re.compile(
    r"(?:Location|Lieu(?:\s+de\s+l['\u2019]?(?:é|e)v[ée]nement)?|Venue|Where|Où)\s*:?\s*"
    r"(.+?)(?=\s*(?:Time|Heure|Date|Register|Inscription|\||\"|\Z)|\n\n)",
    re.I | re.S,
)

_AT_LOCATION = re.compile(
    r"@\s*((?:Salle|Room|Local)\s+\d+[^.\n\|\"]{0,80})",
    re.I,
)

_CAMPUS = re.compile(r"(Campus de [^\n,\.\"]{3,70})", re.I)

_SALLE = re.compile(
    r"((?:Salle|Room|Local)\s+[\w\d\-]+(?:,\s+[^,\n\|\"]{4,50})?)",
    re.I,
)

_BUILDING = re.compile(
    r"((?:Leacock|Pavillon|Hall|Building|Centre|Carrefour|Amphithéâtre|Amphitheater)"
    r"[^,\n\|\"]{3,80})",
    re.I,
)

_ADDRESS = re.compile(
    r"(\d{1,5}\s+(?:rue|av\.|avenue|boulevard|boul\.)\s+[^,\n\|\"]{5,60}(?:,\s*Montr[ée]al[^,\n\|\"]{0,30})?)",
    re.I,
)

_DELIVERY_MODE = re.compile(
    r"\b(En personne(?:\s*,?\s*(?:et|&|ou)\s*(?:en ligne|sur Zoom|hybride|virtuel(?:lement)?)?)?|"
    r"(?:mode\s+)?hybride|en ligne|sur Zoom|virtuel(?:lement)?)\b",
    re.I,
)

_TIME_LABEL = re.compile(
    r"Time:\s*(\d{1,2}:\d{2}(?:\s*(?:to|–|-)\s*\d{1,2}:\d{2})?)",
    re.I,
)

_FR_TIME_RANGE = re.compile(
    r"(?:de|à partir de|from)\s+(\d{1,2}:\d{2}(?:\s*(?:à|au|to|-)\s*\d{1,2}:\d{2})?|\d{1,2}h\d{2}(?:\s*(?:à|au|to|-)\s*\d{1,2}h\d{2})?)",
    re.I,
)

_TIME_RANGE = re.compile(
    r"\b(\d{1,2}:\d{2}(?:\s*[-–]\s*\d{1,2}:\d{2})?\s*(?:AM|PM|am|pm)?)\b",
)

_FR_CLOCK = re.compile(r"\b(\d{1,2}h\d{2})\b", re.I)


def _clean_fragment(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip(" .|\"'")
    cleaned = re.sub(r"\s*View more.*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*Lire la suite.*$", "", cleaned, flags=re.I)
    return cleaned.strip()


def _is_plausible_location(value: str) -> bool:
    if len(value) < 4 or len(value) > 140:
        return False
    lower = value.lower()
    if lower in {"en personne", "online", "virtual", "hybrid"}:
        return True
    if re.fullmatch(r"\d{1,2}[h:]\d{0,2}.*", lower):
        return False
    if re.search(r"^(time|heure|date|register|inscription)\b", lower):
        return False
    return True


def extract_location(text: str) -> str | None:
    if not text:
        return None

    normalized = re.sub(r"\s+", " ", text).strip()
    candidates: list[str] = []

    for pattern in (_LOCATION_LABEL, _AT_LOCATION, _CAMPUS, _SALLE, _BUILDING, _ADDRESS):
        match = pattern.search(normalized)
        if match:
            candidates.append(_clean_fragment(match.group(1)))

    mode = _DELIVERY_MODE.search(normalized)
    if mode:
        candidates.append(_clean_fragment(mode.group(1)))

    for candidate in candidates:
        if _is_plausible_location(candidate):
            return candidate
    return None


def extract_time(text: str) -> str | None:
    if not text:
        return None

    normalized = re.sub(r"\s+", " ", text).strip()
    for pattern in (_TIME_LABEL, _FR_TIME_RANGE, _TIME_RANGE, _FR_CLOCK):
        match = pattern.search(normalized)
        if match:
            return match.group(1).strip()
    return None


def is_midnight_placeholder(dt: datetime) -> bool:
    local = dt.astimezone(MONTREAL) if dt.tzinfo else dt.replace(tzinfo=MONTREAL)
    return local.hour == 0 and local.minute == 0


def _parse_clock(token: str) -> tuple[int, int] | None:
    token = token.strip()
    match = re.match(r"(\d{1,2})h(\d{2})", token, re.I)
    if match:
        return int(match.group(1)), int(match.group(2))

    match = re.match(r"(\d{1,2}):(\d{2})", token)
    if match:
        return int(match.group(1)), int(match.group(2))

    parsed = parse_datetime(token)
    if parsed:
        return parsed.hour, parsed.minute
    return None


def apply_time_to_date(dt: datetime, time_text: str) -> datetime | None:
    if not time_text:
        return None

    start_token = re.split(r"\s*(?:to|–|-|à|au)\s*", time_text, maxsplit=1)[0].strip()
    clock = _parse_clock(start_token)
    if not clock:
        parsed = parse_datetime(time_text)
        if parsed:
            clock = (parsed.hour, parsed.minute)
        else:
            return None

    tz = dt.tzinfo or MONTREAL
    local = dt.astimezone(tz)
    hour, minute = clock
    return local.replace(hour=hour, minute=minute, second=0, microsecond=0)


def enrich_text_fields(
    *,
    title: str | None,
    description: str | None,
    location: str | None,
    start_date: datetime | None,
) -> tuple[str | None, datetime | None]:
    """Fill missing location and refine midnight-only start times from text blobs."""
    blobs = [blob for blob in (description, title) if blob]

    resolved_location = location
    if not resolved_location:
        for blob in blobs:
            resolved_location = extract_location(blob)
            if resolved_location:
                break

    resolved_start = start_date
    if resolved_start and is_midnight_placeholder(resolved_start):
        for blob in blobs:
            time_text = extract_time(blob)
            if not time_text:
                continue
            updated = apply_time_to_date(resolved_start, time_text)
            if updated and not is_midnight_placeholder(updated):
                resolved_start = updated
                break

    return resolved_location, resolved_start
