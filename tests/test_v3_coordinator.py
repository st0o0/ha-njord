"""Tests for the v3 coordinator."""

from __future__ import annotations

from unittest.mock import MagicMock

from google.protobuf.timestamp_pb2 import Timestamp

from custom_components.njord.models import EntityState
from custom_components.njord.proto.njord import njord_pb2 as v3_pb2
from custom_components.njord.v3_coordinator import (
    NjordV3Coordinator,
    _extract_value,
    _parse_manifest,
)

EPOCH = 1720000000


def _ts(epoch: int = EPOCH) -> Timestamp:
    ts = Timestamp()
    ts.FromSeconds(epoch)
    return ts


# --- _parse_manifest ---


def test_parse_manifest_converts_entities():
    response = v3_pb2.ManifestResponse(
        entities=[
            v3_pb2.EntityDefinition(
                entity_id="vienna_frost",
                location="Vienna",
                feature="Frost",
                platform=v3_pb2.ENTITY_PLATFORM_BINARY_SENSOR,
                device_class="safety",
                unit="",
                icon="mdi:snowflake-alert",
                category="Forecast",
                output_kind=v3_pb2.OUTPUT_KIND_ALERT,
            ),
            v3_pb2.EntityDefinition(
                entity_id="vienna_pm25_observation",
                location="Vienna",
                feature="Pm25Observation",
                platform=v3_pb2.ENTITY_PLATFORM_SENSOR,
                device_class="pm25",
                unit="µg/m³",
                category="AirQuality",
                output_kind=v3_pb2.OUTPUT_KIND_OBSERVATION,
            ),
        ]
    )

    entities = _parse_manifest(response)

    assert len(entities) == 2
    assert entities[0].entity_id == "vienna_frost"
    assert entities[0].output_kind == "alert"
    assert entities[0].platform == "binary_sensor"
    assert entities[1].entity_id == "vienna_pm25_observation"
    assert entities[1].output_kind == "observation"
    assert entities[1].unit == "µg/m³"


def test_parse_empty_manifest():
    assert _parse_manifest(v3_pb2.ManifestResponse()) == []


# --- _extract_value ---


def test_extract_observation_value():
    update = v3_pb2.EntityStateUpdate(
        entity_id="vienna_pm25",
        updated_at=_ts(),
        observation=v3_pb2.ObservationValue(value=42.5),
    )
    value = _extract_value(update)
    assert value is not None
    assert value.value == 42.5


def test_extract_alert_value():
    update = v3_pb2.EntityStateUpdate(
        entity_id="vienna_frost",
        updated_at=_ts(),
        alert=v3_pb2.AlertValue(severity=v3_pb2.ALERT_SEVERITY_ORANGE, confidence=0.85),
    )
    value = _extract_value(update)
    assert value is not None
    assert value.severity == v3_pb2.ALERT_SEVERITY_ORANGE


def test_extract_none_when_no_value_set():
    update = v3_pb2.EntityStateUpdate(entity_id="x", updated_at=_ts())
    assert _extract_value(update) is None


# --- Coordinator event processing ---


class TestProcessEvent:
    def _coordinator(self) -> NjordV3Coordinator:
        coord = NjordV3Coordinator.__new__(NjordV3Coordinator)
        coord.v3_entity_states = {}
        return coord

    def test_snapshot_populates_all_entities(self):
        coord = self._coordinator()
        event = v3_pb2.EntityEvent(
            snapshot=v3_pb2.EntitySnapshot(
                states=[
                    v3_pb2.EntityStateUpdate(
                        entity_id="vienna_frost",
                        updated_at=_ts(),
                        alert=v3_pb2.AlertValue(severity=v3_pb2.ALERT_SEVERITY_YELLOW),
                    ),
                    v3_pb2.EntityStateUpdate(
                        entity_id="vienna_pm25",
                        updated_at=_ts(),
                        observation=v3_pb2.ObservationValue(value=12.5),
                    ),
                ]
            )
        )
        coord._process_event(event)

        assert len(coord.v3_entity_states) == 2
        assert coord.v3_entity_states["vienna_frost"].value.severity == v3_pb2.ALERT_SEVERITY_YELLOW
        assert coord.v3_entity_states["vienna_pm25"].value.value == 12.5

    def test_state_update_adds_entity(self):
        coord = self._coordinator()
        event = v3_pb2.EntityEvent(
            state_update=v3_pb2.EntityStateUpdate(
                entity_id="vienna_outdoor",
                updated_at=_ts(),
                score=v3_pb2.ScoreValue(score=85),
            )
        )
        coord._process_event(event)

        assert "vienna_outdoor" in coord.v3_entity_states
        assert coord.v3_entity_states["vienna_outdoor"].value.score == 85
        assert coord.v3_entity_states["vienna_outdoor"].available is True

    def test_state_update_replaces_previous(self):
        coord = self._coordinator()
        coord.v3_entity_states["vienna_pm25"] = EntityState(entity_id="vienna_pm25", value=MagicMock(), available=True)

        event = v3_pb2.EntityEvent(
            state_update=v3_pb2.EntityStateUpdate(
                entity_id="vienna_pm25",
                updated_at=_ts(),
                observation=v3_pb2.ObservationValue(value=99.0),
            )
        )
        coord._process_event(event)

        assert coord.v3_entity_states["vienna_pm25"].value.value == 99.0

    def test_unavailable_marks_entity(self):
        coord = self._coordinator()
        coord.v3_entity_states["vienna_frost"] = EntityState(
            entity_id="vienna_frost", value=MagicMock(), available=True
        )

        event = v3_pb2.EntityEvent(unavailable=v3_pb2.EntityUnavailable(entity_id="vienna_frost", since=_ts()))
        coord._process_event(event)

        assert coord.v3_entity_states["vienna_frost"].available is False

    def test_unavailable_for_unknown_entity_creates_entry(self):
        coord = self._coordinator()
        event = v3_pb2.EntityEvent(unavailable=v3_pb2.EntityUnavailable(entity_id="vienna_frost", since=_ts()))
        coord._process_event(event)

        assert coord.v3_entity_states["vienna_frost"].available is False
        assert coord.v3_entity_states["vienna_frost"].value is None

    def test_available_marks_entity(self):
        coord = self._coordinator()
        coord.v3_entity_states["vienna_frost"] = EntityState(
            entity_id="vienna_frost", value=MagicMock(), available=False
        )

        event = v3_pb2.EntityEvent(available=v3_pb2.EntityAvailable(entity_id="vienna_frost", recovered_at=_ts()))
        coord._process_event(event)

        assert coord.v3_entity_states["vienna_frost"].available is True
