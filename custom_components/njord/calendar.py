"""Calendar platform for njord activity windows."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, Domain
from .coordinator import NjordDataCoordinator, NjordStatusCoordinator
from .helpers import device_info, slugify_location

# Deferred: window lifecycle events (start/end notifications) depend on the njord enrichment-events change.


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
    """Set up njord calendar entities."""
    coordinator: NjordDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sw_version = _get_sw_version(hass, entry)

    async_add_entities(
        [
            NjordActivityCalendar(coordinator, entry, location, sw_version)
            for location in coordinator.data.locations_with(Domain.FORECAST)
        ]
    )

    def calendar_factory(location: str, domain: Domain) -> list[CalendarEntity]:
        if domain != Domain.FORECAST:
            return []
        return [NjordActivityCalendar(coordinator, entry, location, sw_version)]

    coordinator.register_entity_factory("calendar", async_add_entities, calendar_factory)


class NjordActivityCalendar(CoordinatorEntity[NjordDataCoordinator], CalendarEntity):
    """Calendar showing the activity windows of the score features of a location."""

    _attr_has_entity_name = True
    _attr_translation_key = "activity_windows"
    _attr_icon = "mdi:calendar-star"

    def __init__(
        self,
        coordinator: NjordDataCoordinator,
        entry: ConfigEntry,
        location: str,
        sw_version: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._location = location
        self._attr_unique_id = f"{entry.entry_id}_{slugify_location(location)}_activity_windows"
        self._attr_device_info = device_info(entry, location, sw_version)

    @property
    def event(self) -> CalendarEvent | None:
        """The current or next upcoming window."""
        now = dt_util.utcnow()
        upcoming = [ev for ev in self._build_events() if ev.end > now]
        return min(upcoming, key=lambda ev: ev.start, default=None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Windows overlapping the requested range."""
        return [ev for ev in self._build_events() if ev.start < end_date and ev.end > start_date]

    def _build_events(self) -> list[CalendarEvent]:
        if self.coordinator.data is None:
            return []
        events: list[CalendarEvent] = []
        for (location, feature), item in self.coordinator.data.features.items():
            if location != self._location or item.score is None:
                continue
            name = str(feature).replace("_", " ").title()
            for window in item.score.windows:
                start = window.get("start")
                end = window.get("end")
                if start is None or end is None:
                    continue
                limiting = (window.get("limiting") or {}).get("kind")
                events.append(
                    CalendarEvent(
                        summary=f"{name} {window.get('score', 0)}",
                        start=start,
                        end=end,
                        description=f"limiting: {limiting}" if limiting else None,
                    )
                )
        return events
