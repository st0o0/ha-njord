"""Typed data models for njord gRPC API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class HourlyForecastData:
    timestamp: datetime
    temperature: float | None = None
    apparent_temperature: float | None = None
    precipitation: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    wind_bearing: float | None = None
    cloud_cover: float | None = None
    weather_code: int | None = None
    is_day: bool | None = None
    rain: float | None = None
    wind_gusts: float | None = None
    pressure_msl: float | None = None


@dataclass(frozen=True)
class DailyForecastData:
    date: str
    temperature_max: float | None = None
    temperature_min: float | None = None
    precipitation_sum: float | None = None
    wind_speed_max: float | None = None
    wind_gusts_max: float | None = None
    sunrise: str | None = None
    sunset: str | None = None
    weather_code: int | None = None


@dataclass(frozen=True)
class ForecastData:
    location: str
    model: str
    updated_at: int
    hourly: list[HourlyForecastData] = field(default_factory=list)
    daily: list[DailyForecastData] = field(default_factory=list)


@dataclass(frozen=True)
class NjordLocation:
    name: str
    latitude: float
    longitude: float
    models: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NjordConfigData:
    locations: list[NjordLocation] = field(default_factory=list)
    default_models: list[str] = field(default_factory=list)
    horizons: list[int] = field(default_factory=list)
    forecast_days: int = 0
    poll_interval_seconds: int = 0


@dataclass(frozen=True)
class BudgetStatusData:
    monthly_limit: int = 0
    monthly_used: int = 0
    daily_limit: int = 0
    daily_used: int = 0
    usage_percent: float = 0.0


@dataclass(frozen=True)
class ServerStatusData:
    version: str = ""
    uptime_seconds: int = 0
    budget: BudgetStatusData | None = None
