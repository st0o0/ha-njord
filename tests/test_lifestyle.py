"""Tests for typed feature entities: wire conversion, coordinator handling, gating and entities."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.protobuf.timestamp_pb2 import Timestamp
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.njord.const import FEATURE_KEYS, AlertSeverity, AlertType, Feature, feature_enabled
from custom_components.njord.coordinator import NjordCoordinatorData, NjordDataCoordinator
from custom_components.njord.grpc_client import NjordClient, _to_feature
from custom_components.njord.models import FeatureData, ScoreData
from custom_components.njord.proto.njord.v2 import common_pb2, weather_pb2
from tests.conftest import PAST, entity_id_for, init_integration

EPOCH = 1720000000


def _feature(feature: Feature, **values) -> FeatureData:
    return FeatureData(location="home", feature=feature, updated_at=PAST, values=values)


def _scored(feature: Feature, score: int, **values) -> FeatureData:
    return FeatureData(location="home", feature=feature, updated_at=PAST, score=ScoreData(score=score), values=values)


# --- Wire conversion ---


def test_alert_event_converted_with_extras():
    event = weather_pb2.EnrichmentEvent(
        location="home",
        updated_at=Timestamp(seconds=EPOCH),
        uv=weather_pb2.UvAlert(
            alert=weather_pb2.AlertData(
                severity=common_pb2.ALERT_SEVERITY_ORANGE, confidence=0.8, trigger_value=8.5, threshold=6.0
            ),
            uv_level=weather_pb2.UV_LEVEL_HIGH,
            uv_index=8.5,
        ),
    )

    item = _to_feature(event)

    assert item is not None
    assert item.feature is Feature.UV
    assert item.location == "home"
    assert item.updated_at is not None
    assert int(item.updated_at.timestamp()) == EPOCH
    assert item.alert is not None
    assert item.alert.type is AlertType.UV
    assert item.alert.severity is AlertSeverity.ORANGE
    assert item.alert.trigger_value == 8.5
    assert item.alert.peak_value is None
    assert item.values["uv_level"] == "high"
    assert item.values["uv_index"] == 8.5
    assert "alert" not in item.values


def test_score_event_converted():
    event = weather_pb2.EnrichmentEvent(
        location="home",
        laundry=weather_pb2.Laundry(score=weather_pb2.ScoreData(score=82, best_hours=3)),
    )

    item = _to_feature(event)

    assert item is not None
    assert item.feature is Feature.LAUNDRY
    assert item.alert is None
    assert item.score == ScoreData(score=82, best_start=None, best_hours=3)


def test_condition_event_converted_with_enum_text():
    event = weather_pb2.EnrichmentEvent(
        location="home",
        commute_safety=weather_pb2.CommuteSafety(level=weather_pb2.COMMUTE_LEVEL_CAUTION),
    )

    item = _to_feature(event)

    assert item is not None
    assert item.feature is Feature.COMMUTE_SAFETY
    assert item.values["level"] == "caution"


def test_empty_event_is_ignored():
    assert _to_feature(weather_pb2.EnrichmentEvent(location="home")) is None


async def test_get_enrichments_returns_feature_list():
    client = NjordClient("localhost", 1)
    client._channel = MagicMock()
    client._weather_stub = MagicMock()
    client._weather_stub.GetEnrichments = AsyncMock(
        return_value=weather_pb2.GetEnrichmentsResponse(
            location="home",
            events=[
                weather_pb2.EnrichmentEvent(
                    location="home",
                    commute_safety=weather_pb2.CommuteSafety(level=weather_pb2.COMMUTE_LEVEL_SAFE),
                ),
                weather_pb2.EnrichmentEvent(
                    location="home",
                    exercise_advisory=weather_pb2.ExerciseAdvisory(level=weather_pb2.EXERCISE_LEVEL_AVOID),
                ),
                weather_pb2.EnrichmentEvent(location="home"),
            ],
        )
    )

    items = await client.get_enrichments("home")

    assert [(i.feature, i.values["level"]) for i in items] == [
        (Feature.COMMUTE_SAFETY, "safe"),
        (Feature.EXERCISE_ADVISORY, "avoid"),
    ]


# --- Gating ---


def test_empty_active_list_enables_every_feature():
    assert feature_enabled(Feature.UV, None)
    assert feature_enabled(Feature.UV, set())


def test_active_keys_match_case_insensitively():
    assert feature_enabled(Feature.COMMUTE_SAFETY, {"lifestyle:commute"})
    assert not feature_enabled(Feature.EXERCISE_ADVISORY, {"Lifestyle:Commute"})


def test_renamed_features_use_njord_config_names():
    assert FEATURE_KEYS[Feature.SWIMMING_CONDITIONS] == "Marine:Swimming"
    assert FEATURE_KEYS[Feature.APPROACHING_FRONT] == "Insight:FrontApproaching"
    assert FEATURE_KEYS[Feature.FLOOD_RAIN] == "Flood:FloodRain"
    assert len(set(FEATURE_KEYS.values())) == len(FEATURE_KEYS)


# --- Coordinator ---


async def test_stream_keeps_last_item_per_feature(hass: HomeAssistant, mock_client) -> None:
    coordinator = NjordDataCoordinator(hass, mock_client)
    coordinator.data = NjordCoordinatorData()
    created: list[tuple[str, Feature]] = []
    coordinator.register_feature_factory("sensor", MagicMock(), lambda loc, f: created.append((loc, f)) or [])
    first = _feature(Feature.EXERCISE_ADVISORY, level="safe")
    second = _feature(Feature.EXERCISE_ADVISORY, level="avoid")

    async def gen(**kwargs):
        for item in (first, second):
            yield item

    mock_client.stream_enrichments = MagicMock(side_effect=lambda **kwargs: gen(**kwargs))

    await coordinator._run_enrichment_stream()

    assert coordinator.data.features[("home", Feature.EXERCISE_ADVISORY)] is second
    assert created == [("home", Feature.EXERCISE_ADVISORY)]


async def test_stream_skips_entity_creation_for_inactive_feature(hass: HomeAssistant, mock_client) -> None:
    coordinator = NjordDataCoordinator(hass, mock_client)
    coordinator.data = NjordCoordinatorData(active_enrichments={"Lifestyle:Commute"})
    created: list[Feature] = []
    coordinator.register_feature_factory("sensor", MagicMock(), lambda loc, f: created.append(f) or [])

    coordinator._apply_feature(_feature(Feature.EXERCISE_ADVISORY, level="safe"))
    coordinator._apply_feature(_feature(Feature.COMMUTE_SAFETY, level="safe"))

    assert created == [Feature.COMMUTE_SAFETY]


async def test_first_refresh_collects_features(hass: HomeAssistant, mock_client) -> None:
    mock_client.get_enrichments = AsyncMock(return_value=[_scored(Feature.LAUNDRY, 70)])
    coordinator = NjordDataCoordinator(hass, mock_client)

    data = await coordinator._async_update_data()

    assert data.features[("home", Feature.LAUNDRY)].score == ScoreData(score=70)


# --- Entities ---


def _all_features() -> list[FeatureData]:
    return [
        _scored(Feature.LAUNDRY, 82, best_hours=3),
        _feature(Feature.COMMUTE_SAFETY, level="caution"),
        _feature(Feature.EXERCISE_ADVISORY, level="avoid"),
        _feature(
            Feature.VENTILATION_WINDOW,
            best_start=dt_util.utcnow() - timedelta(hours=1),
            best_end=dt_util.utcnow() + timedelta(hours=1),
        ),
        _feature(Feature.GARDENING, planting_safe=True, watering_needed=False, frost_risk=False),
        _feature(Feature.SOLAR_YIELD, kwh_per_kwp=4.25, peak_hour=13),
        _feature(Feature.POLLEN_TREND, peak_type="birch"),
        _feature(Feature.APPROACHING_FRONT, estimated_in_hours=6.5),
        _feature(Feature.SEASONAL_OUTLOOK, months=[{"temperature_anomaly": 1.5}]),
    ]


async def _setup(hass: HomeAssistant, mock_client, entry, items, active: list[str] | None = None):
    status = await mock_client.get_status()
    mock_client.get_status.return_value = replace(status, active_enrichments=active or [])
    mock_client.get_enrichments = AsyncMock(return_value=items)
    await init_integration(hass, entry)
    return entry


def _state(hass: HomeAssistant, entry, platform: str, key: str):
    entity_id = entity_id_for(hass, platform, f"{entry.entry_id}_home_{key}")
    return hass.states.get(entity_id) if entity_id else None


async def test_entities_created_for_active_features_only(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(
        hass,
        mock_client,
        mock_config_entry,
        _all_features(),
        active=["Lifestyle:Laundry", "Lifestyle:Ventilation"],
    )

    assert _state(hass, mock_config_entry, "sensor", "laundry_score") is not None
    assert _state(hass, mock_config_entry, "binary_sensor", "ventilation_window") is not None
    assert _state(hass, mock_config_entry, "sensor", "commute_safety") is None
    assert _state(hass, mock_config_entry, "sensor", "exercise") is None
    assert _state(hass, mock_config_entry, "binary_sensor", "planting_safe") is None


async def test_no_entity_without_data(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(hass, mock_client, mock_config_entry, [_scored(Feature.LAUNDRY, 10)])

    assert _state(hass, mock_config_entry, "sensor", "laundry_score") is not None
    assert _state(hass, mock_config_entry, "sensor", "exercise") is None


async def test_score_sensor_state(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(hass, mock_client, mock_config_entry, _all_features())

    state = _state(hass, mock_config_entry, "sensor", "laundry_score")
    assert state is not None
    assert state.state == "82"


async def test_level_sensors_state(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(hass, mock_client, mock_config_entry, _all_features())

    commute = _state(hass, mock_config_entry, "sensor", "commute_safety")
    exercise = _state(hass, mock_config_entry, "sensor", "exercise")
    assert commute is not None
    assert exercise is not None
    assert commute.state == "caution"
    assert exercise.state == "avoid"


async def test_ventilation_window_open(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(hass, mock_client, mock_config_entry, _all_features())

    state = _state(hass, mock_config_entry, "binary_sensor", "ventilation_window")
    assert state is not None
    assert state.state == "on"


async def test_ventilation_window_closed_outside_window(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    later = _feature(
        Feature.VENTILATION_WINDOW,
        best_start=dt_util.utcnow() + timedelta(hours=2),
        best_end=dt_util.utcnow() + timedelta(hours=4),
    )
    await _setup(hass, mock_client, mock_config_entry, [later])

    state = _state(hass, mock_config_entry, "binary_sensor", "ventilation_window")
    assert state is not None
    assert state.state == "off"


async def test_gardening_planting_safe(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(hass, mock_client, mock_config_entry, _all_features())

    state = _state(hass, mock_config_entry, "binary_sensor", "planting_safe")
    assert state is not None
    assert state.state == "on"


async def test_numeric_and_text_sensors(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(hass, mock_client, mock_config_entry, _all_features())

    solar = _state(hass, mock_config_entry, "sensor", "solar_yield")
    pollen = _state(hass, mock_config_entry, "sensor", "pollen_trend")
    front = _state(hass, mock_config_entry, "sensor", "front_approaching")
    assert solar is not None
    assert pollen is not None
    assert front is not None
    assert solar.state == "4.25"
    assert pollen.state == "birch"
    assert front.state == "6.5"


async def test_streamed_feature_creates_and_updates_entity(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    async def gen(**kwargs):
        for score in (40, 90):
            yield _scored(Feature.LAUNDRY, score)

    mock_client.stream_enrichments = MagicMock(side_effect=lambda **kwargs: gen(**kwargs))
    await _setup(hass, mock_client, mock_config_entry, [])

    state = _state(hass, mock_config_entry, "sensor", "laundry_score")
    assert state is not None
    assert state.state == "90"


def _comparison(*max_temps: float | None) -> FeatureData:
    models = [{"model": f"m{i}", "max_temperature": t} for i, t in enumerate(max_temps)]
    return _feature(Feature.MODEL_COMPARISON, days=[{"year": 2026, "month": 7, "day": 1, "models": models}])


async def test_model_comparison_sensor_shows_spread(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(hass, mock_client, mock_config_entry, [_comparison(21.4, 19.0)], active=["Weather:ModelComparison"])

    state = _state(hass, mock_config_entry, "sensor", "model_comparison")
    assert state is not None
    assert float(state.state) == pytest.approx(2.4)
    assert len(state.attributes["days"]) == 1


async def test_model_comparison_single_model_is_unknown(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await _setup(hass, mock_client, mock_config_entry, [_comparison(21.4, None)], active=["Weather:ModelComparison"])

    state = _state(hass, mock_config_entry, "sensor", "model_comparison")
    assert state is not None
    assert state.state == "unknown"


async def test_model_comparison_sensor_needs_active_enrichment(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    await _setup(hass, mock_client, mock_config_entry, [_comparison(21.4, 19.0)], active=["Weather:Uv"])

    assert _state(hass, mock_config_entry, "sensor", "model_comparison") is None
