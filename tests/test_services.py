"""Tests for the njord.trigger_poll service."""

from __future__ import annotations

import pytest
import voluptuous as vol
from homeassistant.core import HomeAssistant

from custom_components.njord.const import DOMAIN
from tests.conftest import init_integration


async def test_service_registered(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    assert hass.services.has_service(DOMAIN, "trigger_poll")


async def test_service_call_no_params(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    await hass.services.async_call(DOMAIN, "trigger_poll", {}, blocking=True)

    mock_client.trigger_poll.assert_awaited_once_with(location="")


async def test_service_call_with_location(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    await hass.services.async_call(DOMAIN, "trigger_poll", {"location": "graz"}, blocking=True)

    mock_client.trigger_poll.assert_awaited_once_with(location="graz")


async def test_service_rejects_model_field(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(DOMAIN, "trigger_poll", {"location": "graz", "model": "icon_d2"}, blocking=True)

    mock_client.trigger_poll.assert_not_awaited()


async def test_service_removed_on_unload(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)

    assert not hass.services.has_service(DOMAIN, "trigger_poll")
