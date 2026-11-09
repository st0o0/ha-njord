"""Typed data models for njord API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .const import PollPhase

# --- Status ---


@dataclass(frozen=True)
class BudgetStatusData:
    monthly_limit: int = 0
    monthly_used: int = 0
    daily_limit: int = 0
    daily_used: int = 0
    usage_percent: float = 0.0


@dataclass(frozen=True)
class LocationStatusData:
    location: str
    phase: PollPhase = PollPhase.UNSPECIFIED
    next_poll: datetime | None = None
    last_change: datetime | None = None
    miss_count: int = 0
    cycle_seconds: int | None = None


@dataclass(frozen=True)
class ServerStatusData:
    version: str = ""
    uptime_seconds: int = 0
    budget: BudgetStatusData | None = None
    process_start: datetime | None = None
    location_statuses: list[LocationStatusData] = field(default_factory=list)
    active_enrichments: list[str] = field(default_factory=list)
    budget_partial: bool = False
    models_partial: bool = False


# --- Entity models ---


@dataclass(frozen=True)
class ManifestEntity:
    """An entity definition from the njord manifest."""

    entity_id: str
    location: str
    feature: str
    platform: str  # "weather", "sensor", "binary_sensor"
    device_class: str
    unit: str
    icon: str
    category: str
    output_kind: str  # "alert", "score", "condition", "trend", "forecast", "weather", "observation"


@dataclass(frozen=True)
class EntityState:
    """Current state of an entity."""

    entity_id: str
    value: Any
    updated_at: datetime | None = None
    available: bool = True
