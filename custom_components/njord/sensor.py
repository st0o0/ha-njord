"""Sensor platform for njord enrichment data."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NjordDataCoordinator
from .models import AlertData, EnrichmentData, NjordLocation

INDEX_TYPES = [
    ("laundry", "Laundry Index", "mdi:tshirt-crew"),
    ("outdoor", "Outdoor Index", "mdi:pine-tree"),
    ("running", "Running Index", "mdi:run"),
    ("cycling", "Cycling Index", "mdi:bike"),
    ("bbq", "BBQ Index", "mdi:grill"),
    ("irrigation", "Irrigation Index", "mdi:sprinkler"),
    ("solar", "Solar Index", "mdi:solar-power"),
    ("ventilation", "Ventilation Index", "mdi:air-filter"),
]

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
    "frost": "Frost Alert",
    "heat": "Heat Alert",
    "storm": "Storm Alert",
    "heavy_rain": "Heavy Rain Alert",
    "uv": "UV Alert",
    "fog": "Fog Alert",
    "snow": "Snow Alert",
    "pressure_drop": "Pressure Drop Alert",
    "thunderstorm": "Thunderstorm Alert",
}

ALERT_UNITS = {
    "frost": "°C",
    "heat": "°C",
    "storm": "km/h",
    "heavy_rain": "mm",
    "uv": "UV",
    "fog": "m",
    "snow": "cm",
    "pressure_drop": "hPa",
    "thunderstorm": "J/kg",
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

ENERGY_SENSORS = [
    ("heating_demand", "Heating Demand", "%", "mdi:radiator"),
    ("cop_estimate", "COP Estimate", None, "mdi:heat-pump"),
    ("shading", "Shading", "%", "mdi:blinds"),
    ("battery_strategy", "Battery Strategy", None, "mdi:battery-charging"),
    ("night_cooling", "Night Cooling", "%", "mdi:weather-night"),
]


def _device_info(entry: ConfigEntry, location: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{location}")},
        name=f"njord {location}",
        manufacturer="njord",
        model=location,
        entry_type=None,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord sensor entities."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SensorEntity] = []
    locations = {loc for loc, _ in coordinator.data.forecasts}

    for location in sorted(locations):
        for alert_type in ALERT_TYPES:
            entities.append(NjordAlertSensor(coordinator, entry, location, alert_type))

        for key, name, icon in INDEX_TYPES:
            entities.append(NjordIndexSensor(coordinator, entry, location, key, name, icon))

        entities.append(NjordVpdSensor(coordinator, entry, location))

        for key, name, unit, icon in ENERGY_SENSORS:
            entities.append(NjordEnergySensor(coordinator, entry, location, key, name, unit, icon))

        entities.append(NjordTrendSensor(coordinator, entry, location))
        entities.append(NjordSunshineSensor(coordinator, entry, location))
        entities.append(NjordDiurnalAmplitudeSensor(coordinator, entry, location))
        entities.append(NjordHistorySensor(coordinator, entry, location))
        entities.append(NjordHddSensor(coordinator, entry, location))
        entities.append(NjordCddSensor(coordinator, entry, location))
        entities.append(NjordFrostHoursSensor(coordinator, entry, location))
        entities.append(NjordFrostConfidenceSensor(coordinator, entry, location))

    async_add_entities(entities)

    def sensor_factory(location: NjordLocation) -> list[SensorEntity]:
        new_entities: list[SensorEntity] = []
        for alert_type in ALERT_TYPES:
            new_entities.append(NjordAlertSensor(coordinator, entry, location.name, alert_type))
        for key, name, icon in INDEX_TYPES:
            new_entities.append(NjordIndexSensor(coordinator, entry, location.name, key, name, icon))
        new_entities.append(NjordVpdSensor(coordinator, entry, location.name))
        for key, name, unit, icon in ENERGY_SENSORS:
            new_entities.append(NjordEnergySensor(coordinator, entry, location.name, key, name, unit, icon))
        new_entities.append(NjordTrendSensor(coordinator, entry, location.name))
        new_entities.append(NjordSunshineSensor(coordinator, entry, location.name))
        new_entities.append(NjordDiurnalAmplitudeSensor(coordinator, entry, location.name))
        new_entities.append(NjordHistorySensor(coordinator, entry, location.name))
        new_entities.append(NjordHddSensor(coordinator, entry, location.name))
        new_entities.append(NjordCddSensor(coordinator, entry, location.name))
        new_entities.append(NjordFrostHoursSensor(coordinator, entry, location.name))
        new_entities.append(NjordFrostConfidenceSensor(coordinator, entry, location.name))
        return new_entities

    coordinator.register_entity_factory("sensor", async_add_entities, sensor_factory)


class _NjordEnrichmentSensor(CoordinatorEntity[NjordDataCoordinator], SensorEntity):
    """Base class for enrichment sensors."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._attr_device_info = _device_info(entry, location)

    def _enrichment(self) -> EnrichmentData | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.enrichments.get(self._location)


