"""Shared test fixtures for ha-njord."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.njord.const import DOMAIN

PAST = datetime(2000, 1, 1, 12, 0, tzinfo=UTC)
FUTURE = datetime(2099, 1, 1, 12, 0, tzinfo=UTC)


def _make_manifest_response():
    """Build a mock ManifestResponse with sensor entities."""
    mock = MagicMock()
    entity1 = MagicMock()
    entity1.entity_id = "home_frost"
    entity1.location = "home"
    entity1.feature = "Frost"
    entity1.platform = 2  # SENSOR
    entity1.device_class = "temperature"
    entity1.unit = "°C"
    entity1.icon = "mdi:snowflake-alert"
    entity1.category = "alerts"
    entity1.output_kind = 1  # ALERT
    mock.entities = [entity1]
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
    model.phase = 2  # STEADY
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
    """Patch NjordClient with v3 API mocks."""
    mock = AsyncMock()
    mock.connect = AsyncMock()
    mock.close = AsyncMock()
    mock.get_manifest = AsyncMock(return_value=_make_manifest_response())
    mock.get_status = AsyncMock(return_value=_make_status_response())
    mock.trigger_poll = AsyncMock(return_value=_make_trigger_response())

    async def _empty_subscribe(**kwargs):
        return
        yield

    mock.subscribe = MagicMock(side_effect=lambda **kwargs: _empty_subscribe())

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
    return _make_entry(hass)


async def init_integration(hass, entry):
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def entity_id_for(hass, platform: str, unique_id: str) -> str | None:
    from homeassistant.helpers import entity_registry as er

    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, unique_id)
