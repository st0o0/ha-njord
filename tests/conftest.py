"""Shared test fixtures for ha-njord."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.njord.const import DOMAIN

PAST = datetime(2000, 1, 1, 12, 0, tzinfo=UTC)
FUTURE = datetime(2099, 1, 1, 12, 0, tzinfo=UTC)


def _make_manifest_response():
    """Build a mock ManifestResponse with entities across all platforms."""
    mock = MagicMock()

    frost_sensor = MagicMock()
    frost_sensor.entity_id = "home_frost"
    frost_sensor.location = "home"
    frost_sensor.feature = "Frost"
    frost_sensor.platform = 2  # SENSOR
    frost_sensor.device_class = "temperature"
    frost_sensor.unit = "°C"
    frost_sensor.icon = "mdi:snowflake-alert"
    frost_sensor.category = "alerts"
    frost_sensor.output_kind = 2  # SCORE

    frost_alert = MagicMock()
    frost_alert.entity_id = "home_frost_alert"
    frost_alert.location = "home"
    frost_alert.feature = "Frost"
    frost_alert.platform = 3  # BINARY_SENSOR
    frost_alert.device_class = ""
    frost_alert.unit = "°C"
    frost_alert.icon = "mdi:snowflake-alert"
    frost_alert.category = "alerts"
    frost_alert.output_kind = 1  # ALERT

    uv_alert = MagicMock()
    uv_alert.entity_id = "home_uv_alert"
    uv_alert.location = "home"
    uv_alert.feature = "Uv"
    uv_alert.platform = 3  # BINARY_SENSOR
    uv_alert.device_class = ""
    uv_alert.unit = "UV"
    uv_alert.icon = "mdi:weather-sunny-alert"
    uv_alert.category = "alerts"
    uv_alert.output_kind = 1  # ALERT

    weather = MagicMock()
    weather.entity_id = "home_weather"
    weather.location = "home"
    weather.feature = "Weather"
    weather.platform = 1  # WEATHER
    weather.device_class = ""
    weather.unit = ""
    weather.icon = ""
    weather.category = "forecast"
    weather.output_kind = 6  # WEATHER

    mock.entities = [frost_sensor, frost_alert, uv_alert, weather]
    return mock


def _make_status_response():
    """Build a mock StatusResponse."""
    mock = MagicMock()
    mock.version = "1.2.3"
    mock.uptime_seconds = 3600
    mock.budget_partial = False
    mock.models_partial = False
    mock.active_enrichments = ["Forecast:Uv", "Forecast:Frost"]

    budget = MagicMock()
    budget.monthly_limit = 20000
    budget.monthly_used = 5000
    budget.daily_limit = 700
    budget.daily_used = 100
    budget.usage_percent = 25.0
    mock.budget = budget

    process_start = MagicMock()
    process_start.seconds = int(PAST.timestamp())
    process_start.nanos = 0
    mock.process_start = process_start

    model = MagicMock()
    model.location = "home"
    model.phase = 1  # ACTIVE
    next_poll = MagicMock()
    next_poll.seconds = int(FUTURE.timestamp())
    next_poll.nanos = 0
    model.next_poll = next_poll
    model.HasField = lambda f: f in ("next_poll",)
    model.miss_count = 1
    model.cycle_seconds = 3600
    last_change = MagicMock()
    last_change.seconds = 0
    last_change.nanos = 0
    model.last_change = last_change
    mock.models = [model]

    return mock


def _make_trigger_response():
    mock = MagicMock()
    mock.triggered_count = 2
    return mock


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_client():
    """Patch NjordClient and disable stream_coordinator.start_stream for tests."""
    mock = AsyncMock()
    mock.connect = AsyncMock()
    mock.close = AsyncMock()
    mock.get_manifest = AsyncMock(return_value=_make_manifest_response())
    mock.get_status = AsyncMock(return_value=_make_status_response())
    mock.trigger_poll = AsyncMock(return_value=_make_trigger_response())

    async def _blocking_stream():
        await asyncio.get_event_loop().create_future()
        yield  # never reached

    mock.subscribe = AsyncMock(side_effect=lambda **kwargs: _blocking_stream())

    with (
        patch("custom_components.njord.NjordClient", return_value=mock),
        patch("custom_components.njord.config_flow.NjordClient", return_value=mock),
        patch("custom_components.njord.stream_coordinator.NjordStreamCoordinator.start_stream"),
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
    return _make_entry(hass)


async def init_integration(hass, entry):
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def entity_id_for(hass, platform: str, unique_id: str) -> str | None:
    from homeassistant.helpers import entity_registry as er

    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, unique_id)