class NjordAlertSensor(_NjordEnrichmentSensor):
    """Sensor for a weather alert showing the trigger value."""

    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        alert_type: str,
    ) -> None:
        super().__init__(coordinator, entry, location)
        self._alert_type = alert_type
        slug = f"{location}_{alert_type}_alert".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = ALERT_NAMES.get(alert_type, f"{alert_type} Alert")
        self._attr_icon = ALERT_ICONS.get(alert_type, "mdi:alert")
        self._attr_native_unit_of_measurement = ALERT_UNITS.get(alert_type)

    def _get_alert(self) -> AlertData | None:
        enrichment = self._enrichment()
        if enrichment is None:
            return None
        for alert in enrichment.alerts:
            if alert.type == self._alert_type:
                return alert
        return None

    @property
    def available(self) -> bool:
        return self._enrichment() is not None

    @property
    def native_value(self) -> float | None:
        alert = self._get_alert()
        if alert is None:
            return None
        return alert.trigger_value

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        alert = self._get_alert()
        if alert is None:
            return None
        attrs: dict[str, object] = {
            "severity": alert.severity,
            "confidence": alert.confidence,
            "threshold": alert.threshold,
        }
        if alert.peak_value is not None:
            attrs["peak_value"] = alert.peak_value
        if alert.hours_until is not None:
            attrs["hours_until"] = alert.hours_until
        if alert.duration_hours is not None:
            attrs["duration_hours"] = alert.duration_hours
        return attrs


class NjordIndexSensor(_NjordEnrichmentSensor):
    """Sensor for an activity index (0-100)."""

    _attr_native_unit_of_measurement = "%"

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        index_key: str,
        index_name: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator, entry, location)
        self._index_key = index_key
        slug = f"{location}_{index_key}_index".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_translation_key = f"{index_key}_index"
        self._attr_name = index_name
        self._attr_icon = icon

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.indices is not None

    @property
    def native_value(self) -> int | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.indices is None:
            return None
        return getattr(enrichment.indices, self._index_key, None)


class NjordVpdSensor(_NjordEnrichmentSensor):
    """Sensor for Vapour Pressure Deficit."""

    _attr_native_unit_of_measurement = "kPa"
    _attr_icon = "mdi:water-percent"
    _attr_translation_key = "vpd"

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
    ) -> None:
        super().__init__(coordinator, entry, location)
        slug = f"{location}_vpd".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "VPD"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.indices is not None

    @property
    def native_value(self) -> float | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.indices is None:
            return None
        return enrichment.indices.vpd_kpa

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.indices is None:
            return None
        return {"category": enrichment.indices.vpd_category}


class NjordEnergySensor(_NjordEnrichmentSensor):
    """Sensor for an energy metric."""

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        energy_key: str,
        energy_name: str,
        unit: str | None,
        icon: str,
    ) -> None:
        super().__init__(coordinator, entry, location)
        self._energy_key = energy_key
        slug = f"{location}_{energy_key}".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_translation_key = energy_key
        self._attr_name = energy_name
        self._attr_icon = icon
        if unit:
            self._attr_native_unit_of_measurement = unit

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.energy is not None

    @property
    def native_value(self) -> object:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.energy is None:
            return None
        return getattr(enrichment.energy, self._energy_key, None)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        if self._energy_key != "cop_estimate":
            return None
        enrichment = self._enrichment()
        if enrichment is None or enrichment.energy is None:
            return None
        return {
            "cop_optimal": [{"hours_from_now": c.hours_from_now, "cop": c.cop} for c in enrichment.energy.cop_optimal]
        }


class NjordTrendSensor(_NjordEnrichmentSensor):
    """Sensor for weather trend stability."""

    _attr_icon = "mdi:trending-up"
    _attr_translation_key = "weather_trend"

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
    ) -> None:
        super().__init__(coordinator, entry, location)
        slug = f"{location}_weather_trend".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Weather Trend"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.trends is not None

    @property
    def native_value(self) -> str | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.trends is None:
            return None
        return enrichment.trends.stability_label

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.trends is None:
            return None
        t = enrichment.trends
        attrs: dict[str, object] = {}
        if t.precip_starts_in_hours is not None:
            attrs["precip_starts_in_hours"] = t.precip_starts_in_hours
        if t.precip_ends_in_hours is not None:
            attrs["precip_ends_in_hours"] = t.precip_ends_in_hours
        if t.temp_max_in_hours is not None:
            attrs["temp_max_in_hours"] = t.temp_max_in_hours
        if t.temp_min_in_hours is not None:
            attrs["temp_min_in_hours"] = t.temp_min_in_hours
        if t.reliable_hours is not None:
            attrs["reliable_hours"] = t.reliable_hours
        if t.stability_ratio is not None:
            attrs["stability_ratio"] = t.stability_ratio
        if t.decay_rate is not None:
            attrs["decay_rate"] = t.decay_rate
        if t.parameter_trends:
            attrs["parameter_trends"] = [
                {"parameter": p.parameter, "direction": p.direction, "delta": p.delta} for p in t.parameter_trends
            ]
        return attrs if attrs else None


