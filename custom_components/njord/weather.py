"""Weather platform for njord."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .condition_mapper import map_condition
from .const import DOMAIN
from .coordinator import NjordDataCoordinator
from .models import ForecastData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord weather entities."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[NjordWeatherEntity] = []
    for (location, model) in coordinator.data:
        entities.append(
            NjordWeatherEntity(coordinator, entry, location, model)
        )

    async_add_entities(entities)


class NjordWeatherEntity(CoordinatorEntity[NjordDataCoordinator], WeatherEntity):
    """Weather entity for a njord location×model pair."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        model: str,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._location = location
        self._model = model

        slug = f"{location}_{model}".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = model
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{location}")},
            name=f"njord {location}",
            manufacturer="njord",
            model=location,
            entry_type=None,
        )

    @property
    def _forecast_data(self) -> ForecastData | None:
        """Get current forecast data from coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get((self._location, self._model))

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        h = data.hourly[0]
        if h.weather_code is None:
            return None
        return map_condition(h.weather_code, h.is_day if h.is_day is not None else True)

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        return data.hourly[0].temperature

    @property
    def humidity(self) -> float | None:
        """Return the current humidity."""
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        return data.hourly[0].humidity

    @property
    def native_pressure(self) -> float | None:
        """Return the current pressure."""
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        return data.hourly[0].pressure_msl

    @property
    def native_wind_speed(self) -> float | None:
        """Return the current wind speed."""
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        return data.hourly[0].wind_speed

    @property
    def wind_bearing(self) -> float | None:
        """Return the current wind bearing."""
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        return data.hourly[0].wind_bearing

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast."""
        data = self._forecast_data
        if data is None:
            return None

        forecasts: list[Forecast] = []
        for h in data.hourly:
            condition = None
            if h.weather_code is not None:
                condition = map_condition(h.weather_code, h.is_day if h.is_day is not None else True)

            forecasts.append(
                Forecast(
                    datetime=h.timestamp.isoformat(),
                    native_temperature=h.temperature,
                    precipitation=h.precipitation,
                    humidity=h.humidity,
                    native_wind_speed=h.wind_speed,
                    wind_bearing=h.wind_bearing,
                    condition=condition,
                )
            )
        return forecasts

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        data = self._forecast_data
        if data is None:
            return None

        forecasts: list[Forecast] = []
        for d in data.daily:
            condition = None
            if d.weather_code is not None:
                condition = map_condition(d.weather_code, True)

            forecasts.append(
                Forecast(
                    datetime=d.date,
                    native_temperature=d.temperature_max,
                    native_templow=d.temperature_min,
                    precipitation=d.precipitation_sum,
                    native_wind_speed=d.wind_speed_max,
                    condition=condition,
                )
            )
        return forecasts
