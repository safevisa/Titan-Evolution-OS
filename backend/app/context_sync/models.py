"""Context Sync domain types."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

SyncSource = Literal["gmail", "gcal", "github"]


@dataclass
class FetchedItem:
    external_id: str
    source: SyncSource
    title: str
    body_text: str
    occurred_at: datetime
    url: str | None = None
    raw_meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestStats:
    ingested: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