class NjordSunshineSensor(_NjordEnrichmentSensor):
    """Sensor for sunshine percentage."""

    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:white-balance-sunny"
    _attr_translation_key = "sunshine"

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
    ) -> None:
        super().__init__(coordinator, entry, location)
        slug = f"{location}_sunshine_pct".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Sunshine"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.derived is not None

    @property
    def native_value(self) -> float | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.derived is None:
            return None
        return enrichment.derived.sunshine_pct


class NjordDiurnalAmplitudeSensor(_NjordEnrichmentSensor):
    """Sensor for diurnal temperature amplitude."""

    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:thermometer-lines"
    _attr_translation_key = "diurnal_amplitude"

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
    ) -> None:
        super().__init__(coordinator, entry, location)
        slug = f"{location}_diurnal_amplitude".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Diurnal Amplitude"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.derived is not None

    @property
    def native_value(self) -> float | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.derived is None:
            return None
        return enrichment.derived.diurnal_amplitude


class NjordHistorySensor(_NjordEnrichmentSensor):
    """Diagnostic sensor for model performance."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:chart-line"
    _attr_translation_key = "model_performance"

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
    ) -> None:
        super().__init__(coordinator, entry, location)
        slug = f"{location}_model_performance".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Model Performance"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.history is not None

    @property
    def native_value(self) -> float | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.history is None:
            return None
        return enrichment.history.weighted_temperature

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.history is None:
            return None
        h = enrichment.history
        attrs: dict[str, object] = {
            "models": [
                {
                    "model": m.model,
                    "mae_7d": m.mae_7d,
                    "mae_30d": m.mae_30d,
                    "weight": m.weight,
                    "drift": m.drift,
                }
                for m in h.models
            ],
        }
        if h.seasonal_best is not None:
            attrs["seasonal_best"] = h.seasonal_best
        if h.anomaly is not None:
            attrs["anomaly"] = h.anomaly
        if h.anomaly_deviation is not None:
            attrs["anomaly_deviation"] = h.anomaly_deviation
        return attrs


class NjordHddSensor(_NjordEnrichmentSensor):
    """Sensor for Heating Degree Days."""

    _attr_native_unit_of_measurement = "°C·d"
    _attr_icon = "mdi:thermometer-chevron-up"
    _attr_translation_key = "hdd"

    def __init__(self, coordinator, entry, location):
        super().__init__(coordinator, entry, location)
        slug = f"{location}_hdd".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Heating Degree Days"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.indices is not None

    @property
    def native_value(self) -> float | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.indices is None:
            return None
        return enrichment.indices.hdd


class NjordCddSensor(_NjordEnrichmentSensor):
    """Sensor for Cooling Degree Days."""

    _attr_native_unit_of_measurement = "°C·d"
    _attr_icon = "mdi:thermometer-chevron-down"
    _attr_translation_key = "cdd"

    def __init__(self, coordinator, entry, location):
        super().__init__(coordinator, entry, location)
        slug = f"{location}_cdd".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Cooling Degree Days"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.indices is not None

    @property
    def native_value(self) -> float | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.indices is None:
            return None
        return enrichment.indices.cdd


class NjordFrostHoursSensor(_NjordEnrichmentSensor):
    """Sensor for frost hours."""

    _attr_native_unit_of_measurement = "h"
    _attr_icon = "mdi:snowflake-thermometer"
    _attr_translation_key = "frost_hours"

    def __init__(self, coordinator, entry, location):
        super().__init__(coordinator, entry, location)
        slug = f"{location}_frost_hours".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Frost Hours"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.indices is not None

    @property
    def native_value(self) -> int | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.indices is None:
            return None
        return enrichment.indices.frost_hours


class NjordFrostConfidenceSensor(_NjordEnrichmentSensor):
    """Sensor for frost confidence as percentage."""

    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:snowflake-check"
    _attr_translation_key = "frost_confidence"

    def __init__(self, coordinator, entry, location):
        super().__init__(coordinator, entry, location)
        slug = f"{location}_frost_confidence".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Frost Confidence"

    @property
    def available(self) -> bool:
        enrichment = self._enrichment()
        return enrichment is not None and enrichment.indices is not None

    @property
    def native_value(self) -> float | None:
        enrichment = self._enrichment()
        if enrichment is None or enrichment.indices is None:
            return None
        if enrichment.indices.frost_confidence is None:
            return None
        return enrichment.indices.frost_confidence * 100
