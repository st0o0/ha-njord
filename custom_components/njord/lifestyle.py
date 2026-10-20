"""Feature entity descriptions (scores, conditions, trends, forecasts) and value extraction."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.util import dt as dt_util

from .const import DISCHARGE_UNIT, Feature
from .models import FeatureData


def _text(key: str) -> Callable[[FeatureData], str | None]:
    return lambda item: item.values.get(key) or None


def _number(key: str) -> Callable[[FeatureData], float | None]:
    return lambda item: item.values.get(key)


def _time(key: str) -> Callable[[FeatureData], datetime | None]:
    return lambda item: item.values.get(key)


def _score(item: FeatureData) -> int | None:
    return item.score.score if item.score is not None else None


def _pollen_state(item: FeatureData) -> str:
    return item.values.get("peak_type") or "none"


def _first_anomaly(item: FeatureData) -> float | None:
    months = item.values.get("months") or []
    return months[0].get("temperature_anomaly") if months else None


@dataclass(frozen=True, kw_only=True)
class LifestyleSensorDescription:
    """A sensor fed by one feature; value_fn extracts the state from the feature's typed values."""

    feature: Feature
    key: str
    name: str
    icon: str
    value_fn: Callable[[FeatureData], object]
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    options: tuple[str, ...] | None = None
    precision: int | None = None


@dataclass(frozen=True, kw_only=True)
class LifestyleBinarySensorDescription:
    """A binary sensor fed by one feature; is_on_fn decides the state from the feature's typed values."""

    feature: Feature
    key: str
    name: str
    icon: str
    is_on_fn: Callable[[FeatureData], bool]
    device_class: str | None = None


def _ventilation_open(item: FeatureData) -> bool:
    start = item.values.get("best_start")
    end = item.values.get("best_end")
    if start is None or end is None:
        return False
    return start <= dt_util.utcnow() < end


def _planting_safe(item: FeatureData) -> bool:
    return bool(item.values.get("planting_safe"))


def _score_sensor(feature: Feature, key: str, name: str, icon: str) -> LifestyleSensorDescription:
    return LifestyleSensorDescription(
        feature=feature, key=key, name=name, icon=icon, value_fn=_score, unit="points", precision=0
    )


LIFESTYLE_SENSORS: tuple[LifestyleSensorDescription, ...] = (
    _score_sensor(Feature.LAUNDRY, "laundry_score", "Laundry Score", "mdi:tumble-dryer"),
    LifestyleSensorDescription(
        feature=Feature.COMMUTE_SAFETY,
        key="commute_safety",
        name="Commute Safety",
        icon="mdi:car-brake-alert",
        value_fn=_text("level"),
        device_class=SensorDeviceClass.ENUM,
        options=("safe", "caution", "dangerous"),
    ),
    LifestyleSensorDescription(
        feature=Feature.EXERCISE_ADVISORY,
        key="exercise",
        name="Exercise",
        icon="mdi:run",
        value_fn=_text("level"),
        device_class=SensorDeviceClass.ENUM,
        options=("safe", "caution", "avoid"),
    ),
    _score_sensor(Feature.OUTDOOR, "outdoor_score", "Outdoor Score", "mdi:pine-tree"),
    _score_sensor(Feature.BBQ, "bbq_score", "BBQ Score", "mdi:grill"),
    _score_sensor(Feature.SURF_CONDITIONS, "surf_conditions", "Surf Conditions", "mdi:surfing"),
    LifestyleSensorDescription(
        feature=Feature.POLLEN_TREND,
        key="pollen_trend",
        name="Pollen Trend",
        icon="mdi:flower-pollen",
        value_fn=_pollen_state,
    ),
    LifestyleSensorDescription(
        feature=Feature.NIGHT_VENTILATION,
        key="night_ventilation",
        name="Night Ventilation",
        icon="mdi:weather-night",
        value_fn=_time("open_at"),
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    LifestyleSensorDescription(
        feature=Feature.CONFIDENCE_TREND,
        key="confidence_trend",
        name="Forecast Confidence Trend",
        icon="mdi:chart-line",
        value_fn=_text("direction"),
    ),
    LifestyleSensorDescription(
        feature=Feature.SOLAR_YIELD,
        key="solar_yield",
        name="Solar Yield",
        icon="mdi:solar-power",
        value_fn=_number("kwh_per_kwp"),
        unit="kWh/kWp",
        precision=2,
    ),
    LifestyleSensorDescription(
        feature=Feature.FLOOD_TIMELINE,
        key="flood_timeline",
        name="Flood Peak Discharge",
        icon="mdi:waves-arrow-up",
        value_fn=_number("peak_discharge"),
        unit=DISCHARGE_UNIT,
        precision=1,
    ),
    LifestyleSensorDescription(
        feature=Feature.APPROACHING_FRONT,
        key="front_approaching",
        name="Front Approaching",
        icon="mdi:weather-windy",
        value_fn=_number("estimated_in_hours"),
        unit=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        precision=1,
    ),
    LifestyleSensorDescription(
        feature=Feature.SEASONAL_OUTLOOK,
        key="seasonal_outlook",
        name="Seasonal Temperature Anomaly",
        icon="mdi:thermometer-alert",
        value_fn=_first_anomaly,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        precision=1,
    ),
)

LIFESTYLE_BINARY_SENSORS: tuple[LifestyleBinarySensorDescription, ...] = (
    LifestyleBinarySensorDescription(
        feature=Feature.VENTILATION_WINDOW,
        key="ventilation_window",
        name="Ventilation Window",
        icon="mdi:window-open-variant",
        is_on_fn=_ventilation_open,
        device_class="window",
    ),
    LifestyleBinarySensorDescription(
        feature=Feature.GARDENING,
        key="planting_safe",
        name="Planting Safe",
        icon="mdi:sprout",
        is_on_fn=_planting_safe,
    ),
)
