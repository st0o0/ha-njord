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


async def test_consensus_current_state_from_h0(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_consensus")
    assert state is not None
    assert state.attributes.get("temperature") == 20.0
    assert state.attributes.get("agreement") is not None
    assert state.attributes.get("available_models") is not None
    assert state.attributes.get("reliable_hours") is not None
    assert state.attributes["reliable_hours"] > 0


async def test_consensus_supported_features(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_consensus")
    assert state is not None
    features = WeatherEntityFeature(state.attributes["supported_features"])
    assert features & WeatherEntityFeature.FORECAST_HOURLY
    assert features & WeatherEntityFeature.FORECAST_DAILY


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


async def test_extra_state_attributes_with_extras(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
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
                    extra={"cape": 450.0, "uv_index": 7.2},
                ),
            ],
            daily=[
                DailyForecastData(
                    date="2026-07-15",
                    temperature_max=28.0,
                    temperature_min=15.0,
                    weather_code=2,
                ),
                DailyForecastData(date="2026-07-16", temperature_max=25.0, temperature_min=14.0, weather_code=1),
                DailyForecastData(date="2026-07-17", temperature_max=30.0, temperature_min=18.0, weather_code=3),
            ],
        )
    )
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_icon_d2")
    assert state is not None
    assert state.attributes["cape"] == 450.0
    assert state.attributes["uv_index"] == 7.2


async def test_extra_state_attributes_empty(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("weather.njord_home_icon_d2")
    assert state is not None
    assert "cape" not in state.attributes


async def test_hourly_forecast_includes_extras(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
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
                    extra={"cape": 450.0},
                ),
                HourlyForecastData(
                    timestamp=datetime(2026, 7, 15, 13, 0, tzinfo=UTC),
                    temperature=23.0,
                    weather_code=1,
                    is_day=True,
                    extra={},
                ),
            ],
            daily=[
                DailyForecastData(date="2026-07-15", temperature_max=28.0, temperature_min=15.0, weather_code=2),
                DailyForecastData(date="2026-07-16", temperature_max=25.0, temperature_min=14.0, weather_code=1),
                DailyForecastData(date="2026-07-17", temperature_max=30.0, temperature_min=18.0, weather_code=3),
            ],
        )
    )
    await init_integration(hass, mock_config_entry)

    forecasts = await hass.services.async_call(
        "weather",
        "get_forecasts",
        {"entity_id": "weather.njord_home_icon_d2", "type": "hourly"},
        blocking=True,
        return_response=True,
    )
    data = forecasts["weather.njord_home_icon_d2"]["forecast"]
    assert data[0]["cape"] == 450.0
    assert "cape" not in data[1]


async def test_daily_forecast_includes_extras(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
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
            daily=[
                DailyForecastData(
                    date="2026-07-15",
                    temperature_max=28.0,
                    temperature_min=15.0,
                    weather_code=2,
                    extra={"soil_moisture": 23.5},
                ),
                DailyForecastData(
                    date="2026-07-16",
                    temperature_max=25.0,
                    temperature_min=14.0,
                    weather_code=1,
                    extra={},
                ),
                DailyForecastData(
                    date="2026-07-17",
                    temperature_max=30.0,
                    temperature_min=18.0,
                    weather_code=3,
                ),
            ],
        )
    )
    await init_integration(hass, mock_config_entry)

    forecasts = await hass.services.async_call(
        "weather",
        "get_forecasts",
        {"entity_id": "weather.njord_home_icon_d2", "type": "daily"},
        blocking=True,
        return_response=True,
    )
    data = forecasts["weather.njord_home_icon_d2"]["forecast"]
    assert data[0]["soil_moisture"] == 23.5
    assert "soil_moisture" not in data[1]
