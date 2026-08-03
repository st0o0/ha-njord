"""Tests for njord options flow."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.njord.config_flow import ENRICHMENT_GROUPS
from tests.conftest import init_integration


async def test_options_flow_defaults(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    """Opening the options flow should show default values."""
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    schema_keys = list(result["data_schema"].schema.keys())
    schema_key_names = [k.schema for k in schema_keys]
    assert "status_poll_interval" in schema_key_names
    assert "enabled_enrichment_groups" in schema_key_names


async def test_options_flow_custom_values(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    """Submitting custom options should store them on the entry."""
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == "form"

    enabled = [g for g in ENRICHMENT_GROUPS if g != "energy"]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "status_poll_interval": 60,
            "enabled_enrichment_groups": enabled,
        },
    )
    assert result["type"] == "create_entry"

    assert mock_config_entry.options["status_poll_interval"] == 60
    assert "energy" in mock_config_entry.options["disabled_enrichment_groups"]
    assert "alerts" not in mock_config_entry.options["disabled_enrichment_groups"]


async def test_options_poll_interval_only_no_reload(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    """Changing only poll interval should not trigger a reload."""
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "status_poll_interval": 120,
            "enabled_enrichment_groups": ENRICHMENT_GROUPS,
        },
    )
    assert result["type"] == "create_entry"

    assert mock_config_entry.options["status_poll_interval"] == 120
    assert mock_config_entry.options["disabled_enrichment_groups"] == []

    assert mock_config_entry.state.name == "LOADED"
