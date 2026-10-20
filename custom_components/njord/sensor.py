"""Sensor platform for njord domain data and server diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    DEGREE,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, Domain
from .coordinator import NjordDataCoordinator, NjordStatusCoordinator
from .helpers import current_point, device_info, server_device_info, slugify_location
from .models import DomainData

POLLEN_UNIT = "grains/m³"


@dataclass(frozen=True, kw_only=True)
class DomainSensorDescription:
    """One sensor reading a field of the current sample of a domain."""

    key: str
    name: str
    domain: Domain
    field: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    icon: str | None = None
    precision: int | None = None
    extra_fields: tuple[str, ...] = ()
    value_fn: Callable[[object], float | None] | None = None


DOMAIN_SENSORS: tuple[DomainSensorDescription, ...] = (
    DomainSensorDescription(
        key="pm25",
        name="PM2.5",
        domain=Domain.AIR_QUALITY,
        field="pm25",
        unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.PM25,
        precision=1,
    ),
    DomainSensorDescription(
        key="pm10",
        name="PM10",
        domain=Domain.AIR_QUALITY,
        field="pm10",
        unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.PM10,
        precision=1,
    ),
    DomainSensorDescription(
        key="ozone",
        name="Ozone",
        domain=Domain.AIR_QUALITY,
        field="ozone",
        unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.OZONE,
        precision=1,
    ),
    DomainSensorDescription(
        key="birch_pollen",
        name="Birch Pollen",
        domain=Domain.AIR_QUALITY,
        field="birch_pollen",
        unit=POLLEN_UNIT,
        icon="mdi:flower-pollen",
        precision=1,
    ),
    DomainSensorDescription(
        key="grass_pollen",
        name="Grass Pollen",
        domain=Domain.AIR_QUALITY,
        field="grass_pollen",
        unit=POLLEN_UNIT,
        icon="mdi:flower-pollen",
        precision=1,
    ),
    DomainSensorDescription(
        key="alder_pollen",
        name="Alder Pollen",
        domain=Domain.AIR_QUALITY,
        field="alder",
        unit=POLLEN_UNIT,
        icon="mdi:flower-pollen",
        precision=1,
    ),
    DomainSensorDescription(
        key="mugwort_pollen",
        name="Mugwort Pollen",
        domain=Domain.AIR_QUALITY,
        field="mugwort",
        unit=POLLEN_UNIT,
        icon="mdi:flower-pollen",
        precision=1,
    ),
    DomainSensorDescription(
        key="river_discharge",
        name="River Discharge",
        domain=Domain.FLOOD,
        field="discharge",
        unit=UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        icon="mdi:waves-arrow-right",
        precision=1,
        extra_fields=(
            "discharge_mean",
            "discharge_median",
            "discharge_max",
            "discharge_min",
            "discharge_p25",
            "discharge_p75",
        ),
    ),
    DomainSensorDescription(
        key="wave_height",
        name="Wave Height",
        domain=Domain.MARINE,
        field="wave_height",
        unit=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        icon="mdi:waves",
        precision=1,
    ),
    DomainSensorDescription(
        key="wave_period",
        name="Wave Period",
        domain=Domain.MARINE,
        field="wave_period",
        unit=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:sine-wave",
        precision=1,
    ),
    DomainSensorDescription(
        key="wave_direction",
        name="Wave Direction",
        domain=Domain.MARINE,
        field="wave_direction",
        unit=DEGREE,
        icon="mdi:compass-outline",
        precision=0,
    ),
    DomainSensorDescription(
        key="water_temperature",
        name="Water Temperature",
        domain=Domain.MARINE,
        field="water_temperature",
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        precision=1,
    ),
)


def _get_sw_version(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    status_coordinator: NjordStatusCoordinator | None = hass.data[DOMAIN][entry.entry_id].get("status_coordinator")
    if status_coordinator is not None and status_coordinator.data is not None:
        return status_coordinator.data.version or None
    return None


def _domain_sensors(
    coordinator: NjordDataCoordinator, entry: ConfigEntry, location: str, domain: Domain, sw_version: str | None
) -> list[SensorEntity]:
    return [
        NjordDomainSensor(coordinator, entry, location, description, sw_version)
        for description in DOMAIN_SENSORS
        if description.domain == domain
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord sensor entities."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sw_version = _get_sw_version(hass, entry)

    entities: list[SensorEntity] = []
    for location, domain in sorted(coordinator.data.domains, key=lambda key: (key[0], key[1].value)):
        entities.extend(_domain_sensors(coordinator, entry, location, domain, sw_version))

    status_coordinator: NjordStatusCoordinator | None = hass.data[DOMAIN][entry.entry_id].get("status_coordinator")
    if status_coordinator is not None:
        entities.append(NjordMonthlyUsageSensor(status_coordinator, entry, sw_version))
        entities.append(NjordDailyUsageSensor(status_coordinator, entry, sw_version))
        entities.append(NjordVersionSensor(status_coordinator, entry, sw_version))
        entities.append(NjordUptimeSensor(status_coordinator, entry, sw_version))

        if status_coordinator.data is not None:
            for target in status_coordinator.data.targets:
                entities.append(NjordTargetSensor(status_coordinator, entry, target.location, sw_version))

    async_add_entities(entities)

    def sensor_factory(location: str, domain: Domain) -> list[SensorEntity]:
        return _domain_sensors(coordinator, entry, location, domain, sw_version)

    coordinator.register_entity_factory("sensor", async_add_entities, sensor_factory)


class NjordDomainSensor(CoordinatorEntity[NjordDataCoordinator], SensorEntity):
    """Sensor for one field of the current sample of a domain at a location."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        description: DomainSensorDescription,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{slugify_location(location)}_{description.key}"
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class
        self._attr_icon = description.icon
        self._attr_suggested_display_precision = description.precision
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = device_info(entry, location, sw_version)

    def _data(self) -> DomainData | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.domains.get((self._location, self._description.domain))

    def _sample(self):
        data = self._data()
        if data is None:
            return None
        return current_point(data.points)

    @property
    def available(self) -> bool:
        return self._sample() is not None

    @property
    def native_value(self) -> float | None:
        sample = self._sample()
        if sample is None:
            return None
        return getattr(sample, self._description.field, None)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        sample = self._sample()
        data = self._data()
        if sample is None or data is None:
            return None
        attrs: dict[str, object] = {"valid_at": sample.valid_at.isoformat()}
        if data.model_run is not None:
            attrs["model_run"] = data.model_run.isoformat()
        for name in self._description.extra_fields:
            value = getattr(sample, name, None)
            if value is not None:
                attrs[name] = value
        return attrs


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
        self._attr_name = "Monthly Usage"
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
        self._attr_name = "Daily Usage"
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
        self._attr_name = "Version"
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
        self._attr_name = "Uptime"
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
        self._attr_name = f"Poll {location}"
        self._attr_translation_key = "target_poll"
        self._attr_device_info = server_device_info(entry, sw_version)

    def _find_target(self):
        if self.coordinator.data is None:
            return None
        for t in self.coordinator.data.targets:
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
