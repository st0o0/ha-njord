"""Tests for njord diagnostics."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.njord.diagnostics import async_get_config_entry_diagnostics
from tests.conftest import init_integration


async def test_diagnostics_output(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["config"] == {"host": "**REDACTED**", "port": 8081}
    assert diag["options"] == {}
    assert diag["coordinator"] == {
        "locations": ["home"],
        "domains": {"home": ["air_quality", "flood", "forecast", "seasonal"]},
        "features": {"home": ["flood_risk", "frost", "pollen", "uv"]},
        "active_enrichments": ["AirQuality:Pollen", "Flood:FloodRisk", "Forecast:Frost", "Forecast:Uv"],
        "last_update_success": True,
    }
    assert diag["stream_states"] == {"domain": False, "enrichment": False}


async def test_diagnostics_server_status(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    status = diag["server_status"]
    assert status["version"] == "1.2.3"
    assert status["uptime_seconds"] == 3600
    assert status["budget"]["usage_percent"] == 25.0
    assert status["targets_count"] == 1


async def test_diagnostics_before_setup(hass: HomeAssistant, mock_config_entry) -> None:
    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diag["coordinator"] is None
    assert diag["stream_states"] is None
    assert diag["server_status"] == "unavailable"
