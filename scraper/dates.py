from __future__ import annotations

import re
from datetime import datetime, timezone

import dateparser


_LANGUAGES = ["fr", "en"]
_SETTINGS = {
    "RETURN_AS_TIMEZONE_AWARE": True,
    "TIMEZONE": "America/Montreal",
    "PREFER_DAY_OF_MONTH": "first",
}

_DATE_IN_TEXT = re.compile(
    r"(\d{1,2}\s+"
    r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre|"
    r"january|february|march|april|may|june|july|august|september|october|november|december)"
    r"(?:\s+\d{4})?"
    r"(?:,\s*\d{1,2}h\d{0,2}(?:\s*(?:à|au|-)\s*\d{1,2}h\d{0,2})?)?"
    r"(?:\s+\d{4})?)",
    re.I,
)

_EN_MONTH_DATE = re.compile(
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}(?:-\d{1,2})?,?\s+\d{4})",
    re.I,
)

_YEAR_IN_TEXT = re.compile(r"\b(20\d{2})\b")

_URL_YEAR = re.compile(r"[-_/](20\d{2})(?:[/_]|$)")

_ORDINAL = re.compile(r"\b(\d{1,2})\s*(st|nd|rd|th)\b", re.I)

_FR_ORDINAL_DATE = re.compile(
    r"(\d{1,2}(?:er|e|ème)?\s+"
    r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)"
    r"\s+\d{4})",
    re.I,
)

_URL_PATH_DATE = re.compile(r"/(\d{4})/(\d{2})(?:/(\d{2}))?(?:/|\.|(?:[/?#]|$))")


def normalize_date_text(text: str) -> str:
    if not text:
        return ""
    cleaned = _ORDINAL.sub(r"\1", text)
    cleaned = re.sub(r"\s+,", ",", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_datetime(text: str, *, base: datetime | None = None) -> datetime | None:
    if not text or not text.strip():
        return None
    cleaned = normalize_date_text(text.strip())
    cleaned = re.sub(r"\b(\d{1,2})(?:er|e|ème)\b", r"\1", cleaned, flags=re.I)
    return dateparser.parse(
        cleaned,
        languages=_LANGUAGES,
        settings={**_SETTINGS, "RELATIVE_BASE": base or datetime.now(timezone.utc)},
    )


def parse_date_range(text: str) -> tuple[datetime | None, datetime | None]:
    """Parse strings like '7 mai, 14h00 au 16 juin 2026, 15h30'."""
    if not text:
        return None, None

    cleaned = re.sub(r"\s+", " ", text.strip())
    for sep in [" au ", " à ", " - ", " – ", " to "]:
        idx = cleaned.lower().find(sep.strip())
        if idx > 0:
            left = cleaned[:idx].strip(" ,-")
            right = cleaned[idx + len(sep) :].strip(" ,-")
            if not re.search(r"\d{4}", right):
                year_match = re.search(r"\d{4}", left)
                if year_match:
                    right = f"{right} {year_match.group()}"
            start = parse_datetime(left)
            end = parse_datetime(right)
            if start or end:
                return start, end

    single = parse_datetime(cleaned)
    return single, None


def find_dates_in_text(text: str) -> tuple[datetime | None, datetime | None]:
    if not text:
        return None, None
    start, end = parse_date_range(text)
    if start:
        return start, end
    match = _DATE_IN_TEXT.search(text)
    if match:
        return parse_datetime(match.group(1)), None
    match = _EN_MONTH_DATE.search(text)
    if match:
        return parse_datetime(match.group(1)), None
    match = _FR_ORDINAL_DATE.search(text)
    if match:
        return parse_datetime(match.group(1)), None
    return None, None


def find_dates_in_html(html: str) -> tuple[datetime | None, datetime | None]:
    """Parse dates from rendered HTML body text (not raw markup truncation)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    start, end = find_dates_in_text(soup.get_text(" ", strip=True))
    if start:
        return start, end

    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        for key in ("startDate", "start_time", "datePublished"):
            match = re.search(rf'"{key}"\s*:\s*"([^"]+)"', script.string)
            if match:
                parsed = parse_datetime(match.group(1))
                if parsed:
                    return parsed, None
    return None, None


def date_from_url(url: str) -> datetime | None:
    if not url:
        return None
    match = _URL_PATH_DATE.search(url)
    if not match:
        return None
    year, month, day = match.group(1), match.group(2), match.group(3) or "01"
    return parse_datetime(f"{year}-{month}-{day}")


def year_from_url(url: str) -> int | None:
    if not url:
        return None
    match = _URL_YEAR.search(url)
    if match:
        return int(match.group(1))
    return None


def latest_year_in_text(text: str) -> int | None:
    if not text:
        return None
    years = [int(y) for y in _YEAR_IN_TEXT.findall(text)]
    return max(years) if years else None
