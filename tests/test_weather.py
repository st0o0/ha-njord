"""Tests for njord weather entities."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.njord.condition_mapper import map_condition
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
