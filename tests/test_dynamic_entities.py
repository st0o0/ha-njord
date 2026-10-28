"""Tests for dynamic entity creation when a new (location, domain) appears on the domain stream."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.njord.const import Domain
from custom_components.njord.coordinator import NjordCoordinatorData, NjordDataCoordinator
from custom_components.njord.models import AirQualityDomainData, AirQualitySampleData, ForecastDomainData
from tests.conftest import PAST, entity_id_for, forecast_sample, init_integration


def _stream_of(*items):
    async def gen(**kwargs):
        for item in items:
            yield item

    return MagicMock(side_effect=lambda **kwargs: gen(**kwargs))


async def _run(hass: HomeAssistant, client, *updates, known=()) -> list:
    coordinator = NjordDataCoordinator(hass, client)
    coordinator.data = NjordCoordinatorData(domains={key: ForecastDomainData(key[0]) for key in known})
    calls: list[tuple[str, Domain]] = []
    coordinator.register_entity_factory("weather", MagicMock(), lambda loc, dom: calls.append((loc, dom)) or [])
    client.stream_domain_data = _stream_of(*updates)
    await coordinator._run_domain_stream()
    return calls


async def test_new_location_domain_triggers_factory(hass: HomeAssistant, mock_client) -> None:
    update = ForecastDomainData("bern", None, [forecast_sample()])

    calls = await _run(hass, mock_client, update, known=[("home", Domain.FORECAST)])

    assert calls == [("bern", Domain.FORECAST)]


async def test_known_pair_does_not_retrigger(hass: HomeAssistant, mock_client) -> None:
    update = ForecastDomainData("home", None, [forecast_sample()])

    calls = await _run(hass, mock_client, update, known=[("home", Domain.FORECAST)])

    assert calls == []


async def test_new_domain_on_known_location_triggers_factory(hass: HomeAssistant, mock_client) -> None:
    update = AirQualityDomainData("home", None, [])

    calls = await _run(hass, mock_client, update, known=[("home", Domain.FORECAST)])

    assert calls == [("home", Domain.AIR_QUALITY)]


async def test_multiple_factories_all_called(hass: HomeAssistant, mock_client) -> None:
    coordinator = NjordDataCoordinator(hass, mock_client)
    coordinator.data = NjordCoordinatorData()
    weather_add, sensor_add = MagicMock(), MagicMock()
    coordinator.register_entity_factory("weather", weather_add, lambda loc, dom: [MagicMock()])
    coordinator.register_entity_factory("sensor", sensor_add, lambda loc, dom: [MagicMock()])

    coordinator._create_entities_for("bern", Domain.FORECAST)

    weather_add.assert_called_once()
    sensor_add.assert_called_once()


async def test_streamed_location_gets_real_entities(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    weather = ForecastDomainData("bern", None, [forecast_sample()])
    air = AirQualityDomainData("bern", None, [AirQualitySampleData(valid_at=PAST, pm25=7.0, pm10=9.0, ozone=50.0)])
    mock_client.stream_domain_data = _stream_of(weather, air)

    await init_integration(hass, mock_config_entry)
    await hass.async_block_till_done()

    entry_id = mock_config_entry.entry_id
    assert entity_id_for(hass, "weather", f"{entry_id}_bern_weather") is not None
    assert entity_id_for(hass, "event", f"{entry_id}_bern_weather_alert") is not None
    assert entity_id_for(hass, "binary_sensor", f"{entry_id}_bern_frost_alert") is not None
    pm25 = entity_id_for(hass, "sensor", f"{entry_id}_bern_pm25")
    assert pm25 is not None
    state = hass.states.get(pm25)
    assert state is not None
    assert float(state.state) == 7.0
