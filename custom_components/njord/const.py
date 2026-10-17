"""Constants for the njord integration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

DOMAIN = "njord"

DEFAULT_PORT = 8081
DEFAULT_STATUS_POLL_INTERVAL = 30

# Config entry data keys (HA's own constants where they exist) and option keys.
__all__ = ["CONF_HOST", "CONF_PORT"]
CONF_STATUS_POLL_INTERVAL = "status_poll_interval"
CONF_DISABLED_ENRICHMENT_GROUPS = "disabled_enrichment_groups"
CONF_ENABLED_ENRICHMENT_GROUPS = "enabled_enrichment_groups"
CONF_SENSOR_PUSH = "sensor_push"


class EnrichmentGroup(StrEnum):
    """Enrichment groups njord reports as active and the user can disable."""

    ALERTS = "alerts"
    INDICES = "indices"
    TRENDS = "trends"
    DERIVED = "derived"
    CONSENSUS = "consensus"


def parse_enrichment_groups(values: Iterable[str] | None) -> frozenset[EnrichmentGroup]:
    """Convert stored or reported group names, ignoring unknown (legacy) names."""
    known = {group.value: group for group in EnrichmentGroup}
    return frozenset(known[value] for value in values or () if value in known)


class StreamName(StrEnum):
    """Streaming connections tracked by the coordinator."""

    FORECAST = "forecast"
    ENRICHMENT = "enrichment"
    CONFIG = "config"


class SensorKind(StrEnum):
    """External sensor kinds that can be pushed to njord."""

    INDOOR_TEMPERATURE = "indoor_temperature"
    INDOOR_HUMIDITY = "indoor_humidity"


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


class TrendDirection(_WireEnum):
    """Direction of a parameter trend."""

    UNSPECIFIED = "unspecified"
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"


class Stability(_WireEnum):
    """Forecast stability label."""

    UNSPECIFIED = "unspecified"
    CONVERGING = "converging"
    DIVERGING = "diverging"
    STABLE = "stable"


class DewPointComfort(_WireEnum):
    """Dew point comfort category."""

    UNSPECIFIED = "unspecified"
    DRY = "dry"
    COMFORTABLE = "comfortable"
    STICKY = "sticky"
    OPPRESSIVE = "oppressive"
    DANGEROUS = "dangerous"


class VpdCategory(_WireEnum):
    """Vapour pressure deficit category."""

    UNSPECIFIED = "unspecified"
    LOW = "low"
    OPTIMAL = "optimal"
    HIGH = "high"
    CRITICAL = "critical"


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
}
