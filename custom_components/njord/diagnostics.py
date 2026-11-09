"""Diagnostics support for njord."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from .const import DOMAIN
from .coordinator import NjordStatusCoordinator
from .v3_coordinator import NjordV3Coordinator

REDACT_KEYS = {"host"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    data: dict[str, Any] = {}

    data["config"] = async_redact_data(dict(entry.data), REDACT_KEYS)
    data["options"] = dict(entry.options)

    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})

    v3_coord: NjordV3Coordinator | None = entry_data.get("v3_coordinator")
    if v3_coord is not None and v3_coord.data is not None:
        data["v3_coordinator"] = {
            "manifest_entities": len(v3_coord.manifest),
            "entity_states": len(v3_coord.data),
            "last_update_success": v3_coord.last_update_success,
        }
    else:
        data["v3_coordinator"] = None

    status_coordinator: NjordStatusCoordinator | None = entry_data.get("status_coordinator")
    if status_coordinator is not None and status_coordinator.data is not None:
        status = status_coordinator.data
        data["server_status"] = {
            "version": status.version,
            "uptime_seconds": status.uptime_seconds,
            "budget": {
                "monthly_limit": status.budget.monthly_limit,
                "monthly_used": status.budget.monthly_used,
                "daily_limit": status.budget.daily_limit,
                "daily_used": status.budget.daily_used,
                "usage_percent": status.budget.usage_percent,
            }
            if status.budget
            else None,
            "budget_partial": status.budget_partial,
            "models_partial": status.models_partial,
            "location_count": len(status.location_statuses),
        }
    else:
        data["server_status"] = "unavailable"

    return data
