"""Tests for njord integration setup, teardown and migration."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.njord.const import DOMAIN
from custom_components.njord.coordinator import NjordDataCoordinator
from tests.conftest import init_integration


async def test_setup_entry(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert set(entry_data) == {"client", "coordinator", "status_coordinator"}
    mock_client.connect.assert_awaited_once()
    mock_client.get_catalog.assert_awaited()
    mock_client.get_status.assert_awaited()


async def test_unload_entry(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id) is True
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]
    mock_client.close.assert_awaited_once()


async def test_setup_entry_connection_failure(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.connect.side_effect = Exception("Connection refused")

    await init_integration(hass, mock_config_entry)

    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_without_status_still_loads(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.get_status = AsyncMock(side_effect=Exception("status down"))

    await init_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert entry_data["status_coordinator"] is None
    assert entry_data["coordinator"].data.active_enrichments is None


async def test_streams_start_after_setup(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    mock_client.stream_domain_data.assert_called_once()
    mock_client.stream_enrichments.assert_called_once()


async def test_streams_stop_on_unload(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    tasks_before = list(coordinator._stream_tasks)
    assert len(tasks_before) == 2

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id) is True

    assert all(task.done() for task in tasks_before)


async def test_migrate_v1_entry(hass: HomeAssistant, mock_client) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "localhost", "port": 8081},
        options={
            "status_poll_interval": 60,
            "disabled_enrichment_groups": ["trends"],
            "sensor_push": {"home": {"indoor_temperature": ["sensor.x"]}},
        },
        unique_id="localhost:8081",
        version=1,
    )
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", DOMAIN, "old_per_model_sensor", config_entry=entry)

    await init_integration(hass, entry)

    assert entry.version == 2
    assert dict(entry.options) == {"status_poll_interval": 60}
    assert registry.async_get_entity_id("sensor", DOMAIN, "old_per_model_sensor") is None
    assert entry.state is ConfigEntryState.LOADED


async def test_v2_entry_is_not_migrated(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    hass.config_entries.async_update_entry(mock_config_entry, options={"enabled_enrichments": ["flood_risk"]})

    await init_integration(hass, mock_config_entry)

    assert mock_config_entry.version == 2
    assert dict(mock_config_entry.options) == {"enabled_enrichments": ["flood_risk"]}
