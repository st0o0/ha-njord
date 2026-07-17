"""Shared test fixtures for ha-njord."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.njord.const import DOMAIN
from custom_components.njord.models import (
    AlertData,
    ConsensusData,
    CopOptimalHourData,
    DailyForecastData,
    DerivedData,
    EnergyData,
    EnrichmentData,
    ForecastData,
    HistoryData,
    HorizonConsensusData,
    HorizonDerivedData,
    HourlyForecastData,
    IndexData,
    ModelMetricsData,
    NjordConfigData,
    NjordLocation,
    ParameterConsensusData,
    ParameterTrendData,
    TrendData,
)


def _default_config() -> NjordConfigData:
    return NjordConfigData(
        locations=[
            NjordLocation(
                name="home",
                latitude=47.05,
                longitude=8.31,
                models=["icon_d2", "ecmwf_ifs025"],
            ),
        ],
        default_models=["icon_d2", "ecmwf_ifs025"],
        horizons=[3, 6, 12, 24],
        forecast_days=7,
        poll_interval_seconds=3600,
    )


def _default_forecast(location: str = "home", model: str = "icon_d2") -> ForecastData:
    return ForecastData(
        location=location,
        model=model,
        updated_at=1720000000,
        hourly=[
            HourlyForecastData(
                timestamp=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
                temperature=22.5,
                apparent_temperature=21.0,
                humidity=65.0,
                wind_speed=3.5,
                wind_bearing=180.0,
                pressure_msl=1013.0,
                weather_code=1,
                is_day=True,
                precipitation=0.0,
                cloud_cover=30.0,
                rain=0.0,
                wind_gusts=8.0,
            ),
        ],
        daily=[
            DailyForecastData(
                date="2026-07-15",
                temperature_max=28.0,
                temperature_min=15.0,
                precipitation_sum=2.5,
                wind_speed_max=12.0,
                wind_gusts_max=18.0,
                sunrise="2026-07-15T03:48:00+00:00",
                sunset="2026-07-15T19:17:00+00:00",
                weather_code=61,
            ),
            DailyForecastData(
                date="2026-07-16",
                temperature_max=25.0,
                temperature_min=14.0,
                precipitation_sum=0.0,
                wind_speed_max=10.0,
                weather_code=1,
            ),
            DailyForecastData(
                date="2026-07-17",
                temperature_max=30.0,
                temperature_min=18.0,
                precipitation_sum=1.0,
                wind_speed_max=15.0,
                weather_code=3,
            ),
        ],
    )


def _default_consensus() -> ConsensusData:
    temp_horizons = []
    wmo_horizons = []
    is_day_horizons = []
    precip_horizons = []
    wind_horizons = []
    for i in range(49):
        agreement = max(0.0, 0.9 - i * 0.015)
        temp_horizons.append(
            HorizonConsensusData(
                horizon=f"h{i}",
                median=20.0 + (i % 12) * 0.5,
                spread=3.0 + i * 0.1,
                agreement=round(agreement, 2),
                available_models=max(2, 10 - i // 10),
            )
        )
        wmo_horizons.append(
            HorizonConsensusData(horizon=f"h{i}", median=1.0 if i < 24 else 3.0, available_models=max(2, 10 - i // 10))
        )
        is_day_horizons.append(
            HorizonConsensusData(
                horizon=f"h{i}", median=1.0 if 6 <= (i % 24) <= 20 else 0.0, available_models=max(2, 10 - i // 10)
            )
        )
        precip_horizons.append(
            HorizonConsensusData(horizon=f"h{i}", median=0.0 if i < 30 else 0.5, available_models=max(2, 10 - i // 10))
        )
        wind_horizons.append(
            HorizonConsensusData(horizon=f"h{i}", median=5.0 + (i % 8), available_models=max(2, 10 - i // 10))
        )
    return ConsensusData(
        parameters=[
            ParameterConsensusData(parameter="temperature_2m", unit="°C", by_horizon=temp_horizons),
            ParameterConsensusData(parameter="weather_code", unit="wmo code", by_horizon=wmo_horizons),
            ParameterConsensusData(parameter="is_day", by_horizon=is_day_horizons),
            ParameterConsensusData(parameter="precipitation", unit="mm", by_horizon=precip_horizons),
            ParameterConsensusData(parameter="wind_speed_10m", unit="m/s", by_horizon=wind_horizons),
        ],
    )


def _default_enrichment(location: str = "home") -> EnrichmentData:
    return EnrichmentData(
        location=location,
        alerts=[
            AlertData(type="uv", severity="orange", confidence=1.0),
            AlertData(type="frost", severity="none", confidence=0.0),
            AlertData(type="heat", severity="yellow", confidence=0.33),
            AlertData(type="storm", severity="none", confidence=0.0),
            AlertData(type="heavy_rain", severity="none", confidence=0.0),
            AlertData(type="fog", severity="none", confidence=0.0),
            AlertData(type="snow", severity="none", confidence=0.0),
            AlertData(type="pressure_drop", severity="none", confidence=0.0),
            AlertData(type="thunderstorm", severity="none", confidence=0.0),
        ],
        indices=IndexData(
            laundry=47,
            outdoor=56,
            running=48,
            cycling=50,
            bbq=51,
            irrigation=22,
            solar=38,
            ventilation=22,
            hdd=5.2,
            cdd=1.3,
            frost_hours=4,
            frost_confidence=0.85,
            vpd_kpa=0.59,
            vpd_category="optimal",
        ),
        trends=TrendData(
            parameter_trends=[
                ParameterTrendData(parameter="temperature_2m", direction="stable", delta=0.3),
            ],
            stability_label="stable",
            stability_ratio=0.83,
            precip_starts_in_hours=2,
            reliable_hours=3,
        ),
        energy=EnergyData(
            heating_demand=21,
            cop_estimate=10.95,
            shading=12,
            battery_strategy="discharge",
            night_cooling=40,
            cop_optimal=[CopOptimalHourData(hours_from_now=20, cop=14.91)],
        ),
        derived=DerivedData(
            by_horizon=[
                HorizonDerivedData(horizon="h3", beaufort=2, dewpoint_comfort="sticky"),
            ],
            diurnal_amplitude=7.3,
            sunshine_pct=66.4,
            inversion=False,
        ),
        history=HistoryData(
            models=[ModelMetricsData(model="icon_d2", weight=0.5)],
            weighted_temperature=24.48,
        ),
        consensus=_default_consensus(),
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_client():
    """Patch NjordClient across all import sites with canned responses."""
    mock = AsyncMock()
    mock.connect = AsyncMock()
    mock.close = AsyncMock()
    mock.get_config = AsyncMock(return_value=_default_config())
    mock.get_locations = AsyncMock(return_value=["home"])
    mock.get_models = AsyncMock(return_value=["icon_d2", "ecmwf_ifs025"])
    mock.get_forecast = AsyncMock(side_effect=lambda loc, model: _default_forecast(loc, model))
    mock.get_enrichments = AsyncMock(side_effect=lambda loc: _default_enrichment(loc))
    mock.get_status = AsyncMock()

    async def _empty_async_gen(**kwargs):
        return
        yield

    mock.stream_forecasts = MagicMock(side_effect=lambda **kwargs: _empty_async_gen())
    mock.stream_enrichments = MagicMock(side_effect=lambda **kwargs: _empty_async_gen())
    mock.stream_config = MagicMock(side_effect=lambda **kwargs: _empty_async_gen())

    with (
        patch("custom_components.njord.NjordClient", return_value=mock),
        patch("custom_components.njord.config_flow.NjordClient", return_value=mock),
    ):
        yield mock


@pytest.fixture
def mock_config_entry(hass):
    """Create and add a mock config entry for njord."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "localhost", "port": 8081},
        title="njord (localhost)",
        unique_id="localhost:8081",
    )
    entry.add_to_hass(hass)
    return entry


async def init_integration(hass, entry):
    """Set up the njord integration with a config entry."""
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
