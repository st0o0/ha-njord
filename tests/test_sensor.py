"""Tests for njord sensor entities."""

from __future__ import annotations

from dataclasses import replace

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.njord.const import DOMAIN, Domain
from custom_components.njord.coordinator import NjordStatusCoordinator
from custom_components.njord.models import BudgetStatusData, ServerStatusData
from custom_components.njord.sensor import DOMAIN_SENSORS, NjordDailyUsageSensor, NjordMonthlyUsageSensor
from tests.conftest import MODEL_RUN, entity_id_for, init_integration


def _state(hass: HomeAssistant, entry, key: str, platform: str = "sensor"):
    entity_id = entity_id_for(hass, platform, f"{entry.entry_id}_{key}")
    assert entity_id is not None, f"no entity for {key}"
    state = hass.states.get(entity_id)
    assert state is not None
    return state


def test_domain_sensor_keys_are_unique_and_cover_domains() -> None:
    keys = [d.key for d in DOMAIN_SENSORS]
    assert len(keys) == len(set(keys))
    assert {d.domain for d in DOMAIN_SENSORS} == {Domain.AIR_QUALITY, Domain.FLOOD, Domain.MARINE}


async def test_air_quality_sensors(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    pm25 = _state(hass, mock_config_entry, "home_pm25")
    assert float(pm25.state) == pytest.approx(12.34)
    assert pm25.attributes["unit_of_measurement"] == "µg/m³"
    assert pm25.attributes["device_class"] == "pm25"
    assert pm25.attributes["model_run"] == MODEL_RUN.isoformat()
    assert float(_state(hass, mock_config_entry, "home_ozone").state) == 80.0
    assert float(_state(hass, mock_config_entry, "home_birch_pollen").state) == 3.0


async def test_missing_optional_value_reads_unknown(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    assert _state(hass, mock_config_entry, "home_grass_pollen").state == "unknown"


async def test_flood_sensor_has_statistics_attributes(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    discharge = _state(hass, mock_config_entry, "home_river_discharge")
    assert float(discharge.state) == 55.5
    assert discharge.attributes["unit_of_measurement"] == "m³/s"
    assert discharge.attributes["discharge_mean"] == 50.0
    assert "discharge_max" not in discharge.attributes


async def test_no_sensors_for_domain_without_data(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    for key in ("wave_height", "wave_period", "wave_direction", "water_temperature"):
        assert entity_id_for(hass, "sensor", f"{mock_config_entry.entry_id}_home_{key}") is None


async def test_sensor_unavailable_without_samples(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    key = ("home", Domain.AIR_QUALITY)
    coordinator.data.domains[key] = replace(coordinator.data.domains[key], points=[])
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    assert _state(hass, mock_config_entry, "home_pm25").state == "unavailable"


async def test_server_diagnostic_sensors(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    monthly = _state(hass, mock_config_entry, "monthly_usage")
    assert float(monthly.state) == 25.0
    assert monthly.attributes["limit"] == 20000
    assert monthly.attributes["used"] == 5000
    assert float(_state(hass, mock_config_entry, "daily_usage").state) == pytest.approx(14.3)
    assert _state(hass, mock_config_entry, "version").state == "1.2.3"
    assert float(_state(hass, mock_config_entry, "uptime").state) == 1.0


async def test_target_sensor_is_disabled_by_default(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    entity_id = entity_id_for(hass, "sensor", f"{mock_config_entry.entry_id}_home_target")
    assert entity_id is not None
    entry = er.async_get(hass).async_get(entity_id)
    assert entry is not None
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_usage_sensors_unavailable_when_budget_partial(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    status_coordinator = NjordStatusCoordinator(hass, mock_client)
    status_coordinator.data = ServerStatusData(
        budget=BudgetStatusData(monthly_limit=100, monthly_used=10, daily_limit=10, daily_used=5),
        budget_partial=True,
    )

    monthly = NjordMonthlyUsageSensor(status_coordinator, mock_config_entry)
    daily = NjordDailyUsageSensor(status_coordinator, mock_config_entry)
    assert monthly.available is False
    assert daily.available is False

    status_coordinator.data = replace(status_coordinator.data, budget_partial=False)
    assert monthly.native_value == 10.0
    assert daily.native_value == 50.0


async def test_usage_sensors_without_limits(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    status_coordinator = NjordStatusCoordinator(hass, mock_client)
    status_coordinator.data = ServerStatusData(budget=BudgetStatusData())

    monthly = NjordMonthlyUsageSensor(status_coordinator, mock_config_entry)

    assert monthly.available is False
    assert monthly.native_value is None
