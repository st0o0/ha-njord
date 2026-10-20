"""Constants for the njord integration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONF_HOST,
    CONF_PORT,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

DOMAIN = "njord"

DISCHARGE_UNIT = "m³/s"

DEFAULT_PORT = 8081
DEFAULT_STATUS_POLL_INTERVAL = 30

# Config entry data keys (HA's own constants where they exist) and option keys.
__all__ = ["CONF_HOST", "CONF_PORT"]
CONF_STATUS_POLL_INTERVAL = "status_poll_interval"
CONF_ENABLED_ENRICHMENTS = "enabled_enrichments"


class Domain(StrEnum):
    """Data domains njord serves through GetDomainData / StreamDomainData."""

    UNSPECIFIED = "unspecified"
    WEATHER = "weather"
    AIR_QUALITY = "air_quality"
    FLOOD = "flood"
    SOLAR = "solar"
    MARINE = "marine"

    @classmethod
    def _missing_(cls, value: object) -> Domain:
        return cls.UNSPECIFIED


class Enrichment(StrEnum):
    """Enrichment toggles (alerts and lifestyle advisories), named like njord's EnrichmentOptions keys in snake_case."""

    WEATHER_ALERTS = "weather_alerts"
    POLLEN_ALERT = "pollen_alert"
    PM25_ALERT = "pm25_alert"
    FLOOD_RISK = "flood_risk"
    FLOOD_RAIN = "flood_rain"
    SWIMMING_CONDITIONS = "swimming_conditions"
    COMMUTE_SAFETY = "commute_safety"
    VENTILATION_WINDOW = "ventilation_window"
    EXERCISE_ADVISORY = "exercise_advisory"
    LAUNDRY_SCORE = "laundry_score"
    POLLEN_TREND = "pollen_trend"
    NIGHT_VENTILATION = "night_ventilation"
    CONFIDENCE_TREND = "confidence_trend"
    SOLAR_YIELD = "solar_yield"
    GARDENING_ADVISORY = "gardening_advisory"
    OUTDOOR_SCORE = "outdoor_score"
    BBQ_SCORE = "bbq_score"
    FLOOD_TIMELINE = "flood_timeline"
    APPROACHING_FRONT = "approaching_front"
    CLIMATE_ANOMALY = "climate_anomaly"


# Enrichments njord enables by default (EnrichmentOptions property initializers).
DEFAULT_ENABLED_ENRICHMENTS: frozenset[Enrichment] = frozenset(
    {Enrichment.WEATHER_ALERTS, Enrichment.COMMUTE_SAFETY, Enrichment.POLLEN_ALERT, Enrichment.PM25_ALERT}
)


def parse_enrichments(values: Iterable[str] | None) -> frozenset[Enrichment]:
    """Convert stored enrichment names, ignoring unknown names."""
    known = {item.value: item for item in Enrichment}
    return frozenset(known[value] for value in values or () if value in known)


class StreamName(StrEnum):
    """Streaming connections tracked by the coordinator."""

    DOMAIN = "domain"
    ENRICHMENT = "enrichment"


class AlertEvent(StrEnum):
    """Event types fired by the weather alert event entity."""

    STARTED = "alert_started"
    ESCALATED = "alert_escalated"
    DEESCALATED = "alert_deescalated"
    CLEARED = "alert_cleared"


class AlertSeverity(StrEnum):
    """Alert severity as exposed by njord; unknown values read as NONE."""

    NONE = "none"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"

    @classmethod
    def _missing_(cls, value: object) -> AlertSeverity:
        return cls.NONE

    @property
    def rank(self) -> int:
        return _SEVERITY_RANK[self]


_SEVERITY_RANK: dict[AlertSeverity, int] = {
    AlertSeverity.NONE: 0,
    AlertSeverity.YELLOW: 1,
    AlertSeverity.ORANGE: 2,
    AlertSeverity.RED: 3,
}


class AlertType(StrEnum):
    """Alert types as exposed by njord; unknown values read as UNSPECIFIED."""

    UNSPECIFIED = "unspecified"
    FROST = "frost"
    HEAT = "heat"
    STORM = "storm"
    HEAVY_RAIN = "heavy_rain"
    UV = "uv"
    FOG = "fog"
    SNOW = "snow"
    PRESSURE_DROP = "pressure_drop"
    THUNDERSTORM = "thunderstorm"
    ICE = "ice"
    WIND_CHILL = "wind_chill"
    VISIBILITY = "visibility"
    TROPICAL_NIGHT = "tropical_night"
    HUMIDITY = "humidity"
    POLLEN = "pollen"
    PM25 = "pm25"
    FLOOD_RISK = "flood_risk"
    FLOOD_RAIN = "flood_rain"
    SWIMMING_CONDITIONS = "swimming_conditions"

    @classmethod
    def _missing_(cls, value: object) -> AlertType:
        return cls.UNSPECIFIED


