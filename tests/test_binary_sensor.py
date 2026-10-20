"""Tests for njord alert binary sensors."""

from __future__ import annotations

from dataclasses import replace

from homeassistant.core import HomeAssistant

from custom_components.njord.const import DEFAULT_ENABLED_ENRICHMENTS as DEFAULTS
from custom_components.njord.const import DOMAIN, AlertType, enabled_alert_types
from custom_components.njord.models import AlertData
from tests.conftest import default_enrichment, entity_id_for, init_integration


def _alert_state(hass: HomeAssistant, entry, alert_type: str, location: str = "home"):
    entity_id = entity_id_for(hass, "binary_sensor", f"{entry.entry_id}_{location}_{alert_type}_alert")
    return hass.states.get(entity_id) if entity_id else None


async def test_default_entry_creates_enabled_alert_types_only(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    await init_integration(hass, mock_config_entry)

    for alert_type in enabled_alert_types(DEFAULTS):
        assert _alert_state(hass, mock_config_entry, alert_type) is not None, alert_type
    for alert_type in (AlertType.FLOOD_RISK, AlertType.FLOOD_RAIN, AlertType.SWIMMING_CONDITIONS):
        assert _alert_state(hass, mock_config_entry, alert_type) is None, alert_type


async def test_all_enrichments_create_all_nineteen_alerts(hass: HomeAssistant, mock_client, all_alerts_entry) -> None:
    await init_integration(hass, all_alerts_entry)

    created = [t for t in AlertType if t is not AlertType.UNSPECIFIED and _alert_state(hass, all_alerts_entry, t)]
    assert len(created) == 19


async def test_active_alert_is_on_with_attributes(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = _alert_state(hass, mock_config_entry, "uv")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["severity"] == "orange"
    assert state.attributes["confidence"] == 1.0
    assert state.attributes["trigger_value"] == 8.5
    assert state.attributes["threshold"] == 6.0
    assert state.attributes["peak_value"] == 9.2
    assert state.attributes["hours_until"] == 2
    assert state.attributes["duration_hours"] == 4
    assert state.attributes["unit"] == "UV"
    assert state.attributes["friendly_name"] == "Home UV Alert"


async def test_pollen_alert_on_without_optional_attributes(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = _alert_state(hass, mock_config_entry, "pollen")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["unit"] == "grains/m³"
    assert "peak_value" not in state.attributes
    assert "hours_until" not in state.attributes


async def test_inactive_and_missing_alerts_are_off(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    frost = _alert_state(hass, mock_config_entry, "frost")
    heat = _alert_state(hass, mock_config_entry, "heat")
    assert frost is not None
    assert frost.state == "off"
    assert "severity" not in frost.attributes
    assert heat is not None
    assert heat.state == "off"


async def test_flood_alert_on_when_enabled(hass: HomeAssistant, mock_client, all_alerts_entry) -> None:
    await init_integration(hass, all_alerts_entry)

    state = _alert_state(hass, all_alerts_entry, "flood_risk")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["severity"] == "red"
    assert state.attributes["unit"] == "m³/s"


async def test_alert_follows_coordinator_update(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    coordinator.data.enrichments["home"] = replace(
        default_enrichment(), alerts=[AlertData(type="frost", severity="yellow", trigger_value=-2.0, threshold=0.0)]
    )
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    frost = _alert_state(hass, mock_config_entry, "frost")
    uv = _alert_state(hass, mock_config_entry, "uv")
    assert frost is not None
    assert frost.state == "on"
    assert uv is not None
    assert uv.state == "off"


async def test_alert_unavailable_without_enrichment(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    del coordinator.data.enrichments["home"]
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    state = _alert_state(hass, mock_config_entry, "uv")
    assert state is not None
    assert state.state == "unavailable"


async def test_no_alert_entities_when_server_reports_alerts_inactive(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    status = await mock_client.get_status()
    mock_client.get_status.return_value = replace(status, active_enrichments=[])

    await init_integration(hass, mock_config_entry)

    assert _alert_state(hass, mock_config_entry, "uv") is None
    assert entity_id_for(hass, "event", f"{mock_config_entry.entry_id}_home_weather_alert") is None
    assert entity_id_for(hass, "binary_sensor", f"{mock_config_entry.entry_id}_domain_stream") is not None


async def test_no_alert_entities_when_all_enrichments_disabled(hass: HomeAssistant, mock_client) -> None:
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "localhost", "port": 8081},
        options={"enabled_enrichments": []},
        unique_id="localhost:8081",
        version=2,
    )
    entry.add_to_hass(hass)

    await init_integration(hass, entry)

    assert _alert_state(hass, entry, "uv") is None
    assert entity_id_for(hass, "event", f"{entry.entry_id}_home_weather_alert") is None
