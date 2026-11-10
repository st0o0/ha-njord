"""Shared helpers for njord entity construction."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DOMAIN


class _Timed(Protocol):
    valid_at: datetime


def slugify_location(location: str) -> str:
    return location.replace("-", "_").replace(" ", "_").lower()


def entity_name_from_id(entity_id: str, location: str) -> str | None:
    """Derive a human-readable entity name from the njord entity_id.

    Strips the location slug prefix and converts the remainder to title case.
    Returns None for weather entities (they use the device name alone).
    """
    prefix = slugify_location(location) + "_"
    if not entity_id.startswith(prefix):
        return entity_id.replace("_", " ").title()
    suffix = entity_id[len(prefix):]
    if suffix == "weather" or suffix.endswith("_weather"):
        return None
    return suffix.replace("_", " ").title()


def device_info(entry: ConfigEntry, location: str, sw_version: str | None = None) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{location}")},
        name=location.title(),
        manufacturer="njord",
        model="Weather Station",
        sw_version=sw_version,
        entry_type=None,
    )


def server_device_info(entry: ConfigEntry, sw_version: str | None = None) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_server")},
        name="Server",
        manufacturer="njord",
        model="Weather Service",
        sw_version=sw_version,
        entry_type=None,
    )


def current_point[T: _Timed](points: Sequence[T], now: datetime | None = None) -> T | None:
    """The latest sample at or before now, else the first sample."""
    if not points:
        return None
    now = now or dt_util.utcnow()
    current = None
    for point in points:
        if point.valid_at <= now:
            current = point
        else:
            break
    return current if current is not None else points[0]
