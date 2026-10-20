"""Tests for the njord config flow (version 2: connection, then enrichments)."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.njord.config_flow import NjordConfigFlow
from custom_components.njord.const import DEFAULT_ENABLED_ENRICHMENTS, DOMAIN


async def _start_user_flow(hass: HomeAssistant, host: str = "localhost", port: int = 8081):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(result["flow_id"], user_input={"host": host, "port": port})


def test_flow_version_is_2() -> None:
    assert NjordConfigFlow.VERSION == 2


async def test_user_step_leads_to_enrichments_step(hass: HomeAssistant, mock_client) -> None:
    result = await _start_user_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "enrichments"
    assert result["description_placeholders"] == {"locations": "1"}
    mock_client.close.assert_awaited()


async def test_config_flow_creates_entry_with_default_enrichments(hass: HomeAssistant, mock_client) -> None:
    result = await _start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"enabled_enrichments": sorted(e.value for e in DEFAULT_ENABLED_ENRICHMENTS)},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "njord (localhost)"
    assert result["data"] == {"host": "localhost", "port": 8081}
    assert result["options"] == {"enabled_enrichments": ["pm25_alert", "pollen_alert", "weather_alerts"]}


async def test_config_flow_custom_enrichments(hass: HomeAssistant, mock_client) -> None:
    result = await _start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"enabled_enrichments": ["flood_risk", "swimming_conditions"]}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == {"enabled_enrichments": ["flood_risk", "swimming_conditions"]}


async def test_config_flow_cannot_connect(hass: HomeAssistant, mock_client) -> None:
    mock_client.get_catalog.side_effect = Exception("Connection refused")

    result = await _start_user_flow(hass, "badhost", 9999)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_config_flow_duplicate_abort(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    result = await _start_user_flow(hass)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_updates_connection(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"host": "newhost", "port": 9000}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert dict(mock_config_entry.data) == {"host": "newhost", "port": 9000}
