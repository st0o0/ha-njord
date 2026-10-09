"""Shared horizon offset utilities for time-based enrichment lookups."""

from __future__ import annotations

from datetime import UTC, datetime


def current_horizon_offset(updated_at: datetime | None) -> int:
    if updated_at is None:
        return 0
    elapsed = (datetime.now(UTC) - updated_at).total_seconds()
    return max(0, int(elapsed // 3600))


def _parse_horizon(horizon: str) -> int:
    return int(horizon[1:])


def find_nearest_horizon[T](horizons: list[T], offset: int) -> T | None:
    if not horizons:
        return None
    best: T | None = None
    best_h = -1
    for entry in horizons:
        h = _parse_horizon(entry.horizon)  # type: ignore[attr-defined]
        if h >= offset and (best is None or h < best_h):
            best = entry
            best_h = h
    if best is not None:
        return best
    return horizons[-1]
