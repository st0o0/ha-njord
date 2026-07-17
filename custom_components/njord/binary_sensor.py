"""Binary sensor platform for njord weather alerts."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NjordDataCoordinator
from .models import AlertData, NjordLocation

ALERT_TYPES = [
    "frost",
    "heat",
    "storm",
    "heavy_rain",
    "uv",
    "fog",
    "snow",
    "pressure_drop",
    "thunderstorm",
]

ALERT_NAMES = {
    "frost": "Frost",
    "heat": "Heat",
    "storm": "Storm",
    "heavy_rain": "Heavy Rain",
    "uv": "UV",
    "fog": "Fog",
    "snow": "Snow",
    "pressure_drop": "Pressure Drop",
    "thunderstorm": "Thunderstorm",
}

ALERT_ICONS = {
    "frost": "mdi:snowflake-alert",
    "heat": "mdi:thermometer-alert",
    "storm": "mdi:weather-hurricane",
    "heavy_rain": "mdi:weather-pouring",
    "uv": "mdi:sun-wireless",
    "fog": "mdi:weather-fog",
    "snow": "mdi:snowflake",
    "pressure_drop": "mdi:gauge-low",
    "thunderstorm": "mdi:weather-lightning",
}


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
        for alert_type in ALERT_TYPES:
            entities.append(NjordAlertEntity(coordinator, entry, location, alert_type))

        enrichment = coordinator.data.enrichments.get(location)
        if enrichment and enrichment.derived is not None:
            entities.append(NjordInversionEntity(coordinator, entry, location))

    async_add_entities(entities)

    def binary_sensor_factory(location: NjordLocation) -> list[BinarySensorEntity]:
        new_entities: list[BinarySensorEntity] = []
        for alert_type in ALERT_TYPES:
            new_entities.append(NjordAlertEntity(coordinator, entry, location.name, alert_type))
        enrichment = coordinator.data.enrichments.get(location.name)
        if enrichment and enrichment.derived is not None:
            new_entities.append(NjordInversionEntity(coordinator, entry, location.name))
        return new_entities

    coordinator.register_entity_factory("binary_sensor", async_add_entities, binary_sensor_factory)


class NjordAlertEntity(CoordinatorEntity[NjordDataCoordinator], BinarySensorEntity):
    """Binary sensor for a njord weather alert."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        alert_type: str,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._alert_type = alert_type

        slug = f"{location}_{alert_type}_alert".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_translation_key = f"{alert_type}_alert"
        self._attr_name = f"{ALERT_NAMES.get(alert_type, alert_type)} Alert"
        self._attr_icon = ALERT_ICONS.get(alert_type, "mdi:alert")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{location}")},
            name=f"njord {location}",
            manufacturer="njord",
            model=location,
            entry_type=None,
        )

    def _get_alert(self) -> AlertData | None:
        if self.coordinator.data is None:
            return None
        enrichment = self.coordinator.data.enrichments.get(self._location)
        if enrichment is None:
            return None
        for alert in enrichment.alerts:
            if alert.type == self._alert_type:
                return alert
        return None

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None and self._location in self.coordinator.data.enrichments

    @property
    def is_on(self) -> bool | None:
        alert = self._get_alert()
        if alert is None:
            return None
        return alert.severity != "none"

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        alert = self._get_alert()
        if alert is None:
            return None
        return {
            "severity": alert.severity,
            "confidence": alert.confidence,
        }


class NjordInversionEntity(CoordinatorEntity[NjordDataCoordinator], BinarySensorEntity):
    """Binary sensor for temperature inversion detection."""

    _attr_has_entity_name = True
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
