"""Typed data models for njord gRPC API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .const import AlertSeverity, AlertType, Domain, Feature, PollPhase

# --- Domain data ---


@dataclass(frozen=True)
class ForecastSampleData:
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
    uv_index_clear_sky: float | None = None
    showers: float | None = None
    soil_moisture_0_to_1cm: float | None = None
    soil_moisture_1_to_3cm: float | None = None
    evapotranspiration: float | None = None
    vapour_pressure_deficit: float | None = None
    boundary_layer_height: float | None = None
    cloud_cover_low: float | None = None
    cloud_cover_mid: float | None = None
    cloud_cover_high: float | None = None
    convective_inhibition: float | None = None
    lifted_index: float | None = None
    surface_pressure: float | None = None
    wind_speed_80m: float | None = None
    wind_direction_80m: float | None = None
    wind_speed_120m: float | None = None
    wind_direction_120m: float | None = None
    temperature_80m: float | None = None
    temperature_120m: float | None = None
    wind_direction_10m: float | None = None
    snow_depth: float | None = None
    shortwave_radiation: float | None = None
    direct_radiation: float | None = None
    diffuse_radiation: float | None = None
    direct_normal_irradiance: float | None = None
    sunshine_duration: float | None = None
    global_tilted_irradiance: float | None = None
    wet_bulb_temperature_2m: float | None = None
    snowfall_height: float | None = None
    wind_speed_100m: float | None = None
    wind_direction_100m: float | None = None
    thunderstorm_probability: float | None = None
    precipitation_type: float | None = None
    surface_temperature: float | None = None
    snowfall_water_equivalent: float | None = None


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
    dust: float | None = None
    ammonia: float | None = None
    olive_pollen: float | None = None
    us_aqi: float | None = None
    uv_index: float | None = None
    uv_index_clear_sky: float | None = None
    ragweed_pollen: float | None = None
    european_aqi_pm25: float | None = None
    european_aqi_pm10: float | None = None
    european_aqi_nitrogen_dioxide: float | None = None
    european_aqi_ozone: float | None = None
    european_aqi_sulphur_dioxide: float | None = None
    aerosol_optical_depth: float | None = None
    carbon_dioxide: float | None = None
    methane: float | None = None
    us_aqi_pm25: float | None = None
    us_aqi_pm10: float | None = None
    us_aqi_nitrogen_dioxide: float | None = None
    us_aqi_ozone: float | None = None
    us_aqi_sulphur_dioxide: float | None = None
    us_aqi_carbon_monoxide: float | None = None
    carbon_monoxide: float | None = None
    sulphur_dioxide: float | None = None
    nitrogen_dioxide: float | None = None
    european_aqi: float | None = None


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
    wind_wave_height: float | None = None
    wind_wave_period: float | None = None
    wind_wave_direction: float | None = None
    wind_wave_peak_period: float | None = None
    swell_wave_height: float | None = None
    swell_wave_period: float | None = None
    swell_wave_direction: float | None = None
    swell_wave_peak_period: float | None = None
    sea_level_height_msl: float | None = None
    ocean_current_velocity: float | None = None
    ocean_current_direction: float | None = None
    secondary_swell_wave_height: float | None = None
    secondary_swell_wave_direction: float | None = None
    secondary_swell_wave_period: float | None = None
    tertiary_swell_wave_height: float | None = None
    tertiary_swell_wave_direction: float | None = None
    tertiary_swell_wave_period: float | None = None
    invert_barometer_height: float | None = None
    wave_peak_period: float | None = None


@dataclass(frozen=True)
class SeasonalSampleData:
    valid_at: datetime
    temperature_anomaly: float | None = None
    precipitation_anomaly: float | None = None
    precipitation_mean: float | None = None


@dataclass(frozen=True)
class EnsembleSampleData:
    valid_at: datetime
    temperature_spread: float | None = None
    precipitation_spread: float | None = None
    wind_speed_spread: float | None = None
    pressure_msl_spread: float | None = None
    cloud_cover_spread: float | None = None
    wind_gusts_10m_spread: float | None = None
    cape_spread: float | None = None
    snowfall_spread: float | None = None
    rain_spread: float | None = None
    dew_point_2m_spread: float | None = None
    relative_humidity_2m_spread: float | None = None
    surface_pressure_spread: float | None = None
    wind_direction_10m_spread: float | None = None
    wet_bulb_temperature_2m_spread: float | None = None
    wind_speed_100m_spread: float | None = None


@dataclass(frozen=True)
class ForecastDomainData:
    location: str
    model_run: datetime | None = None
    points: list[ForecastSampleData] = field(default_factory=list)
    domain: Domain = Domain.FORECAST
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


@dataclass(frozen=True)
class EnsembleDomainData:
    location: str
    model_run: datetime | None = None
    points: list[EnsembleSampleData] = field(default_factory=list)
    domain: Domain = Domain.ENSEMBLE


DomainData = (
    ForecastDomainData
    | AirQualityDomainData
    | FloodDomainData
    | MarineDomainData
    | SeasonalDomainData
    | EnsembleDomainData
)


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
    windows: list[dict[str, Any]] = field(default_factory=list)


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
