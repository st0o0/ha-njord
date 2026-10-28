"""Weather platform for njord."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntity,
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_utc_time_change
from homeassistant.util import dt as dt_util

from .condition_mapper import map_condition
from .const import DOMAIN, Domain
from .coordinator import NjordDataCoordinator, NjordStatusCoordinator
from .helpers import current_point, device_info, slugify_location
from .models import ForecastDomainData, ForecastSampleData


def _get_sw_version(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    status_coordinator: NjordStatusCoordinator | None = hass.data[DOMAIN][entry.entry_id].get("status_coordinator")
    if status_coordinator is not None and status_coordinator.data is not None:
        return status_coordinator.data.version or None
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord weather entities, one per location with weather data."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sw_version = _get_sw_version(hass, entry)

    entities: list[WeatherEntity] = [
        NjordWeatherEntity(coordinator, entry, location, sw_version)
        for location in coordinator.data.locations_with(Domain.FORECAST)
    ]
    for location, model in sorted(coordinator.data.model_domains):
        entities.append(NjordWeatherEntity(coordinator, entry, location, sw_version, model=model))
    async_add_entities(entities)

    def weather_factory(location: str, domain: Domain) -> list[WeatherEntity]:
        if domain != Domain.FORECAST:
            return []
        return [NjordWeatherEntity(coordinator, entry, location, sw_version)]

    coordinator.register_entity_factory("weather", async_add_entities, weather_factory)

    def model_factory(location: str, model: str) -> list[WeatherEntity]:
        return [NjordWeatherEntity(coordinator, entry, location, sw_version, model=model)]

    coordinator.register_model_factory("weather", async_add_entities, model_factory)


def _condition(sample: ForecastSampleData) -> str:
    return map_condition(sample.weather_code, sample.is_day if sample.is_day is not None else True)


class NjordWeatherEntity(SingleCoordinatorWeatherEntity[NjordDataCoordinator]):
    """Weather entity for one model of one njord location; no model means the primary model."""

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
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        sw_version: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._model = model
        slug = slugify_location(location)
        if model is None:
            self._attr_unique_id = f"{entry.entry_id}_{slug}_weather"
        else:
            info = coordinator.data.model_info.get(model) if coordinator.data is not None else None
            self._attr_unique_id = f"{entry.entry_id}_{slug}_{model}_weather"
            self._attr_name = (info.display_name if info is not None else "") or model
        self._attr_device_info = device_info(entry, location, sw_version)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_track_utc_time_change(self.hass, self._async_hourly_refresh, minute=0, second=0))

    @callback
    def _async_hourly_refresh(self, now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def _weather(self) -> ForecastDomainData | None:
        if self.coordinator.data is None:
            return None
        if self._model is not None:
            return self.coordinator.data.model_domains.get((self._location, self._model))
        data = self.coordinator.data.domains.get((self._location, Domain.FORECAST))
        return data if isinstance(data, ForecastDomainData) else None

    def _current(self) -> ForecastSampleData | None:
        data = self._weather
        return current_point(data.points) if data is not None else None

    @property
    def available(self) -> bool:
        return self._current() is not None

    @property
    def condition(self) -> str | None:
        sample = self._current()
        return _condition(sample) if sample is not None else None

    @property
    def native_temperature(self) -> float | None:
        sample = self._current()
        return sample.temperature if sample is not None else None

    @property
    def native_apparent_temperature(self) -> float | None:
        sample = self._current()
        return sample.apparent_temperature if sample is not None else None

    @property
    def native_dew_point(self) -> float | None:
        sample = self._current()
        return sample.dew_point if sample is not None else None

    @property
    def humidity(self) -> float | None:
        sample = self._current()
        return sample.humidity if sample is not None else None

    @property
    def native_pressure(self) -> float | None:
        sample = self._current()
        return sample.pressure if sample is not None else None

    @property
    def native_wind_speed(self) -> float | None:
        sample = self._current()
        return sample.wind_speed if sample is not None else None

    @property
    def native_wind_gust_speed(self) -> float | None:
        sample = self._current()
        return sample.wind_gusts if sample is not None else None

    @property
    def cloud_coverage(self) -> float | None:
        sample = self._current()
        return sample.cloud_cover if sample is not None else None

    @property
    def uv_index(self) -> float | None:
        sample = self._current()
        return sample.uv_index if sample is not None else None

    @property
    def native_visibility(self) -> float | None:
        sample = self._current()
        return sample.visibility if sample is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        data = self._weather
        sample = self._current()
        if data is None or sample is None:
            return None
        attrs: dict[str, object] = {"valid_at": sample.valid_at.isoformat()}
        if data.model_run is not None:
            attrs["model_run"] = data.model_run.isoformat()
        for name in ("cape", "rain", "snowfall", "soil_temperature", "freezing_level_height"):
            value = getattr(sample, name)
            if value is not None:
                attrs[name] = value
        attrs.update(self._model_attributes())
        return attrs

    def _model_attributes(self) -> dict[str, object]:
        model = self._model or self.coordinator.data.primary_model(self._location)
        if not model:
            return {}
        attrs: dict[str, object] = {"model": model}
        info = self.coordinator.data.model_info.get(model)
        if info is None:
            return attrs
        for name, value in (
            ("model_name", info.display_name),
            ("provider", info.provider),
            ("region", info.region),
            ("resolution_km", info.resolution_km),
            ("forecast_hours", info.max_forecast_hours),
        ):
            if value not in (None, ""):
                attrs[name] = value
        return attrs

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        data = self._weather
        if data is None:
            return None

        now = dt_util.utcnow()
        forecasts: list[Forecast] = []
        for point in data.points:
            if point.valid_at < now:
                continue
            forecast = Forecast(
                datetime=point.valid_at.isoformat(),
                native_temperature=point.temperature,
                native_apparent_temperature=point.apparent_temperature,
                native_dew_point=point.dew_point,
                native_precipitation=point.precipitation,
                precipitation_probability=round(point.precipitation_probability),
                humidity=point.humidity,
                native_pressure=point.pressure,
                native_wind_speed=point.wind_speed,
                cloud_coverage=point.cloud_cover,
                uv_index=point.uv_index,
                condition=_condition(point),
                is_daytime=point.is_day,
            )
            if point.wind_gusts is not None:
                forecast["native_wind_gust_speed"] = point.wind_gusts
            forecasts.append(forecast)
        return forecasts or None
