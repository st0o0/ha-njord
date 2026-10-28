"""Event platform for njord alerts."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, AlertEvent, AlertSeverity, AlertType, Domain, alert_type_of, enabled_alert_types
from .coordinator import NjordDataCoordinator, NjordStatusCoordinator
from .helpers import device_info, slugify_location
from .models import AlertData

EVENT_ALERT_STARTED = AlertEvent.STARTED
EVENT_ALERT_ESCALATED = AlertEvent.ESCALATED
EVENT_ALERT_DEESCALATED = AlertEvent.DEESCALATED
EVENT_ALERT_CLEARED = AlertEvent.CLEARED

DATA_EVENT_TYPES = ["domain_updated", "features_updated"]
FEATURE_EVENT_TYPES = [
    "score_threshold",
    "condition_changed",
    "window_opened",
    "window_closing_soon",
    "window_closed",
]
SCORE_THRESHOLDS: tuple[int, ...] = (30, 50, 70, 80)
WINDOW_CLOSING_SOON = timedelta(minutes=30)
_UNSEEN: object = object()


def _get_sw_version(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    status_coordinator: NjordStatusCoordinator | None = hass.data[DOMAIN][entry.entry_id].get("status_coordinator")
    if status_coordinator is not None and status_coordinator.data is not None:
        return status_coordinator.data.version or None
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up njord event entities."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sw_version = _get_sw_version(hass, entry)

    def alert_events(location: str) -> list[EventEntity]:
        alert_types = frozenset(enabled_alert_types(coordinator.data.active_enrichments))
        if not alert_types:
            return []
        return [NjordAlertEvent(coordinator, entry, location, alert_types, sw_version)]

    def lifecycle_events(location: str) -> list[EventEntity]:
        return [
            NjordDataEvent(coordinator, entry, location, sw_version),
            NjordFeatureEvent(coordinator, entry, location, sw_version),
        ]

    entities: list[EventEntity] = []
    for location in coordinator.data.locations_with(Domain.FORECAST):
        entities.extend(alert_events(location))
        entities.extend(lifecycle_events(location))
    async_add_entities(entities)

    def event_factory(location: str, domain: Domain) -> list[EventEntity]:
        if domain != Domain.FORECAST:
            return []
        return alert_events(location) + lifecycle_events(location)

    coordinator.register_entity_factory("event", async_add_entities, event_factory)


class NjordAlertEvent(CoordinatorEntity[NjordDataCoordinator], EventEntity):
    """Event entity that fires on alert transitions of a location."""

    _attr_has_entity_name = True
    _attr_translation_key = "weather_alert"
    _attr_icon = "mdi:weather-lightning-rainy"
    _attr_event_types = [event.value for event in AlertEvent]

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        alert_types: frozenset[AlertType],
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._alert_types = alert_types
        self._previous_alerts: dict[AlertType, AlertSeverity] = self._current_alert_map()

        self._attr_unique_id = f"{entry.entry_id}_{slugify_location(location)}_weather_alert"
        self._attr_device_info = device_info(entry, location, sw_version)

    def _alerts(self) -> dict[AlertType, AlertData]:
        if self.coordinator.data is None:
            return {}
        result: dict[AlertType, AlertData] = {}
        for (location, feature), item in self.coordinator.data.features.items():
            if location != self._location or item.alert is None:
                continue
            alert_type = alert_type_of(feature)
            if alert_type in self._alert_types:
                result[alert_type] = item.alert
        return result

    def _current_alert_map(self) -> dict[AlertType, AlertSeverity]:
        return {t: a.severity for t, a in self._alerts().items() if a.severity != AlertSeverity.NONE}

    def _alert_data(self, alert_type: AlertType) -> dict[str, object]:
        base: dict[str, object] = {"type": alert_type, "location": self._location}
        a = self._alerts().get(alert_type)
        if a is None:
            return base
        data: dict[str, object] = {
            "type": alert_type,
            "location": self._location,
            "severity": a.severity,
            "confidence": a.confidence,
            "trigger_value": a.trigger_value,
            "threshold": a.threshold,
        }
        if a.peak_value is not None:
            data["peak_value"] = a.peak_value
        if a.hours_until is not None:
            data["hours_until"] = a.hours_until
        if a.duration_hours is not None:
            data["duration_hours"] = a.duration_hours
        return data

    @callback
    def _handle_coordinator_update(self) -> None:
        current = self._current_alert_map()

        all_types = set(self._previous_alerts) | set(current)
        for alert_type in all_types:
            prev_severity = self._previous_alerts.get(alert_type)
            curr_severity = current.get(alert_type)

            if prev_severity == curr_severity:
                continue

            if prev_severity is None and curr_severity is not None:
                self._trigger_event(EVENT_ALERT_STARTED, self._alert_data(alert_type))
            elif prev_severity is not None and curr_severity is None:
                self._trigger_event(
                    EVENT_ALERT_CLEARED,
                    {
                        "type": alert_type,
                        "location": self._location,
                        "previous_severity": prev_severity,
                    },
                )
            elif prev_severity is not None and curr_severity is not None:
                escalated = curr_severity.rank > prev_severity.rank
                event_type = EVENT_ALERT_ESCALATED if escalated else EVENT_ALERT_DEESCALATED
                data = self._alert_data(alert_type)
                data["previous_severity"] = prev_severity
                self._trigger_event(event_type, data)

        self._previous_alerts = current
        self.async_write_ha_state()


class NjordDataEvent(CoordinatorEntity[NjordDataCoordinator], EventEntity):
    """Event entity that fires when new domain data or changed features arrive for a location."""

    _attr_has_entity_name = True
    _attr_translation_key = "data_lifecycle"
    _attr_icon = "mdi:database-refresh"
    _attr_event_types = DATA_EVENT_TYPES

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._last_model_runs: dict[Domain, datetime | None] = self._current_model_runs()
        self._previous_feature_keys: set[str] = set()
        self._feature_stamps: dict[str, datetime | None] = self._current_feature_stamps()

        self._attr_unique_id = f"{entry.entry_id}_{slugify_location(location)}_data_lifecycle"
        self._attr_device_info = device_info(entry, location, sw_version)

    def _current_model_runs(self) -> dict[Domain, datetime | None]:
        if self.coordinator.data is None:
            return {}
        return {
            domain: data.model_run
            for (location, domain), data in self.coordinator.data.domains.items()
            if location == self._location
        }

    def _current_feature_stamps(self) -> dict[str, datetime | None]:
        if self.coordinator.data is None:
            return {}
        return {
            str(feature): item.updated_at
            for (location, feature), item in self.coordinator.data.features.items()
            if location == self._location
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        for domain, model_run in self._current_model_runs().items():
            if domain in self._last_model_runs and self._last_model_runs[domain] == model_run:
                continue
            self._last_model_runs[domain] = model_run
            if model_run is None:
                continue
            self._trigger_event(
                "domain_updated",
                {"location": self._location, "domain": str(domain), "model_run": model_run.isoformat()},
            )

        stamps = self._current_feature_stamps()
        changed = {key for key, stamp in stamps.items() if self._feature_stamps.get(key, _UNSEEN) != stamp}
        self._feature_stamps = stamps
        self._previous_feature_keys = changed
        if changed:
            self._trigger_event("features_updated", {"location": self._location, "features": sorted(changed)})

        self.async_write_ha_state()


class NjordFeatureEvent(CoordinatorEntity[NjordDataCoordinator], EventEntity):
    """Event entity that fires on score threshold crossings, condition changes and window transitions."""

    _attr_has_entity_name = True
    _attr_translation_key = "feature_transitions"
    _attr_icon = "mdi:swap-vertical-bold"
    _attr_event_types = FEATURE_EVENT_TYPES

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._previous_scores: dict[str, int] = {}
        self._previous_conditions: dict[str, str] = {}
        self._active_windows: dict[str, dict] = {}
        self._unsubs: dict[str, list[Callable[[], None]]] = {}

        self._attr_unique_id = f"{entry.entry_id}_{slugify_location(location)}_feature_transitions"
        self._attr_device_info = device_info(entry, location, sw_version)

    async def async_will_remove_from_hass(self) -> None:
        for unsubs in self._unsubs.values():
            for unsub in unsubs:
                unsub()
        self._unsubs.clear()
        await super().async_will_remove_from_hass()

    def _items(self) -> list:
        if self.coordinator.data is None:
            return []
        return [item for (location, _), item in self.coordinator.data.features.items() if location == self._location]

    @staticmethod
    def _threshold_level(score: int) -> int:
        return sum(1 for t in SCORE_THRESHOLDS if score >= t)

    def _check_score(self, key: str, score: int) -> None:
        previous = self._previous_scores.get(key)
        self._previous_scores[key] = score
        if previous is None:
            return
        old_level, new_level = self._threshold_level(previous), self._threshold_level(score)
        if old_level == new_level:
            return
        up = new_level > old_level
        threshold = SCORE_THRESHOLDS[(new_level if up else old_level) - 1]
        self._trigger_event(
            "score_threshold",
            {
                "location": self._location,
                "feature": key,
                "score": score,
                "previous_score": previous,
                "direction": "up" if up else "down",
                "threshold": threshold,
            },
        )

    def _check_condition(self, key: str, level: str) -> None:
        previous = self._previous_conditions.get(key)
        self._previous_conditions[key] = level
        if previous is None or previous == level:
            return
        self._trigger_event(
            "condition_changed",
            {"location": self._location, "feature": key, "condition": level, "previous_condition": previous},
        )

    @staticmethod
    def _active_window(windows: list[dict], now: datetime) -> dict | None:
        for window in windows:
            start, end = window.get("start"), window.get("end")
            if isinstance(start, datetime) and isinstance(end, datetime) and start <= now < end:
                return window
        return None

    def _window_data(self, key: str, window: dict) -> dict[str, object]:
        data: dict[str, object] = {
            "location": self._location,
            "feature": key,
            "start": window["start"].isoformat(),
            "end": window["end"].isoformat(),
        }
        if "score" in window:
            data["score"] = window["score"]
        return data

    def _clear_timers(self, key: str) -> None:
        for unsub in self._unsubs.pop(key, []):
            unsub()

    def _schedule_window(self, key: str, window: dict) -> None:
        self._clear_timers(key)
        end = window["end"]
        timers: list[Callable[[], None]] = []
        closing_at = end - WINDOW_CLOSING_SOON
        if closing_at > dt_util.utcnow():
            timers.append(async_track_point_in_time(self.hass, lambda _: self._fire_closing(key), closing_at))
        timers.append(async_track_point_in_time(self.hass, lambda _: self._fire_closed(key), end))
        self._unsubs[key] = timers

    @callback
    def _fire_closing(self, key: str) -> None:
        window = self._active_windows.get(key)
        if window is None:
            return
        self._trigger_event("window_closing_soon", self._window_data(key, window))
        self.async_write_ha_state()

    @callback
    def _fire_closed(self, key: str) -> None:
        window = self._active_windows.pop(key, None)
        self._clear_timers(key)
        if window is None:
            return
        self._trigger_event("window_closed", self._window_data(key, window))
        self.async_write_ha_state()

    def _check_windows(self, key: str, windows: list[dict], now: datetime) -> None:
        active = self._active_window(windows, now)
        known = self._active_windows.get(key)
        if active is None:
            if known is not None:
                self._fire_closed(key)
            return
        if known is not None and known.get("start") == active["start"] and known.get("end") == active["end"]:
            return
        if known is not None:
            self._fire_closed(key)
        self._active_windows[key] = active
        self._schedule_window(key, active)
        self._trigger_event("window_opened", self._window_data(key, active))

    @callback
    def _handle_coordinator_update(self) -> None:
        now = dt_util.utcnow()
        for item in self._items():
            key = str(item.feature)
            if item.score is not None:
                self._check_score(key, item.score.score)
                if item.score.windows:
                    self._check_windows(key, item.score.windows, now)
            elif item.alert is None:
                level = item.values.get("level")
                if isinstance(level, str) and level:
                    self._check_condition(key, level)
        self.async_write_ha_state()