class _WireEnum(StrEnum):
    """Base for closed-set text values delivered by njord; unknown values read as UNSPECIFIED."""

    @classmethod
    def _missing_(cls, value: object):
        return cls.UNSPECIFIED

    @property
    def is_known(self) -> bool:
        return self.value != "unspecified"


class PollPhase(_WireEnum):
    """Poll phase of a (location, model) target."""

    UNSPECIFIED = "unspecified"
    DISCOVERY = "discovery"
    STEADY = "steady"


@dataclass(frozen=True)
class AlertMeta:
    name: str
    unit: str
    icon: str
    precision: int
    device_class: SensorDeviceClass | None = None


# Insertion order is the entity creation order. UNSPECIFIED has no entry and creates no entity.
ALERT_META: dict[AlertType, AlertMeta] = {
    AlertType.FROST: AlertMeta(
        "Frost Alert", UnitOfTemperature.CELSIUS, "mdi:snowflake-alert", 1, SensorDeviceClass.TEMPERATURE
    ),
    AlertType.HEAT: AlertMeta(
        "Heat Alert", UnitOfTemperature.CELSIUS, "mdi:thermometer-alert", 1, SensorDeviceClass.TEMPERATURE
    ),
    AlertType.STORM: AlertMeta(
        "Storm Alert", UnitOfSpeed.METERS_PER_SECOND, "mdi:weather-hurricane", 0, SensorDeviceClass.WIND_SPEED
    ),
    AlertType.HEAVY_RAIN: AlertMeta("Heavy Rain Alert", "mm", "mdi:weather-pouring", 1),
    AlertType.UV: AlertMeta("UV Alert", "UV", "mdi:sun-wireless", 0),
    AlertType.FOG: AlertMeta("Fog Alert", UnitOfLength.METERS, "mdi:weather-fog", 0, SensorDeviceClass.DISTANCE),
    AlertType.SNOW: AlertMeta("Snow Alert", UnitOfLength.CENTIMETERS, "mdi:snowflake", 0, SensorDeviceClass.DISTANCE),
    AlertType.PRESSURE_DROP: AlertMeta(
        "Pressure Drop Alert", UnitOfPressure.HPA, "mdi:gauge-low", 0, SensorDeviceClass.PRESSURE
    ),
    AlertType.THUNDERSTORM: AlertMeta(
        "Thunderstorm Alert", UnitOfSpeed.METERS_PER_SECOND, "mdi:weather-lightning", 0, SensorDeviceClass.WIND_SPEED
    ),
    AlertType.ICE: AlertMeta(
        "Ice Alert", UnitOfTemperature.CELSIUS, "mdi:snowflake-thermometer", 1, SensorDeviceClass.TEMPERATURE
    ),
    AlertType.WIND_CHILL: AlertMeta(
        "Wind Chill Alert", UnitOfTemperature.CELSIUS, "mdi:thermometer-minus", 1, SensorDeviceClass.TEMPERATURE
    ),
    AlertType.VISIBILITY: AlertMeta(
        "Visibility Alert", UnitOfLength.METERS, "mdi:eye-off", 0, SensorDeviceClass.DISTANCE
    ),
    AlertType.TROPICAL_NIGHT: AlertMeta(
        "Tropical Night Alert", UnitOfTemperature.CELSIUS, "mdi:weather-night", 1, SensorDeviceClass.TEMPERATURE
    ),
    AlertType.HUMIDITY: AlertMeta("Humidity Alert", PERCENTAGE, "mdi:water-percent", 0, SensorDeviceClass.HUMIDITY),
    AlertType.POLLEN: AlertMeta("Pollen Alert", "grains/m³", "mdi:flower-pollen", 1),
    AlertType.PM25: AlertMeta(
        "PM2.5 Alert", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, "mdi:blur", 1, SensorDeviceClass.PM25
    ),
    AlertType.FLOOD_RISK: AlertMeta("Flood Risk Alert", DISCHARGE_UNIT, "mdi:home-flood", 1),
    AlertType.FLOOD_RAIN: AlertMeta("Flood Rain Alert", "mm", "mdi:weather-pouring", 1),
    AlertType.SWIMMING_CONDITIONS: AlertMeta("Swimming Conditions Alert", UnitOfLength.METERS, "mdi:swim", 1),
}


