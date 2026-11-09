"""Tests for the v3 entity factory."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.njord.entity_factory import create_binary_sensors, create_sensors
from custom_components.njord.models import ManifestEntity


def _entity(
    entity_id: str = "vienna_frost",
    output_kind: str = "alert",
    platform: str = "binary_sensor",
    **kwargs,
) -> ManifestEntity:
    defaults = {
        "location": "Vienna",
        "feature": "Frost",
        "device_class": "",
        "unit": "",
        "icon": "",
        "category": "Forecast",
    }
    defaults.update(kwargs)
    return ManifestEntity(entity_id=entity_id, output_kind=output_kind, platform=platform, **defaults)


def test_sensors_exclude_alerts_and_weather():
    manifest = [
        _entity("vienna_frost", "alert"),
        _entity("vienna_weather", "weather"),
        _entity("vienna_outdoor", "score", "sensor"),
        _entity("vienna_pm25_observation", "observation", "sensor"),
    ]
    sensors = create_sensors(manifest, MagicMock(), MagicMock(), None)
    assert len(sensors) == 2


def test_binary_sensors_only_alerts():
    manifest = [
        _entity("vienna_frost", "alert"),
        _entity("vienna_heat", "alert", feature="Heat"),
        _entity("vienna_outdoor", "score", "sensor"),
    ]
    sensors = create_binary_sensors(manifest, MagicMock(), MagicMock(), None)
    assert len(sensors) == 2


def test_empty_manifest_produces_no_entities():
    assert create_sensors([], MagicMock(), MagicMock(), None) == []
    assert create_binary_sensors([], MagicMock(), MagicMock(), None) == []
