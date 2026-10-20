"""gRPC client for communicating with the njord weather service."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Iterable
from datetime import UTC, datetime
from typing import TypeVar

import grpc

# Ensure proto package path is on sys.path before importing generated stubs.
from . import proto as _proto_pkg  # noqa: F401
from .const import AlertSeverity, AlertType, Domain, PollPhase
from .models import (
    AirQualityDomainData,
    AirQualitySampleData,
    AlertData,
    BudgetStatusData,
    CatalogData,
    DomainData,
    EnrichmentData,
    FloodDomainData,
    FloodSampleData,
    LifestyleData,
    LocationStatusData,
    MarineDomainData,
    MarineSampleData,
    ModelInfoData,
    NjordLocation,
    ServerStatusData,
    SolarDomainData,
    SolarSampleData,
    TargetData,
    WeatherDomainData,
    WeatherSampleData,
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
    Domain.WEATHER: weather_pb2.DOMAIN_WEATHER,
    Domain.AIR_QUALITY: weather_pb2.DOMAIN_AIR_QUALITY,
    Domain.FLOOD: weather_pb2.DOMAIN_FLOOD,
    Domain.SOLAR: weather_pb2.DOMAIN_SOLAR,
    Domain.MARINE: weather_pb2.DOMAIN_MARINE,
}

_POLL_PHASE_MAP: dict[int, PollPhase] = {
    ops_pb2.POLL_PHASE_UNSPECIFIED: PollPhase.UNSPECIFIED,
    ops_pb2.POLL_PHASE_DISCOVERY: PollPhase.DISCOVERY,
    ops_pb2.POLL_PHASE_STEADY: PollPhase.STEADY,
}

_ALERT_TYPE_MAP: dict[int, AlertType] = {
    common_pb2.ALERT_TYPE_UNSPECIFIED: AlertType.UNSPECIFIED,
    common_pb2.ALERT_TYPE_FROST: AlertType.FROST,
    common_pb2.ALERT_TYPE_HEAT: AlertType.HEAT,
    common_pb2.ALERT_TYPE_STORM: AlertType.STORM,
    common_pb2.ALERT_TYPE_HEAVY_RAIN: AlertType.HEAVY_RAIN,
    common_pb2.ALERT_TYPE_UV: AlertType.UV,
    common_pb2.ALERT_TYPE_FOG: AlertType.FOG,
    common_pb2.ALERT_TYPE_SNOW: AlertType.SNOW,
    common_pb2.ALERT_TYPE_PRESSURE_DROP: AlertType.PRESSURE_DROP,
    common_pb2.ALERT_TYPE_THUNDERSTORM: AlertType.THUNDERSTORM,
    common_pb2.ALERT_TYPE_ICE: AlertType.ICE,
    common_pb2.ALERT_TYPE_WIND_CHILL: AlertType.WIND_CHILL,
    common_pb2.ALERT_TYPE_VISIBILITY: AlertType.VISIBILITY,
    common_pb2.ALERT_TYPE_TROPICAL_NIGHT: AlertType.TROPICAL_NIGHT,
    common_pb2.ALERT_TYPE_HUMIDITY: AlertType.HUMIDITY,
    common_pb2.ALERT_TYPE_POLLEN: AlertType.POLLEN,
    common_pb2.ALERT_TYPE_PM25: AlertType.PM25,
    common_pb2.ALERT_TYPE_FLOOD_RISK: AlertType.FLOOD_RISK,
    common_pb2.ALERT_TYPE_FLOOD_RAIN: AlertType.FLOOD_RAIN,
    common_pb2.ALERT_TYPE_SWIMMING_CONDITIONS: AlertType.SWIMMING_CONDITIONS,
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
    )


def _to_location(pb: common_pb2.LocationInfo) -> NjordLocation:
    return NjordLocation(name=pb.name, latitude=pb.latitude, longitude=pb.longitude, models=list(pb.models))


def _to_catalog_data(pb: weather_pb2.GetCatalogResponse) -> CatalogData:
    return CatalogData(
        locations=[_to_location(loc) for loc in pb.locations],
        model_info={info.id: _to_model_info(info) for info in pb.models},
    )


def _to_weather_sample(pb: weather_pb2.WeatherSample) -> WeatherSampleData:
    return WeatherSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        temperature=pb.temperature,
        apparent_temperature=pb.apparent_temperature,
        wind_speed=pb.wind_speed,
        precipitation=pb.precipitation,
        precipitation_probability=pb.precipitation_probability,
        cloud_cover=pb.cloud_cover,
        pressure=pb.pressure,
        weather_code=pb.weather_code,
        humidity=pb.humidity,
        dew_point=pb.dew_point,
        uv_index=pb.uv_index,
        ensemble_std_dev=_opt(pb, "ensemble_std_dev"),
        wind_gusts=_opt(pb, "wind_gusts"),
        visibility=_opt(pb, "visibility"),
        cape=_opt(pb, "cape"),
        rain=_opt(pb, "rain"),
        snowfall=_opt(pb, "snowfall"),
        soil_temperature=_opt(pb, "soil_temperature"),
        freezing_level_height=_opt(pb, "freezing_level_height"),
        is_day=_opt(pb, "is_day"),
    )


def _to_air_quality_sample(pb: weather_pb2.AirQualitySample) -> AirQualitySampleData:
    return AirQualitySampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        pm25=pb.pm25,
        pm10=pb.pm10,
        ozone=pb.ozone,
        birch_pollen=_opt(pb, "birch_pollen"),
        grass_pollen=_opt(pb, "grass_pollen"),
        alder=_opt(pb, "alder"),
        mugwort=_opt(pb, "mugwort"),
    )


def _to_flood_sample(pb: weather_pb2.FloodSample) -> FloodSampleData:
    return FloodSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        discharge=pb.discharge,
        discharge_mean=_opt(pb, "discharge_mean"),
        discharge_median=_opt(pb, "discharge_median"),
        discharge_max=_opt(pb, "discharge_max"),
        discharge_min=_opt(pb, "discharge_min"),
        discharge_p25=_opt(pb, "discharge_p25"),
        discharge_p75=_opt(pb, "discharge_p75"),
    )


def _to_solar_sample(pb: weather_pb2.SolarSample) -> SolarSampleData:
    return SolarSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        direct_radiation=pb.direct_radiation,
        diffuse_radiation=pb.diffuse_radiation,
        shortwave_radiation=pb.shortwave_radiation,
        sunshine_duration=pb.sunshine_duration,
    )


def _to_marine_sample(pb: weather_pb2.MarineSample) -> MarineSampleData:
    return MarineSampleData(
        valid_at=_ts_to_dt(pb.valid_at),
        wave_height=pb.wave_height,
        wave_period=pb.wave_period,
        wave_direction=pb.wave_direction,
        water_temperature=_opt(pb, "water_temperature"),
    )


def _to_domain_data(pb: weather_pb2.DomainDataUpdate) -> DomainData | None:
    """Convert a DomainDataUpdate; None when the payload is empty or of an unknown kind."""
    model_run = _optional_ts(pb.model_run)
    match pb.WhichOneof("data"):
        case "weather":
            return WeatherDomainData(pb.location, model_run, [_to_weather_sample(p) for p in pb.weather.points])
        case "air_quality":
            return AirQualityDomainData(
                pb.location, model_run, [_to_air_quality_sample(p) for p in pb.air_quality.points]
            )
        case "flood":
            return FloodDomainData(pb.location, model_run, [_to_flood_sample(p) for p in pb.flood.points])
        case "solar":
            return SolarDomainData(pb.location, model_run, [_to_solar_sample(p) for p in pb.solar.points])
        case "marine":
            return MarineDomainData(pb.location, model_run, [_to_marine_sample(p) for p in pb.marine.points])
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


def _to_alert(pb: common_pb2.Alert) -> AlertData:
    return AlertData(
        type=_ALERT_TYPE_MAP.get(pb.type, AlertType.UNSPECIFIED),
        severity=_ALERT_SEVERITY_MAP.get(pb.severity, AlertSeverity.NONE),
        confidence=pb.confidence,
        trigger_value=pb.trigger_value,
        threshold=pb.threshold,
        peak_value=_opt(pb, "peak_value"),
        hours_until=_opt(pb, "hours_until"),
        duration_hours=_opt(pb, "duration_hours"),
    )


def _to_lifestyle(pb: weather_pb2.LifestyleUpdate, location: str, updated_at: datetime | None) -> LifestyleData:
    return LifestyleData(type=pb.type, location=location, data=dict(pb.data), updated_at=updated_at)


def _to_enrichment_data(pb: weather_pb2.GetEnrichmentsResponse) -> EnrichmentData:
    now = datetime.now(UTC)
    return EnrichmentData(
        location=pb.location,
        alerts=[_to_alert(a) for a in pb.alerts.alerts],
        updated_at=now,
        lifestyle=[_to_lifestyle(item, pb.location, now) for item in pb.lifestyle],
    )


def _to_enrichment_event(pb: weather_pb2.EnrichmentEvent) -> EnrichmentData | LifestyleData | None:
    """Convert an EnrichmentEvent; None for payload kinds this client does not know."""
    match pb.WhichOneof("payload"):
        case "alerts":
            return EnrichmentData(
                location=pb.location,
                alerts=[_to_alert(a) for a in pb.alerts.alerts],
                updated_at=_optional_ts(pb.updated_at),
            )
        case "lifestyle":
            return _to_lifestyle(pb.lifestyle, pb.location, _optional_ts(pb.updated_at))
    return None


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

    async def get_domain_data(self, location: str, domain: Domain) -> DomainData | None:
        """Retrieve the current data of one domain for a location; None when the payload is empty."""
        self._ensure_connected()
        assert self._weather_stub is not None
        pb_domain = _DOMAIN_TO_PB.get(domain)
        if pb_domain is None:
            raise ValueError(f"Domain {domain!r} cannot be requested")
        resp = await self._weather_stub.GetDomainData(
            weather_pb2.GetDomainDataRequest(location=location, domain=pb_domain)
        )
        return _to_domain_data(resp)

    async def get_status(self) -> ServerStatusData:
        """Retrieve njord's server status."""
        self._ensure_connected()
        assert self._ops_stub is not None
        resp = await self._ops_stub.GetStatus(ops_pb2.GetStatusRequest())
        return _to_server_status(resp)

    async def get_enrichments(self, location: str) -> EnrichmentData:
        """Retrieve enrichment data (alerts and lifestyle advisories) for a location."""
        self._ensure_connected()
        assert self._weather_stub is not None
        resp = await self._weather_stub.GetEnrichments(weather_pb2.GetEnrichmentsRequest(location=location))
        return _to_enrichment_data(resp)

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
    ) -> AsyncIterator[EnrichmentData | LifestyleData]:
        """Stream real-time enrichment updates (alerts of a location or one lifestyle advisory) with auto-reconnect."""
        self._ensure_connected()
        assert self._weather_stub is not None
        req = weather_pb2.StreamEnrichmentsRequest(location=location or "")

        async for item in self._stream_with_reconnect(
            lambda: self._weather_stub.StreamEnrichments(req),
            _to_enrichment_event,
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
