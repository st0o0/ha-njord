"""Shared test fixtures for ha-njord."""

import sys
import types
from enum import Enum


class _Platform(str, Enum):
    WEATHER = "weather"


class _UnitOfPressure(str, Enum):
    HPA = "hPa"


class _UnitOfSpeed(str, Enum):
    METERS_PER_SECOND = "m/s"


class _UnitOfTemperature(str, Enum):
    CELSIUS = "°C"


class _WeatherEntityFeature:
    FORECAST_DAILY = 1
    FORECAST_HOURLY = 2


class _DataUpdateCoordinator:
    def __init_subclass__(cls, **kw):
        pass

    def __class_getitem__(cls, item):
        return cls


class _CoordinatorEntity:
    def __init_subclass__(cls, **kw):
        pass

    def __class_getitem__(cls, item):
        return cls


_HA_STUBS: dict[str, dict[str, object]] = {
    "homeassistant": {},
    "homeassistant.config_entries": {
        "ConfigEntry": object,
        "ConfigFlow": type("ConfigFlow", (), {}),
        "ConfigFlowResult": dict,
    },
    "homeassistant.core": {
        "HomeAssistant": object,
    },
    "homeassistant.const": {
        "Platform": _Platform,
        "UnitOfPressure": _UnitOfPressure,
        "UnitOfSpeed": _UnitOfSpeed,
        "UnitOfTemperature": _UnitOfTemperature,
    },
    "homeassistant.components": {},
    "homeassistant.components.weather": {
        "Forecast": dict,
        "WeatherEntity": type("WeatherEntity", (), {}),
        "WeatherEntityFeature": _WeatherEntityFeature,
    },
    "homeassistant.helpers": {},
    "homeassistant.helpers.device_registry": {
        "DeviceInfo": dict,
    },
    "homeassistant.helpers.entity_platform": {
        "AddEntitiesCallback": object,
    },
    "homeassistant.helpers.update_coordinator": {
        "DataUpdateCoordinator": _DataUpdateCoordinator,
        "CoordinatorEntity": _CoordinatorEntity,
        "UpdateFailed": type("UpdateFailed", (Exception,), {}),
    },
}

for mod_name, attrs in _HA_STUBS.items():
    mod = types.ModuleType(mod_name)
    for attr_name, attr_val in attrs.items():
        setattr(mod, attr_name, attr_val)
    parts = mod_name.rsplit(".", 1)
    if len(parts) == 2:
        parent_name, child_name = parts
        if parent_name in sys.modules:
            setattr(sys.modules[parent_name], child_name, mod)
    sys.modules.setdefault(mod_name, mod)
