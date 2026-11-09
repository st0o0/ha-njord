"""Tests for njord server diagnostic sensor entities."""

from __future__ import annotations

from dataclasses import replace

from homeassistant.core import HomeAssistant

from custom_components.njord.coordinator import NjordStatusCoordinator
from custom_components.njord.models import BudgetStatusData, ServerStatusData
from custom_components.njord.sensor import NjordDailyUsageSensor, NjordMonthlyUsageSensor
from tests.conftest import entity_id_for


def _state(hass: HomeAssistant, entry, key: str, platform: str = "sensor"):
    entity_id = entity_id_for(hass, platform, f"{entry.entry_id}_{key}")
    assert entity_id is not None, f"no entity for {key}"
    state = hass.states.get(entity_id)
    assert state is not None
    return state


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
