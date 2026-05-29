from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from scraper.models import Event


class EventStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    location TEXT,
                    url TEXT,
                    source_url TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    discipline TEXT NOT NULL,
                    status TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    sources_ok INTEGER DEFAULT 0,
                    sources_failed INTEGER DEFAULT 0,
                    events_found INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS scrape_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    source_url TEXT NOT NULL,
                    source_name TEXT,
                    adapter TEXT,
                    error TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES scrape_runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_date);
                CREATE INDEX IF NOT EXISTS idx_events_discipline ON events(discipline);
                CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_url);
                """
            )

    def clear_events(self) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM events")
            conn.commit()

    def upsert_events(self, events: list[Event]) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            for event in events:
                row = event.to_row()
                conn.execute(
                    """
                    INSERT INTO events (
                        id, title, description, start_date, end_date, location, url,
                        source_url, source_name, discipline, status, scraped_at,
                        first_seen_at, last_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        description = excluded.description,
                        start_date = excluded.start_date,
                        end_date = excluded.end_date,
                        location = excluded.location,
                        url = excluded.url,
                        status = excluded.status,
                        scraped_at = excluded.scraped_at,
                        last_seen_at = excluded.last_seen_at
                    """,
                    (
                        row["id"],
                        row["title"],
                        row["description"],
                        row["start_date"],
                        row["end_date"],
                        row["location"],
                        row["url"],
                        row["source_url"],
                        row["source_name"],
                        row["discipline"],
                        row["status"],
                        row["scraped_at"],
                        now,
                        now,
                    ),
                )
            conn.commit()
        return len(events)

    def start_run(self) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO scrape_runs (started_at) VALUES (?)",
                (datetime.now(timezone.utc).isoformat(),),
            )
            conn.commit()
            return int(cur.lastrowid)

    def finish_run(
        self,
        run_id: int,
        *,
        sources_ok: int,
        sources_failed: int,
        events_found: int,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE scrape_runs
                SET finished_at = ?, sources_ok = ?, sources_failed = ?, events_found = ?
                WHERE id = ?
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    sources_ok,
                    sources_failed,
                    events_found,
                    run_id,
                ),
            )
            conn.commit()

    def log_error(
        self,
        run_id: int,
        *,
        source_url: str,
        source_name: str,
        adapter: str,
        error: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO scrape_errors (run_id, source_url, source_name, adapter, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    source_url,
                    source_name,
                    adapter,
                    error,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()

    def export_json(self, path: Path, *, upcoming_only: bool = False) -> dict[str, object]:
        from scraper.filters import filter_upcoming_events

        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY start_date IS NULL, start_date, title"
            ).fetchall()
            run = conn.execute(
                "SELECT sources_ok, sources_failed, finished_at FROM scrape_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()

        records = [dict(row) for row in rows]
        if upcoming_only:
            records = filter_upcoming_events(records)

        payload: dict[str, object] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "region": "Montreal, QC, Canada",
            "topic": "Social sciences (political science, philosophy, economics, sociology, anthropology, psychology, history, religious studies)",
            "event_count": len(records),
            "sources_ok": run["sources_ok"] if run else None,
            "sources_failed": run["sources_failed"] if run else None,
            "events": records,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return payload
