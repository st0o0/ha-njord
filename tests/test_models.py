"""Tests for v3 data models."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.njord.models import EntityState, ManifestEntity


def test_manifest_entity_from_kwargs():
    """ManifestEntity is a frozen dataclass with all fields."""
    entity = ManifestEntity(
        entity_id="vienna_frost",
        location="Vienna",
        feature="Frost",
        platform="binary_sensor",
        device_class="safety",
        unit="",
        icon="mdi:snowflake-alert",
        category="Forecast",
        output_kind="alert",
    )

    assert entity.entity_id == "vienna_frost"
    assert entity.platform == "binary_sensor"
    assert entity.output_kind == "alert"
    assert entity.location == "Vienna"


def test_manifest_entity_is_frozen():
    """ManifestEntity should be immutable."""
    entity = ManifestEntity(
        entity_id="x",
        location="L",
        feature="F",
        platform="sensor",
        device_class="",
        unit="",
        icon="",
        category="",
        output_kind="observation",
    )
    import pytest

    with pytest.raises(AttributeError):
        entity.entity_id = "y"  # type: ignore[misc]


def test_entity_state_defaults():
    """EntityState has sensible defaults."""
    state = EntityState(entity_id="vienna_frost", value=42.0)

    assert state.entity_id == "vienna_frost"
    assert state.value == 42.0
    assert state.updated_at is None
    assert state.available is True


def test_entity_state_with_timestamp():
    """EntityState can carry a timestamp and availability."""
    now = datetime(2026, 7, 11, 12, 0, 0, tzinfo=UTC)
    state = EntityState(
        entity_id="vienna_pm25_observation",
        value=12.5,
        updated_at=now,
        available=False,
    )

    assert state.updated_at == now
    assert state.available is False
