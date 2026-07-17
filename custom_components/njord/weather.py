"""Weather platform for njord."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
from .models import ConsensusData, ForecastData, HorizonConsensusData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord weather entities."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[WeatherEntity] = []
    for (location, model) in coordinator.data.forecasts:
        entities.append(
            NjordWeatherEntity(coordinator, entry, location, model)
        )

    locations = {loc for loc, _ in coordinator.data.forecasts}
    for location in sorted(locations):
        enrichment = coordinator.data.enrichments.get(location)
        if enrichment and enrichment.consensus:
            entities.append(
                NjordConsensusWeatherEntity(coordinator, entry, location)
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
        return self.coordinator.data.forecasts.get((self._location, self._model))

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

    @property
    def native_apparent_temperature(self) -> float | None:
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        return data.hourly[0].apparent_temperature

    @property
    def cloud_cover(self) -> float | None:
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        return data.hourly[0].cloud_cover

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
                    cloud_cover=h.cloud_cover,
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


_CONSENSUS_PARAM_MAP = {
    "temperature_2m": "temperature",
    "apparent_temperature": "apparent_temperature",
    "relative_humidity_2m": "humidity",
    "pressure_msl": "pressure",
    "wind_speed_10m": "wind_speed",
    "wind_direction_10m": "wind_bearing",
    "cloud_cover": "cloud_cover",
    "precipitation": "precipitation",
    "weather_code": "weather_code",
    "dew_point_2m": "dew_point",
    "visibility": "visibility",
}


class NjordConsensusWeatherEntity(CoordinatorEntity[NjordDataCoordinator], WeatherEntity):
    """Weather entity using multi-model consensus values."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    _DAILY_HORIZONS = ["h24", "h48", "h72", "h96"]

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
    ) -> None:
        super().__init__(coordinator)
        self._location = location

        slug = f"{location}_consensus".replace("-", "_").replace(" ", "_").lower()
        self._attr_unique_id = f"{entry.entry_id}_{slug}"
        self._attr_name = "Consensus"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{location}")},
            name=f"njord {location}",
            manufacturer="njord",
            model=location,
            entry_type=None,
        )

    def _consensus(self) -> ConsensusData | None:
        if self.coordinator.data is None:
            return None
        enrichment = self.coordinator.data.enrichments.get(self._location)
        if enrichment is None:
            return None
        return enrichment.consensus

    def _get_horizon_value(self, parameter: str, horizon: str = "h3") -> float | None:
        consensus = self._consensus()
        if consensus is None:
            return None
        for param in consensus.parameters:
            if param.parameter == parameter:
                for h in param.by_horizon:
                    if h.horizon == horizon:
                        return h.median
        return None

    def _get_horizon_data(self, parameter: str, horizon: str = "h3") -> HorizonConsensusData | None:
        consensus = self._consensus()
        if consensus is None:
            return None
        for param in consensus.parameters:
            if param.parameter == parameter:
                for h in param.by_horizon:
                    if h.horizon == horizon:
                        return h
        return None

    @property
    def available(self) -> bool:
        return self._consensus() is not None

    @property
    def condition(self) -> str | None:
        wmo = self._get_horizon_value("weather_code")
        if wmo is None:
            return None
        is_day_val = self._get_horizon_value("is_day")
        is_day = is_day_val is not None and is_day_val >= 0.5
        return map_condition(int(round(wmo)), is_day)

    @property
    def native_temperature(self) -> float | None:
        return self._get_horizon_value("temperature_2m")

    @property
    def humidity(self) -> float | None:
        return self._get_horizon_value("relative_humidity_2m")

    @property
    def native_pressure(self) -> float | None:
        return self._get_horizon_value("pressure_msl")

    @property
    def native_wind_speed(self) -> float | None:
        return self._get_horizon_value("wind_speed_10m")

    @property
    def wind_bearing(self) -> float | None:
        return self._get_horizon_value("wind_direction_10m")

    @property
    def native_apparent_temperature(self) -> float | None:
        return self._get_horizon_value("apparent_temperature")

    @property
    def cloud_cover(self) -> float | None:
        return self._get_horizon_value("cloud_cover")

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        temp_h = self._get_horizon_data("temperature_2m")
        if temp_h is None:
            return None
        return {
            "agreement": temp_h.agreement,
            "available_models": temp_h.available_models,
            "spread": temp_h.spread,
        }

    async def async_forecast_daily(self) -> list[Forecast] | None:
        consensus = self._consensus()
        if consensus is None:
            return None

        today = datetime.now(timezone.utc).date()
        forecasts: list[Forecast] = []
        for horizon in self._DAILY_HORIZONS:
            temp = self._get_horizon_value("temperature_2m", horizon)
            if temp is None:
                continue
            hours = int(horizon[1:])
            forecast_date = today + timedelta(hours=hours)
            precip = self._get_horizon_value("precipitation", horizon)
            wmo = self._get_horizon_value("weather_code", horizon)
            condition = None
            if wmo is not None:
                condition = map_condition(int(round(wmo)), True)

            forecasts.append(
                Forecast(
                    datetime=forecast_date.isoformat(),
                    native_temperature=temp,
                    precipitation=precip,
                    condition=condition,
                )
            )
        return forecasts

