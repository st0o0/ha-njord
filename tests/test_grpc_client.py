"""Tests for the njord gRPC client: protobuf converters and NjordClient against mocked stubs."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import grpc
import pytest
from google.protobuf.timestamp_pb2 import Timestamp

from custom_components.njord.const import AlertSeverity, AlertType, Domain, Feature, PollPhase
from custom_components.njord.grpc_client import (
    NjordClient,
    _to_domain_data,
    _to_feature,
    _to_model_info,
    _to_server_status,
    _to_target_data,
)
from custom_components.njord.models import (
    AirQualityDomainData,
    FloodDomainData,
    MarineDomainData,
    WeatherDomainData,
)
from custom_components.njord.proto.njord.v2 import common_pb2, ops_pb2, weather_pb2

EPOCH = 1720000000
EXPECTED_DT = datetime.fromtimestamp(EPOCH, tz=UTC)


def _ts(epoch: int = EPOCH) -> Timestamp:
    ts = Timestamp()
    ts.FromSeconds(epoch)
    return ts


async def _aiter(*items, error: Exception | None = None):
    for item in items:
        yield item
    if error is not None:
        raise error


# --- Domain data converters ---


def test_weather_update_converted():
    pb = weather_pb2.DomainDataUpdate(
        location="home",
        domain=weather_pb2.DOMAIN_WEATHER,
        model_run=_ts(),
        weather=weather_pb2.WeatherData(
            points=[
                weather_pb2.WeatherSample(
                    valid_at=_ts(),
                    temperature=21.5,
                    apparent_temperature=20.0,
                    wind_speed=4.0,
                    weather_code=61,
                    humidity=70.0,
                    wind_gusts=9.5,
                    is_day=False,
                ),
                weather_pb2.WeatherSample(valid_at=_ts(EPOCH + 3600), temperature=19.0),
            ]
        ),
    )

    data = _to_domain_data(pb)

    assert isinstance(data, WeatherDomainData)
    assert data.location == "home"
    assert data.domain is Domain.WEATHER
    assert data.model_run == EXPECTED_DT
    first, second = data.points
    assert first.valid_at == EXPECTED_DT
    assert first.temperature == 21.5
    assert first.weather_code == 61
    assert first.wind_gusts == 9.5
    assert first.is_day is False
    assert first.cape is None
    assert second.is_day is None
    assert second.wind_gusts is None


def test_air_quality_update_converted():
    pb = weather_pb2.DomainDataUpdate(
        location="home",
        air_quality=weather_pb2.AirQualityData(
            points=[weather_pb2.AirQualitySample(valid_at=_ts(), pm25=11.0, pm10=19.0, ozone=70.0, mugwort=2.0)]
        ),
    )

    data = _to_domain_data(pb)

    assert isinstance(data, AirQualityDomainData)
    assert data.model_run is None
    sample = data.points[0]
    assert (sample.pm25, sample.pm10, sample.ozone) == (11.0, 19.0, 70.0)
    assert sample.mugwort == 2.0
    assert sample.birch_pollen is None


def test_flood_update_converted():
    pb = weather_pb2.DomainDataUpdate(
        location="rhine",
        flood=weather_pb2.FloodData(
            points=[weather_pb2.FloodSample(valid_at=_ts(), discharge=120.5, discharge_p75=140.0)]
        ),
    )

    data = _to_domain_data(pb)

    assert isinstance(data, FloodDomainData)
    assert data.points[0].discharge == 120.5
    assert data.points[0].discharge_p75 == 140.0
    assert data.points[0].discharge_mean is None


def test_marine_update_converted():
    pb = weather_pb2.DomainDataUpdate(
        location="coast",
        marine=weather_pb2.MarineData(
            points=[weather_pb2.MarineSample(valid_at=_ts(), wave_height=1.5, wave_period=8.0, wave_direction=270.0)]
        ),
    )

    data = _to_domain_data(pb)

    assert isinstance(data, MarineDomainData)
    assert data.points[0].wave_height == 1.5
    assert data.points[0].water_temperature is None


def test_satellite_update_is_not_consumed():
    pb = weather_pb2.DomainDataUpdate(location="home", satellite=weather_pb2.SatelliteData())

    assert _to_domain_data(pb) is None


def test_update_without_payload_is_none():
    assert _to_domain_data(weather_pb2.DomainDataUpdate(location="home")) is None


# --- Enrichment converters ---


def test_alert_feature_converted():
    pb = weather_pb2.EnrichmentEvent(
        location="home",
        updated_at=_ts(),
        flood_risk=weather_pb2.FloodRiskAlert(
            alert=weather_pb2.AlertData(
                severity=common_pb2.ALERT_SEVERITY_ORANGE,
                confidence=0.8,
                trigger_value=300.0,
                threshold=200.0,
                peak_value=310.0,
                hours_until=5,
            )
        ),
    )

    item = _to_feature(pb)

    assert item is not None
    assert item.location == "home"
    assert item.feature is Feature.FLOOD_RISK
    assert item.updated_at == EXPECTED_DT
    alert = item.alert
    assert alert is not None
    assert alert.type is AlertType.FLOOD_RISK
    assert alert.severity is AlertSeverity.ORANGE
    assert (alert.confidence, alert.trigger_value, alert.threshold) == (0.8, 300.0, 200.0)
    assert alert.peak_value == 310.0
    assert alert.hours_until == 5
    assert alert.duration_hours is None


def test_score_feature_converted():
    pb = weather_pb2.EnrichmentEvent(
        location="home",
        laundry=weather_pb2.Laundry(score=weather_pb2.ScoreData(score=72, best_hours=3)),
    )

    item = _to_feature(pb)

    assert item is not None
    assert item.feature is Feature.LAUNDRY
    assert item.alert is None
    assert item.score is not None
    assert (item.score.score, item.score.best_hours) == (72, 3)


def test_event_without_feature_is_none():
    assert _to_feature(weather_pb2.EnrichmentEvent(location="home")) is None


# --- Ops converters ---


def test_server_status_converted():
    pb = ops_pb2.StatusResponse(
        version="1.2.3+abc",
        uptime_seconds=7200,
        process_start=_ts(),
        budget=ops_pb2.BudgetStatus(
            monthly_limit=100, monthly_used=10, daily_limit=10, daily_used=1, usage_percent=10.0
        ),
        models=[
            ops_pb2.ModelStatus(location="home", phase=ops_pb2.POLL_PHASE_DISCOVERY, next_poll=_ts(), miss_count=2)
        ],
        active_enrichments=["Weather:Frost"],
        budget_partial=True,
    )

    status = _to_server_status(pb)

    assert status.version == "1.2.3+abc"
    assert status.uptime_seconds == 7200
    assert status.process_start == EXPECTED_DT
    assert status.budget is not None
    assert status.budget.monthly_used == 10
    assert status.budget_partial is True
    assert status.models_partial is False
    assert status.active_enrichments == ["Weather:Frost"]
    location_status = status.location_statuses[0]
    assert location_status.phase is PollPhase.DISCOVERY
    assert location_status.next_poll == EXPECTED_DT
    assert location_status.last_change is None


def test_server_status_without_budget():
    status = _to_server_status(ops_pb2.StatusResponse(version="1"))
    assert status.budget is None
    assert status.process_start is None


def test_target_converted():
    pb = ops_pb2.TriggerTarget(
        location="home",
        phase=ops_pb2.POLL_PHASE_STEADY,
        next_poll=_ts(),
        last_change=_ts(EPOCH - 60),
        miss_count=3,
        cycle_seconds=3600,
    )

    target = _to_target_data(pb)

    assert target.location == "home"
    assert target.phase is PollPhase.STEADY
    assert target.last_change == datetime.fromtimestamp(EPOCH - 60, tz=UTC)
    assert target.miss_count == 3
    assert target.cycle_seconds == 3600


# --- Unary RPCs against mocked stubs ---


def _connected_client() -> NjordClient:
    client = NjordClient("localhost", 8081)
    client._channel = MagicMock()
    client._weather_stub = MagicMock()
    client._ops_stub = MagicMock()
    return client


async def test_not_connected_raises():
    client = NjordClient("localhost", 8081)
    with pytest.raises(RuntimeError, match="not connected"):
        await client.get_catalog()


async def test_connect_and_close_manage_channel():
    client = NjordClient("localhost", 8081)
    await client.connect()
    assert client._weather_stub is not None
    assert client._ops_stub is not None
    await client.close()
    assert client._channel is None
    assert client._weather_stub is None


async def test_get_catalog():
    client = _connected_client()
    client._weather_stub.GetCatalog = AsyncMock(
        return_value=weather_pb2.GetCatalogResponse(
            locations=[common_pb2.LocationInfo(name="home", latitude=47.0, longitude=8.0, models=["icon_d2"])],
            models=[
                common_pb2.ModelInfo(
                    id="icon_d2",
                    display_name="ICON-D2",
                    coverage_tier=common_pb2.COVERAGE_TIER_REGIONAL,
                    resolution_km=2.2,
                )
            ],
        )
    )

    catalog = await client.get_catalog()

    assert [loc.name for loc in catalog.locations] == ["home"]
    assert catalog.locations[0].models == ["icon_d2"]
    info = catalog.model_info["icon_d2"]
    assert info.coverage_tier == "regional"
    assert info.resolution_km == 2.2
    assert info.max_forecast_hours is None


async def test_get_domain_data_sends_location_and_domain():
    client = _connected_client()
    client._weather_stub.GetDomainData = AsyncMock(
        return_value=weather_pb2.DomainDataUpdate(
            location="home", flood=weather_pb2.FloodData(points=[weather_pb2.FloodSample(valid_at=_ts())])
        )
    )

    data = await client.get_domain_data("home", Domain.FLOOD)

    request = client._weather_stub.GetDomainData.await_args.args[0]
    assert request.location == "home"
    assert request.domain == weather_pb2.DOMAIN_FLOOD
    assert isinstance(data, FloodDomainData)


async def test_get_domain_data_empty_payload_is_none():
    client = _connected_client()
    client._weather_stub.GetDomainData = AsyncMock(return_value=weather_pb2.DomainDataUpdate(location="home"))
    assert await client.get_domain_data("home", Domain.MARINE) is None


async def test_get_domain_data_rejects_unspecified_domain():
    client = _connected_client()
    with pytest.raises(ValueError, match="cannot be requested"):
        await client.get_domain_data("home", Domain.UNSPECIFIED)


async def test_get_enrichments():
    client = _connected_client()
    client._weather_stub.GetEnrichments = AsyncMock(
        return_value=weather_pb2.GetEnrichmentsResponse(
            location="home",
            events=[
                weather_pb2.EnrichmentEvent(
                    location="home",
                    updated_at=_ts(),
                    uv=weather_pb2.UvAlert(
                        alert=weather_pb2.AlertData(severity=common_pb2.ALERT_SEVERITY_RED), uv_index=9.0
                    ),
                ),
                weather_pb2.EnrichmentEvent(location="home"),
            ],
        )
    )

    items = await client.get_enrichments("home")

    assert client._weather_stub.GetEnrichments.await_args.args[0].location == "home"
    assert len(items) == 1
    assert items[0].feature is Feature.UV
    assert items[0].alert is not None
    assert items[0].alert.severity is AlertSeverity.RED
    assert items[0].updated_at is not None


async def test_get_status_and_targets_and_trigger():
    client = _connected_client()
    client._ops_stub.GetStatus = AsyncMock(return_value=ops_pb2.StatusResponse(version="2.0"))
    client._ops_stub.GetTargets = AsyncMock(
        return_value=ops_pb2.GetTargetsResponse(targets=[ops_pb2.TriggerTarget(location="home")])
    )
    client._ops_stub.TriggerPoll = AsyncMock(return_value=ops_pb2.TriggerPollResponse(triggered_count=4))

    assert (await client.get_status()).version == "2.0"
    assert [t.location for t in await client.get_targets()] == ["home"]
    assert await client.trigger_poll("graz") == 4
    assert client._ops_stub.TriggerPoll.await_args.args[0].location == "graz"
    await client.trigger_poll()
    assert client._ops_stub.TriggerPoll.await_args.args[0].location == ""


# --- Streams ---


async def test_stream_domain_data_skips_unconvertible_messages():
    client = _connected_client()
    weather = weather_pb2.DomainDataUpdate(
        location="home", weather=weather_pb2.WeatherData(points=[weather_pb2.WeatherSample(valid_at=_ts())])
    )
    empty = weather_pb2.DomainDataUpdate(location="home")
    aq = weather_pb2.DomainDataUpdate(
        location="home", air_quality=weather_pb2.AirQualityData(points=[weather_pb2.AirQualitySample(valid_at=_ts())])
    )
    client._weather_stub.StreamDomainData = MagicMock(return_value=_aiter(weather, empty, aq))
    on_reconnect = MagicMock()

    received = []
    async for item in client.stream_domain_data(
        domains=[Domain.WEATHER, Domain.AIR_QUALITY, Domain.SATELLITE], on_reconnect=on_reconnect
    ):
        received.append(item)
        if len(received) == 2:
            break

    assert [type(item) for item in received] == [WeatherDomainData, AirQualityDomainData]
    request = client._weather_stub.StreamDomainData.call_args.args[0]
    assert request.location == ""
    assert list(request.domains) == [
        weather_pb2.DOMAIN_WEATHER,
        weather_pb2.DOMAIN_AIR_QUALITY,
        weather_pb2.DOMAIN_SATELLITE,
    ]
    on_reconnect.assert_called_once_with()


async def test_stream_enrichments_skips_unknown_payloads():
    client = _connected_client()
    unknown = weather_pb2.EnrichmentEvent(location="home")
    known = weather_pb2.EnrichmentEvent(location="bern", frost=weather_pb2.FrostAlert())
    client._weather_stub.StreamEnrichments = MagicMock(return_value=_aiter(unknown, known))

    async for item in client.stream_enrichments(location="bern"):
        assert item.location == "bern"
        assert item.feature is Feature.FROST
        break

    assert client._weather_stub.StreamEnrichments.call_args.args[0].location == "bern"


def _rpc_error(code: grpc.StatusCode) -> grpc.aio.AioRpcError:
    return grpc.aio.AioRpcError(code, grpc.aio.Metadata(), grpc.aio.Metadata(), "boom")


async def test_stream_reconnects_after_error_and_reports_state():
    client = _connected_client()
    update = weather_pb2.DomainDataUpdate(
        location="home", weather=weather_pb2.WeatherData(points=[weather_pb2.WeatherSample(valid_at=_ts())])
    )
    client._weather_stub.StreamDomainData = MagicMock(
        side_effect=[_aiter(error=_rpc_error(grpc.StatusCode.UNAVAILABLE)), _aiter(update)]
    )
    events: list[str] = []

    with patch("custom_components.njord.grpc_client.asyncio.sleep", new=AsyncMock()) as sleep:
        async for item in client.stream_domain_data(
            on_disconnect=lambda: events.append("disconnect"), on_reconnect=lambda: events.append("reconnect")
        ):
            assert isinstance(item, WeatherDomainData)
            break

    assert events == ["reconnect", "disconnect", "reconnect"]
    sleep.assert_awaited_once_with(1.0)
    assert client._weather_stub.StreamDomainData.call_count == 2


async def test_stream_ends_on_cancelled():
    client = _connected_client()
    client._weather_stub.StreamEnrichments = MagicMock(return_value=_aiter(error=_rpc_error(grpc.StatusCode.CANCELLED)))

    items = [item async for item in client.stream_enrichments()]

    assert items == []
    assert client._weather_stub.StreamEnrichments.call_count == 1


def test_model_info_enabled_is_mapped():
    off = _to_model_info(common_pb2.ModelInfo(id="a", enabled=False))
    on = _to_model_info(common_pb2.ModelInfo(id="b", enabled=True))

    assert (off.enabled, on.enabled) == (False, True)


def test_weather_update_carries_model():
    pb = weather_pb2.DomainDataUpdate(
        location="home", domain=weather_pb2.DOMAIN_WEATHER, model="ecmwf_ifs025", weather=weather_pb2.WeatherData()
    )

    data = _to_domain_data(pb)

    assert isinstance(data, WeatherDomainData)
    assert data.model == "ecmwf_ifs025"


async def test_get_domain_data_sends_model():
    client = _connected_client()
    client._weather_stub.GetDomainData = AsyncMock(
        return_value=weather_pb2.DomainDataUpdate(location="home", weather=weather_pb2.WeatherData())
    )

    await client.get_domain_data("home", Domain.WEATHER, model="icon_d2")
    await client.get_domain_data("home", Domain.WEATHER)

    first, second = (c.args[0] for c in client._weather_stub.GetDomainData.await_args_list)
    assert first.model == "icon_d2"
    assert second.model == ""


def test_model_comparison_feature_converted():
    pb = weather_pb2.EnrichmentEvent(
        location="home",
        model_comparison=weather_pb2.ModelComparison(
            days=[
                weather_pb2.ModelComparisonDay(
                    year=2026,
                    month=7,
                    day=1,
                    models=[
                        weather_pb2.ModelDayValues(model="icon_d2", max_temperature=21.4, precipitation=0.5),
                        weather_pb2.ModelDayValues(model="ecmwf_ifs025", max_temperature=19.0),
                    ],
                )
            ]
        ),
    )

    item = _to_feature(pb)

    assert item is not None
    assert item.feature is Feature.MODEL_COMPARISON
    assert "forecast" not in item.values
    days = item.values["days"]
    assert len(days) == 1
    assert days[0]["day"] == 1
    assert [m["model"] for m in days[0]["models"]] == ["icon_d2", "ecmwf_ifs025"]
    assert days[0]["models"][0]["max_temperature"] == 21.4
    assert days[0]["models"][1]["max_temperature"] == 19.0
