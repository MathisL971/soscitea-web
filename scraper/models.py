from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventStatus(str, Enum):
    UPCOMING = "upcoming"
    PAST = "past"
    TBD = "tbd"


@dataclass
class Source:
    url: str
    name: str
    discipline: str
    adapter: str
    priority: int = 2
    org_id: int | None = None
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Source:
        return cls(
            url=data["url"],
            name=data["name"],
            discipline=data["discipline"],
            adapter=data["adapter"],
            priority=data.get("priority", 2),
            org_id=data.get("org_id"),
            notes=data.get("notes"),
        )


@dataclass
class Event:
    title: str
    source_url: str
    source_name: str
    discipline: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    description: str | None = None
    location: str | None = None
    url: str | None = None
    status: EventStatus = EventStatus.UPCOMING
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def fingerprint(self) -> str:
        parts = [
            self.source_url,
            _normalize(self.title),
            self.start_date.isoformat() if self.start_date else "",
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]

    def to_row(self) -> dict[str, Any]:
        return {
            "id": self.fingerprint(),
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "location": self.location,
            "url": self.url,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "discipline": self.discipline,
            "status": self.status.value,
            "scraped_at": self.scraped_at.isoformat(),
        }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())
