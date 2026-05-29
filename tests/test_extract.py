from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from scraper.extract import apply_time_to_date, enrich_text_fields, extract_location, extract_time, is_midnight_placeholder

MONTREAL = ZoneInfo("America/Montreal")


def test_extract_location_from_mcgill_description() -> None:
    text = (
        'Time: 12:00 to 13:00 Location: Leacock Building 855 rue Sherbrooke Ouest, '
        'Montreal, QC, H3A 2T7, CA "Monopsony Power and Structural Change"'
    )
    assert extract_location(text) == "Leacock Building 855 rue Sherbrooke Ouest, Montreal, QC, H3A 2T7, CA"


def test_extract_location_from_campus_phrase() -> None:
    text = "Symposium international & ADIMAP 2026 Du 1er au 3 juin 2026 Campus de Québec"
    assert extract_location(text) == "Campus de Québec"


def test_extract_location_from_at_salle() -> None:
    text = "Séminaire @ Salle 309, CRÉ, mode hybride"
    assert extract_location(text) == "Salle 309, CRÉ, mode hybride"


def test_extract_time_from_english_label() -> None:
    text = "Tuesday, June 2, 2026 Time: 12:00 to 13:00 Location: Leacock 429"
    assert extract_time(text) == "12:00 to 13:00"


def test_extract_time_from_french_range() -> None:
    text = "Mardi 2 juin 2026 de 17:00 à 19:00 En personne"
    assert extract_time(text) == "17:00 à 19:00"


def test_enrich_text_fields_fills_location_and_time() -> None:
    description = (
        "Francesco Amodio (McGill University) Tuesday, June 2, 2026 "
        "Time: 12:00 to 13:00 Location: Leacock 429 View more"
    )
    start = datetime(2026, 6, 2, 0, 0, tzinfo=MONTREAL)
    location, updated_start = enrich_text_fields(
        title="Seminar",
        description=description,
        location=None,
        start_date=start,
    )
    assert location == "Leacock 429"
    assert updated_start is not None
    assert is_midnight_placeholder(updated_start) is False
    local = updated_start.astimezone(MONTREAL)
    assert local.hour == 12
    assert local.minute == 0


def test_apply_time_to_date_french_clock() -> None:
    start = datetime(2026, 6, 2, 0, 0, tzinfo=MONTREAL)
    updated = apply_time_to_date(start, "17h00")
    assert updated is not None
    assert updated.astimezone(MONTREAL).hour == 17
