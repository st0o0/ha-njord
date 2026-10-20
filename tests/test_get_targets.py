"""Tests for poll targets (status coordinator and target sensors)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.njord.const import DOMAIN
from tests.conftest import entity_id_for, init_integration


async def test_get_targets_called_on_setup(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    mock_client.get_targets.assert_called()
    status_coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["status_coordinator"]
    assert [t.location for t in status_coordinator.data.targets] == ["home"]


async def test_one_target_sensor_per_location(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    entity_id = entity_id_for(hass, "sensor", f"{mock_config_entry.entry_id}_home_target")
    assert entity_id is not None
    assert entity_id_for(hass, "sensor", f"{mock_config_entry.entry_id}_home_icon_d2_target") is None
    entry = er.async_get(hass).async_get(entity_id)
    assert entry is not None
    assert entry.disabled_by is not None
