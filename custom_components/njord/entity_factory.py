"""Factory that creates HA entities from the njord manifest."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry

from .models import ManifestEntity
from .stream_coordinator import NjordV3Coordinator


def create_sensors(
    manifest: list[ManifestEntity],
    coordinator: NjordV3Coordinator,
    entry: ConfigEntry,
    sw_version: str | None,
) -> list:
    """Create sensor entities for all non-alert, non-weather manifest entries."""
    from .entities import NjordV3Sensor

    return [
        NjordV3Sensor(coordinator, entry, e, sw_version) for e in manifest if e.output_kind not in ("alert", "weather")
    ]


def create_binary_sensors(
    manifest: list[ManifestEntity],
    coordinator: NjordV3Coordinator,
    entry: ConfigEntry,
    sw_version: str | None,
) -> list:
    """Create binary sensor entities for alert manifest entries."""
    from .entities import NjordV3AlertBinarySensor

    return [NjordV3AlertBinarySensor(coordinator, entry, e, sw_version) for e in manifest if e.output_kind == "alert"]


def create_weather_entities(
    manifest: list[ManifestEntity],
    coordinator: NjordV3Coordinator,
    entry: ConfigEntry,
    sw_version: str | None,
) -> list:
    """Create weather entities for weather manifest entries."""
    from .weather import NjordV3WeatherEntity

    return [NjordV3WeatherEntity(coordinator, entry, e, sw_version) for e in manifest if e.output_kind == "weather"]
