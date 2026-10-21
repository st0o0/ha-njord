"""Tests for the coordinator's stream tasks and stream health."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from custom_components.njord.const import DOMAIN, Domain, Feature, StreamName
from custom_components.njord.coordinator import NjordCoordinatorData, NjordDataCoordinator
from custom_components.njord.models import AlertData, FeatureData, NjordLocation, WeatherDomainData
from tests.conftest import weather_sample


def _coordinator(hass: HomeAssistant, client) -> NjordDataCoordinator:
    coordinator = NjordDataCoordinator(hass, client)
    coordinator.data = NjordCoordinatorData()
    return coordinator


def _stream_of(*items):
    async def gen(**kwargs):
        for item in items:
            yield item

    return MagicMock(side_effect=lambda **kwargs: gen(**kwargs))


async def test_domain_stream_stores_update_and_creates_entities_once(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)
    created: list[tuple[str, Domain]] = []
    coordinator.register_entity_factory("weather", MagicMock(), lambda loc, dom: created.append((loc, dom)) or [])
    first = WeatherDomainData("home", None, [weather_sample()])
    second = WeatherDomainData("home", None, [weather_sample(temperature=1.0)])
    mock_client.stream_domain_data = _stream_of(first, second)

    await coordinator._run_domain_stream()

    assert coordinator.data.domains[("home", Domain.WEATHER)] is second
    assert created == [("home", Domain.WEATHER)]


async def test_domain_stream_requests_tracked_domains(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)
    mock_client.stream_domain_data = _stream_of()

    await coordinator._run_domain_stream()

    kwargs = mock_client.stream_domain_data.call_args.kwargs
    assert kwargs["location"] is None
    assert set(kwargs["domains"]) == {Domain.WEATHER, Domain.AIR_QUALITY, Domain.FLOOD, Domain.MARINE}


async def test_enrichment_stream_stores_feature_by_location_and_feature(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)
    old = FeatureData("home", Feature.UV, alert=AlertData(type="uv", severity="red"))
    coordinator.data.features[("home", Feature.UV)] = old
    event = FeatureData("home", Feature.UV, alert=AlertData(type="uv", severity="orange"))
    other = FeatureData("home", Feature.STORM, alert=AlertData(type="storm", severity="yellow"))
    mock_client.stream_enrichments = _stream_of(event, other)

    await coordinator._run_enrichment_stream()

    assert coordinator.data.features[("home", Feature.UV)] is event
    assert coordinator.data.features[("home", Feature.STORM)] is other


async def test_factory_error_does_not_stop_other_factories(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)
    add_entities = MagicMock()

    def broken(location, domain):
        raise RuntimeError("boom")

    coordinator.register_entity_factory("sensor", MagicMock(), broken)
    coordinator.register_entity_factory("weather", add_entities, lambda loc, dom: [MagicMock()])

    coordinator._create_entities_for("home", Domain.WEATHER)

    add_entities.assert_called_once()


async def test_stream_failure_marks_stream_disconnected(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)
    coordinator.stream_states[StreamName.DOMAIN] = True

    async def failing(**kwargs):
        raise RuntimeError("stream broke")
        yield

    mock_client.stream_domain_data = MagicMock(side_effect=lambda **kwargs: failing())

    await coordinator._run_domain_stream()

    assert coordinator.stream_states[StreamName.DOMAIN] is False


async def test_connect_and_disconnect_callbacks_update_state(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)

    coordinator._on_stream_connect(StreamName.ENRICHMENT)
    assert coordinator.stream_states[StreamName.ENRICHMENT] is True
    assert coordinator.stream_states[StreamName.DOMAIN] is False

    coordinator._on_stream_disconnect(StreamName.ENRICHMENT)
    assert coordinator.stream_states[StreamName.ENRICHMENT] is False


async def test_repair_issue_after_grace_period_and_cleared_on_reconnect(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)
    issue_id = "stream_domain_disconnected"
    registry = ir.async_get(hass)

    coordinator._on_stream_disconnect(StreamName.DOMAIN)
    coordinator._on_stream_disconnect(StreamName.DOMAIN)
    assert registry.async_get_issue(DOMAIN, issue_id) is None

    coordinator._stream_disconnect_times[StreamName.DOMAIN] -= 61
    coordinator._on_stream_disconnect(StreamName.DOMAIN)
    assert registry.async_get_issue(DOMAIN, issue_id) is not None

    coordinator._on_stream_connect(StreamName.DOMAIN)
    assert registry.async_get_issue(DOMAIN, issue_id) is None


async def test_stop_streams_cancels_tasks(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)

    async def never_ending(**kwargs):
        while True:
            await asyncio.sleep(10)
            yield

    mock_client.stream_domain_data = MagicMock(side_effect=lambda **kwargs: never_ending())
    mock_client.stream_enrichments = MagicMock(side_effect=lambda **kwargs: never_ending())

    coordinator.start_streams()
    assert len(coordinator._stream_tasks) == 2

    await coordinator.stop_streams()
    assert coordinator._stream_tasks == []


async def test_secondary_model_update_goes_to_model_domains(hass: HomeAssistant, mock_client) -> None:
    coordinator = _coordinator(hass, mock_client)
    coordinator.data.locations = [NjordLocation(name="home", latitude=1.0, longitude=2.0, models=["icon_d2", "other"])]
    created: list[tuple[str, str]] = []
    coordinator.register_model_factory("weather", MagicMock(), lambda loc, model: created.append((loc, model)) or [])
    primary = WeatherDomainData("home", None, [weather_sample()], model="icon_d2")
    unlabeled = WeatherDomainData("home", None, [weather_sample(temperature=2.0)])
    secondary = WeatherDomainData("home", None, [weather_sample(temperature=3.0)], model="other")
    again = WeatherDomainData("home", None, [weather_sample(temperature=4.0)], model="other")
    mock_client.stream_domain_data = _stream_of(primary, secondary, unlabeled, again)

    await coordinator._run_domain_stream()

    assert coordinator.data.domains[("home", Domain.WEATHER)] is unlabeled
    assert coordinator.data.model_domains == {("home", "other"): again}
    assert created == [("home", "other")]
