"""Tests for njord stream health binary sensors."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.njord.const import DOMAIN, StreamName
from tests.conftest import entity_id_for, init_integration


def _stream_entity_id(hass: HomeAssistant, entry, stream_name: str) -> str:
    entity_id = entity_id_for(hass, "binary_sensor", f"{entry.entry_id}_{stream_name}_stream")
    assert entity_id is not None, f"Stream sensor for {stream_name} not found"
    return entity_id


async def test_stream_sensors_created_and_off(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    for stream in ("domain", "enrichment"):
        state = hass.states.get(_stream_entity_id(hass, mock_config_entry, stream))
        assert state is not None
        assert state.state == "off"


async def test_removed_streams_have_no_sensor(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    for stream in ("forecast", "config"):
        assert entity_id_for(hass, "binary_sensor", f"{mock_config_entry.entry_id}_{stream}_stream") is None


async def test_stream_sensor_follows_stream_state(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    coordinator.stream_states[StreamName.DOMAIN] = True
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    domain_state = hass.states.get(_stream_entity_id(hass, mock_config_entry, "domain"))
    enrichment_state = hass.states.get(_stream_entity_id(hass, mock_config_entry, "enrichment"))
    assert domain_state is not None
    assert domain_state.state == "on"
    assert enrichment_state is not None
    assert enrichment_state.state == "off"
