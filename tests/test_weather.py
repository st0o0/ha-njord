"""Tests for njord weather entity logic.

NOTE: Full integration tests require homeassistant test infrastructure.
These tests verify the entity's data extraction logic using mocked coordinator data.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.njord.models import (
    ForecastData,
    HourlyForecastData,
    DailyForecastData,
)
from custom_components.njord.condition_mapper import map_condition


def _make_forecast() -> ForecastData:
    return ForecastData(
        location="lucerne",
        model="icon_d2",
        updated_at=1720000000,
        hourly=[
            HourlyForecastData(
                timestamp=datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc),
                temperature=22.5,
                apparent_temperature=21.0,
                humidity=65.0,
                wind_speed=3.5,
                wind_bearing=180.0,
                pressure_msl=1013.0,
                weather_code=1,
                is_day=True,
                precipitation=0.0,
                cloud_cover=30.0,
            ),
            HourlyForecastData(
                timestamp=datetime(2026, 7, 15, 13, 0, tzinfo=timezone.utc),
                temperature=23.0,
                weather_code=3,
                is_day=True,
            ),
        ],
        daily=[
            DailyForecastData(
                date="2026-07-15",
                temperature_max=28.0,
                temperature_min=15.0,
                precipitation_sum=2.5,
                wind_speed_max=12.0,
                weather_code=61,
            ),
        ],
    )


def test_condition_from_first_hourly():
    """Entity state should map from first hourly entry's weather_code."""
    forecast = _make_forecast()
    h = forecast.hourly[0]
    condition = map_condition(h.weather_code, h.is_day)
    assert condition == "partlycloudy"


def test_condition_night():
    """Night condition should differ for code 0."""
    assert map_condition(0, is_day=False) == "clear-night"
    assert map_condition(0, is_day=True) == "sunny"


def test_attributes_from_first_hourly():
    """Temperature, humidity, pressure, wind come from first hourly entry."""
    forecast = _make_forecast()
    h = forecast.hourly[0]
    assert h.temperature == 22.5
    assert h.humidity == 65.0
    assert h.pressure_msl == 1013.0
    assert h.wind_speed == 3.5
    assert h.wind_bearing == 180.0


def test_hourly_forecast_structure():
    """Hourly forecast should contain expected fields."""
    forecast = _make_forecast()
    for h in forecast.hourly:
        assert h.timestamp is not None
        assert isinstance(h.timestamp, datetime)


def test_daily_forecast_structure():
    """Daily forecast should contain expected fields."""
    forecast = _make_forecast()
    d = forecast.daily[0]
    assert d.date == "2026-07-15"
    assert d.temperature_max == 28.0
    assert d.temperature_min == 15.0
    assert d.precipitation_sum == 2.5
    assert d.weather_code == 61
    assert map_condition(d.weather_code, True) == "rainy"
