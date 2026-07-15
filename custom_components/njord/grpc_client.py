"""gRPC client for communicating with the njord weather service."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone
from typing import TypeVar

import grpc

from .models import (
    BudgetStatusData,
    DailyForecastData,
    ForecastData,
    HourlyForecastData,
    NjordConfigData,
    NjordLocation,
    ServerStatusData,
)

# Ensure proto package path is on sys.path before importing generated stubs.
from . import proto as _proto_pkg  # noqa: F401
from .proto.njord.v1 import config_service_pb2, config_service_pb2_grpc
from .proto.njord.v1 import forecast_service_pb2, forecast_service_pb2_grpc

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

_BACKOFF_INITIAL = 1.0
_BACKOFF_MAX = 60.0
_BACKOFF_FACTOR = 2.0


# --- Protobuf to dataclass converters ---


def _to_hourly(pb: forecast_service_pb2.HourlyForecast) -> HourlyForecastData:
    return HourlyForecastData(
        timestamp=datetime.fromtimestamp(pb.timestamp, tz=timezone.utc),
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
    )


def _to_forecast_data(pb: forecast_service_pb2.GetForecastResponse | forecast_service_pb2.ForecastUpdate) -> ForecastData:
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
        resp = await self._forecast_stub.GetLocations(
            forecast_service_pb2.GetLocationsRequest()
        )
        return list(resp.locations)

    async def get_models(self, location: str) -> list[str]:
        """Retrieve available weather models for a location."""
        self._ensure_connected()
        assert self._forecast_stub is not None
        resp = await self._forecast_stub.GetModels(
            forecast_service_pb2.GetModelsRequest(location=location)
        )
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
        resp = await self._config_stub.GetConfig(
            config_service_pb2.GetConfigRequest()
        )
        return _to_config_data(resp)

    async def get_status(self) -> ServerStatusData:
        """Retrieve njord's server status."""
        self._ensure_connected()
        assert self._config_stub is not None
        resp = await self._config_stub.GetStatus(
            config_service_pb2.GetStatusRequest()
        )
        return _to_server_status(resp)

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
        req = forecast_service_pb2.StreamForecastsRequest(
            location=location or ""
        )

        async for item in self._stream_with_reconnect(
            lambda: self._forecast_stub.StreamForecasts(req),
            _to_forecast_data,
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
