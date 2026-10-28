"""Binary sensor platform for njord alerts and stream health."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ALERT_META,
    DOMAIN,
    AlertSeverity,
    AlertType,
    Domain,
    Feature,
    StreamName,
    enabled_alert_types,
    feature_enabled,
)
from .coordinator import NjordDataCoordinator, NjordStatusCoordinator
from .helpers import device_info, server_device_info, slugify_location
from .lifestyle import LIFESTYLE_BINARY_SENSORS, LifestyleBinarySensorDescription
from .models import AlertData, FeatureData
from .sensor import _attributes


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
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sw_version = _get_sw_version(hass, entry)

    def alert_entities(location: str) -> list[BinarySensorEntity]:
        alert_types = enabled_alert_types(coordinator.data.active_enrichments)
        return [NjordAlertBinarySensor(coordinator, entry, location, t, sw_version) for t in alert_types]

    def feature_entities(location: str, feature: Feature) -> list[BinarySensorEntity]:
        return [
            NjordLifestyleBinarySensor(coordinator, entry, location, description, sw_version)
            for description in LIFESTYLE_BINARY_SENSORS
            if description.feature == feature
        ]

    entities: list[BinarySensorEntity] = []
    for location, feature in sorted(coordinator.data.features):
        if feature_enabled(feature, coordinator.data.active_enrichments):
            entities.extend(feature_entities(location, feature))
    for location in coordinator.data.locations_with(Domain.FORECAST):
        entities.extend(alert_entities(location))

    for stream_name in StreamName:
        entities.append(NjordStreamSensor(coordinator, entry, stream_name, sw_version))

    async_add_entities(entities)

    def binary_sensor_factory(location: str, domain: Domain) -> list[BinarySensorEntity]:
        # Alerts are per location: they are created when the location's weather domain first appears.
        return alert_entities(location) if domain == Domain.FORECAST else []

    coordinator.register_entity_factory("binary_sensor", async_add_entities, binary_sensor_factory)
    coordinator.register_feature_factory("binary_sensor", async_add_entities, feature_entities)


class NjordAlertBinarySensor(CoordinatorEntity[NjordDataCoordinator], BinarySensorEntity):
    """Binary sensor that is on while an alert of one type is active at a location."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        alert_type: AlertType,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._alert_type = alert_type
        meta = ALERT_META[alert_type]
        self._unit = meta.unit
        self._attr_unique_id = f"{entry.entry_id}_{slugify_location(location)}_{alert_type}_alert"
        self._attr_name = meta.name
        self._attr_icon = meta.icon
        self._attr_device_info = device_info(entry, location, sw_version)

    def _get_alert(self) -> AlertData | None:
        if self.coordinator.data is None:
            return None
        item = self.coordinator.data.features.get((self._location, Feature(self._alert_type.value)))
        return item.alert if item is not None else None

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None

    @property
    def is_on(self) -> bool:
        alert = self._get_alert()
        return alert is not None and alert.severity != AlertSeverity.NONE

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        alert = self._get_alert()
        if alert is None or alert.severity == AlertSeverity.NONE:
            return None
        attrs: dict[str, object] = {
            "severity": alert.severity,
            "confidence": alert.confidence,
            "trigger_value": alert.trigger_value,
            "threshold": alert.threshold,
            "unit": self._unit,
        }
        if alert.peak_value is not None:
            attrs["peak_value"] = alert.peak_value
        if alert.hours_until is not None:
            attrs["hours_until"] = alert.hours_until
        if alert.duration_hours is not None:
            attrs["duration_hours"] = alert.duration_hours
        return attrs


class NjordLifestyleBinarySensor(CoordinatorEntity[NjordDataCoordinator], BinarySensorEntity):
    """Binary sensor for one lifestyle advisory of a location."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        description: LifestyleBinarySensorDescription,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{slugify_location(location)}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        if description.device_class is not None:
            self._attr_device_class = BinarySensorDeviceClass(description.device_class)
        self._attr_device_info = device_info(entry, location, sw_version)

    def _item(self) -> FeatureData | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.features.get((self._location, self._description.feature))

    @property
    def available(self) -> bool:
        return self._item() is not None

    @property
    def is_on(self) -> bool | None:
        item = self._item()
        if item is None:
            return None
        return self._description.is_on_fn(item)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        item = self._item()
        if item is None:
            return None
        attrs: dict[str, object] = _attributes(item)
        if item.updated_at is not None:
            attrs["updated_at"] = item.updated_at.isoformat()
        return attrs


class NjordStreamSensor(CoordinatorEntity[NjordDataCoordinator], BinarySensorEntity):
    """Binary sensor for gRPC stream connection state."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    _STREAM_NAMES = {
        StreamName.DOMAIN: "Domain Data Stream",
        StreamName.ENRICHMENT: "Enrichment Stream",
    }

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        stream_name: StreamName,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._stream_name = stream_name
        self._attr_unique_id = f"{entry.entry_id}_{stream_name}_stream"
        self._attr_name = self._STREAM_NAMES.get(stream_name, f"{stream_name} Stream")
        self._attr_translation_key = f"{stream_name}_stream"
        self._attr_device_info = server_device_info(entry, sw_version)

    @property
    def is_on(self) -> bool:
        return self.coordinator.stream_states.get(self._stream_name, False)
