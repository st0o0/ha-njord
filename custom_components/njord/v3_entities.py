"""Generic entity classes driven by the njord manifest."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import device_info
from .models import EntityState, ManifestEntity
from .v3_coordinator import NjordV3Coordinator

_SEVERITY_NAMES = {0: "none", 1: "yellow", 2: "orange", 3: "red"}
_CONFIDENCE_NAMES = {0: "unspecified", 1: "low", 2: "medium", 3: "high"}


class NjordV3Sensor(CoordinatorEntity[NjordV3Coordinator], SensorEntity):
    """A generic v3 sensor for scores, conditions, trends, forecasts, and observations."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NjordV3Coordinator,
        entry: ConfigEntry,
        manifest_entity: ManifestEntity,
        sw_version: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._manifest = manifest_entity
        self._attr_unique_id = f"{entry.entry_id}_{manifest_entity.entity_id}"
        self._attr_translation_key = manifest_entity.entity_id
        self._attr_device_info = device_info(entry, manifest_entity.location, sw_version)
        if manifest_entity.unit:
            self._attr_native_unit_of_measurement = manifest_entity.unit
        if manifest_entity.device_class:
            self._attr_device_class = manifest_entity.device_class
        if manifest_entity.output_kind in ("score", "observation"):
            self._attr_state_class = SensorStateClass.MEASUREMENT

    def _state(self) -> EntityState | None:
        v3_states: dict[str, EntityState] | None = getattr(self.coordinator, "v3_entity_states", None)
        if v3_states is None:
            return None
        return v3_states.get(self._manifest.entity_id)

    @property
    def available(self) -> bool:
        state = self._state()
        if state is None:
            return False
        return state.available

    @property
    def native_value(self) -> float | str | None:
        state = self._state()
        if state is None:
            return None
        value = state.value
        if value is None:
            return None
        return self._extract_primary(value)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        state = self._state()
        if state is None:
            return None
        value = state.value
        if value is None:
            return None
        return self._extract_attributes(value)

    def _extract_primary(self, value: Any) -> float | str | None:
        kind = self._manifest.output_kind
        if kind == "observation":
            return value.value if hasattr(value, "value") else value
        if kind == "score":
            return value.score if hasattr(value, "score") else value
        if kind == "condition":
            return "on" if (hasattr(value, "active") and value.active) else "off"
        if kind == "trend":
            extra = getattr(value, "extra", {})
            return next(iter(extra.values()), None) if extra else None
        if kind == "forecast":
            extra = getattr(value, "extra", {})
            return next(iter(extra.values()), None) if extra else None
        return None

    def _extract_attributes(self, value: Any) -> dict[str, Any] | None:
        kind = self._manifest.output_kind
        if kind == "score" and hasattr(value, "best_start"):
            attrs: dict[str, Any] = {}
            if value.best_start and (value.best_start.seconds or value.best_start.nanos):
                attrs["best_start"] = value.best_start.ToDatetime().replace(tzinfo=UTC).isoformat()
            if value.best_hours:
                attrs["best_hours"] = value.best_hours
            return attrs or None
        if kind in ("condition", "trend", "forecast"):
            extra = getattr(value, "extra", {})
            return dict(extra) if extra else None
        return None


class NjordV3AlertBinarySensor(CoordinatorEntity[NjordV3Coordinator], BinarySensorEntity):
    """A generic v3 binary sensor for alerts."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NjordV3Coordinator,
        entry: ConfigEntry,
        manifest_entity: ManifestEntity,
        sw_version: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._manifest = manifest_entity
        self._attr_unique_id = f"{entry.entry_id}_{manifest_entity.entity_id}"
        self._attr_translation_key = manifest_entity.entity_id
        self._attr_device_info = device_info(entry, manifest_entity.location, sw_version)
        if manifest_entity.device_class:
            self._attr_device_class = manifest_entity.device_class

    def _state(self) -> EntityState | None:
        v3_states: dict[str, EntityState] | None = getattr(self.coordinator, "v3_entity_states", None)
        if v3_states is None:
            return None
        return v3_states.get(self._manifest.entity_id)

    @property
    def available(self) -> bool:
        state = self._state()
        if state is None:
            return False
        return state.available

    @property
    def is_on(self) -> bool | None:
        state = self._state()
        if state is None:
            return None
        value = state.value
        if value is None:
            return None
        severity = getattr(value, "severity", 0)
        return severity > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        state = self._state()
        if state is None:
            return None
        value = state.value
        if value is None:
            return None
        attrs: dict[str, Any] = {}
        severity = getattr(value, "severity", 0)
        attrs["severity"] = _SEVERITY_NAMES.get(severity, "unknown")
        if hasattr(value, "confidence"):
            attrs["confidence"] = round(value.confidence, 2)
        if hasattr(value, "confidence_level"):
            attrs["confidence_level"] = _CONFIDENCE_NAMES.get(value.confidence_level, "unspecified")
        if hasattr(value, "trigger_value"):
            attrs["trigger_value"] = round(value.trigger_value, 2)
        if hasattr(value, "threshold"):
            attrs["threshold"] = round(value.threshold, 2)
        hours_until = getattr(value, "hours_until", None)
        if hours_until is not None:
            attrs["hours_until"] = hours_until
        duration = getattr(value, "duration_hours", None)
        if duration is not None:
            attrs["duration_hours"] = duration
        extra = getattr(value, "extra", {})
        if extra:
            attrs.update(extra)
        return attrs or None
