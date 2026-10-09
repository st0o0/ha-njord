"""Tests for horizon offset utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.njord.horizon import current_horizon_offset, find_nearest_horizon
from custom_components.njord.models import HorizonDerivedData


def test_offset_after_2_5_hours() -> None:
    ts = datetime.now(UTC) - timedelta(hours=2, minutes=30)
    assert current_horizon_offset(ts) == 2


def test_offset_at_zero() -> None:
    ts = datetime.now(UTC) - timedelta(minutes=30)
    assert current_horizon_offset(ts) == 0


def test_offset_never_negative() -> None:
    ts = datetime.now(UTC) + timedelta(hours=1)
    assert current_horizon_offset(ts) == 0


def test_offset_none_returns_zero() -> None:
    assert current_horizon_offset(None) == 0


def test_nearest_before_first_horizon() -> None:
    horizons = [
        HorizonDerivedData(horizon="h3", beaufort=4),
        HorizonDerivedData(horizon="h6", beaufort=5),
        HorizonDerivedData(horizon="h12", beaufort=3),
        HorizonDerivedData(horizon="h24", beaufort=2),
    ]
    result = find_nearest_horizon(horizons, 0)
    assert result is not None
    assert result.beaufort == 4


def test_nearest_exact_match() -> None:
    horizons = [
        HorizonDerivedData(horizon="h3", beaufort=4),
        HorizonDerivedData(horizon="h6", beaufort=5),
        HorizonDerivedData(horizon="h12", beaufort=3),
        HorizonDerivedData(horizon="h24", beaufort=2),
    ]
    result = find_nearest_horizon(horizons, 6)
    assert result is not None
    assert result.beaufort == 5


def test_nearest_between_horizons() -> None:
    horizons = [
        HorizonDerivedData(horizon="h3", beaufort=4),
        HorizonDerivedData(horizon="h6", beaufort=5),
        HorizonDerivedData(horizon="h12", beaufort=3),
        HorizonDerivedData(horizon="h24", beaufort=2),
    ]
    result = find_nearest_horizon(horizons, 4)
    assert result is not None
    assert result.beaufort == 5


def test_nearest_beyond_all_clamps_to_last() -> None:
    horizons = [
        HorizonDerivedData(horizon="h3", beaufort=4),
        HorizonDerivedData(horizon="h6", beaufort=5),
        HorizonDerivedData(horizon="h12", beaufort=3),
        HorizonDerivedData(horizon="h24", beaufort=2),
    ]
    result = find_nearest_horizon(horizons, 100)
    assert result is not None
    assert result.beaufort == 2


def test_nearest_consensus_h0_unchanged() -> None:
    horizons = [
        HorizonDerivedData(horizon="h0", beaufort=1),
        HorizonDerivedData(horizon="h1", beaufort=2),
        HorizonDerivedData(horizon="h2", beaufort=3),
        HorizonDerivedData(horizon="h3", beaufort=4),
    ]
    result = find_nearest_horizon(horizons, 0)
    assert result is not None
    assert result.beaufort == 1


def test_nearest_empty_list() -> None:
    result = find_nearest_horizon([], 0)
    assert result is None
