"""Re-tier sources.json: priority 1 = core Montreal SSH, 2 = broad/secondary, 3 = skip."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources.json"

# Explicit priority-1 core sources (by name substring match, case-insensitive).
CORE_MARKERS = (
    # University departments
    "udem political science",
    "concordia political science",
    "mcgill political science calendar",
    "uqam cepp",
    "concordia philosophy",
    "mcgill philosophy",
    "udem economics",
    "concordia economics news",
    "mcgill economics",
    "mcgill isid",
    "uqam esg economics",
    "concordia socio-anthro",
    "mcgill sociology",
    "mcgill sociology seminars",
    "mcgill misc",
    "mcgill anthropology",
    "udem sociology",
    "udem anthropology",
    "uqam socio-anthro",
    "concordia cissc",
    "mcgill psychology",
    "concordia psychology colloquia",
    "udem psychology",
    "uqam psychology",
    "mcgill history",
    "concordia arts & science events",
    "udem history",
    "uqam history",
    "mcgill religious studies",
    "uqam religious studies",
    "udem religious studies",
    # Research centres & institutes
    "cic",
    "canadian international council",
    "cridaq",
    "cré",
    "cirst —",
    "ceim",
    "celat",
    "crises",
    "enap events",
    "cirano",
    "cireq",
    "gripp",
    "irpp",
    "sqsp congress",
    "conférence de montréal",
    "forum americas",
    "mcgill deep",
    "mcgill cirm",
    "mcgill cipss",
    "mcgill lin centre",
    "concordia shift",
    "social justice centre",
    "streets café",
    "belles heures",
    "psgsa concordia",
    "montreal phil sci network",
)

# Broad feeds — useful but noisy; scrape with --priority 2.
BROAD_MARKERS = (
    "concordia all events",
    "uqam all events",
    "mcgill faculty of arts",
    "udem institutional calendar",
    "mcgill beatty",
    "concordia jurist",
    "sip read book",
)

# Always skip (defer, broken, or zero yield).
FORCE_SKIP_URLS = {
    "https://docs.google.com/document/d/1s4-KJamzKa6HSF3aNP3talvI-b1eAVIt1o_SdFis_tc/edit?tab=t.0",
    "https://framagenda.org/remote.php/dav/public-calendars/zQHSGsKNDxPwAFr6?export",
    "https://sqsp.uqam.ca/",
    "https://www.mcgill.ca/politicalscience/events",
    "https://www.ted.com/",
    "https://www.iarfconference.com/conf/index.php?id=2929184",
    "https://cupaconcordia.com/",
    "https://www.federationhss.ca/en",
    "https://www.aeepum.com/",
    "https://www.philo-uqam-cegep.com/liste/",
}

SKIP_ADAPTERS = {"linktree", "skip"}


def tier(source: dict) -> tuple[int, str | None]:
    url = source["url"]
    name = source["name"].lower()
    adapter = source.get("adapter", "")

    if url in FORCE_SKIP_URLS or adapter in SKIP_ADAPTERS:
        note = source.get("notes") or "Deferred — low yield or duplicate"
        return 3, note

    if adapter == "generic":
        return 3, source.get("notes") or "No parser — deferred until adapter exists"

    if any(m in name for m in CORE_MARKERS):
        return 1, source.get("notes")

    if any(m in name for m in BROAD_MARKERS):
        return 2, source.get("notes")

    if adapter in {"eventbrite", "wordpress_archive"}:
        return 2, source.get("notes")

    if source.get("priority", 2) == 1:
        return 1, source.get("notes")

    return 3, source.get("notes") or "Deferred — secondary source"


def main() -> None:
    items = json.loads(SOURCES.read_text(encoding="utf-8"))
    backup = ROOT / "sources.full.json"
    if not backup.exists():
        backup.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    counts = {1: 0, 2: 0, 3: 0}
    for item in items:
        priority, notes = tier(item)
        item["priority"] = priority
        if priority == 3 and item.get("adapter") not in SKIP_ADAPTERS:
            item["adapter"] = "skip"
        if notes:
            item["notes"] = notes
        counts[priority] += 1

    SOURCES.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {SOURCES.name}: priority 1={counts[1]}, 2={counts[2]}, 3={counts[3]}")
    print(f"Full backup: {backup.name}")


if __name__ == "__main__":
    main()
