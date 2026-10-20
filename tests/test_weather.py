"""Tests for the njord weather entity."""

from __future__ import annotations

from dataclasses import replace

import pytest
from homeassistant.core import HomeAssistant

from custom_components.njord.const import DOMAIN, Domain
from tests.conftest import FUTURE, MODEL_RUN, PAST, entity_id_for, init_integration, weather_sample


def _entity_id(hass: HomeAssistant, entry, location: str = "home") -> str:
    entity_id = entity_id_for(hass, "weather", f"{entry.entry_id}_{location}_weather")
    assert entity_id is not None
    return entity_id


async def test_one_weather_entity_per_location_with_weather_data(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    await init_integration(hass, mock_config_entry)

    assert len(hass.states.async_entity_ids("weather")) == 1
    assert entity_id_for(hass, "weather", f"{mock_config_entry.entry_id}_home_icon_d2_weather") is None


async def test_no_weather_entity_without_weather_data(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    from tests.conftest import default_domain_data

    mock_client.get_domain_data.side_effect = lambda loc, dom: (
        None if dom == Domain.WEATHER else default_domain_data(loc, dom)
    )

    await init_integration(hass, mock_config_entry)

    assert hass.states.async_entity_ids("weather") == []


async def test_current_conditions(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get(_entity_id(hass, mock_config_entry))
    assert state is not None
    assert state.state == "partlycloudy"
    attrs = state.attributes
    assert attrs["temperature"] == pytest.approx(22.5)
    assert attrs["apparent_temperature"] == pytest.approx(21.0)
    assert attrs["dew_point"] == pytest.approx(15.0)
    assert attrs["humidity"] == 65.0
    assert attrs["pressure"] == pytest.approx(1013.0)
    assert attrs["cloud_coverage"] == 30.0
    assert attrs["uv_index"] == 5.0
    # m/s from njord, metric km/h in HA
    assert attrs["wind_speed"] == pytest.approx(3.5 * 3.6, abs=0.1)
    assert attrs["wind_gust_speed"] == pytest.approx(8.0 * 3.6, abs=0.1)
    assert attrs["visibility"] == pytest.approx(20.0)


async def test_extra_attributes(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    attrs = hass.states.get(_entity_id(hass, mock_config_entry)).attributes
    assert attrs["valid_at"] == PAST.isoformat()
    assert attrs["model_run"] == MODEL_RUN.isoformat()
    assert attrs["cape"] == 120.0
    assert "snowfall" not in attrs


async def test_night_condition_uses_is_day(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    key = ("home", Domain.WEATHER)

    coordinator.data.domains[key] = replace(
        coordinator.data.domains[key], points=[weather_sample(weather_code=0, is_day=False)]
    )
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    assert hass.states.get(_entity_id(hass, mock_config_entry)).state == "clear-night"


async def test_unavailable_without_points(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    key = ("home", Domain.WEATHER)

    coordinator.data.domains[key] = replace(coordinator.data.domains[key], points=[])
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    assert hass.states.get(_entity_id(hass, mock_config_entry)).state == "unavailable"


async def _forecast(hass: HomeAssistant, entity_id: str, forecast_type: str = "hourly"):
    response = await hass.services.async_call(
        "weather",
        "get_forecasts",
        {"entity_id": entity_id, "type": forecast_type},
        blocking=True,
        return_response=True,
    )
    return response[entity_id]["forecast"]


async def test_hourly_forecast_contains_only_future_points(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    forecast = await _forecast(hass, _entity_id(hass, mock_config_entry))

    assert len(forecast) == 1
    item = forecast[0]
    assert item["datetime"] == FUTURE.isoformat()
    assert item["temperature"] == 25.0
    assert item["condition"] == "partlycloudy"
    assert item["precipitation_probability"] == 40
    assert item["is_daytime"] is True
    assert item["humidity"] == 65.0
    assert item["wind_gust_speed"] == pytest.approx(8.0 * 3.6, abs=0.1)


async def test_daily_forecast_is_not_supported(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    from homeassistant.exceptions import HomeAssistantError

    await init_integration(hass, mock_config_entry)

    with pytest.raises(HomeAssistantError, match="does not support"):
        await _forecast(hass, _entity_id(hass, mock_config_entry), "daily")


async def test_forecast_without_gusts_omits_key(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    key = ("home", Domain.WEATHER)
    coordinator.data.domains[key] = replace(
        coordinator.data.domains[key], points=[weather_sample(FUTURE, wind_gusts=None)]
    )

    forecast = await _forecast(hass, _entity_id(hass, mock_config_entry))

    assert "wind_gust_speed" not in forecast[0]
