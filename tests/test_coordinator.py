"""Tests for the njord coordinators (unary refresh)."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.njord.const import DOMAIN, Domain, Feature, PollPhase
from custom_components.njord.coordinator import NjordCoordinatorData, NjordDataCoordinator, NjordStatusCoordinator
from tests.conftest import default_domain_data, init_integration


async def test_coordinator_fetches_catalog_domains_and_enrichments(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    await init_integration(hass, mock_config_entry)

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    assert isinstance(coordinator.data, NjordCoordinatorData)
    assert [loc.name for loc in coordinator.data.locations] == ["home"]
    assert set(coordinator.data.domains) == {
        ("home", Domain.FORECAST),
        ("home", Domain.AIR_QUALITY),
        ("home", Domain.FLOOD),
        ("home", Domain.SEASONAL),
    }
    assert "icon_d2" in coordinator.data.model_info
    assert set(coordinator.data.features) == {
        ("home", Feature.UV),
        ("home", Feature.FROST),
        ("home", Feature.POLLEN),
        ("home", Feature.FLOOD_RISK),
    }
    assert coordinator.data.active_enrichments == {
        "Forecast:Uv",
        "Forecast:Frost",
        "AirQuality:Pollen",
        "Flood:FloodRisk",
    }


async def test_solar_is_not_requested(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    requested = {call.args[1] for call in mock_client.get_domain_data.await_args_list}
    assert requested == {Domain.FORECAST, Domain.AIR_QUALITY, Domain.FLOOD, Domain.MARINE, Domain.SEASONAL}


async def test_domain_failure_skips_only_that_domain(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    async def fail_flood(location, domain, model=""):
        if domain == Domain.FLOOD:
            raise RuntimeError("no flood data")
        return default_domain_data(location, domain)

    mock_client.get_domain_data.side_effect = fail_flood

    await init_integration(hass, mock_config_entry)

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    assert ("home", Domain.FORECAST) in coordinator.data.domains
    assert ("home", Domain.FLOOD) not in coordinator.data.domains


async def test_enrichment_failure_does_not_block_domains(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.get_enrichments = AsyncMock(side_effect=Exception("enrichment error"))

    await init_integration(hass, mock_config_entry)

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    assert ("home", Domain.FORECAST) in coordinator.data.domains
    assert coordinator.data.features == {}


async def test_catalog_failure_retries_setup(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    mock_client.get_catalog = AsyncMock(side_effect=Exception("down"))

    await init_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_status_coordinator_merges_targets(hass: HomeAssistant, mock_client) -> None:
    coordinator = NjordStatusCoordinator(hass, mock_client)

    status = await coordinator._async_update_data()

    assert status.version == "1.2.3"
    assert [(t.location, t.phase) for t in status.targets] == [("home", PollPhase.STEADY)]


async def test_status_coordinator_survives_target_failure(hass: HomeAssistant, mock_client) -> None:
    mock_client.get_targets = AsyncMock(side_effect=Exception("no targets"))
    coordinator = NjordStatusCoordinator(hass, mock_client)

    status = await coordinator._async_update_data()

    assert status.targets == []


async def test_coordinator_has_no_update_interval(hass: HomeAssistant, mock_client) -> None:
    assert NjordDataCoordinator(hass, mock_client).update_interval is None


async def test_secondary_models_are_fetched_per_model(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    weather_models = [
        call.kwargs.get("model", "")
        for call in mock_client.get_domain_data.await_args_list
        if call.args[1] == Domain.FORECAST
    ]
    assert sorted(weather_models) == ["", "ecmwf_ifs025"]
    assert set(coordinator.data.model_domains) == {("home", "ecmwf_ifs025")}
    assert coordinator.data.model_domains[("home", "ecmwf_ifs025")].model == "ecmwf_ifs025"


async def test_failed_secondary_model_fetch_keeps_refresh_alive(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    async def fail_secondary(location, domain, model=""):
        if model:
            raise RuntimeError("model down")
        return default_domain_data(location, domain)

    mock_client.get_domain_data.side_effect = fail_secondary

    await init_integration(hass, mock_config_entry)

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    assert coordinator.data.model_domains == {}
    assert ("home", Domain.FORECAST) in coordinator.data.domains
