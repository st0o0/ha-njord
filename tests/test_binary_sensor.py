"""Tests for njord binary sensor entities."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.conftest import init_integration


async def test_uv_alert_on(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("binary_sensor.njord_home_uv_alert")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["severity"] == "orange"
    assert state.attributes["confidence"] == 1.0


async def test_frost_alert_off(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("binary_sensor.njord_home_frost_alert")
    assert state is not None
    assert state.state == "off"
    assert state.attributes["severity"] == "none"


async def test_heat_alert_on(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = hass.states.get("binary_sensor.njord_home_heat_alert")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["severity"] == "yellow"
    assert state.attributes["confidence"] == pytest.approx(0.33)


async def test_all_alert_entities_exist(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    alert_types = ["frost", "heat", "storm", "heavy_rain", "uv", "fog", "snow", "pressure_drop", "thunderstorm"]
    for alert_type in alert_types:
        state = hass.states.get(f"binary_sensor.njord_home_{alert_type}_alert")
        assert state is not None, f"Missing alert entity: {alert_type}"


async def test_inversion_entity_disabled_by_default(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    registry = er.async_get(hass)
    entry = registry.async_get("binary_sensor.njord_home_inversion")
    assert entry is not None
    assert entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION

    state = hass.states.get("binary_sensor.njord_home_inversion")
    assert state is None


async def test_alert_entities_enabled_by_default(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    registry = er.async_get(hass)
    alert_types = ["frost", "heat", "storm", "heavy_rain", "uv", "fog", "snow", "pressure_drop", "thunderstorm"]
    for alert_type in alert_types:
        entry = registry.async_get(f"binary_sensor.njord_home_{alert_type}_alert")
        assert entry is not None, f"Missing alert entity: {alert_type}"
        assert entry.disabled_by is None, f"Alert {alert_type} should be enabled by default"
