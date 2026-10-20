"""Tests for the njord alert event entity."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.njord.const import DOMAIN, AlertEvent, Feature
from custom_components.njord.models import AlertData, FeatureData
from tests.conftest import entity_id_for, init_integration

EVENT_UNIQUE = "{}_home_weather_alert"


def _state(hass: HomeAssistant, entry):
    entity_id = entity_id_for(hass, "event", EVENT_UNIQUE.format(entry.entry_id))
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def _push(hass: HomeAssistant, entry, *alerts: AlertData) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    baseline = [
        AlertData(type="pollen", severity="yellow", trigger_value=40.0, threshold=30.0),
        AlertData(type="flood_risk", severity="red", trigger_value=300.0, threshold=200.0),
    ]
    coordinator.data.features = {
        ("home", Feature(a.type.value)): FeatureData("home", Feature(a.type.value), alert=a)
        for a in [*baseline, *alerts]
    }
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()


def _uv(severity: str) -> AlertData:
    return AlertData(type="uv", severity=severity, trigger_value=8.5, threshold=6.0, peak_value=9.0, hours_until=2)


async def test_event_entity_defaults(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    state = _state(hass, mock_config_entry)
    assert state.attributes["event_types"] == [e.value for e in AlertEvent]
    assert state.attributes["icon"] == "mdi:weather-lightning-rainy"
    assert state.attributes.get("event_type") is None


async def test_alert_started(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    await _push(hass, mock_config_entry, _uv("orange"), AlertData(type="frost", severity="yellow", threshold=0.0))

    state = _state(hass, mock_config_entry)
    assert state.attributes["event_type"] == "alert_started"
    assert state.attributes["type"] == "frost"
    assert state.attributes["location"] == "home"
    assert state.attributes["severity"] == "yellow"


async def test_alert_escalated_and_deescalated(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    await _push(hass, mock_config_entry, _uv("red"))
    state = _state(hass, mock_config_entry)
    assert state.attributes["event_type"] == "alert_escalated"
    assert state.attributes["previous_severity"] == "orange"
    assert state.attributes["severity"] == "red"
    assert state.attributes["peak_value"] == 9.0
    assert state.attributes["hours_until"] == 2

    await _push(hass, mock_config_entry, _uv("yellow"))
    state = _state(hass, mock_config_entry)
    assert state.attributes["event_type"] == "alert_deescalated"
    assert state.attributes["previous_severity"] == "red"


async def test_alert_cleared(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    await _push(hass, mock_config_entry)

    state = _state(hass, mock_config_entry)
    assert state.attributes["event_type"] == "alert_cleared"
    assert state.attributes["type"] == "uv"
    assert state.attributes["previous_severity"] == "orange"


async def test_severity_none_counts_as_cleared(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    await _push(hass, mock_config_entry, _uv("none"))

    assert _state(hass, mock_config_entry).attributes["event_type"] == "alert_cleared"


async def test_unchanged_alerts_fire_nothing(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    await _push(hass, mock_config_entry, _uv("orange"))

    assert _state(hass, mock_config_entry).attributes.get("event_type") is None


async def test_disabled_alert_types_are_ignored(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    # heat is not an active enrichment for the default entry
    await _push(hass, mock_config_entry, _uv("orange"), AlertData(type="heat", severity="red"))

    assert _state(hass, mock_config_entry).attributes.get("event_type") is None


async def test_enabled_extra_alert_type_fires(hass: HomeAssistant, mock_client, all_alerts_entry) -> None:
    await init_integration(hass, all_alerts_entry)

    await _push(hass, all_alerts_entry, _uv("orange"), AlertData(type="flood_risk", severity="orange"))

    state = _state(hass, all_alerts_entry)
    assert state.attributes["event_type"] == "alert_deescalated"
    assert state.attributes["type"] == "flood_risk"
