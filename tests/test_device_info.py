"""Tests for njord device registration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from tests.conftest import entity_id_for, init_integration


def _device_for(hass: HomeAssistant, platform: str, unique_id: str) -> dr.DeviceEntry:
    entity_id = entity_id_for(hass, platform, unique_id)
    assert entity_id is not None, f"no entity registered for unique_id={unique_id}"
    entity_entry = er.async_get(hass).async_get(entity_id)
    assert entity_entry is not None
    assert entity_entry.device_id is not None
    device = dr.async_get(hass).async_get(entity_entry.device_id)
    assert device is not None
    return device


async def test_location_entities_share_one_device(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    prefix = mock_config_entry.entry_id

    frost_sensor = _device_for(hass, "sensor", f"{prefix}_home_frost")
    frost_alert = _device_for(hass, "binary_sensor", f"{prefix}_home_frost_alert")
    weather = _device_for(hass, "weather", f"{prefix}_home_weather")

    assert frost_sensor.id == frost_alert.id == weather.id
    assert frost_sensor.model == "Weather Station"
    assert frost_sensor.manufacturer == "njord"
    assert frost_sensor.sw_version == "1.2.3"


async def test_server_entities_share_server_device(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    prefix = mock_config_entry.entry_id

    version = _device_for(hass, "sensor", f"{prefix}_version")
    button = _device_for(hass, "button", f"{prefix}_trigger_poll")

    assert version.id == button.id
    assert version.model == "Weather Service"
    assert version.sw_version == "1.2.3"
    assert version.manufacturer == "njord"
