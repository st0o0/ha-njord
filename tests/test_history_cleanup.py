"""Tests for the removal of the History enrichment and the status partial flags."""

from __future__ import annotations

from dataclasses import replace

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.njord.const import DOMAIN
from custom_components.njord.diagnostics import async_get_config_entry_diagnostics
from tests.conftest import init_integration


def _register_sensor(hass, entry, unique_suffix: str, object_id: str) -> str:
    registry = er.async_get(hass)
    reg_entry = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_{unique_suffix}",
        suggested_object_id=object_id,
        config_entry=entry,
    )
    return reg_entry.entity_id


async def test_stale_model_performance_entity_is_removed(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    stale_id = _register_sensor(hass, mock_config_entry, "home_model_performance", "home_model_performance")

    await init_integration(hass, mock_config_entry)

    assert er.async_get(hass).async_get(stale_id) is None


async def test_other_sensors_are_untouched(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    _register_sensor(hass, mock_config_entry, "home_model_performance", "home_model_performance")

    await init_integration(hass, mock_config_entry)

    assert er.async_get(hass).async_get("sensor.home_diurnal_amplitude") is not None


async def test_setup_without_stale_entities_removes_nothing(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    await init_integration(hass, mock_config_entry)

    registry = er.async_get(hass)
    remaining = [e for e in er.async_entries_for_config_entry(registry, mock_config_entry.entry_id)]
    assert remaining
    assert all(not e.unique_id.endswith("_model_performance") for e in remaining)


async def test_usage_sensors_unavailable_on_budget_partial(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.get_status.return_value = replace(mock_client.get_status.return_value, budget_partial=True)

    await init_integration(hass, mock_config_entry)

    assert hass.states.get("sensor.server_monthly_usage").state == "unavailable"
    assert hass.states.get("sensor.server_daily_usage").state == "unavailable"


async def test_usage_sensors_available_on_complete_status(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    assert hass.states.get("sensor.server_monthly_usage").state == "25.0"
    assert hass.states.get("sensor.server_daily_usage").state == "14.3"


async def test_diagnostics_report_partial_flags(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.get_status.return_value = replace(
        mock_client.get_status.return_value, budget_partial=True, models_partial=True
    )
    await init_integration(hass, mock_config_entry)

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["server_status"]["budget_partial"] is True
    assert diag["server_status"]["models_partial"] is True


async def test_options_form_ignores_legacy_history_group(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    hass.config_entries.async_update_entry(mock_config_entry, options={"disabled_enrichment_groups": ["history"]})
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
