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


# --- Enrichment data models ---


@dataclass(frozen=True)
class AlertData:
    type: str
    severity: str = "none"
    confidence: float = 0.0


@dataclass(frozen=True)
class IndexData:
    laundry: int = 0
    outdoor: int = 0
    running: int = 0
    cycling: int = 0
    bbq: int = 0
    irrigation: int = 0
    solar: int = 0
    ventilation: int = 0
    vpd_kpa: float | None = None
    vpd_category: str | None = None


@dataclass(frozen=True)
class ParameterTrendData:
    parameter: str
    direction: str = "stable"
    delta: float = 0.0


@dataclass(frozen=True)
class TrendData:
    parameter_trends: list[ParameterTrendData] = field(default_factory=list)
    weather_change_description: str | None = None
    precip_starts_in_hours: int | None = None
    precip_ends_in_hours: int | None = None
    temp_max_in_hours: int | None = None
    temp_min_in_hours: int | None = None
    stability_label: str | None = None
    stability_ratio: float | None = None
    decay_rate: float | None = None
    reliable_hours: int | None = None


@dataclass(frozen=True)
class CopOptimalHourData:
    hours_from_now: int
    cop: float


@dataclass(frozen=True)
class EnergyData:
    heating_demand: int = 0
    cop_estimate: float | None = None
    shading: int = 0
    battery_strategy: str = "hold"
    night_cooling: int = 0
    cop_optimal: list[CopOptimalHourData] = field(default_factory=list)


@dataclass(frozen=True)
class HorizonDerivedData:
    horizon: str
    beaufort: int | None = None
    wind_chill: float | None = None
    dewpoint_comfort: str | None = None
    wmo_description: str | None = None


@dataclass(frozen=True)
class DerivedData:
    by_horizon: list[HorizonDerivedData] = field(default_factory=list)
    diurnal_amplitude: float | None = None
    sunshine_pct: float | None = None
    inversion: bool | None = None


@dataclass(frozen=True)
class ModelMetricsData:
    model: str
    mae_7d: float | None = None
    mae_30d: float | None = None
    weight: float = 0.0
    drift: float | None = None


@dataclass(frozen=True)
class HistoryData:
    models: list[ModelMetricsData] = field(default_factory=list)
    seasonal_best: str | None = None
    anomaly: bool | None = None
    anomaly_deviation: float | None = None
    weighted_temperature: float | None = None


@dataclass(frozen=True)
class HorizonConsensusData:
    horizon: str
    median: float | None = None
    trimmed_mean: float | None = None
    spread: float | None = None
    iqr: float | None = None
    agreement: float | None = None
    available_models: int = 0


@dataclass(frozen=True)
class ParameterConsensusData:
    parameter: str
    unit: str = ""
    by_horizon: list[HorizonConsensusData] = field(default_factory=list)


@dataclass(frozen=True)
class ConsensusData:
    parameters: list[ParameterConsensusData] = field(default_factory=list)


@dataclass(frozen=True)
class EnrichmentData:
    location: str
    alerts: list[AlertData] = field(default_factory=list)
    indices: IndexData | None = None
    trends: TrendData | None = None
    energy: EnergyData | None = None
    derived: DerivedData | None = None
    history: HistoryData | None = None
    consensus: ConsensusData | None = None
