"""Weather platform for njord."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .condition_mapper import map_condition
from .const import DOMAIN
from .coordinator import NjordDataCoordinator
from .models import ConsensusData, ForecastData, HorizonConsensusData, NjordLocation


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord weather entities."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[WeatherEntity] = []
    for location, model in coordinator.data.forecasts:
        entities.append(NjordWeatherEntity(coordinator, entry, location, model))

    locations = {loc for loc, _ in coordinator.data.forecasts}
    for location in sorted(locations):
        enrichment = coordinator.data.enrichments.get(location)
        if enrichment and enrichment.consensus:
            entities.append(NjordConsensusWeatherEntity(coordinator, entry, location))

    async_add_entities(entities)

    def weather_factory(location: NjordLocation) -> list[WeatherEntity]:
        new_entities: list[WeatherEntity] = []
        for model in location.models:
            new_entities.append(NjordWeatherEntity(coordinator, entry, location.name, model))
        enrichment = coordinator.data.enrichments.get(location.name)
        if enrichment and enrichment.consensus:
            new_entities.append(NjordConsensusWeatherEntity(coordinator, entry, location.name))
        return new_entities

    coordinator.register_entity_factory("weather", async_add_entities, weather_factory)


class NjordWeatherEntity(SingleCoordinatorWeatherEntity[NjordDataCoordinator]):
    """Weather entity for a njord location×model pair."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND

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

        data = coordinator.data.forecasts.get((location, model))
        features = WeatherEntityFeature(0)
        if data and data.hourly:
            features |= WeatherEntityFeature.FORECAST_HOURLY
        if data and len(data.daily) >= 3:
            features |= WeatherEntityFeature.FORECAST_DAILY
        self._attr_supported_features = features

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None and (self._location, self._model) in self.coordinator.data.forecasts

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

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
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

    def _daily_condition_from_hourly(self, date_str: str) -> str | None:
        """Derive daily condition from midday hourly entry as fallback."""
        data = self._forecast_data
        if data is None or not data.hourly:
            return None
        midday = None
        for h in data.hourly:
            if h.timestamp.strftime("%Y-%m-%d") == date_str:
                if midday is None or abs(h.timestamp.hour - 12) < abs(midday.timestamp.hour - 12):
                    midday = h
        if midday is None or midday.weather_code is None:
            return None
        return map_condition(midday.weather_code, True)

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        data = self._forecast_data
        if data is None:
            return None

        forecasts: list[Forecast] = []
        for d in data.daily:
            if d.temperature_max is None and d.temperature_min is None:
                continue
            condition = None
            if d.weather_code is not None:
                condition = map_condition(d.weather_code, True)
            else:
                condition = self._daily_condition_from_hourly(d.date)

            forecasts.append(
                Forecast(
                    datetime=f"{d.date}T00:00:00+00:00",
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


_AGREEMENT_THRESHOLD = 0.5


class NjordConsensusWeatherEntity(SingleCoordinatorWeatherEntity[NjordDataCoordinator]):
    """Weather entity using multi-model consensus values with hourly granularity."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND

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

        features = WeatherEntityFeature(0)
        if self._sorted_horizons() and len(self._sorted_horizons()) >= 2:
            features |= WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
        self._attr_supported_features = features

    def _consensus(self) -> ConsensusData | None:
        if self.coordinator.data is None:
            return None
        enrichment = self.coordinator.data.enrichments.get(self._location)
        if enrichment is None:
            return None
        return enrichment.consensus

    def _sorted_horizons(self) -> list[str]:
        consensus = self._consensus()
        if consensus is None:
            return []
        for param in consensus.parameters:
            if param.parameter == "temperature_2m":
                return sorted(
                    [h.horizon for h in param.by_horizon],
                    key=lambda x: int(x[1:]),
                )
        return []

    def _horizon_values(self, horizon: str) -> dict[str, float | None]:
        consensus = self._consensus()
        if consensus is None:
            return {}
        result: dict[str, float | None] = {}
        for param in consensus.parameters:
            for h in param.by_horizon:
                if h.horizon == horizon:
                    result[param.parameter] = h.median
                    break
        return result

    def _get_horizon_value(self, parameter: str, horizon: str = "h0") -> float | None:
        consensus = self._consensus()
        if consensus is None:
            return None
        for param in consensus.parameters:
            if param.parameter == parameter:
                for h in param.by_horizon:
                    if h.horizon == horizon:
                        return h.median
        return None

    def _get_horizon_data(self, parameter: str, horizon: str = "h0") -> HorizonConsensusData | None:
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

    def _reliable_hours(self) -> int:
        consensus = self._consensus()
        if consensus is None:
            return 0
        temp_param = None
        for param in consensus.parameters:
            if param.parameter == "temperature_2m":
                temp_param = param
                break
        if temp_param is None:
            return 0
        by_hours = sorted(temp_param.by_horizon, key=lambda h: int(h.horizon[1:]))
        count = 0
        for h in by_hours:
            if h.agreement is None or h.agreement < _AGREEMENT_THRESHOLD:
                break
            count += 1
        return count

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        temp_h = self._get_horizon_data("temperature_2m")
        if temp_h is None:
            return None
        return {
            "agreement": temp_h.agreement,
            "available_models": temp_h.available_models,
            "spread": temp_h.spread,
            "reliable_hours": self._reliable_hours(),
        }

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        consensus = self._consensus()
        if consensus is None:
            return None

        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        forecasts: list[Forecast] = []

        for horizon in self._sorted_horizons():
            hours = int(horizon[1:])
            if hours == 0:
                continue
            vals = self._horizon_values(horizon)
            if not vals:
                continue

            forecast_time = now + timedelta(hours=hours)
            condition = None
            wmo = vals.get("weather_code")
            if wmo is not None:
                condition = map_condition(int(round(wmo)), True)

            forecasts.append(
                Forecast(
                    datetime=forecast_time.isoformat(),
                    native_temperature=vals.get("temperature_2m"),
                    precipitation=vals.get("precipitation"),
                    humidity=vals.get("relative_humidity_2m"),
                    native_wind_speed=vals.get("wind_speed_10m"),
                    wind_bearing=vals.get("wind_direction_10m"),
                    cloud_cover=vals.get("cloud_cover"),
                    condition=condition,
                )
            )
        return forecasts

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        consensus = self._consensus()
        if consensus is None:
            return None

        now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        today = now.date()

        days: dict[str, list[tuple[int, dict[str, float | None]]]] = {}
        for horizon in self._sorted_horizons():
            hours = int(horizon[1:])
            forecast_time = now + timedelta(hours=hours)
            forecast_date = forecast_time.date()
            if forecast_date <= today:
                continue
            date_str = forecast_date.isoformat()
            vals = self._horizon_values(horizon)
            if vals:
                days.setdefault(date_str, []).append((forecast_time.hour, vals))

        forecasts: list[Forecast] = []
        for date_str in sorted(days.keys()):
            entries = days[date_str]
            temps = [v.get("temperature_2m") for _, v in entries if v.get("temperature_2m") is not None]
            precips = [v.get("precipitation") for _, v in entries if v.get("precipitation") is not None]
            winds = [v.get("wind_speed_10m") for _, v in entries if v.get("wind_speed_10m") is not None]

            midday_entry = min(entries, key=lambda e: abs(e[0] - 12))
            midday_wmo = midday_entry[1].get("weather_code")
            condition = None
            if midday_wmo is not None:
                condition = map_condition(int(round(midday_wmo)), True)

            forecasts.append(
                Forecast(
                    datetime=f"{date_str}T00:00:00+00:00",
                    native_temperature=max(temps) if temps else None,
                    native_templow=min(temps) if temps else None,
                    precipitation=sum(precips) if precips else None,
                    native_wind_speed=max(winds) if winds else None,
                    condition=condition,
                )
            )
        return forecasts
