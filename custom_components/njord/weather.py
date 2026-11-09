"""Weather entity fed from WeatherValue via the Subscribe stream."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.util import dt as dt_util

from .helpers import device_info
from .models import EntityState, ManifestEntity
from .stream_coordinator import NjordStreamCoordinator

_CONDITION_MAP: dict[str, str] = {
    "clear": "sunny",
    "mostly_clear": "sunny",
    "partly_cloudy": "partlycloudy",
    "overcast": "cloudy",
    "fog": "fog",
    "drizzle": "rainy",
    "rain": "rainy",
    "heavy_rain": "pouring",
    "snow": "snowy",
    "heavy_snow": "snowy",
    "thunderstorm": "lightning-rainy",
    "sleet": "snowy-rainy",
    "hail": "hail",
    "windy": "windy",
}


class NjordWeatherEntity(SingleCoordinatorWeatherEntity[NjordStreamCoordinator]):
    """Weather entity driven by v3 WeatherValue from the Subscribe stream."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_visibility_unit = UnitOfLength.METERS

    def __init__(
        self,
        coordinator: NjordStreamCoordinator,
        entry: ConfigEntry,
        manifest_entity: ManifestEntity,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._manifest = manifest_entity
        self._attr_unique_id = f"{entry.entry_id}_{manifest_entity.entity_id}"
        self._attr_device_info = device_info(entry, manifest_entity.location, sw_version)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_track_utc_time_change(self.hass, self._async_hourly_refresh, minute=0, second=0))

    @callback
    def _async_hourly_refresh(self, now: datetime) -> None:
        self.async_write_ha_state()

    def _state(self) -> EntityState | None:
        return self.coordinator.v3_entity_states.get(self._manifest.entity_id)

    @property
    def available(self) -> bool:
        state = self._state()
        return state is not None and state.available

    def _weather_value(self):
        state = self._state()
        return state.value if state is not None else None

    @property
    def condition(self) -> str | None:
        wv = self._weather_value()
        if wv is None:
            return None
        return _CONDITION_MAP.get(wv.condition, wv.condition)

    @property
    def native_temperature(self) -> float | None:
        wv = self._weather_value()
        return wv.temperature if wv is not None else None

    @property
    def native_apparent_temperature(self) -> float | None:
        wv = self._weather_value()
        return wv.apparent_temperature if wv is not None else None

    @property
    def humidity(self) -> float | None:
        wv = self._weather_value()
        return wv.humidity if wv is not None else None

    @property
    def native_pressure(self) -> float | None:
        wv = self._weather_value()
        return wv.pressure if wv is not None else None

    @property
    def native_wind_speed(self) -> float | None:
        wv = self._weather_value()
        return wv.wind_speed if wv is not None else None

    @property
    def cloud_coverage(self) -> float | None:
        return None

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        wv = self._weather_value()
        if wv is None or not wv.hourly_forecast:
            return None

        now = dt_util.utcnow()
        forecasts: list[Forecast] = []
        for point in wv.hourly_forecast:
            point_time = point.time.ToDatetime()
            if point_time < now:
                continue
            forecast = Forecast(
                datetime=point_time.isoformat(),
                native_temperature=point.temperature,
                native_apparent_temperature=point.apparent_temperature,
                humidity=point.humidity,
                native_pressure=point.pressure,
                native_wind_speed=point.wind_speed,
                condition=_CONDITION_MAP.get(point.condition, point.condition),
            )
            if point.HasField("precipitation_probability"):
                forecast["precipitation_probability"] = round(point.precipitation_probability)
            if point.HasField("precipitation"):
                forecast["native_precipitation"] = point.precipitation
            if point.HasField("cloud_cover"):
                forecast["cloud_coverage"] = point.cloud_cover
            forecasts.append(forecast)
        return forecasts or None
