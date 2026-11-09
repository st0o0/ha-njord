"""Sensor platform for njord entities and server diagnostics."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NjordStatusCoordinator
from .helpers import server_device_info, slugify_location


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
    """Set up njord sensor entities."""
    sw_version = _get_sw_version(hass, entry)

    entities: list[SensorEntity] = []

    status_coordinator: NjordStatusCoordinator | None = hass.data[DOMAIN][entry.entry_id].get("status_coordinator")
    if status_coordinator is not None:
        entities.append(NjordMonthlyUsageSensor(status_coordinator, entry, sw_version))
        entities.append(NjordDailyUsageSensor(status_coordinator, entry, sw_version))
        entities.append(NjordVersionSensor(status_coordinator, entry, sw_version))
        entities.append(NjordUptimeSensor(status_coordinator, entry, sw_version))

        if status_coordinator.data is not None:
            for loc_status in status_coordinator.data.location_statuses:
                entities.append(NjordTargetSensor(status_coordinator, entry, loc_status.location, sw_version))

    v3_coordinator = hass.data[DOMAIN][entry.entry_id].get("v3_coordinator")
    if v3_coordinator is not None:
        from .entity_factory import create_v3_sensors

        entities.extend(create_v3_sensors(v3_coordinator.manifest, v3_coordinator, entry, sw_version))

    async_add_entities(entities)


class NjordMonthlyUsageSensor(CoordinatorEntity[NjordStatusCoordinator], SensorEntity):
    """Diagnostic sensor for monthly API usage percentage."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "%"
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:calendar-month"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: NjordStatusCoordinator, entry: ConfigEntry, sw_version: str | None = None) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_monthly_usage"
        self._attr_translation_key = "monthly_usage"
        self._attr_device_info = server_device_info(entry, sw_version)

    @property
    def available(self) -> bool:
        return (
            self.coordinator.data is not None
            and not self.coordinator.data.budget_partial
            and self.coordinator.data.budget is not None
            and self.coordinator.data.budget.monthly_limit > 0
        )

    @property
    def native_value(self) -> float | None:
        status = self.coordinator.data
        if status is None or status.budget is None or status.budget.monthly_limit == 0:
            return None
        return round(status.budget.monthly_used / status.budget.monthly_limit * 100, 1)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        status = self.coordinator.data
        if status is None or status.budget is None:
            return None
        return {
            "limit": status.budget.monthly_limit,
            "used": status.budget.monthly_used,
        }


class NjordDailyUsageSensor(CoordinatorEntity[NjordStatusCoordinator], SensorEntity):
    """Diagnostic sensor for daily API usage percentage."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "%"
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:calendar-today"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: NjordStatusCoordinator, entry: ConfigEntry, sw_version: str | None = None) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_usage"
        self._attr_translation_key = "daily_usage"
        self._attr_device_info = server_device_info(entry, sw_version)

    @property
    def available(self) -> bool:
        return (
            self.coordinator.data is not None
            and not self.coordinator.data.budget_partial
            and self.coordinator.data.budget is not None
            and self.coordinator.data.budget.daily_limit > 0
        )

    @property
    def native_value(self) -> float | None:
        status = self.coordinator.data
        if status is None or status.budget is None or status.budget.daily_limit == 0:
            return None
        return round(status.budget.daily_used / status.budget.daily_limit * 100, 1)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        status = self.coordinator.data
        if status is None or status.budget is None:
            return None
        return {
            "limit": status.budget.daily_limit,
            "used": status.budget.daily_used,
        }


class NjordVersionSensor(CoordinatorEntity[NjordStatusCoordinator], SensorEntity):
    """Diagnostic sensor for njord server version."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:tag"

    def __init__(self, coordinator: NjordStatusCoordinator, entry: ConfigEntry, sw_version: str | None = None) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_version"
        self._attr_translation_key = "version"
        self._attr_device_info = server_device_info(entry, sw_version)

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None

    @property
    def native_value(self) -> str | None:
        status = self.coordinator.data
        if status is None:
            return None
        return status.version.split("+")[0]


class NjordUptimeSensor(CoordinatorEntity[NjordStatusCoordinator], SensorEntity):
    """Diagnostic sensor for njord server uptime."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:server"
    _attr_translation_key = "uptime"

    def __init__(self, coordinator: NjordStatusCoordinator, entry: ConfigEntry, sw_version: str | None = None) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_uptime"
        self._attr_device_info = server_device_info(entry, sw_version)

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None

    @property
    def native_value(self) -> float | None:
        status = self.coordinator.data
        if status is None:
            return None
        return round(status.uptime_seconds / 3600, 1)


class NjordTargetSensor(CoordinatorEntity[NjordStatusCoordinator], SensorEntity):
    """Diagnostic sensor showing the next poll of a location."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:radar"

    def __init__(
        self,
        coordinator: NjordStatusCoordinator,
        entry: ConfigEntry,
        location: str,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._target_location = location
        self._attr_unique_id = f"{entry.entry_id}_{slugify_location(location)}_target"
        self._attr_translation_placeholders = {"location": location}
        self._attr_translation_key = "target_poll"
        self._attr_device_info = server_device_info(entry, sw_version)

    def _find_target(self):
        if self.coordinator.data is None:
            return None
        for t in self.coordinator.data.location_statuses:
            if t.location == self._target_location:
                return t
        return None

    @property
    def available(self) -> bool:
        return self._find_target() is not None

    @property
    def native_value(self):
        t = self._find_target()
        if t is None or t.next_poll is None:
            return None
        return t.next_poll

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        t = self._find_target()
        if t is None:
            return None
        attrs: dict[str, object] = {
            "phase": t.phase.value,
            "miss_count": t.miss_count,
        }
        if t.last_change is not None:
            attrs["last_change"] = t.last_change.isoformat()
        if t.cycle_seconds is not None:
            attrs["cycle_seconds"] = t.cycle_seconds
        return attrs
