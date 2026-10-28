"""Event platform for njord alerts."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, AlertEvent, AlertSeverity, AlertType, Domain, alert_type_of, enabled_alert_types
from .coordinator import NjordDataCoordinator, NjordStatusCoordinator
from .helpers import device_info, slugify_location
from .models import AlertData

EVENT_ALERT_STARTED = AlertEvent.STARTED
EVENT_ALERT_ESCALATED = AlertEvent.ESCALATED
EVENT_ALERT_DEESCALATED = AlertEvent.DEESCALATED
EVENT_ALERT_CLEARED = AlertEvent.CLEARED


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

    entities: list[EventEntity] = []
    for location in coordinator.data.locations_with(Domain.FORECAST):
        entities.extend(alert_events(location))
    async_add_entities(entities)

    def event_factory(location: str, domain: Domain) -> list[EventEntity]:
        return alert_events(location) if domain == Domain.FORECAST else []

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
        self._attr_name = "Weather Alert"
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
