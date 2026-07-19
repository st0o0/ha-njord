"""Binary sensor platform for njord derived metrics."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NjordDataCoordinator
from .models import NjordLocation


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord binary sensor entities."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[BinarySensorEntity] = []

    locations = {loc for loc, _ in coordinator.data.forecasts}

    for location in sorted(locations):
        enrichment = coordinator.data.enrichments.get(location)
        if enrichment and enrichment.derived is not None:
            entities.append(NjordInversionEntity(coordinator, entry, location))

    async_add_entities(entities)

    def binary_sensor_factory(location: NjordLocation) -> list[BinarySensorEntity]:
        new_entities: list[BinarySensorEntity] = []
        enrichment = coordinator.data.enrichments.get(location.name)
        if enrichment and enrichment.derived is not None:
            new_entities.append(NjordInversionEntity(coordinator, entry, location.name))
        return new_entities

    coordinator.register_entity_factory("binary_sensor", async_add_entities, binary_sensor_factory)


class NjordInversionEntity(CoordinatorEntity[NjordDataCoordinator], BinarySensorEntity):
    """Binary sensor for temperature inversion detection."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:arrow-collapse-vertical"
    _attr_translation_key = "inversion"

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
    ) -> None:
        super().__init__(coordinator)
        self._location = location

        slug = f"{location}_inversion".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Inversion"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{location}")},
            name=f"njord {location}",
            manufacturer="njord",
            model=location,
            entry_type=None,
        )

    @property
    def available(self) -> bool:
        if self.coordinator.data is None:
            return False
        enrichment = self.coordinator.data.enrichments.get(self._location)
        return enrichment is not None and enrichment.derived is not None

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        enrichment = self.coordinator.data.enrichments.get(self._location)
        if enrichment is None or enrichment.derived is None:
            return None
        return enrichment.derived.inversion
