"""gRPC client for communicating with the njord weather service."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from typing import TypeVar

import grpc

# Ensure proto package path is on sys.path before importing generated stubs.
from . import proto as _proto_pkg  # noqa: F401
from .models import (
    AlertData,
    BudgetStatusData,
    ConsensusData,
    CopOptimalHourData,
    DailyForecastData,
    DerivedData,
    EnergyData,
    EnrichmentData,
    ForecastData,
    HistoryData,
    HorizonConsensusData,
    HorizonDerivedData,
    HourlyForecastData,
    IndexData,
    ModelMetricsData,
    NjordConfigData,
    NjordLocation,
    ParameterConsensusData,
    ParameterTrendData,
    ServerStatusData,
    TrendData,
)
from .proto.njord.v1 import config_service_pb2, config_service_pb2_grpc, forecast_service_pb2, forecast_service_pb2_grpc

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

_BACKOFF_INITIAL = 1.0
_BACKOFF_MAX = 60.0
_BACKOFF_FACTOR = 2.0


# --- Protobuf to dataclass converters ---


def _parse_extra(pb_extra) -> dict[str, float | str | bool]:
    result: dict[str, float | str | bool] = {}
    for pv in pb_extra:
        field = pv.WhichOneof("value")
        if field == "numeric":
            result[pv.name] = pv.numeric
        elif field == "text":
            result[pv.name] = pv.text
        elif field == "flag":
            result[pv.name] = pv.flag
    return result


def _to_hourly(pb: forecast_service_pb2.HourlyForecast) -> HourlyForecastData:
    return HourlyForecastData(
        timestamp=datetime.fromtimestamp(pb.timestamp, tz=UTC),
        temperature=pb.temperature if pb.HasField("temperature") else None,
        apparent_temperature=pb.apparent_temperature if pb.HasField("apparent_temperature") else None,
        precipitation=pb.precipitation if pb.HasField("precipitation") else None,
        humidity=pb.humidity if pb.HasField("humidity") else None,
        wind_speed=pb.wind_speed if pb.HasField("wind_speed") else None,
        wind_bearing=pb.wind_bearing if pb.HasField("wind_bearing") else None,
        cloud_cover=pb.cloud_cover if pb.HasField("cloud_cover") else None,
        weather_code=pb.weather_code if pb.HasField("weather_code") else None,
        is_day=pb.is_day if pb.HasField("is_day") else None,
        rain=pb.rain if pb.HasField("rain") else None,
        wind_gusts=pb.wind_gusts if pb.HasField("wind_gusts") else None,
        pressure_msl=pb.pressure_msl if pb.HasField("pressure_msl") else None,
        extra=_parse_extra(pb.extra),
    )


def _to_daily(pb: forecast_service_pb2.DailyForecast) -> DailyForecastData:
    return DailyForecastData(
        date=pb.date,
        temperature_max=pb.temperature_max if pb.HasField("temperature_max") else None,
        temperature_min=pb.temperature_min if pb.HasField("temperature_min") else None,
        precipitation_sum=pb.precipitation_sum if pb.HasField("precipitation_sum") else None,
        wind_speed_max=pb.wind_speed_max if pb.HasField("wind_speed_max") else None,
        wind_gusts_max=pb.wind_gusts_max if pb.HasField("wind_gusts_max") else None,
        sunrise=pb.sunrise or None,
        sunset=pb.sunset or None,
        weather_code=pb.weather_code if pb.HasField("weather_code") else None,
        extra=_parse_extra(pb.extra),
    )


def _to_forecast_data(
    pb: forecast_service_pb2.GetForecastResponse | forecast_service_pb2.ForecastUpdate,
) -> ForecastData:
    return ForecastData(
        location=pb.location,
        model=pb.model,
        updated_at=pb.updated_at,
        hourly=[_to_hourly(h) for h in pb.hourly],
        daily=[_to_daily(d) for d in pb.daily],
    )


def _to_location(pb: config_service_pb2.LocationConfig) -> NjordLocation:
    return NjordLocation(
        name=pb.name,
        latitude=pb.latitude,
        longitude=pb.longitude,
        models=list(pb.models),
    )


def _to_config_data(pb: config_service_pb2.NjordConfig) -> NjordConfigData:
    return NjordConfigData(
        locations=[_to_location(loc) for loc in pb.locations],
        default_models=list(pb.default_models),
        horizons=list(pb.horizons),
        forecast_days=pb.forecast_days,
        poll_interval_seconds=pb.poll_interval_seconds,
    )


def _to_budget_status(pb: config_service_pb2.BudgetStatus) -> BudgetStatusData:
    return BudgetStatusData(
        monthly_limit=pb.monthly_limit,
        monthly_used=pb.monthly_used,
        daily_limit=pb.daily_limit,
        daily_used=pb.daily_used,
        usage_percent=pb.usage_percent,
    )


def _to_server_status(pb: config_service_pb2.ServerStatus) -> ServerStatusData:
    return ServerStatusData(
        version=pb.version,
        uptime_seconds=pb.uptime_seconds,
        budget=_to_budget_status(pb.budget) if pb.HasField("budget") else None,
    )


# --- Enrichment protobuf converters ---

_ALERT_TYPE_MAP: dict[int, str] = {
    0: "unspecified",
    1: "frost",
    2: "heat",
    3: "storm",
    4: "heavy_rain",
    5: "uv",
    6: "fog",
    7: "snow",
    8: "pressure_drop",
    9: "thunderstorm",
}

_ALERT_SEVERITY_MAP: dict[int, str] = {
    0: "none",
    1: "yellow",
    2: "orange",
    3: "red",
}


def _to_alert(pb: forecast_service_pb2.Alert) -> AlertData:
    return AlertData(
        type=_ALERT_TYPE_MAP.get(pb.type, "unspecified"),
        severity=_ALERT_SEVERITY_MAP.get(pb.severity, "none"),
        confidence=pb.confidence,
        trigger_value=pb.trigger_value,
        threshold=pb.threshold,
        peak_value=pb.peak_value if pb.HasField("peak_value") else None,
        hours_until=pb.hours_until if pb.HasField("hours_until") else None,
        duration_hours=pb.duration_hours if pb.HasField("duration_hours") else None,
    )


def _to_index_data(pb: forecast_service_pb2.IndexUpdate) -> IndexData:
    return IndexData(
        laundry=pb.laundry,
        outdoor=pb.outdoor,
        running=pb.running,
        cycling=pb.cycling,
        bbq=pb.bbq,
        irrigation=pb.irrigation,
        solar=pb.solar,
        ventilation=pb.ventilation,
        hdd=pb.hdd,
        cdd=pb.cdd,
        frost_hours=pb.frost_hours if pb.HasField("frost_hours") else None,
        frost_confidence=pb.frost_confidence if pb.HasField("frost_confidence") else None,
        vpd_kpa=pb.vpd_kpa if pb.HasField("vpd_kpa") else None,
        vpd_category=pb.vpd_category if pb.HasField("vpd_category") else None,
    )


def _to_parameter_trend(pb: forecast_service_pb2.ParameterTrend) -> ParameterTrendData:
    return ParameterTrendData(
        parameter=pb.parameter,
        direction=pb.direction,
        delta=pb.delta,
    )


def _to_trend_data(pb: forecast_service_pb2.TrendUpdate) -> TrendData:
    return TrendData(
        parameter_trends=[_to_parameter_trend(t) for t in pb.parameter_trends],
        weather_change_description=pb.weather_change_description if pb.HasField("weather_change_description") else None,
        precip_starts_in_hours=pb.precip_starts_in_hours if pb.HasField("precip_starts_in_hours") else None,
        precip_ends_in_hours=pb.precip_ends_in_hours if pb.HasField("precip_ends_in_hours") else None,
        temp_max_in_hours=pb.temp_max_in_hours if pb.HasField("temp_max_in_hours") else None,
        temp_min_in_hours=pb.temp_min_in_hours if pb.HasField("temp_min_in_hours") else None,
        stability_label=pb.stability_label if pb.HasField("stability_label") else None,
        stability_ratio=pb.stability_ratio if pb.HasField("stability_ratio") else None,
        decay_rate=pb.decay_rate if pb.HasField("decay_rate") else None,
        reliable_hours=pb.reliable_hours if pb.HasField("reliable_hours") else None,
    )


def _to_cop_optimal_hour(pb: forecast_service_pb2.CopOptimalHour) -> CopOptimalHourData:
    return CopOptimalHourData(
        hours_from_now=pb.hours_from_now,
        cop=pb.cop,
    )


def _to_energy_data(pb: forecast_service_pb2.EnergyUpdate) -> EnergyData:
    return EnergyData(
        heating_demand=pb.heating_demand,
        cop_estimate=pb.cop_estimate if pb.HasField("cop_estimate") else None,
        shading=pb.shading,
        battery_strategy=pb.battery_strategy,
        night_cooling=pb.night_cooling,
        cop_optimal=[_to_cop_optimal_hour(c) for c in pb.cop_optimal],
    )


def _to_horizon_derived(pb: forecast_service_pb2.HorizonDerived) -> HorizonDerivedData:
    return HorizonDerivedData(
        horizon=pb.horizon,
        beaufort=pb.beaufort if pb.HasField("beaufort") else None,
        wind_chill=pb.wind_chill if pb.HasField("wind_chill") else None,
        dewpoint_comfort=pb.dewpoint_comfort if pb.HasField("dewpoint_comfort") else None,
        wmo_description=pb.wmo_description if pb.HasField("wmo_description") else None,
    )


def _to_derived_data(pb: forecast_service_pb2.DerivedUpdate) -> DerivedData:
    scalars = pb.scalars if pb.HasField("scalars") else None
    return DerivedData(
        by_horizon=[_to_horizon_derived(h) for h in pb.by_horizon],
        diurnal_amplitude=scalars.diurnal_amplitude if scalars and scalars.HasField("diurnal_amplitude") else None,
        sunshine_pct=scalars.sunshine_pct if scalars and scalars.HasField("sunshine_pct") else None,
        inversion=scalars.inversion if scalars and scalars.HasField("inversion") else None,
    )


def _to_model_metrics(pb: forecast_service_pb2.ModelMetrics) -> ModelMetricsData:
    return ModelMetricsData(
        model=pb.model,
        mae_7d=pb.mae_7d if pb.HasField("mae_7d") else None,
        mae_30d=pb.mae_30d if pb.HasField("mae_30d") else None,
        weight=pb.weight,
        drift=pb.drift if pb.HasField("drift") else None,
    )


def _to_history_data(pb: forecast_service_pb2.HistoryUpdate) -> HistoryData:
    return HistoryData(
        models=[_to_model_metrics(m) for m in pb.models],
        seasonal_best=pb.seasonal_best if pb.HasField("seasonal_best") else None,
        anomaly=pb.anomaly if pb.HasField("anomaly") else None,
        anomaly_deviation=pb.anomaly_deviation if pb.HasField("anomaly_deviation") else None,
        weighted_temperature=pb.weighted_temperature if pb.HasField("weighted_temperature") else None,
    )


def _to_horizon_consensus(pb: forecast_service_pb2.HorizonConsensus) -> HorizonConsensusData:
    return HorizonConsensusData(
        horizon=pb.horizon,
        median=pb.median if pb.HasField("median") else None,
        trimmed_mean=pb.trimmed_mean if pb.HasField("trimmed_mean") else None,
        spread=pb.spread if pb.HasField("spread") else None,
        iqr=pb.iqr if pb.HasField("iqr") else None,
        agreement=pb.agreement if pb.HasField("agreement") else None,
        available_models=pb.available_models,
    )


def _to_parameter_consensus(pb: forecast_service_pb2.ParameterConsensus) -> ParameterConsensusData:
    return ParameterConsensusData(
        parameter=pb.parameter,
        unit=pb.unit,
        by_horizon=[_to_horizon_consensus(h) for h in pb.by_horizon],
    )


def _to_consensus_data(pb: forecast_service_pb2.ConsensusUpdate) -> ConsensusData:
    return ConsensusData(
        parameters=[_to_parameter_consensus(p) for p in pb.parameters],
    )


def _to_enrichment_data(pb: forecast_service_pb2.GetEnrichmentsResponse) -> EnrichmentData:
    return EnrichmentData(
        location=pb.location,
        alerts=[_to_alert(a) for a in pb.alerts.alerts] if pb.HasField("alerts") else [],
        indices=_to_index_data(pb.indices) if pb.HasField("indices") else None,
        trends=_to_trend_data(pb.trends) if pb.HasField("trends") else None,
        energy=_to_energy_data(pb.energy) if pb.HasField("energy") else None,
        derived=_to_derived_data(pb.derived) if pb.HasField("derived") else None,
        history=_to_history_data(pb.history) if pb.HasField("history") else None,
        consensus=_to_consensus_data(pb.consensus) if pb.HasField("consensus") else None,
    )


def _to_enrichment_event(pb: forecast_service_pb2.EnrichmentEvent) -> EnrichmentData:
    payload_field = pb.WhichOneof("payload")
    alerts = []
    indices = trends = energy = derived = history = consensus = None
    if payload_field == "alerts":
        alerts = [_to_alert(a) for a in pb.alerts.alerts]
    elif payload_field == "indices":
        indices = _to_index_data(pb.indices)
    elif payload_field == "trends":
        trends = _to_trend_data(pb.trends)
    elif payload_field == "energy":
        energy = _to_energy_data(pb.energy)
    elif payload_field == "derived":
        derived = _to_derived_data(pb.derived)
    elif payload_field == "history":
        history = _to_history_data(pb.history)
    elif payload_field == "consensus":
        consensus = _to_consensus_data(pb.consensus)
    return EnrichmentData(
        location=pb.location,
        alerts=alerts,
        indices=indices,
        trends=trends,
        energy=energy,
        derived=derived,
        history=history,
        consensus=consensus,
    )


# --- Client ---


class NjordClient:
    """Async gRPC client for the njord weather service."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._channel: grpc.aio.Channel | None = None
        self._forecast_stub: forecast_service_pb2_grpc.ForecastServiceStub | None = None
        self._config_stub: config_service_pb2_grpc.ConfigServiceStub | None = None

    async def connect(self) -> None:
        """Open an insecure gRPC channel to njord."""
        target = f"{self._host}:{self._port}"
        self._channel = grpc.aio.insecure_channel(target)
        self._forecast_stub = forecast_service_pb2_grpc.ForecastServiceStub(self._channel)
        self._config_stub = config_service_pb2_grpc.ConfigServiceStub(self._channel)

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._forecast_stub = None
            self._config_stub = None

    async def __aenter__(self) -> NjordClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def _ensure_connected(self) -> None:
        if self._channel is None:
            raise RuntimeError("NjordClient is not connected. Call connect() first.")

    # --- Unary RPCs ---

    async def get_locations(self) -> list[str]:
        """Retrieve all configured location names."""
        self._ensure_connected()
        assert self._forecast_stub is not None
        resp = await self._forecast_stub.GetLocations(forecast_service_pb2.GetLocationsRequest())
        return list(resp.locations)

    async def get_models(self, location: str) -> list[str]:
        """Retrieve available weather models for a location."""
        self._ensure_connected()
        assert self._forecast_stub is not None
        resp = await self._forecast_stub.GetModels(forecast_service_pb2.GetModelsRequest(location=location))
        return list(resp.models)

    async def get_forecast(self, location: str, model: str) -> ForecastData:
        """Retrieve the current forecast for a location and model."""
        self._ensure_connected()
        assert self._forecast_stub is not None
        resp = await self._forecast_stub.GetForecast(
            forecast_service_pb2.GetForecastRequest(location=location, model=model)
        )
        return _to_forecast_data(resp)

    async def get_config(self) -> NjordConfigData:
        """Retrieve njord's current configuration."""
        self._ensure_connected()
        assert self._config_stub is not None
        resp = await self._config_stub.GetConfig(config_service_pb2.GetConfigRequest())
        return _to_config_data(resp)

    async def get_status(self) -> ServerStatusData:
        """Retrieve njord's server status."""
        self._ensure_connected()
        assert self._config_stub is not None
        resp = await self._config_stub.GetStatus(config_service_pb2.GetStatusRequest())
        return _to_server_status(resp)

    async def get_enrichments(self, location: str) -> EnrichmentData:
        """Retrieve enrichment data for a location."""
        self._ensure_connected()
        assert self._forecast_stub is not None
        resp = await self._forecast_stub.GetEnrichments(forecast_service_pb2.GetEnrichmentsRequest(location=location))
        return _to_enrichment_data(resp)

    # --- Streaming RPCs ---

    async def stream_forecasts(
        self,
        location: str | None = None,
        *,
        on_disconnect: Callable[[], None] | None = None,
        on_reconnect: Callable[[], None] | None = None,
    ) -> AsyncIterator[ForecastData]:
        """Stream real-time forecast updates with auto-reconnect."""
        self._ensure_connected()
        assert self._forecast_stub is not None
        req = forecast_service_pb2.StreamForecastsRequest(location=location or "")

        async for item in self._stream_with_reconnect(
            lambda: self._forecast_stub.StreamForecasts(req),
            _to_forecast_data,
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
    ) -> AsyncIterator[EnrichmentData]:
        """Stream real-time enrichment updates with auto-reconnect."""
        self._ensure_connected()
        assert self._forecast_stub is not None
        req = forecast_service_pb2.StreamEnrichmentsRequest(location=location or "")

        async for item in self._stream_with_reconnect(
            lambda: self._forecast_stub.StreamEnrichments(req),
            _to_enrichment_event,
            on_disconnect=on_disconnect,
            on_reconnect=on_reconnect,
        ):
            yield item

    async def stream_config(
        self,
        *,
        on_disconnect: Callable[[], None] | None = None,
        on_reconnect: Callable[[], None] | None = None,
    ) -> AsyncIterator[NjordConfigData]:
        """Stream real-time config change notifications with auto-reconnect."""
        self._ensure_connected()
        assert self._config_stub is not None
        req = config_service_pb2.StreamConfigRequest()

        async for item in self._stream_with_reconnect(
            lambda: self._config_stub.StreamConfig(req),
            _to_config_data,
            on_disconnect=on_disconnect,
            on_reconnect=on_reconnect,
        ):
            yield item

    async def _stream_with_reconnect(
        self,
        call_factory: Callable[[], grpc.aio.UnaryStreamCall],
        converter: Callable[[object], T],
        *,
        on_disconnect: Callable[[], None] | None = None,
        on_reconnect: Callable[[], None] | None = None,
    ) -> AsyncIterator[T]:
        """Generic reconnecting stream wrapper with exponential backoff."""
        backoff = _BACKOFF_INITIAL
        first_connect = True

        while True:
            try:
                call = call_factory()
                if not first_connect and on_reconnect:
                    on_reconnect()
                first_connect = False

                async for message in call:
                    backoff = _BACKOFF_INITIAL
                    yield converter(message)

                return

            except grpc.aio.AioRpcError as err:
                if err.code() == grpc.StatusCode.CANCELLED:
                    return

                _LOGGER.warning(
                    "Stream disconnected (%s), reconnecting in %.1fs",
                    err.code(),
                    backoff,
                )
                if on_disconnect:
                    on_disconnect()

                await asyncio.sleep(backoff)
                backoff = min(backoff * _BACKOFF_FACTOR, _BACKOFF_MAX)
