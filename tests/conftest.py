"""Shared test fixtures for ha-njord."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.njord.const import (
    DOMAIN,
    AlertSeverity,
    AlertType,
    Domain,
    Feature,
    PollPhase,
)
from custom_components.njord.models import (
    AirQualityDomainData,
    AirQualitySampleData,
    AlertData,
    BudgetStatusData,
    CatalogData,
    FeatureData,
    FloodDomainData,
    FloodSampleData,
    ModelInfoData,
    NjordLocation,
    ServerStatusData,
    TargetData,
    WeatherDomainData,
    WeatherSampleData,
)

# One sample in the past (the "current" one) and one far in the future (the forecast).
PAST = datetime(2000, 1, 1, 12, 0, tzinfo=UTC)
FUTURE = datetime(2099, 1, 1, 12, 0, tzinfo=UTC)
MODEL_RUN = datetime(2000, 1, 1, 6, 0, tzinfo=UTC)


def weather_sample(valid_at: datetime = PAST, **overrides) -> WeatherSampleData:
    values = {
        "valid_at": valid_at,
        "temperature": 22.5,
        "apparent_temperature": 21.0,
        "wind_speed": 3.5,
        "precipitation": 0.4,
        "precipitation_probability": 40.4,
        "cloud_cover": 30.0,
        "pressure": 1013.0,
        "weather_code": 1,
        "humidity": 65.0,
        "dew_point": 15.0,
        "uv_index": 5.0,
        "is_day": True,
        "wind_gusts": 8.0,
        "visibility": 20000.0,
        "cape": 120.0,
    }
    values.update(overrides)
    return WeatherSampleData(**values)


def default_catalog() -> CatalogData:
    return CatalogData(
        locations=[NjordLocation(name="home", latitude=47.05, longitude=8.31, models=["icon_d2", "ecmwf_ifs025"])],
        model_info={
            "icon_d2": ModelInfoData(
                id="icon_d2",
                display_name="ICON-D2",
                provider="DWD",
                region="DE, CH, AT",
                coverage_tier="regional",
                resolution_km=2.2,
                max_forecast_hours=60,
            ),
            "ecmwf_ifs025": ModelInfoData(
                id="ecmwf_ifs025",
                display_name="ECMWF IFS",
                provider="ECMWF",
                region="Global",
                coverage_tier="global",
                resolution_km=25.0,
                max_forecast_hours=360,
            ),
        },
    )


def default_domain_data(location: str, domain: Domain, model: str = ""):
    """Canned data per domain; marine has none."""
    match domain:
        case Domain.WEATHER:
            return WeatherDomainData(
                location, MODEL_RUN, [weather_sample(), weather_sample(FUTURE, temperature=25.0)], model=model
            )
        case Domain.AIR_QUALITY:
            return AirQualityDomainData(
                location,
                MODEL_RUN,
                [AirQualitySampleData(valid_at=PAST, pm25=12.34, pm10=20.0, ozone=80.0, birch_pollen=3.0)],
            )
        case Domain.FLOOD:
            return FloodDomainData(
                location, MODEL_RUN, [FloodSampleData(valid_at=PAST, discharge=55.5, discharge_mean=50.0)]
            )
    return None


def default_enrichment(location: str = "home") -> list[FeatureData]:
    def alert(feature: Feature, **fields) -> FeatureData:
        return FeatureData(
            location=location,
            feature=feature,
            updated_at=PAST,
            alert=AlertData(type=AlertType(feature.value), **fields),
        )

    return [
        alert(
            Feature.UV,
            severity=AlertSeverity.ORANGE,
            confidence=1.0,
            trigger_value=8.5,
            threshold=6.0,
            peak_value=9.2,
            hours_until=2,
            duration_hours=4,
        ),
        alert(Feature.FROST, severity=AlertSeverity.NONE),
        alert(Feature.POLLEN, severity=AlertSeverity.YELLOW, trigger_value=40.0, threshold=30.0),
        alert(Feature.FLOOD_RISK, severity=AlertSeverity.RED, trigger_value=300.0, threshold=200.0),
    ]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


async def _empty_async_gen(**kwargs):
    return
    yield


@pytest.fixture
def mock_client():
    """Patch NjordClient across all import sites with canned responses."""
    mock = AsyncMock()
    mock.connect = AsyncMock()
    mock.close = AsyncMock()
    mock.get_catalog = AsyncMock(return_value=default_catalog())
    mock.get_domain_data = AsyncMock(
        side_effect=lambda location, domain, model="": default_domain_data(location, domain, model)
    )
    mock.get_enrichments = AsyncMock(side_effect=lambda location: default_enrichment(location))
    mock.get_status = AsyncMock(
        return_value=ServerStatusData(
            version="1.2.3",
            uptime_seconds=3600,
            budget=BudgetStatusData(
                monthly_limit=20000, monthly_used=5000, daily_limit=700, daily_used=100, usage_percent=25.0
            ),
            active_enrichments=["Weather:Uv", "Weather:Frost", "AirQuality:Pollen", "Flood:FloodRisk"],
        )
    )
    mock.trigger_poll = AsyncMock(return_value=2)
    mock.get_targets = AsyncMock(
        return_value=[
            TargetData(
                location="home",
                phase=PollPhase.STEADY,
                next_poll=datetime(2099, 1, 1, 12, 30, tzinfo=UTC),
                miss_count=1,
            ),
        ]
    )
    mock.stream_domain_data = MagicMock(side_effect=lambda **kwargs: _empty_async_gen())
    mock.stream_enrichments = MagicMock(side_effect=lambda **kwargs: _empty_async_gen())

    with (
        patch("custom_components.njord.NjordClient", return_value=mock),
        patch("custom_components.njord.config_flow.NjordClient", return_value=mock),
    ):
        yield mock


def _make_entry(hass, options: dict | None = None, version: int = 3):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "localhost", "port": 8081},
        options=options or {},
        title="njord (localhost)",
        unique_id="localhost:8081",
        version=version,
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_config_entry(hass):
    """A v3 config entry for njord."""
    return _make_entry(hass)


@pytest.fixture
def all_alerts_entry(hass, mock_client):
    """A v3 config entry whose server reports no active-enrichment filter (every feature enabled)."""
    mock_client.get_status.return_value = replace(mock_client.get_status.return_value, active_enrichments=[])
    return _make_entry(hass)


async def init_integration(hass, entry):
    """Set up the njord integration with a config entry."""
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def entity_id_for(hass, platform: str, unique_id: str) -> str | None:
    """Resolve an entity id through the entity registry by unique id."""
    from homeassistant.helpers import entity_registry as er

    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, unique_id)
