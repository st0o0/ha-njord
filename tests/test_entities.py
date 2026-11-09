"""Tests for generic entity classes."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.njord.entities import NjordAlertBinarySensor, NjordEntitySensor
from custom_components.njord.models import EntityState, ManifestEntity


def _manifest(
    entity_id: str = "vienna_frost",
    output_kind: str = "alert",
    **kwargs,
) -> ManifestEntity:
    defaults = {
        "location": "Vienna",
        "feature": "Frost",
        "platform": "sensor",
        "device_class": "",
        "unit": "",
        "icon": "",
        "category": "Forecast",
    }
    defaults.update(kwargs)
    return ManifestEntity(entity_id=entity_id, output_kind=output_kind, **defaults)


def _coordinator(states: dict[str, EntityState] | None = None):
    coord = MagicMock()
    coord.v3_entity_states = states or {}
    return coord


def _entry():
    entry = MagicMock()
    entry.entry_id = "test_entry"
    return entry


class TestNjordEntitySensor:
    def test_unique_id(self):
        sensor = NjordEntitySensor(_coordinator(), _entry(), _manifest("vienna_pm25_observation", "observation"), None)
        assert sensor._attr_unique_id == "test_entry_vienna_pm25_observation"

    def test_observation_value(self):
        value = MagicMock()
        value.value = 42.5
        state = EntityState(entity_id="vienna_pm25", value=value, available=True)
        sensor = NjordEntitySensor(
            _coordinator({"vienna_pm25": state}), _entry(), _manifest("vienna_pm25", "observation"), None
        )
        assert sensor.native_value == 42.5

    def test_score_value(self):
        value = MagicMock()
        value.score = 85
        state = EntityState(entity_id="vienna_outdoor", value=value, available=True)
        sensor = NjordEntitySensor(
            _coordinator({"vienna_outdoor": state}), _entry(), _manifest("vienna_outdoor", "score"), None
        )
        assert sensor.native_value == 85

    def test_condition_value(self):
        value = MagicMock()
        value.active = True
        state = EntityState(entity_id="vienna_commute", value=value, available=True)
        sensor = NjordEntitySensor(
            _coordinator({"vienna_commute": state}), _entry(), _manifest("vienna_commute", "condition"), None
        )
        assert sensor.native_value == "on"

    def test_unavailable_when_no_state(self):
        sensor = NjordEntitySensor(_coordinator({}), _entry(), _manifest("vienna_pm25", "observation"), None)
        assert sensor.available is False
        assert sensor.native_value is None

    def test_unavailable_when_entity_marked_unavailable(self):
        state = EntityState(entity_id="vienna_pm25", value=None, available=False)
        sensor = NjordEntitySensor(
            _coordinator({"vienna_pm25": state}), _entry(), _manifest("vienna_pm25", "observation"), None
        )
        assert sensor.available is False

    def test_unit_set_from_manifest(self):
        sensor = NjordEntitySensor(_coordinator(), _entry(), _manifest("x", "observation", unit="µg/m³"), None)
        assert sensor._attr_native_unit_of_measurement == "µg/m³"

    def test_no_unit_when_empty(self):
        sensor = NjordEntitySensor(_coordinator(), _entry(), _manifest("x", "observation", unit=""), None)
        assert not hasattr(sensor, "_attr_native_unit_of_measurement")


class TestNjordAlertBinarySensor:
    def test_unique_id(self):
        sensor = NjordAlertBinarySensor(_coordinator(), _entry(), _manifest("vienna_frost", "alert"), None)
        assert sensor._attr_unique_id == "test_entry_vienna_frost"

    def test_is_on_when_severity_above_none(self):
        value = MagicMock()
        value.severity = 2  # orange
        state = EntityState(entity_id="vienna_frost", value=value, available=True)
        sensor = NjordAlertBinarySensor(
            _coordinator({"vienna_frost": state}), _entry(), _manifest("vienna_frost", "alert"), None
        )
        assert sensor.is_on is True

    def test_is_off_when_severity_none(self):
        value = MagicMock()
        value.severity = 0
        state = EntityState(entity_id="vienna_frost", value=value, available=True)
        sensor = NjordAlertBinarySensor(
            _coordinator({"vienna_frost": state}), _entry(), _manifest("vienna_frost", "alert"), None
        )
        assert sensor.is_on is False

    def test_attributes_include_severity_and_confidence(self):
        value = MagicMock()
        value.severity = 1
        value.confidence = 0.85
        value.confidence_level = 2
        value.trigger_value = 33.0
        value.threshold = 30.0
        value.hours_until = 3
        value.duration_hours = 6
        value.extra = {"expected_max": 35.0}
        state = EntityState(entity_id="vienna_heat", value=value, available=True)
        sensor = NjordAlertBinarySensor(
            _coordinator({"vienna_heat": state}), _entry(), _manifest("vienna_heat", "alert"), None
        )
        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["severity"] == "yellow"
        assert attrs["confidence"] == 0.85
        assert attrs["confidence_level"] == "medium"
        assert attrs["hours_until"] == 3
        assert attrs["expected_max"] == 35.0

    def test_unavailable_when_no_state(self):
        sensor = NjordAlertBinarySensor(_coordinator({}), _entry(), _manifest("vienna_frost", "alert"), None)
        assert sensor.available is False
        assert sensor.is_on is None
