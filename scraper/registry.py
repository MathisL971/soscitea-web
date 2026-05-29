from __future__ import annotations

import json
from pathlib import Path

from scraper.adapters.base import BaseAdapter
from scraper.adapters.cic import CicAdapter
from scraper.adapters.cirst import CirstAdapter
from scraper.adapters.centres import (
    BellesHeuresAdapter,
    CireqAdapter,
    CiranoAdapter,
    CreAdapter,
    EnapAdapter,
    WordpressHeadingsAdapter,
)
from scraper.adapters.batch_b import (
    ConferenceMontrealAdapter,
    GrippAdapter,
    IrppEventsAdapter,
    ShiftAdapter,
    SqspCongressAdapter,
    UdemCalendrierAdapter,
)
from scraper.adapters.concordia import ConcordiaDepartmentAdapter, ConcordiaEventsAdapter
from scraper.adapters.cridaq import CridaqAdapter
from scraper.adapters.forum_americas import ForumAmericasAdapter
from scraper.adapters.linktree import LinktreeAdapter
from scraper.adapters.mcgill import McGillEventsAdapter, McGillSeminarsAdapter
from scraper.adapters.misc import (
    EventbriteAdapter,
    GenericAdapter,
    SkipAdapter,
    WordpressArchiveAdapter,
)
from scraper.adapters.udem_activites import UdemActivitesAdapter
from scraper.adapters.uqam import UqamCalendarAdapter
from scraper.adapters.wix import WixAdapter
from scraper.models import Source

ADAPTERS: dict[str, BaseAdapter] = {
    adapter.name: adapter
    for adapter in [
        UdemActivitesAdapter(),
        ConcordiaEventsAdapter(),
        ConcordiaDepartmentAdapter(),
        CicAdapter(),
        CirstAdapter(),
        CreAdapter(),
        EnapAdapter(),
        CiranoAdapter(),
        CireqAdapter(),
        BellesHeuresAdapter(),
        WordpressHeadingsAdapter(),
        UdemCalendrierAdapter(),
        IrppEventsAdapter(),
        GrippAdapter(),
        ShiftAdapter(),
        SqspCongressAdapter(),
        ConferenceMontrealAdapter(),
        CridaqAdapter(),
        WixAdapter(),
        ForumAmericasAdapter(),
        McGillEventsAdapter(),
        McGillSeminarsAdapter(),
        UqamCalendarAdapter(),
        LinktreeAdapter(),
        GenericAdapter(),
        SkipAdapter(),
        EventbriteAdapter(),
        WordpressArchiveAdapter(),
    ]
}


def load_sources(path: Path) -> list[Source]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Source.from_dict(item) for item in data]


def get_adapter(name: str) -> BaseAdapter:
    if name not in ADAPTERS:
        raise KeyError(f"Unknown adapter: {name}")
    return ADAPTERS[name]
