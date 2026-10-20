"""Typed data models for njord gRPC API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .const import AlertSeverity, AlertType, Domain, PollPhase

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
    ensemble_std_dev: float | None = None
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
class SolarSampleData:
    valid_at: datetime
    direct_radiation: float
    diffuse_radiation: float
    shortwave_radiation: float
    sunshine_duration: float


@dataclass(frozen=True)
class MarineSampleData:
    valid_at: datetime
    wave_height: float
    wave_period: float
    wave_direction: float
    water_temperature: float | None = None


@dataclass(frozen=True)
class WeatherDomainData:
    location: str
    model_run: datetime | None = None
    points: list[WeatherSampleData] = field(default_factory=list)
    domain: Domain = Domain.WEATHER


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
class SolarDomainData:
    location: str
    model_run: datetime | None = None
    points: list[SolarSampleData] = field(default_factory=list)
    domain: Domain = Domain.SOLAR


@dataclass(frozen=True)
class MarineDomainData:
    location: str
    model_run: datetime | None = None
    points: list[MarineSampleData] = field(default_factory=list)
    domain: Domain = Domain.MARINE


DomainData = WeatherDomainData | AirQualityDomainData | FloodDomainData | SolarDomainData | MarineDomainData


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
class LifestyleData:
    """One lifestyle advisory; the keys of data depend on type (all values are strings)."""

    type: str
    location: str
    data: dict[str, str] = field(default_factory=dict)
    updated_at: datetime | None = None


@dataclass(frozen=True)
class EnrichmentData:
    """Alerts of a location, plus the lifestyle advisories a unary GetEnrichments returned."""

    location: str
    alerts: list[AlertData] = field(default_factory=list)
    updated_at: datetime | None = None
    lifestyle: list[LifestyleData] = field(default_factory=list)