# Alert types each enrichment toggle gates. Insertion order of ALERT_META is the entity creation order.
ENRICHMENT_ALERT_TYPES: dict[Enrichment, frozenset[AlertType]] = {
    Enrichment.WEATHER_ALERTS: frozenset(
        {
            AlertType.FROST,
            AlertType.HEAT,
            AlertType.STORM,
            AlertType.HEAVY_RAIN,
            AlertType.UV,
            AlertType.FOG,
            AlertType.SNOW,
            AlertType.PRESSURE_DROP,
            AlertType.THUNDERSTORM,
            AlertType.ICE,
            AlertType.WIND_CHILL,
            AlertType.VISIBILITY,
            AlertType.TROPICAL_NIGHT,
            AlertType.HUMIDITY,
        }
    ),
    Enrichment.POLLEN_ALERT: frozenset({AlertType.POLLEN}),
    Enrichment.PM25_ALERT: frozenset({AlertType.PM25}),
    Enrichment.FLOOD_RISK: frozenset({AlertType.FLOOD_RISK}),
    Enrichment.FLOOD_RAIN: frozenset({AlertType.FLOOD_RAIN}),
    Enrichment.SWIMMING_CONDITIONS: frozenset({AlertType.SWIMMING_CONDITIONS}),
}


def enabled_alert_types(enabled: Iterable[Enrichment]) -> list[AlertType]:
    """Alert types gated on by the enabled enrichments, in entity creation order."""
    allowed: set[AlertType] = set()
    for enrichment in enabled:
        allowed |= ENRICHMENT_ALERT_TYPES.get(enrichment, frozenset())
    return [alert_type for alert_type in ALERT_META if alert_type in allowed]


class LifestyleType(StrEnum):
    """Lifestyle advisory types as sent by njord (LifestyleUpdate.type)."""

    VENTILATION = "ventilation"
    EXERCISE = "exercise"
    LAUNDRY_SCORE = "laundry_score"
    COMMUTE_SAFETY = "commute_safety"
    POLLEN_TREND = "pollen_trend"
    NIGHT_VENTILATION = "night_ventilation"
    CONFIDENCE_TREND = "confidence_trend"
    SOLAR_YIELD = "solar_yield"
    GARDENING = "gardening"
    OUTDOOR_SCORE = "outdoor_score"
    BBQ_SCORE = "bbq_score"
    FLOOD_TIMELINE = "flood_timeline"
    FRONT_APPROACHING = "front_approaching"
    CLIMATE_ANOMALY = "climate_anomaly"


# The enrichment toggle that gates each lifestyle type.
LIFESTYLE_ENRICHMENT: dict[LifestyleType, Enrichment] = {
    LifestyleType.VENTILATION: Enrichment.VENTILATION_WINDOW,
    LifestyleType.EXERCISE: Enrichment.EXERCISE_ADVISORY,
    LifestyleType.LAUNDRY_SCORE: Enrichment.LAUNDRY_SCORE,
    LifestyleType.COMMUTE_SAFETY: Enrichment.COMMUTE_SAFETY,
    LifestyleType.POLLEN_TREND: Enrichment.POLLEN_TREND,
    LifestyleType.NIGHT_VENTILATION: Enrichment.NIGHT_VENTILATION,
    LifestyleType.CONFIDENCE_TREND: Enrichment.CONFIDENCE_TREND,
    LifestyleType.SOLAR_YIELD: Enrichment.SOLAR_YIELD,
    LifestyleType.GARDENING: Enrichment.GARDENING_ADVISORY,
    LifestyleType.OUTDOOR_SCORE: Enrichment.OUTDOOR_SCORE,
    LifestyleType.BBQ_SCORE: Enrichment.BBQ_SCORE,
    LifestyleType.FLOOD_TIMELINE: Enrichment.FLOOD_TIMELINE,
    LifestyleType.FRONT_APPROACHING: Enrichment.APPROACHING_FRONT,
    LifestyleType.CLIMATE_ANOMALY: Enrichment.CLIMATE_ANOMALY,
}


def enabled_lifestyle_types(enabled: Iterable[Enrichment]) -> frozenset[LifestyleType]:
    """Lifestyle types whose enrichment toggle is enabled."""
    enabled_set = set(enabled)
    return frozenset(kind for kind, toggle in LIFESTYLE_ENRICHMENT.items() if toggle in enabled_set)
