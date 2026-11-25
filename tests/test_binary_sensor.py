"""Tests for njord alert binary sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.njord.const import DOMAIN
from custom_components.njord.models import EntityState
from tests.conftest import entity_id_for, init_integration


def _alert_entity_id(hass: HomeAssistant, entry, alert_id: str) -> str | None:
    return entity_id_for(hass, "binary_sensor", f"{entry.entry_id}_{alert_id}")


def _alert_state(hass: HomeAssistant, entry, alert_id: str):
    eid = _alert_entity_id(hass, entry, alert_id)
    return hass.states.get(eid) if eid else None


async def test_alert_entities_created_from_manifest(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    assert _alert_entity_id(hass, mock_config_entry, "home_frost_alert") is not None
    assert _alert_entity_id(hass, mock_config_entry, "home_uv_alert") is not None


async def test_alert_is_on_when_severity_above_zero(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    value = MagicMock()
    value.severity = 2
    coordinator.v3_entity_states["home_uv_alert"] = EntityState(entity_id="home_uv_alert", value=value, available=True)
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()

    state = _alert_state(hass, mock_config_entry, "home_uv_alert")
    assert state is not None
    assert state.state == "on"


async def test_alert_is_off_when_severity_zero(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    value = MagicMock()
    value.severity = 0
    coordinator.v3_entity_states["home_frost_alert"] = EntityState(
        entity_id="home_frost_alert", value=value, available=True
    )
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()

    state = _alert_state(hass, mock_config_entry, "home_frost_alert")
    assert state is not None
    assert state.state == "off"


async def test_alert_unavailable_without_state(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = _alert_state(hass, mock_config_entry, "home_frost_alert")
    assert state is not None
    assert state.state == "unavailable"


async def test_alert_attributes_populated(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    value = MagicMock()
    value.severity = 2
    value.confidence = 0.95
    value.confidence_level = 3
    value.trigger_value = 8.5
    value.threshold = 6.0
    value.hours_until = 2
    value.duration_hours = 4
    value.extra = {}
    coordinator.v3_entity_states["home_uv_alert"] = EntityState(entity_id="home_uv_alert", value=value, available=True)
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()

    state = _alert_state(hass, mock_config_entry, "home_uv_alert")
    assert state is not None
    attrs = state.attributes
    assert attrs["severity"] == "orange"
    assert attrs["confidence"] == 0.95
    assert attrs["trigger_value"] == 8.5
    assert attrs["threshold"] == 6.0
    assert attrs["hours_until"] == 2
    assert attrs["duration_hours"] == 4
