"""Tests for lifestyle advisories: wire conversion, coordinator handling and entities."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from google.protobuf.timestamp_pb2 import Timestamp
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.njord.const import (
    CONF_ENABLED_ENRICHMENTS,
    LIFESTYLE_ENRICHMENT,
    Enrichment,
    LifestyleType,
    enabled_lifestyle_types,
)
from custom_components.njord.coordinator import NjordCoordinatorData, NjordDataCoordinator
from custom_components.njord.grpc_client import NjordClient, _to_enrichment_event
from custom_components.njord.models import EnrichmentData, LifestyleData
from custom_components.njord.proto.njord.v2 import weather_pb2
from tests.conftest import _make_entry, default_enrichment, entity_id_for, init_integration

EPOCH = 1720000000


def _time(delta: timedelta) -> str:
    return (dt_util.utcnow() + delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lifestyle(kind: str, **data: str) -> LifestyleData:
    return LifestyleData(type=kind, location="home", data=data)


def _event(kind: str, **data: str) -> weather_pb2.EnrichmentEvent:
    return weather_pb2.EnrichmentEvent(
        location="home",
        type_name="lifestyle",
        updated_at=Timestamp(seconds=EPOCH),
        lifestyle=weather_pb2.LifestyleUpdate(type=kind, data=data),
    )


# --- Wire conversion ---


def test_lifestyle_event_converted():
    item = _to_enrichment_event(_event("laundry_score", score="82", best_hours="3"))

    assert isinstance(item, LifestyleData)
    assert item.type == "laundry_score"
    assert item.location == "home"
    assert item.data == {"score": "82", "best_hours": "3"}
    assert item.updated_at is not None
    assert int(item.updated_at.timestamp()) == EPOCH


async def test_get_enrichments_carries_lifestyle():
    client = NjordClient("localhost", 1)
    client._channel = MagicMock()
    client._weather_stub = MagicMock()
    client._weather_stub.GetEnrichments = AsyncMock(
        return_value=weather_pb2.GetEnrichmentsResponse(
            location="home",
            lifestyle=[
                weather_pb2.LifestyleUpdate(type="commute_safety", data={"level": "Caution", "risks": "Strong wind"}),
                weather_pb2.LifestyleUpdate(type="exercise", data={"level": "Safe"}),
            ],
        )
    )

    enrichment = await client.get_enrichments("home")

    assert [(i.type, i.location, i.data["level"]) for i in enrichment.lifestyle] == [
        ("commute_safety", "home", "Caution"),
        ("exercise", "home", "Safe"),
    ]
    assert enrichment.alerts == []


# --- Enrichment toggles ---


def test_every_lifestyle_type_has_a_toggle():
    assert set(LIFESTYLE_ENRICHMENT) == set(LifestyleType)
    assert len(set(LIFESTYLE_ENRICHMENT.values())) == len(LifestyleType)


def test_enabled_lifestyle_types_follow_toggles():
    enabled = enabled_lifestyle_types({Enrichment.VENTILATION_WINDOW, Enrichment.WEATHER_ALERTS})

    assert enabled == {LifestyleType.VENTILATION}


# --- Coordinator ---


async def test_stream_keeps_alerts_and_lifestyle_apart(hass: HomeAssistant, mock_client) -> None:
    coordinator = NjordDataCoordinator(hass, mock_client)
    coordinator.data = NjordCoordinatorData()
    created: list[tuple[str, str]] = []
    coordinator.register_lifestyle_factory("sensor", MagicMock(), lambda loc, kind: created.append((loc, kind)) or [])
    alerts = EnrichmentData(location="home", alerts=[])
    first = _lifestyle("exercise", level="Safe")
    second = _lifestyle("exercise", level="Avoid")

    async def gen(**kwargs):
        for item in (alerts, first, second):
            yield item

    mock_client.stream_enrichments = MagicMock(side_effect=lambda **kwargs: gen(**kwargs))

    await coordinator._run_enrichment_stream()

    assert coordinator.data.enrichments["home"] is alerts
    assert coordinator.data.lifestyle[("home", "exercise")] is second
    assert created == [("home", "exercise")]


async def test_first_refresh_collects_lifestyle(hass: HomeAssistant, mock_client) -> None:
    mock_client.get_enrichments = AsyncMock(
        return_value=replace(default_enrichment(), lifestyle=[_lifestyle("laundry_score", score="70")])
    )
    coordinator = NjordDataCoordinator(hass, mock_client)

    data = await coordinator._async_update_data()

    assert data.lifestyle[("home", "laundry_score")].data == {"score": "70"}


# --- Entities ---


def _lifestyle_entry(hass: HomeAssistant, *toggles: Enrichment):
    return _make_entry(hass, {CONF_ENABLED_ENRICHMENTS: [t.value for t in toggles]})


def _all_lifestyle(**overrides: LifestyleData) -> list[LifestyleData]:
    items = {
        "laundry_score": _lifestyle("laundry_score", score="82", best_start="2099-01-01T10:00:00Z", best_hours="3"),
        "commute_safety": _lifestyle("commute_safety", level="Caution", risks="Strong wind"),
        "exercise": _lifestyle("exercise", level="Avoid", reasons="High ozone", best_window="2099-01-01T08:00:00Z"),
        "ventilation": _lifestyle(
            "ventilation", best_start=_time(timedelta(hours=-1)), best_end=_time(timedelta(hours=1)), reason="dry"
        ),
        "gardening": _lifestyle("gardening", planting_safe="true", watering_needed="false", frost_risk="false"),
        "solar_yield": _lifestyle("solar_yield", kwh_per_kwp="4.25", peak_hour="13"),
        "night_ventilation": _lifestyle("night_ventilation", open_at="2099-01-01T22:00:00Z", low_temp="12"),
        "pollen_trend": _lifestyle("pollen_trend", trend_birch="rising", peak_type="birch"),
        "front_approaching": _lifestyle("front_approaching", estimated_in_hours="6.5", pressure_drop="8"),
    }
    items.update(overrides)
    return list(items.values())


async def _setup(hass: HomeAssistant, mock_client, entry, items: list[LifestyleData]):
    mock_client.get_enrichments = AsyncMock(return_value=replace(default_enrichment(), lifestyle=items))
    await init_integration(hass, entry)
    return entry


def _state(hass: HomeAssistant, entry, platform: str, key: str):
    entity_id = entity_id_for(hass, platform, f"{entry.entry_id}_home_{key}")
    return hass.states.get(entity_id) if entity_id else None


async def test_entities_created_for_enabled_lifestyle_types_only(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.LAUNDRY_SCORE, Enrichment.VENTILATION_WINDOW)
    await _setup(hass, mock_client, entry, _all_lifestyle())

    assert _state(hass, entry, "sensor", "laundry_score") is not None
    assert _state(hass, entry, "binary_sensor", "ventilation_window") is not None
    assert _state(hass, entry, "sensor", "commute_safety") is None
    assert _state(hass, entry, "sensor", "exercise") is None
    assert _state(hass, entry, "binary_sensor", "planting_safe") is None


async def test_no_entity_without_data(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, *LIFESTYLE_ENRICHMENT.values())
    await _setup(hass, mock_client, entry, [_lifestyle("laundry_score", score="10")])

    assert _state(hass, entry, "sensor", "laundry_score") is not None
    assert _state(hass, entry, "sensor", "exercise") is None


async def test_score_sensor_state_and_attributes(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.LAUNDRY_SCORE)
    await _setup(hass, mock_client, entry, _all_lifestyle())

    state = _state(hass, entry, "sensor", "laundry_score")
    assert state is not None
    assert state.state == "82.0"
    assert state.attributes["best_start"] == "2099-01-01T10:00:00Z"
    assert state.attributes["best_hours"] == "3"
    assert state.attributes["friendly_name"] == "Home Laundry Score"


async def test_level_sensors_expose_safe_caution_dangerous_avoid(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.COMMUTE_SAFETY, Enrichment.EXERCISE_ADVISORY)
    await _setup(hass, mock_client, entry, _all_lifestyle())

    commute = _state(hass, entry, "sensor", "commute_safety")
    exercise = _state(hass, entry, "sensor", "exercise")
    assert commute is not None
    assert exercise is not None
    assert commute.state == "Caution"
    assert commute.attributes["risks"] == "Strong wind"
    assert exercise.state == "Avoid"
    assert exercise.attributes["reasons"] == "High ozone"


async def test_unknown_level_reads_unknown(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.COMMUTE_SAFETY)
    await _setup(hass, mock_client, entry, [_lifestyle("commute_safety", level="Weird")])

    state = _state(hass, entry, "sensor", "commute_safety")
    assert state is not None
    assert state.state == "unknown"


async def test_ventilation_window_open_and_closed(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.VENTILATION_WINDOW)
    await _setup(hass, mock_client, entry, _all_lifestyle())
    opened = _state(hass, entry, "binary_sensor", "ventilation_window")
    assert opened is not None
    assert opened.state == "on"
    assert opened.attributes["reason"] == "dry"


async def test_ventilation_window_closed_outside_window(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.VENTILATION_WINDOW)
    later = _lifestyle("ventilation", best_start=_time(timedelta(hours=2)), best_end=_time(timedelta(hours=4)))
    await _setup(hass, mock_client, entry, [later])

    state = _state(hass, entry, "binary_sensor", "ventilation_window")
    assert state is not None
    assert state.state == "off"


async def test_gardening_planting_safe_binary_sensor(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.GARDENING_ADVISORY)
    await _setup(hass, mock_client, entry, _all_lifestyle())

    state = _state(hass, entry, "binary_sensor", "planting_safe")
    assert state is not None
    assert state.state == "on"
    assert state.attributes["frost_risk"] == "false"


async def test_numeric_and_text_sensors(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.SOLAR_YIELD, Enrichment.POLLEN_TREND, Enrichment.APPROACHING_FRONT)
    await _setup(hass, mock_client, entry, _all_lifestyle())

    solar = _state(hass, entry, "sensor", "solar_yield")
    pollen = _state(hass, entry, "sensor", "pollen_trend")
    front = _state(hass, entry, "sensor", "front_approaching")
    assert solar is not None
    assert pollen is not None
    assert front is not None
    assert solar.state == "4.25"
    assert pollen.state == "birch"
    assert front.state == "6.5"


async def test_streamed_lifestyle_creates_and_updates_entity(hass: HomeAssistant, mock_client) -> None:
    entry = _lifestyle_entry(hass, Enrichment.LAUNDRY_SCORE)
    gate = []

    async def gen(**kwargs):
        for item in (_lifestyle("laundry_score", score="40"), _lifestyle("laundry_score", score="90")):
            gate.append(item)
            yield item

    mock_client.stream_enrichments = MagicMock(side_effect=lambda **kwargs: gen(**kwargs))
    await _setup(hass, mock_client, entry, [])

    state = _state(hass, entry, "sensor", "laundry_score")
    assert state is not None
    assert state.state == "90.0"
