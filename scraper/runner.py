from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from scraper.browser import close_browser
from scraper.db import EventStore
from scraper.enrich import finalize_status
from scraper.http import create_client
from scraper.registry import get_adapter, load_sources

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCES = ROOT / "sources.json"
DEFAULT_DB = ROOT / "data" / "events.db"
DEFAULT_EXPORT = ROOT / "data" / "upcoming_events.json"
ARCHIVE_EXPORT = ROOT / "data" / "all_events.json"


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run_scrape(
    *,
    sources_path: Path = DEFAULT_SOURCES,
    db_path: Path = DEFAULT_DB,
    export_path: Path | None = DEFAULT_EXPORT,
    archive_path: Path | None = ARCHIVE_EXPORT,
    priority_max: int = 3,
    adapter_filter: str | None = None,
) -> int:
    logger = logging.getLogger("scraper.runner")
    sources = load_sources(sources_path)
    sources = [s for s in sources if s.priority <= priority_max]
    if adapter_filter:
        sources = [s for s in sources if s.adapter == adapter_filter]

    store = EventStore(db_path)
    store.init_schema()
    store.clear_events()
    run_id = store.start_run()

    total_events = 0
    ok = 0
    failed = 0

    try:
        with create_client() as client:
            for source in sources:
                adapter = get_adapter(source.adapter)
                logger.info("Scraping %s via %s", source.name, source.adapter)
                try:
                    events = adapter.scrape(client, source)
                    events = [finalize_status(e) for e in events]
                    count = store.upsert_events(events)
                    total_events += count
                    ok += 1
                    logger.info("  -> %d events", count)
                except Exception as exc:
                    failed += 1
                    logger.error("  -> failed: %s", exc)
                    store.log_error(
                        run_id,
                        source_url=source.url,
                        source_name=source.name,
                        adapter=source.adapter,
                        error=str(exc),
                    )
    finally:
        close_browser()

    store.finish_run(
        run_id,
        sources_ok=ok,
        sources_failed=failed,
        events_found=total_events,
    )

    upcoming_count = 0
    if export_path:
        payload = store.export_json(export_path, upcoming_only=True)
        upcoming_count = int(payload["event_count"])
        logger.info("Exported %d upcoming events to %s", upcoming_count, export_path)

    if archive_path:
        store.export_json(archive_path, upcoming_only=False)
        logger.info("Archived full inventory to %s", archive_path)

    logger.info(
        "Done: %d sources ok, %d failed, %d raw events, %d upcoming in export",
        ok,
        failed,
        total_events,
        upcoming_count,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Montreal social-science events scraper (nightly inventory refresh)",
    )
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--archive", type=Path, default=ARCHIVE_EXPORT)
    parser.add_argument("--no-export", action="store_true")
    parser.add_argument("--priority", type=int, default=1, help="Max source priority (1=core, 2=+broad, 3=all)")
    parser.add_argument("--adapter", type=str, default=None, help="Run only this adapter")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)
    return run_scrape(
        sources_path=args.sources,
        db_path=args.db,
        export_path=None if args.no_export else args.export,
        archive_path=None if args.no_export else args.archive,
        priority_max=args.priority,
        adapter_filter=args.adapter,
    )


if __name__ == "__main__":
    sys.exit(main())
