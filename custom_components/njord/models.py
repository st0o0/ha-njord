"""Typed data models for njord gRPC API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .const import AlertSeverity, AlertType, Domain, Feature, PollPhase

# --- Domain data ---


@dataclass(frozen=True)
class WeatherSampleData:
    valid_at: datetime
    temperature: float
    apparent_temperature: float
    wind_speed: float
    precipitation: float
    precipitation_probability: float
    cloud_cover: float
    pressure: float
    weather_code: int
    humidity: float
    dew_point: float
    uv_index: float
    wind_gusts: float | None = None
    visibility: float | None = None
    cape: float | None = None
    rain: float | None = None
    snowfall: float | None = None
    soil_temperature: float | None = None
    freezing_level_height: float | None = None
    is_day: bool | None = None


@dataclass(frozen=True)
class AirQualitySampleData:
    valid_at: datetime
    pm25: float
    pm10: float
    ozone: float
    birch_pollen: float | None = None
    grass_pollen: float | None = None
    alder: float | None = None
    mugwort: float | None = None


@dataclass(frozen=True)
class FloodSampleData:
    valid_at: datetime
    discharge: float
    discharge_mean: float | None = None
    discharge_median: float | None = None
    discharge_max: float | None = None
    discharge_min: float | None = None
    discharge_p25: float | None = None
    discharge_p75: float | None = None


@dataclass(frozen=True)
class MarineSampleData:
    valid_at: datetime
    wave_height: float
    wave_period: float
    wave_direction: float
    water_temperature: float | None = None


@dataclass(frozen=True)
class SeasonalSampleData:
    valid_at: datetime
    temperature_anomaly: float | None = None
    precipitation_anomaly: float | None = None
    precipitation_mean: float | None = None


@dataclass(frozen=True)
class WeatherDomainData:
    location: str
    model_run: datetime | None = None
    points: list[WeatherSampleData] = field(default_factory=list)
    domain: Domain = Domain.WEATHER
    model: str = ""


@dataclass(frozen=True)
class AirQualityDomainData:
    location: str
    model_run: datetime | None = None
    points: list[AirQualitySampleData] = field(default_factory=list)
    domain: Domain = Domain.AIR_QUALITY


@dataclass(frozen=True)
class FloodDomainData:
    location: str
    model_run: datetime | None = None
    points: list[FloodSampleData] = field(default_factory=list)
    domain: Domain = Domain.FLOOD


@dataclass(frozen=True)
class MarineDomainData:
    location: str
    model_run: datetime | None = None
    points: list[MarineSampleData] = field(default_factory=list)
    domain: Domain = Domain.MARINE


@dataclass(frozen=True)
class SeasonalDomainData:
    location: str
    model_run: datetime | None = None
    points: list[SeasonalSampleData] = field(default_factory=list)
    domain: Domain = Domain.SEASONAL


DomainData = WeatherDomainData | AirQualityDomainData | FloodDomainData | MarineDomainData | SeasonalDomainData


# --- Catalog ---


@dataclass(frozen=True)
class ModelInfoData:
    id: str
    display_name: str = ""
    provider: str = ""
    region: str = ""
    coverage_tier: str = "unspecified"
    max_forecast_hours: int | None = None
    resolution_km: float | None = None
    description: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class NjordLocation:
    name: str
    latitude: float
    longitude: float
    models: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CatalogData:
    locations: list[NjordLocation] = field(default_factory=list)
    model_info: dict[str, ModelInfoData] = field(default_factory=dict)


# --- Status ---


@dataclass(frozen=True)
class BudgetStatusData:
    monthly_limit: int = 0
    monthly_used: int = 0
    daily_limit: int = 0
    daily_used: int = 0
    usage_percent: float = 0.0


@dataclass(frozen=True)
class LocationStatusData:
    location: str
    phase: PollPhase = PollPhase.UNSPECIFIED
    next_poll: datetime | None = None
    last_change: datetime | None = None
    miss_count: int = 0
    cycle_seconds: int | None = None


@dataclass(frozen=True)
class TargetData:
    location: str
    phase: PollPhase = PollPhase.UNSPECIFIED
    next_poll: datetime | None = None
    last_change: datetime | None = None
    miss_count: int = 0
    cycle_seconds: int | None = None


@dataclass(frozen=True)
class ServerStatusData:
    version: str = ""
    uptime_seconds: int = 0
    budget: BudgetStatusData | None = None
    process_start: datetime | None = None
    location_statuses: list[LocationStatusData] = field(default_factory=list)
    active_enrichments: list[str] = field(default_factory=list)
    budget_partial: bool = False
    models_partial: bool = False
    targets: list[TargetData] = field(default_factory=list)


# --- Enrichments ---


@dataclass(frozen=True)
class AlertData:
    type: AlertType
    severity: AlertSeverity = AlertSeverity.NONE
    confidence: float = 0.0
    trigger_value: float = 0.0
    threshold: float = 0.0
    peak_value: float | None = None
    hours_until: int | None = None
    duration_hours: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "type", AlertType(self.type))
        object.__setattr__(self, "severity", AlertSeverity(self.severity))


@dataclass(frozen=True)
class ScoreData:
    score: int = 0
    best_start: datetime | None = None
    best_hours: int = 0


@dataclass(frozen=True)
class FeatureData:
    """One typed feature result of a location.

    Alert features carry `alert`, score features carry `score`; the feature-specific fields of every feature are in
    `values` with native types (numbers, bools, datetimes, lowercase enum text, lists).
    """

    location: str
    feature: Feature
    updated_at: datetime | None = None
    alert: AlertData | None = None
    score: ScoreData | None = None
    values: dict[str, Any] = field(default_factory=dict)
