"""Tests for njord weather entities."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from homeassistant.components.weather import WeatherEntityFeature
from homeassistant.core import HomeAssistant

from custom_components.njord.condition_mapper import map_condition
from custom_components.njord.models import DailyForecastData, ForecastData, HourlyForecastData
from tests.conftest import init_integration


def test_condition_mapping_day():
    assert map_condition(0, is_day=True) == "sunny"
    assert map_condition(1, is_day=True) == "partlycloudy"
    assert map_condition(61, is_day=True) == "rainy"


def test_condition_mapping_night():
    assert map_condition(0, is_day=False) == "clear-night"


async def test_weather_entity_state(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_icon_d2")
    assert state is not None
    assert state.state == "partlycloudy"
    assert state.attributes["temperature"] == 22.5
    assert state.attributes["humidity"] == 65.0
    assert state.attributes["pressure"] == 1013.0
    assert state.attributes["wind_speed"] == pytest.approx(12.6, abs=0.1)
    assert state.attributes["wind_bearing"] == 180.0


async def test_weather_entity_second_model(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_ecmwf_ifs025")
    assert state is not None
    assert state.state == "partlycloudy"


async def test_consensus_weather_entity(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_consensus")
    assert state is not None
    assert state.attributes.get("agreement") is not None
    assert state.attributes.get("available_models") is not None


async def test_supported_features_with_hourly_and_daily(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_icon_d2")
    assert state is not None
    features = WeatherEntityFeature(state.attributes["supported_features"])
    assert features & WeatherEntityFeature.FORECAST_HOURLY
    assert features & WeatherEntityFeature.FORECAST_DAILY


async def test_supported_features_hourly_only(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.get_forecast = AsyncMock(
        side_effect=lambda loc, model: ForecastData(
            location=loc,
            model=model,
            updated_at=1720000000,
            hourly=[
                HourlyForecastData(
                    timestamp=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
                    temperature=22.5,
                    weather_code=1,
                    is_day=True,
                ),
            ],
            daily=[],
        )
    )
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_icon_d2")
    assert state is not None
    features = WeatherEntityFeature(state.attributes["supported_features"])
    assert features & WeatherEntityFeature.FORECAST_HOURLY
    assert not (features & WeatherEntityFeature.FORECAST_DAILY)


async def test_supported_features_stub_has_no_features(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.get_forecast = AsyncMock(side_effect=Exception("fetch error"))
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_icon_d2")
    assert state is not None
    features = WeatherEntityFeature(state.attributes["supported_features"])
    assert not (features & WeatherEntityFeature.FORECAST_HOURLY)
    assert not (features & WeatherEntityFeature.FORECAST_DAILY)


async def test_weather_entity_available_with_data(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_icon_d2")
    assert state is not None
    assert state.state != "unavailable"


async def test_weather_entity_available_with_stub(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.get_forecast = AsyncMock(side_effect=Exception("fetch error"))
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_icon_d2")
    assert state is not None
    assert state.state == "unknown"
