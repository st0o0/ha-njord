"""Binary sensor platform for njord alerts."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NjordStatusCoordinator


def _get_sw_version(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    status_coordinator: NjordStatusCoordinator | None = hass.data[DOMAIN][entry.entry_id].get("status_coordinator")
    if status_coordinator is not None and status_coordinator.data is not None:
        return status_coordinator.data.version or None
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord binary sensor entities."""
    sw_version = _get_sw_version(hass, entry)

    entities: list[BinarySensorEntity] = []

    coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
    if coordinator is not None:
        from .entity_factory import create_binary_sensors

        entities.extend(create_binary_sensors(coordinator.manifest, coordinator, entry, sw_version))

    async_add_entities(entities)
