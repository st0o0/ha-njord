"""Tests for njord sensor entities."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from tests.conftest import init_integration


async def test_index_sensors_exist(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    indices = ["laundry", "outdoor", "running", "cycling", "bbq", "irrigation", "solar", "ventilation"]
    for idx in indices:
        state = hass.states.get(f"sensor.njord_home_{idx}_index")
        assert state is not None, f"Missing index sensor: {idx}"


async def test_bbq_index_value(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_bbq_index")
    assert state is not None
    assert state.state == "51"


async def test_vpd_sensor(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_vpd")
    assert state is not None
    assert float(state.state) == pytest.approx(0.59)
    assert state.attributes["category"] == "optimal"


async def test_heating_demand(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_heating_demand")
    assert state is not None
    assert state.state == "21"


async def test_cop_estimate_with_optimal(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_cop_estimate")
    assert state is not None
    assert float(state.state) == pytest.approx(10.95)
    assert "cop_optimal" in state.attributes
    assert len(state.attributes["cop_optimal"]) == 1


async def test_battery_strategy(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_battery_strategy")
    assert state is not None
    assert state.state == "discharge"


async def test_weather_trend(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_weather_trend")
    assert state is not None
    assert state.state == "stable"
    assert state.attributes["precip_starts_in_hours"] == 2
    assert state.attributes["reliable_hours"] == 3


async def test_sunshine_pct(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_sunshine")
    assert state is not None
    assert float(state.state) == pytest.approx(66.4)


async def test_diurnal_amplitude(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_diurnal_amplitude")
    assert state is not None
    assert float(state.state) == pytest.approx(7.3)


async def test_model_performance_diagnostic(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.njord_home_model_performance")
    assert state is not None
    assert float(state.state) == pytest.approx(24.48)
    assert "models" in state.attributes
