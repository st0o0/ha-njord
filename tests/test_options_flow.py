"""Tests for the njord options flow."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.njord.const import DOMAIN
from tests.conftest import init_integration


async def _configure(hass: HomeAssistant, entry, **overrides):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"
    user_input = {
        "status_poll_interval": 30,
        "enabled_enrichments": ["weather_alerts", "pollen_alert", "pm25_alert"],
    }
    user_input.update(overrides)
    return await hass.config_entries.options.async_configure(result["flow_id"], user_input=user_input)


async def test_options_form_fields_and_defaults(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    defaults = {key.schema: key.default() for key in result["data_schema"].schema}
    assert defaults == {
        "status_poll_interval": 30,
        "enabled_enrichments": ["pm25_alert", "pollen_alert", "weather_alerts"],
    }


async def test_options_form_shows_stored_enrichments(hass: HomeAssistant, mock_client, all_alerts_entry) -> None:
    await init_integration(hass, all_alerts_entry)

    result = await hass.config_entries.options.async_init(all_alerts_entry.entry_id)

    defaults = {key.schema: key.default() for key in result["data_schema"].schema}
    assert len(defaults["enabled_enrichments"]) == 6


async def test_poll_interval_only_change_does_not_reload(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    reload = AsyncMock()
    hass.config_entries.async_reload = reload

    result = await _configure(hass, mock_config_entry, status_poll_interval=120)
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert mock_config_entry.options["status_poll_interval"] == 120
    reload.assert_not_awaited()
    status_coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["status_coordinator"]
    assert status_coordinator.update_interval == timedelta(seconds=120)


async def test_enrichment_change_reloads_entry(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    reload = AsyncMock()
    hass.config_entries.async_reload = reload

    result = await _configure(hass, mock_config_entry, enabled_enrichments=["flood_risk", "weather_alerts"])
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert mock_config_entry.options["enabled_enrichments"] == ["flood_risk", "weather_alerts"]
    reload.assert_awaited_once_with(mock_config_entry.entry_id)


async def test_disabling_all_enrichments_is_stored(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    result = await _configure(hass, mock_config_entry, enabled_enrichments=[])

    assert result["type"] == "create_entry"
    assert mock_config_entry.options["enabled_enrichments"] == []
