"""Tests for the njord activity calendar entity."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.core import HomeAssistant

from custom_components.njord.calendar import NjordActivityCalendar
from custom_components.njord.const import DOMAIN, Feature
from custom_components.njord.models import FeatureData, ScoreData
from tests.conftest import PAST, init_integration


async def _calendar(hass: HomeAssistant, entry) -> tuple[NjordActivityCalendar, object]:
    await init_integration(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    return NjordActivityCalendar(coordinator, entry, "home"), coordinator


async def test_calendar_translation_key(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    calendar, _ = await _calendar(hass, mock_config_entry)

    assert calendar.translation_key == "activity_windows"


async def test_build_events_empty_without_data(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    calendar, coordinator = await _calendar(hass, mock_config_entry)

    coordinator.data = None

    assert calendar._build_events() == []


async def test_build_events_empty_without_windows(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    calendar, coordinator = await _calendar(hass, mock_config_entry)
    coordinator.data.features.clear()

    assert calendar._build_events() == []


async def test_build_events_from_score_windows(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    calendar, coordinator = await _calendar(hass, mock_config_entry)
    start = datetime(2099, 1, 1, 10, 0, tzinfo=UTC)
    end = datetime(2099, 1, 1, 13, 0, tzinfo=UTC)
    coordinator.data.features.clear()
    coordinator.data.features[("home", Feature.LAUNDRY)] = FeatureData(
        location="home",
        feature=Feature.LAUNDRY,
        updated_at=PAST,
        score=ScoreData(
            score=80,
            windows=[
                {"start": start, "end": end, "score": 80, "limiting": {"kind": "wind"}},
                {"start": None, "end": end, "score": 10},
            ],
        ),
    )
    coordinator.data.features[("other", Feature.LAUNDRY)] = FeatureData(
        location="other",
        feature=Feature.LAUNDRY,
        updated_at=PAST,
        score=ScoreData(score=70, windows=[{"start": start, "end": end, "score": 70}]),
    )

    events = calendar._build_events()

    assert len(events) == 1
    assert events[0].start == start
    assert events[0].end == end
    assert events[0].summary.endswith("80")
    assert events[0].description == "limiting: wind"
    assert calendar.event is not None
    assert calendar.event.start == start
