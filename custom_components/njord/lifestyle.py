"""Lifestyle advisory entity descriptions and value extraction."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.util import dt as dt_util

from .const import DISCHARGE_UNIT, LifestyleType
from .models import LifestyleData

TRUE = "true"


def parse_time(value: str | None) -> datetime | None:
    """Parse njord's UTC timestamp text; None when absent or malformed."""
    if not value:
        return None
    return dt_util.parse_datetime(value)


def parse_number(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _text(key: str) -> Callable[[LifestyleData], str | None]:
    return lambda item: item.data.get(key) or None


def _number(key: str) -> Callable[[LifestyleData], float | None]:
    return lambda item: parse_number(item.data.get(key))


def _time(key: str) -> Callable[[LifestyleData], datetime | None]:
    return lambda item: parse_time(item.data.get(key))


def _pollen_state(item: LifestyleData) -> str:
    return item.data.get("peak_type") or "none"


@dataclass(frozen=True, kw_only=True)
class LifestyleSensorDescription:
    """A sensor fed by one lifestyle type; value_fn extracts the state from the type's key-value data."""

    type: LifestyleType
    key: str
    name: str
    icon: str
    value_fn: Callable[[LifestyleData], object]
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    options: tuple[str, ...] | None = None
    precision: int | None = None


@dataclass(frozen=True, kw_only=True)
class LifestyleBinarySensorDescription:
    """A binary sensor fed by one lifestyle type; is_on_fn decides the state from the type's data."""

    type: LifestyleType
    key: str
    name: str
    icon: str
    is_on_fn: Callable[[LifestyleData], bool]
    device_class: str | None = None


def _ventilation_open(item: LifestyleData) -> bool:
    start = parse_time(item.data.get("best_start"))
    end = parse_time(item.data.get("best_end"))
    if start is None or end is None:
        return False
    return start <= dt_util.utcnow() < end


def _planting_safe(item: LifestyleData) -> bool:
    return item.data.get("planting_safe") == TRUE


LIFESTYLE_SENSORS: tuple[LifestyleSensorDescription, ...] = (
    LifestyleSensorDescription(
        type=LifestyleType.LAUNDRY_SCORE,
        key="laundry_score",
        name="Laundry Score",
        icon="mdi:tumble-dryer",
        value_fn=_number("score"),
        unit="points",
        precision=0,
    ),
    LifestyleSensorDescription(
        type=LifestyleType.COMMUTE_SAFETY,
        key="commute_safety",
        name="Commute Safety",
        icon="mdi:car-brake-alert",
        value_fn=_text("level"),
        device_class=SensorDeviceClass.ENUM,
        options=("Safe", "Caution", "Dangerous"),
    ),
    LifestyleSensorDescription(
        type=LifestyleType.EXERCISE,
        key="exercise",
        name="Exercise",
        icon="mdi:run",
        value_fn=_text("level"),
        device_class=SensorDeviceClass.ENUM,
        options=("Safe", "Caution", "Avoid"),
    ),
    LifestyleSensorDescription(
        type=LifestyleType.OUTDOOR_SCORE,
        key="outdoor_score",
        name="Outdoor Score",
        icon="mdi:pine-tree",
        value_fn=_number("score"),
        unit="points",
        precision=0,
    ),
    LifestyleSensorDescription(
        type=LifestyleType.BBQ_SCORE,
        key="bbq_score",
        name="BBQ Score",
        icon="mdi:grill",
        value_fn=_number("score"),
        unit="points",
        precision=0,
    ),
    LifestyleSensorDescription(
        type=LifestyleType.POLLEN_TREND,
        key="pollen_trend",
        name="Pollen Trend",
        icon="mdi:flower-pollen",
        value_fn=_pollen_state,
    ),
    LifestyleSensorDescription(
        type=LifestyleType.NIGHT_VENTILATION,
        key="night_ventilation",
        name="Night Ventilation",
        icon="mdi:weather-night",
        value_fn=_time("open_at"),
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    LifestyleSensorDescription(
        type=LifestyleType.CONFIDENCE_TREND,
        key="confidence_trend",
        name="Forecast Confidence Trend",
        icon="mdi:chart-line",
        value_fn=_text("direction"),
    ),
    LifestyleSensorDescription(
        type=LifestyleType.SOLAR_YIELD,
        key="solar_yield",
        name="Solar Yield",
        icon="mdi:solar-power",
        value_fn=_number("kwh_per_kwp"),
        unit="kWh/kWp",
        precision=2,
    ),
    LifestyleSensorDescription(
        type=LifestyleType.FLOOD_TIMELINE,
        key="flood_timeline",
        name="Flood Peak Discharge",
        icon="mdi:waves-arrow-up",
        value_fn=_number("peak_discharge"),
        unit=DISCHARGE_UNIT,
        precision=1,
    ),
    LifestyleSensorDescription(
        type=LifestyleType.FRONT_APPROACHING,
        key="front_approaching",
        name="Front Approaching",
        icon="mdi:weather-windy",
        value_fn=_number("estimated_in_hours"),
        unit=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        precision=1,
    ),
    LifestyleSensorDescription(
        type=LifestyleType.CLIMATE_ANOMALY,
        key="climate_anomaly",
        name="Temperature Anomaly",
        icon="mdi:thermometer-alert",
        value_fn=_number("temp_anomaly"),
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        precision=1,
    ),
)

LIFESTYLE_BINARY_SENSORS: tuple[LifestyleBinarySensorDescription, ...] = (
    LifestyleBinarySensorDescription(
        type=LifestyleType.VENTILATION,
        key="ventilation_window",
        name="Ventilation Window",
        icon="mdi:window-open-variant",
        is_on_fn=_ventilation_open,
        device_class="window",
    ),
    LifestyleBinarySensorDescription(
        type=LifestyleType.GARDENING,
        key="planting_safe",
        name="Planting Safe",
        icon="mdi:sprout",
        is_on_fn=_planting_safe,
    ),
)
