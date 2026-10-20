"""Constants for the njord integration."""

from __future__ import annotations

from collections.abc import Collection
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


class Domain(StrEnum):
    """Data domains njord serves through GetDomainData / StreamDomainData."""

    UNSPECIFIED = "unspecified"
    WEATHER = "weather"
    AIR_QUALITY = "air_quality"
    FLOOD = "flood"
    MARINE = "marine"
    SEASONAL = "seasonal"
    SATELLITE = "satellite"

    @classmethod
    def _missing_(cls, value: object) -> Domain:
        return cls.UNSPECIFIED


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
    DUST = "dust"
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
    AlertType.DUST: AlertMeta("Dust Alert", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, "mdi:weather-dust", 1),
    AlertType.FLOOD_RISK: AlertMeta("Flood Risk Alert", DISCHARGE_UNIT, "mdi:home-flood", 1),
    AlertType.FLOOD_RAIN: AlertMeta("Flood Rain Alert", "mm", "mdi:weather-pouring", 1),
    AlertType.SWIMMING_CONDITIONS: AlertMeta("Swimming Conditions Alert", UnitOfLength.METERS, "mdi:swim", 1),
}


class Feature(StrEnum):
    """Njord features as identified by the EnrichmentEvent oneof case (alerts, scores, conditions, trends, forecasts)."""

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
    DUST = "dust"
    FLOOD_RISK = "flood_risk"
    FLOOD_RAIN = "flood_rain"
    SWIMMING_CONDITIONS = "swimming_conditions"
    BBQ = "bbq"
    LAUNDRY = "laundry"
    OUTDOOR = "outdoor"
    SURF_CONDITIONS = "surf_conditions"
    COMMUTE_SAFETY = "commute_safety"
    VENTILATION_WINDOW = "ventilation_window"
    NIGHT_VENTILATION = "night_ventilation"
    EXERCISE_ADVISORY = "exercise_advisory"
    GARDENING = "gardening"
    FLOOD_TIMELINE = "flood_timeline"
    SOLAR_YIELD = "solar_yield"
    SATELLITE_RADIATION = "satellite_radiation"
    APPROACHING_FRONT = "approaching_front"
    CONFIDENCE_TREND = "confidence_trend"
    POLLEN_TREND = "pollen_trend"
    SEASONAL_OUTLOOK = "seasonal_outlook"


# njord's `<Category>:<Name>` toggle key per feature, as listed in StatusResponse.active_enrichments.
FEATURE_KEYS: dict[Feature, str] = {
    Feature.FROST: "Weather:Frost",
    Feature.HEAT: "Weather:Heat",
    Feature.STORM: "Weather:Storm",
    Feature.HEAVY_RAIN: "Weather:HeavyRain",
    Feature.UV: "Weather:Uv",
    Feature.FOG: "Weather:Fog",
    Feature.SNOW: "Weather:Snow",
    Feature.PRESSURE_DROP: "Weather:PressureDrop",
    Feature.THUNDERSTORM: "Weather:Thunderstorm",
    Feature.ICE: "Weather:Ice",
    Feature.WIND_CHILL: "Weather:WindChill",
    Feature.VISIBILITY: "Weather:Visibility",
    Feature.TROPICAL_NIGHT: "Weather:TropicalNight",
    Feature.HUMIDITY: "Weather:Humidity",
    Feature.POLLEN: "AirQuality:Pollen",
    Feature.PM25: "AirQuality:Pm25",
    Feature.DUST: "AirQuality:Dust",
    Feature.POLLEN_TREND: "AirQuality:PollenTrend",
    Feature.FLOOD_RISK: "Flood:FloodRisk",
    Feature.FLOOD_RAIN: "Flood:FloodRain",
    Feature.FLOOD_TIMELINE: "Flood:FloodTimeline",
    Feature.SWIMMING_CONDITIONS: "Marine:Swimming",
    Feature.SURF_CONDITIONS: "Marine:Surf",
    Feature.COMMUTE_SAFETY: "Lifestyle:Commute",
    Feature.EXERCISE_ADVISORY: "Lifestyle:Exercise",
    Feature.LAUNDRY: "Lifestyle:Laundry",
    Feature.OUTDOOR: "Lifestyle:Outdoor",
    Feature.BBQ: "Lifestyle:Bbq",
    Feature.NIGHT_VENTILATION: "Lifestyle:NightVentilation",
    Feature.VENTILATION_WINDOW: "Lifestyle:Ventilation",
    Feature.GARDENING: "Lifestyle:Gardening",
    Feature.CONFIDENCE_TREND: "Insight:ConfidenceTrend",
    Feature.APPROACHING_FRONT: "Insight:FrontApproaching",
    Feature.SEASONAL_OUTLOOK: "Insight:SeasonalOutlook",
    Feature.SOLAR_YIELD: "Energy:SolarYield",
    Feature.SATELLITE_RADIATION: "Energy:SatelliteRadiation",
}


def feature_enabled(feature: Feature, active: Collection[str] | None) -> bool:
    """Whether njord runs the feature; an unknown or empty active set means every feature is enabled."""
    if not active:
        return True
    return FEATURE_KEYS[feature].lower() in {key.lower() for key in active}


def alert_type_of(feature: Feature) -> AlertType:
    """The alert type of an alert feature; UNSPECIFIED for every other feature."""
    return AlertType(feature.value)


def enabled_alert_types(active: Collection[str] | None) -> list[AlertType]:
    """Alert types njord runs, in entity creation order."""
    return [t for t in ALERT_META if feature_enabled(Feature(t.value), active)]
