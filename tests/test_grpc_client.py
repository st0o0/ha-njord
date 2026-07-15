"""Tests for NjordClient against a mock gRPC server."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock

import grpc
import pytest

from custom_components.njord.proto.njord.v1 import (
    config_service_pb2,
    config_service_pb2_grpc,
    forecast_service_pb2,
    forecast_service_pb2_grpc,
)
from custom_components.njord.grpc_client import (
    NjordClient,
    _BACKOFF_INITIAL,
)
from custom_components.njord.models import (
    ForecastData,
    NjordConfigData,
    ServerStatusData,
)


# --- Mock Servicers ---


class MockForecastServicer(forecast_service_pb2_grpc.ForecastServiceServicer):
    def __init__(self) -> None:
        self.stream_call_count = 0
        self.fail_stream_on_call: int | None = None

    async def GetLocations(self, request, context):
        return forecast_service_pb2.GetLocationsResponse(
            locations=["lucerne", "zurich"]
        )

    async def GetModels(self, request, context):
        return forecast_service_pb2.GetModelsResponse(
            location=request.location,
            models=["icon_d2", "ecmwf_ifs025"],
        )

    async def GetForecast(self, request, context):
        return forecast_service_pb2.GetForecastResponse(
            location=request.location,
            model=request.model,
            updated_at=1720000000,
            hourly=[
                forecast_service_pb2.HourlyForecast(
                    timestamp=1720000000,
                    temperature=22.5,
                    weather_code=3,
                    is_day=True,
                ),
            ],
            daily=[
                forecast_service_pb2.DailyForecast(
                    date="2026-07-15",
                    temperature_max=28.0,
                    temperature_min=15.0,
                    weather_code=2,
                ),
            ],
        )

    async def GetEnrichments(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)

    async def StreamForecasts(self, request, context):
        self.stream_call_count += 1
        if self.fail_stream_on_call == self.stream_call_count:
            await context.abort(grpc.StatusCode.UNAVAILABLE, "simulated disconnect")
            return
        for i in range(3):
            yield forecast_service_pb2.ForecastUpdate(
                location=request.location or "lucerne",
                model="icon_d2",
                updated_at=1720000000 + i,
                hourly=[],
                daily=[],
            )

    async def StreamEnrichments(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)


class MockConfigServicer(config_service_pb2_grpc.ConfigServiceServicer):
    def __init__(self) -> None:
        self.stream_call_count = 0

    async def GetConfig(self, request, context):
        return config_service_pb2.NjordConfig(
            locations=[
                config_service_pb2.LocationConfig(
                    name="lucerne",
                    latitude=47.05,
                    longitude=8.31,
                    models=["icon_d2"],
                ),
            ],
            default_models=["icon_d2", "ecmwf_ifs025"],
            horizons=[1, 3, 6],
            forecast_days=7,
            poll_interval_seconds=300,
        )

    async def StreamConfig(self, request, context):
        self.stream_call_count += 1
        for i in range(2):
            yield config_service_pb2.NjordConfig(
                locations=[
                    config_service_pb2.LocationConfig(
                        name="lucerne",
                        latitude=47.05,
                        longitude=8.31,
                        models=["icon_d2"],
                    ),
                ],
                default_models=["icon_d2"],
                horizons=[1, 3],
                forecast_days=7 + i,
                poll_interval_seconds=300,
            )

    async def GetStatus(self, request, context):
        return config_service_pb2.ServerStatus(
            version="1.2.3",
            uptime_seconds=3600,
            budget=config_service_pb2.BudgetStatus(
                monthly_limit=20000,
                monthly_used=5000,
                daily_limit=700,
                daily_used=100,
                usage_percent=25.0,
            ),
        )

    async def AddLocation(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)

    async def RemoveLocation(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)

    async def UpdateLocation(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)

    async def UpdateForecastSettings(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)

    async def UpdateEnrichmentConfig(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)

    async def UpdateBudget(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)


# --- Fixtures ---


@pytest.fixture()
async def mock_server():
    """Start a mock gRPC server and return (port, forecast_servicer, config_servicer)."""
    forecast_servicer = MockForecastServicer()
    config_servicer = MockConfigServicer()
    server = grpc.aio.server()
    forecast_service_pb2_grpc.add_ForecastServiceServicer_to_server(
        forecast_servicer, server
    )
    config_service_pb2_grpc.add_ConfigServiceServicer_to_server(
        config_servicer, server
    )
    port = server.add_insecure_port("[::]:0")
    await server.start()
    yield port, forecast_servicer, config_servicer
    await server.stop(grace=0)


@pytest.fixture()
async def client(mock_server):
    """Create a connected NjordClient pointing at the mock server."""
    port, _, _ = mock_server
    c = NjordClient(host="localhost", port=port)
    await c.connect()
    yield c
    await c.close()


# --- Unary RPC Tests ---


@pytest.mark.asyncio
async def test_get_locations(client):
    locations = await client.get_locations()
    assert locations == ["lucerne", "zurich"]


@pytest.mark.asyncio
async def test_get_models(client):
    models = await client.get_models("lucerne")
    assert models == ["icon_d2", "ecmwf_ifs025"]


@pytest.mark.asyncio
async def test_get_forecast(client):
    forecast = await client.get_forecast("lucerne", "icon_d2")
    assert isinstance(forecast, ForecastData)
    assert forecast.location == "lucerne"
    assert forecast.model == "icon_d2"
    assert len(forecast.hourly) == 1
    assert forecast.hourly[0].temperature == 22.5
    assert forecast.hourly[0].weather_code == 3
    assert forecast.hourly[0].is_day is True
    assert isinstance(forecast.hourly[0].timestamp, datetime)
    assert len(forecast.daily) == 1
    assert forecast.daily[0].temperature_max == 28.0


@pytest.mark.asyncio
async def test_get_config(client):
    config = await client.get_config()
    assert isinstance(config, NjordConfigData)
    assert len(config.locations) == 1
    assert config.locations[0].name == "lucerne"
    assert config.locations[0].latitude == pytest.approx(47.05)
    assert config.default_models == ["icon_d2", "ecmwf_ifs025"]
    assert config.horizons == [1, 3, 6]
    assert config.forecast_days == 7


@pytest.mark.asyncio
async def test_get_status(client):
    status = await client.get_status()
    assert isinstance(status, ServerStatusData)
    assert status.version == "1.2.3"
    assert status.uptime_seconds == 3600
    assert status.budget is not None
    assert status.budget.monthly_limit == 20000
    assert status.budget.usage_percent == pytest.approx(25.0)


# --- Context Manager Test ---


@pytest.mark.asyncio
async def test_context_manager(mock_server):
    port, _, _ = mock_server
    async with NjordClient(host="localhost", port=port) as client:
        locations = await client.get_locations()
        assert locations == ["lucerne", "zurich"]


@pytest.mark.asyncio
async def test_not_connected_raises():
    client = NjordClient(host="localhost", port=9999)
    with pytest.raises(RuntimeError, match="not connected"):
        await client.get_locations()


# --- Streaming Tests ---


@pytest.mark.asyncio
async def test_stream_forecasts(client):
    updates: list[ForecastData] = []
    async for update in client.stream_forecasts():
        updates.append(update)
    assert len(updates) == 3
    assert all(isinstance(u, ForecastData) for u in updates)
    assert updates[0].location == "lucerne"
    assert updates[0].model == "icon_d2"


@pytest.mark.asyncio
async def test_stream_forecasts_with_location(client):
    updates: list[ForecastData] = []
    async for update in client.stream_forecasts(location="zurich"):
        updates.append(update)
    assert len(updates) == 3
    assert all(u.location == "zurich" for u in updates)


@pytest.mark.asyncio
async def test_stream_config(client):
    configs: list[NjordConfigData] = []
    async for config in client.stream_config():
        configs.append(config)
    assert len(configs) == 2
    assert all(isinstance(c, NjordConfigData) for c in configs)
    assert configs[0].forecast_days == 7
    assert configs[1].forecast_days == 8


# --- Reconnect Tests ---


@pytest.mark.asyncio
async def test_stream_reconnects_on_failure(mock_server, monkeypatch):
    port, forecast_servicer, _ = mock_server
    forecast_servicer.fail_stream_on_call = 1

    # Speed up backoff for testing
    import custom_components.njord.grpc_client as client_module
    monkeypatch.setattr(client_module, "_BACKOFF_INITIAL", 0.05)
    monkeypatch.setattr(client_module, "_BACKOFF_MAX", 0.1)

    on_disconnect = MagicMock()
    on_reconnect = MagicMock()

    client = NjordClient(host="localhost", port=port)
    await client.connect()

    updates: list[ForecastData] = []
    async for update in client.stream_forecasts(
        on_disconnect=on_disconnect,
        on_reconnect=on_reconnect,
    ):
        updates.append(update)
        if len(updates) >= 3:
            break

    await client.close()

    assert len(updates) == 3
    assert on_disconnect.call_count >= 1
    assert on_reconnect.call_count >= 1
