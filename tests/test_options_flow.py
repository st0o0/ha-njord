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
    user_input = {"status_poll_interval": 30}
    user_input.update(overrides)
    return await hass.config_entries.options.async_configure(result["flow_id"], user_input=user_input)


async def test_options_form_fields_and_defaults(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    defaults = {key.schema: key.default() for key in result["data_schema"].schema}
    assert defaults == {"status_poll_interval": 30}


async def test_poll_interval_change_updates_coordinator(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
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
