"""gRPC client for communicating with the njord weather service."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator, Callable, Iterable
from datetime import UTC, datetime
from typing import TypeVar

import grpc

# Ensure proto package path is on sys.path before importing generated stubs.
from . import proto as _proto_pkg  # noqa: F401
from .const import AlertSeverity, AlertType, Domain, Feature, PollPhase, alert_type_of
from .models import (
    AirQualityDomainData,
    AirQualitySampleData,
    AlertData,
    BudgetStatusData,
    CatalogData,
    DomainData,
    EnsembleDomainData,
    EnsembleSampleData,
    FeatureData,
    FloodDomainData,
    FloodSampleData,
    ForecastDomainData,
    ForecastSampleData,
    LocationStatusData,
    MarineDomainData,
    MarineSampleData,
    ModelInfoData,
    NjordLocation,
    ScoreData,
    SeasonalDomainData,
    SeasonalSampleData,
    ServerStatusData,
    TargetData,
)
from .proto.njord.v2 import (
    common_pb2,
    ops_pb2,
    ops_pb2_grpc,
    weather_pb2,
    weather_pb2_grpc,
)

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

_BACKOFF_INITIAL = 1.0
_BACKOFF_MAX = 60.0
_BACKOFF_FACTOR = 2.0


# --- Protobuf to dataclass converters ---


def _ts_to_dt(ts) -> datetime:
    return ts.ToDatetime().replace(tzinfo=UTC)


def _optional_ts(ts) -> datetime | None:
    return _ts_to_dt(ts) if ts.seconds or ts.nanos else None


def _opt(pb, name: str):
    return getattr(pb, name) if pb.HasField(name) else None


_COVERAGE_TIER_MAP: dict[int, str] = {
    common_pb2.COVERAGE_TIER_UNSPECIFIED: "unspecified",
    common_pb2.COVERAGE_TIER_GLOBAL: "global",
    common_pb2.COVERAGE_TIER_CONTINENTAL: "continental",
    common_pb2.COVERAGE_TIER_REGIONAL: "regional",
}

_DOMAIN_TO_PB: dict[Domain, int] = {
    Domain.FORECAST: common_pb2.DOMAIN_FORECAST,
    Domain.AIR_QUALITY: common_pb2.DOMAIN_AIR_QUALITY,
    Domain.FLOOD: common_pb2.DOMAIN_FLOOD,
    Domain.MARINE: common_pb2.DOMAIN_MARINE,
    Domain.SEASONAL: common_pb2.DOMAIN_SEASONAL,
    Domain.ENSEMBLE: common_pb2.DOMAIN_ENSEMBLE,
}

_PB_TO_DOMAIN: dict[int, Domain] = {v: k for k, v in _DOMAIN_TO_PB.items()}

_POLL_PHASE_MAP: dict[int, PollPhase] = {
    ops_pb2.POLL_PHASE_UNSPECIFIED: PollPhase.UNSPECIFIED,
    ops_pb2.POLL_PHASE_DISCOVERY: PollPhase.DISCOVERY,
    ops_pb2.POLL_PHASE_STEADY: PollPhase.STEADY,
}

_ALERT_SEVERITY_MAP: dict[int, AlertSeverity] = {
    common_pb2.ALERT_SEVERITY_NONE: AlertSeverity.NONE,
    common_pb2.ALERT_SEVERITY_YELLOW: AlertSeverity.YELLOW,
    common_pb2.ALERT_SEVERITY_ORANGE: AlertSeverity.ORANGE,
    common_pb2.ALERT_SEVERITY_RED: AlertSeverity.RED,
}


def _to_model_info(pb: common_pb2.ModelInfo) -> ModelInfoData:
    return ModelInfoData(
        id=pb.id,
        display_name=pb.display_name,
        provider=pb.provider,
        region=pb.region,
        coverage_tier=_COVERAGE_TIER_MAP.get(pb.coverage_tier, "unspecified"),
        max_forecast_hours=_opt(pb, "max_forecast_hours"),
        resolution_km=_opt(pb, "resolution_km"),
        description=_opt(pb, "description"),
        enabled=pb.enabled,
    )


def _to_location(pb: common_pb2.LocationInfo) -> NjordLocation:
    resolved: dict[str, frozenset[str]] = {}
    for schema in pb.resolved_domains:
        domain = _PB_TO_DOMAIN.get(schema.domain)
        if domain is not None:
            resolved[domain.value] = frozenset(schema.fields)
    return NjordLocation(
        name=pb.name, latitude=pb.latitude, longitude=pb.longitude, models=list(pb.models), resolved_domains=resolved
    )


def _to_catalog_data(pb: weather_pb2.GetCatalogResponse) -> CatalogData:
    return CatalogData(
        locations=[_to_location(loc) for loc in pb.locations],
        model_info={info.id: _to_model_info(info) for info in pb.models},
    )


def _to_forecast_sample(pb: weather_pb2.ForecastSample) -> ForecastSampleData:
    return ForecastSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        temperature=_opt(pb, "temperature"),
        apparent_temperature=_opt(pb, "apparent_temperature"),
        wind_speed=_opt(pb, "wind_speed"),
        precipitation=_opt(pb, "precipitation"),
        precipitation_probability=_opt(pb, "precipitation_probability"),
        cloud_cover=_opt(pb, "cloud_cover"),
        pressure=_opt(pb, "pressure"),
        weather_code=pb.weather_code,
        humidity=_opt(pb, "humidity"),
        dew_point=_opt(pb, "dew_point"),
        uv_index=_opt(pb, "uv_index"),
        wind_gusts=_opt(pb, "wind_gusts"),
        visibility=_opt(pb, "visibility"),
        cape=_opt(pb, "cape"),
        rain=_opt(pb, "rain"),
        snowfall=_opt(pb, "snowfall"),
        soil_temperature=_opt(pb, "soil_temperature"),
        freezing_level_height=_opt(pb, "freezing_level_height"),
        is_day=_opt(pb, "is_day"),
        uv_index_clear_sky=_opt(pb, "uv_index_clear_sky"),
        showers=_opt(pb, "showers"),
        soil_moisture_0_to_1cm=_opt(pb, "soil_moisture_0_to_1cm"),
        soil_moisture_1_to_3cm=_opt(pb, "soil_moisture_1_to_3cm"),
        evapotranspiration=_opt(pb, "evapotranspiration"),
        vapour_pressure_deficit=_opt(pb, "vapour_pressure_deficit"),
        boundary_layer_height=_opt(pb, "boundary_layer_height"),
        cloud_cover_low=_opt(pb, "cloud_cover_low"),
        cloud_cover_mid=_opt(pb, "cloud_cover_mid"),
        cloud_cover_high=_opt(pb, "cloud_cover_high"),
        convective_inhibition=_opt(pb, "convective_inhibition"),
        lifted_index=_opt(pb, "lifted_index"),
        surface_pressure=_opt(pb, "surface_pressure"),
        wind_speed_80m=_opt(pb, "wind_speed_80m"),
        wind_direction_80m=_opt(pb, "wind_direction_80m"),
        wind_speed_120m=_opt(pb, "wind_speed_120m"),
        wind_direction_120m=_opt(pb, "wind_direction_120m"),
        temperature_80m=_opt(pb, "temperature_80m"),
        temperature_120m=_opt(pb, "temperature_120m"),
        wind_direction_10m=_opt(pb, "wind_direction_10m"),
        snow_depth=_opt(pb, "snow_depth"),
        shortwave_radiation=_opt(pb, "shortwave_radiation"),
        direct_radiation=_opt(pb, "direct_radiation"),
        diffuse_radiation=_opt(pb, "diffuse_radiation"),
        direct_normal_irradiance=_opt(pb, "direct_normal_irradiance"),
        sunshine_duration=_opt(pb, "sunshine_duration"),
        global_tilted_irradiance=_opt(pb, "global_tilted_irradiance"),
        wet_bulb_temperature_2m=_opt(pb, "wet_bulb_temperature_2m"),
        snowfall_height=_opt(pb, "snowfall_height"),
        wind_speed_100m=_opt(pb, "wind_speed_100m"),
        wind_direction_100m=_opt(pb, "wind_direction_100m"),
        thunderstorm_probability=_opt(pb, "thunderstorm_probability"),
        precipitation_type=_opt(pb, "precipitation_type"),
        surface_temperature=_opt(pb, "surface_temperature"),
        snowfall_water_equivalent=_opt(pb, "snowfall_water_equivalent"),
    )


def _to_air_quality_sample(pb: weather_pb2.AirQualitySample) -> AirQualitySampleData:
    return AirQualitySampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        pm25=_opt(pb, "pm25"),
        pm10=_opt(pb, "pm10"),
        ozone=_opt(pb, "ozone"),
        birch_pollen=_opt(pb, "birch_pollen"),
        grass_pollen=_opt(pb, "grass_pollen"),
        alder=_opt(pb, "alder"),
        mugwort=_opt(pb, "mugwort"),
        dust=_opt(pb, "dust"),
        ammonia=_opt(pb, "ammonia"),
        olive_pollen=_opt(pb, "olive_pollen"),
        us_aqi=_opt(pb, "us_aqi"),
        uv_index=_opt(pb, "uv_index"),
        uv_index_clear_sky=_opt(pb, "uv_index_clear_sky"),
        ragweed_pollen=_opt(pb, "ragweed_pollen"),
        european_aqi_pm25=_opt(pb, "european_aqi_pm25"),
        european_aqi_pm10=_opt(pb, "european_aqi_pm10"),
        european_aqi_nitrogen_dioxide=_opt(pb, "european_aqi_nitrogen_dioxide"),
        european_aqi_ozone=_opt(pb, "european_aqi_ozone"),
        european_aqi_sulphur_dioxide=_opt(pb, "european_aqi_sulphur_dioxide"),
        aerosol_optical_depth=_opt(pb, "aerosol_optical_depth"),
        carbon_dioxide=_opt(pb, "carbon_dioxide"),
        methane=_opt(pb, "methane"),
        us_aqi_pm25=_opt(pb, "us_aqi_pm25"),
        us_aqi_pm10=_opt(pb, "us_aqi_pm10"),
        us_aqi_nitrogen_dioxide=_opt(pb, "us_aqi_nitrogen_dioxide"),
        us_aqi_ozone=_opt(pb, "us_aqi_ozone"),
        us_aqi_sulphur_dioxide=_opt(pb, "us_aqi_sulphur_dioxide"),
        us_aqi_carbon_monoxide=_opt(pb, "us_aqi_carbon_monoxide"),
        carbon_monoxide=_opt(pb, "carbon_monoxide"),
        sulphur_dioxide=_opt(pb, "sulphur_dioxide"),
        nitrogen_dioxide=_opt(pb, "nitrogen_dioxide"),
        european_aqi=_opt(pb, "european_aqi"),
    )


def _to_flood_sample(pb: weather_pb2.FloodSample) -> FloodSampleData:
    return FloodSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        discharge=_opt(pb, "discharge"),
        discharge_mean=_opt(pb, "discharge_mean"),
        discharge_median=_opt(pb, "discharge_median"),
        discharge_max=_opt(pb, "discharge_max"),
        discharge_min=_opt(pb, "discharge_min"),
        discharge_p25=_opt(pb, "discharge_p25"),
        discharge_p75=_opt(pb, "discharge_p75"),
    )


def _to_marine_sample(pb: weather_pb2.MarineSample) -> MarineSampleData:
    return MarineSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        wave_height=_opt(pb, "wave_height"),
        wave_period=_opt(pb, "wave_period"),
        wave_direction=_opt(pb, "wave_direction"),
        water_temperature=_opt(pb, "water_temperature"),
        wind_wave_height=_opt(pb, "wind_wave_height"),
        wind_wave_period=_opt(pb, "wind_wave_period"),
        wind_wave_direction=_opt(pb, "wind_wave_direction"),
        wind_wave_peak_period=_opt(pb, "wind_wave_peak_period"),
        swell_wave_height=_opt(pb, "swell_wave_height"),
        swell_wave_period=_opt(pb, "swell_wave_period"),
        swell_wave_direction=_opt(pb, "swell_wave_direction"),
        swell_wave_peak_period=_opt(pb, "swell_wave_peak_period"),
        sea_level_height_msl=_opt(pb, "sea_level_height_msl"),
        ocean_current_velocity=_opt(pb, "ocean_current_velocity"),
        ocean_current_direction=_opt(pb, "ocean_current_direction"),
        secondary_swell_wave_height=_opt(pb, "secondary_swell_wave_height"),
        secondary_swell_wave_direction=_opt(pb, "secondary_swell_wave_direction"),
        secondary_swell_wave_period=_opt(pb, "secondary_swell_wave_period"),
        tertiary_swell_wave_height=_opt(pb, "tertiary_swell_wave_height"),
        tertiary_swell_wave_direction=_opt(pb, "tertiary_swell_wave_direction"),
        tertiary_swell_wave_period=_opt(pb, "tertiary_swell_wave_period"),
        invert_barometer_height=_opt(pb, "invert_barometer_height"),
        wave_peak_period=_opt(pb, "wave_peak_period"),
    )


def _to_seasonal_sample(pb: weather_pb2.SeasonalSample) -> SeasonalSampleData:
    return SeasonalSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        temperature_anomaly=_opt(pb, "temperature_anomaly"),
        precipitation_anomaly=_opt(pb, "precipitation_anomaly"),
        precipitation_mean=_opt(pb, "precipitation_mean"),
    )


def _to_ensemble_sample(pb: weather_pb2.EnsembleSample) -> EnsembleSampleData:
    return EnsembleSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        temperature_spread=_opt(pb, "temperature_spread"),
        precipitation_spread=_opt(pb, "precipitation_spread"),
        wind_speed_spread=_opt(pb, "wind_speed_spread"),
        pressure_msl_spread=_opt(pb, "pressure_msl_spread"),
        cloud_cover_spread=_opt(pb, "cloud_cover_spread"),
        wind_gusts_10m_spread=_opt(pb, "wind_gusts_10m_spread"),
        cape_spread=_opt(pb, "cape_spread"),
        snowfall_spread=_opt(pb, "snowfall_spread"),
        rain_spread=_opt(pb, "rain_spread"),
        dew_point_2m_spread=_opt(pb, "dew_point_2m_spread"),
        relative_humidity_2m_spread=_opt(pb, "relative_humidity_2m_spread"),
        surface_pressure_spread=_opt(pb, "surface_pressure_spread"),
        wind_direction_10m_spread=_opt(pb, "wind_direction_10m_spread"),
        wet_bulb_temperature_2m_spread=_opt(pb, "wet_bulb_temperature_2m_spread"),
        wind_speed_100m_spread=_opt(pb, "wind_speed_100m_spread"),
    )


def _to_domain_data(pb: weather_pb2.DomainDataUpdate) -> DomainData | None:
    """Convert a DomainDataUpdate; None when the payload is empty or of an unknown kind."""
    model_run = _optional_ts(pb.model_run)
    match pb.WhichOneof("data"):
        case "forecast":
            return ForecastDomainData(
                pb.location, model_run, [_to_forecast_sample(p) for p in pb.forecast.points], model=pb.model
            )
        case "air_quality":
            return AirQualityDomainData(
                pb.location, model_run, [_to_air_quality_sample(p) for p in pb.air_quality.points]
            )
        case "flood":
            return FloodDomainData(pb.location, model_run, [_to_flood_sample(p) for p in pb.flood.points])
        case "marine":
            return MarineDomainData(pb.location, model_run, [_to_marine_sample(p) for p in pb.marine.points])
        case "seasonal":
            return SeasonalDomainData(pb.location, model_run, [_to_seasonal_sample(p) for p in pb.seasonal.points])
        case "ensemble":
            return EnsembleDomainData(pb.location, model_run, [_to_ensemble_sample(p) for p in pb.ensemble.points])
    return None


def _to_budget_status(pb: ops_pb2.BudgetStatus) -> BudgetStatusData:
    return BudgetStatusData(
        monthly_limit=pb.monthly_limit,
        monthly_used=pb.monthly_used,
        daily_limit=pb.daily_limit,
        daily_used=pb.daily_used,
        usage_percent=pb.usage_percent,
    )


def _to_location_status(pb: ops_pb2.ModelStatus) -> LocationStatusData:
    return LocationStatusData(
        location=pb.location,
        phase=_POLL_PHASE_MAP.get(pb.phase, PollPhase.UNSPECIFIED),
        next_poll=_optional_ts(pb.next_poll),
        last_change=_ts_to_dt(pb.last_change) if pb.HasField("last_change") else None,
        miss_count=pb.miss_count,
        cycle_seconds=_opt(pb, "cycle_seconds"),
    )


def _to_server_status(pb: ops_pb2.StatusResponse) -> ServerStatusData:
    return ServerStatusData(
        version=pb.version,
        uptime_seconds=pb.uptime_seconds,
        budget=_to_budget_status(pb.budget) if pb.HasField("budget") else None,
        process_start=_optional_ts(pb.process_start),
        location_statuses=[_to_location_status(m) for m in pb.models],
        active_enrichments=list(pb.active_enrichments),
        budget_partial=pb.budget_partial,
        models_partial=pb.models_partial,
    )


def _to_target_data(pb: ops_pb2.TriggerTarget) -> TargetData:
    return TargetData(
        location=pb.location,
        phase=_POLL_PHASE_MAP.get(pb.phase, PollPhase.UNSPECIFIED),
        next_poll=_optional_ts(pb.next_poll),
        last_change=_ts_to_dt(pb.last_change) if pb.HasField("last_change") else None,
        miss_count=pb.miss_count,
        cycle_seconds=_opt(pb, "cycle_seconds"),
    )


_WRAPPER_FIELDS = {"alert", "score", "condition", "trend", "forecast"}


def _enum_text(field, number: int) -> str:
    """Lowercase wire text of an enum value without the enum-name prefix (UV_LEVEL_HIGH -> high)."""
    name = field.enum_type.values_by_number[number].name
    prefix = re.sub(r"(?<!^)(?=[A-Z])", "_", field.enum_type.name).upper() + "_"
    return (name[len(prefix) :] if name.startswith(prefix) else name).lower()


def _field_value(pb, field):
    """Native Python value of one proto field; None when an optional field is unset."""
    repeated = field.is_repeated if hasattr(field, "is_repeated") else field.label == field.LABEL_REPEATED
    if repeated:
        return [_scalar(field, item) for item in getattr(pb, field.name)]
    if field.type == field.TYPE_MESSAGE or getattr(field, "has_presence", False):
        if not pb.HasField(field.name):
            return None
    return _scalar(field, getattr(pb, field.name))


def _scalar(field, value):
    if field.type == field.TYPE_ENUM:
        return _enum_text(field, value)
    if field.type == field.TYPE_MESSAGE:
        if field.message_type.full_name == "google.protobuf.Timestamp":
            return _ts_to_dt(value)
        return _message_values(value)
    return value


def _message_values(pb, skip: frozenset[str] = frozenset()) -> dict:
    values = {}
    for field in pb.DESCRIPTOR.fields:
        if field.name in skip:
            continue
        value = _field_value(pb, field)
        if value is not None:
            values[field.name] = value
    return values


def _to_alert(alert_type: AlertType, pb: weather_pb2.AlertData) -> AlertData:
    return AlertData(
        type=alert_type,
        severity=_ALERT_SEVERITY_MAP.get(pb.severity, AlertSeverity.NONE),
        confidence=pb.confidence,
        trigger_value=pb.trigger_value,
        threshold=pb.threshold,
        peak_value=_opt(pb, "peak_value"),
        hours_until=_opt(pb, "hours_until"),
        duration_hours=_opt(pb, "duration_hours"),
    )


def _to_feature(pb: weather_pb2.EnrichmentEvent) -> FeatureData | None:
    """Convert an EnrichmentEvent; None for feature kinds this client does not know."""
    case = pb.WhichOneof("feature")
    if case is None:
        return None
    try:
        feature = Feature(case)
    except ValueError:
        return None
    payload = getattr(pb, case)
    alert = None
    score = None
    if (alert_type := alert_type_of(feature)) != AlertType.UNSPECIFIED:
        alert = _to_alert(alert_type, payload.alert)
    elif "score" in payload.DESCRIPTOR.fields_by_name:
        sc = payload.score
        score = ScoreData(
            score=sc.score,
            best_start=_optional_ts(sc.best_start),
            best_hours=sc.best_hours,
            windows=[_message_values(w) for w in getattr(sc, "windows", [])],
        )
    values = _message_values(payload, skip=frozenset(_WRAPPER_FIELDS))
    return FeatureData(
        location=pb.location,
        feature=feature,
        updated_at=_optional_ts(pb.updated_at),
        alert=alert,
        score=score,
        values=values,
    )


# --- Client ---


class NjordClient:
    """Async gRPC client for the njord weather service."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._channel: grpc.aio.Channel | None = None
        self._weather_stub: weather_pb2_grpc.WeatherServiceStub | None = None
        self._ops_stub: ops_pb2_grpc.OpsServiceStub | None = None

    async def connect(self) -> None:
        """Open an insecure gRPC channel to njord."""
        target = f"{self._host}:{self._port}"
        self._channel = grpc.aio.insecure_channel(target)
        self._weather_stub = weather_pb2_grpc.WeatherServiceStub(self._channel)
        self._ops_stub = ops_pb2_grpc.OpsServiceStub(self._channel)

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._weather_stub = None
            self._ops_stub = None

    async def __aenter__(self) -> NjordClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def _ensure_connected(self) -> None:
        if self._channel is None:
            raise RuntimeError("NjordClient is not connected. Call connect() first.")

    # --- Unary RPCs ---

    async def get_catalog(self) -> CatalogData:
        """Retrieve all locations and deduplicated model info."""
        self._ensure_connected()
        assert self._weather_stub is not None
        resp = await self._weather_stub.GetCatalog(weather_pb2.GetCatalogRequest())
        return _to_catalog_data(resp)

    async def get_domain_data(self, location: str, domain: Domain, model: str = "") -> DomainData | None:
        """Retrieve the current data of one domain for a location; None when the payload is empty.

        An empty model selects the primary weather model.
        """
        self._ensure_connected()
        assert self._weather_stub is not None
        pb_domain = _DOMAIN_TO_PB.get(domain)
        if pb_domain is None:
            raise ValueError(f"Domain {domain!r} cannot be requested")
        resp = await self._weather_stub.GetDomainData(
            weather_pb2.GetDomainDataRequest(location=location, domain=pb_domain, model=model)
        )
        return _to_domain_data(resp)

    async def get_status(self) -> ServerStatusData:
        """Retrieve njord's server status."""
        self._ensure_connected()
        assert self._ops_stub is not None
        resp = await self._ops_stub.GetStatus(ops_pb2.GetStatusRequest())
        return _to_server_status(resp)

    async def get_enrichments(self, location: str) -> list[FeatureData]:
        """Retrieve the current typed feature results of a location."""
        self._ensure_connected()
        assert self._weather_stub is not None
        resp = await self._weather_stub.GetEnrichments(weather_pb2.GetEnrichmentsRequest(location=location))
        return [f for e in resp.events if (f := _to_feature(e)) is not None]

    async def get_targets(self) -> list[TargetData]:
        """Retrieve all poll targets and their state."""
        self._ensure_connected()
        assert self._ops_stub is not None
        resp = await self._ops_stub.GetTargets(ops_pb2.GetTargetsRequest())
        return [_to_target_data(t) for t in resp.targets]

    async def trigger_poll(self, location: str = "") -> int:
        """Trigger a poll (all locations when empty) and return triggered_count."""
        self._ensure_connected()
        assert self._ops_stub is not None
        resp = await self._ops_stub.TriggerPoll(ops_pb2.TriggerPollRequest(location=location))
        return resp.triggered_count

    # --- Streaming RPCs ---

    async def stream_domain_data(
        self,
        location: str | None = None,
        domains: Iterable[Domain] = (),
        *,
        on_disconnect: Callable[[], None] | None = None,
        on_reconnect: Callable[[], None] | None = None,
    ) -> AsyncIterator[DomainData]:
        """Stream domain data updates with auto-reconnect; no domains means every domain."""
        self._ensure_connected()
        assert self._weather_stub is not None
        req = weather_pb2.StreamDomainDataRequest(
            location=location or "",
            domains=[_DOMAIN_TO_PB[d] for d in domains if d in _DOMAIN_TO_PB],
        )

        async for item in self._stream_with_reconnect(
            lambda: self._weather_stub.StreamDomainData(req),
            _to_domain_data,
            on_disconnect=on_disconnect,
            on_reconnect=on_reconnect,
        ):
            yield item

    async def stream_enrichments(
        self,
        location: str | None = None,
        *,
        on_disconnect: Callable[[], None] | None = None,
        on_reconnect: Callable[[], None] | None = None,
    ) -> AsyncIterator[FeatureData]:
        """Stream real-time typed feature results with auto-reconnect."""
        self._ensure_connected()
        assert self._weather_stub is not None
        req = weather_pb2.StreamEnrichmentsRequest(location=location or "")

        async for item in self._stream_with_reconnect(
            lambda: self._weather_stub.StreamEnrichments(req),
            _to_feature,
            on_disconnect=on_disconnect,
            on_reconnect=on_reconnect,
        ):
            yield item

    async def _stream_with_reconnect(
        self,
        call_factory: Callable[[], grpc.aio.UnaryStreamCall],
        converter: Callable[[object], T | None],
        *,
        on_disconnect: Callable[[], None] | None = None,
        on_reconnect: Callable[[], None] | None = None,
    ) -> AsyncIterator[T]:
        """Generic reconnecting stream wrapper with exponential backoff; skips messages the converter drops."""
        backoff = _BACKOFF_INITIAL
        connected = False

        while True:
            try:
                call = call_factory()
                if not connected and on_reconnect:
                    on_reconnect()
                    connected = True

                async for message in call:
                    backoff = _BACKOFF_INITIAL
                    converted = converter(message)
                    if converted is not None:
                        yield converted

                _LOGGER.debug("Stream ended normally, reconnecting in %.1fs", backoff)

            except grpc.aio.AioRpcError as err:
                if err.code() == grpc.StatusCode.CANCELLED:
                    return

                _LOGGER.warning(
                    "Stream disconnected (%s), reconnecting in %.1fs",
                    err.code(),
                    backoff,
                )
                if connected and on_disconnect:
                    on_disconnect()
                    connected = False

            await asyncio.sleep(backoff)
            backoff = min(backoff * _BACKOFF_FACTOR, _BACKOFF_MAX)
