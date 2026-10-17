"""Shared helpers for njord entity construction."""

from __future__ import annotations

from collections.abc import Collection

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_DISABLED_ENRICHMENT_GROUPS, DOMAIN, EnrichmentGroup, parse_enrichment_groups


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


def disabled_groups_of(entry: ConfigEntry) -> frozenset[EnrichmentGroup]:
    """Enrichment groups the user disabled; unknown stored names are ignored."""
    return parse_enrichment_groups(entry.options.get(CONF_DISABLED_ENRICHMENT_GROUPS, []))


def group_enabled(
    group: EnrichmentGroup,
    active: Collection[str] | None,
    disabled: Collection[str],
) -> bool:
    """A group is enabled when the server reports it active (or no list) and the user did not disable it."""
    return (active is None or group in active) and group not in disabled
