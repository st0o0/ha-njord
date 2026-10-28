"""Tests for njord alert binary sensors."""

from __future__ import annotations

from dataclasses import replace

from homeassistant.core import HomeAssistant

from custom_components.njord.const import DOMAIN, AlertType, Feature
from custom_components.njord.models import AlertData, FeatureData
from tests.conftest import PAST, entity_id_for, init_integration


def _alert_state(hass: HomeAssistant, entry, alert_type: str, location: str = "home"):
    entity_id = entity_id_for(hass, "binary_sensor", f"{entry.entry_id}_{location}_{alert_type}_alert")
    return hass.states.get(entity_id) if entity_id else None


async def test_default_entry_creates_alerts_of_active_enrichments_only(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    await init_integration(hass, mock_config_entry)

    for alert_type in ("uv", "frost", "pollen", "flood_risk"):
        assert _alert_state(hass, mock_config_entry, alert_type) is not None, alert_type
    for alert_type in ("heat", "flood_rain", "swimming_conditions"):
        assert _alert_state(hass, mock_config_entry, alert_type) is None, alert_type


async def test_unfiltered_server_creates_all_alerts(hass: HomeAssistant, mock_client, all_alerts_entry) -> None:
    await init_integration(hass, all_alerts_entry)

    created = [t for t in AlertType if t is not AlertType.UNSPECIFIED and _alert_state(hass, all_alerts_entry, t)]
    assert len(created) == 22


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


async def test_inactive_and_missing_alerts_are_off(hass: HomeAssistant, mock_client, all_alerts_entry) -> None:
    await init_integration(hass, all_alerts_entry)

    frost = _alert_state(hass, all_alerts_entry, "frost")
    heat = _alert_state(hass, all_alerts_entry, "heat")
    assert frost is not None
    assert frost.state == "off"
    assert "severity" not in frost.attributes
    assert heat is not None
    assert heat.state == "off"


async def test_flood_alert_on_when_active(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = _alert_state(hass, mock_config_entry, "flood_risk")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["severity"] == "red"
    assert state.attributes["unit"] == "m³/s"


async def test_alert_follows_coordinator_update(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    coordinator.data.features[("home", Feature.FROST)] = FeatureData(
        location="home",
        feature=Feature.FROST,
        updated_at=PAST,
        alert=AlertData(type="frost", severity="yellow", trigger_value=-2.0, threshold=0.0),
    )
    del coordinator.data.features[("home", Feature.UV)]
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    frost = _alert_state(hass, mock_config_entry, "frost")
    uv = _alert_state(hass, mock_config_entry, "uv")
    assert frost is not None
    assert frost.state == "on"
    assert uv is not None
    assert uv.state == "off"


async def test_alert_off_without_feature_result(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    coordinator.data.features.clear()
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    state = _alert_state(hass, mock_config_entry, "uv")
    assert state is not None
    assert state.state == "off"


async def test_unlisted_feature_creates_no_entity_when_streamed(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    coordinator._apply_feature(
        FeatureData(
            location="home", feature=Feature.HEAT, updated_at=PAST, alert=AlertData(type="heat", severity="red")
        )
    )
    await hass.async_block_till_done()

    assert _alert_state(hass, mock_config_entry, "heat") is None


async def test_status_without_active_enrichments_keeps_every_entity(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    status = await mock_client.get_status()
    mock_client.get_status.return_value = replace(status, active_enrichments=[])

    await init_integration(hass, mock_config_entry)

    assert _alert_state(hass, mock_config_entry, "uv") is not None
    assert _alert_state(hass, mock_config_entry, "heat") is not None
    assert entity_id_for(hass, "binary_sensor", f"{mock_config_entry.entry_id}_domain_stream") is not None


async def test_new_alert_types_are_created(hass: HomeAssistant, mock_client, all_alerts_entry) -> None:
    await init_integration(hass, all_alerts_entry)

    assert _alert_state(hass, all_alerts_entry, "compound_heat_stress") is not None
    assert _alert_state(hass, all_alerts_entry, "migraine_risk") is not None
