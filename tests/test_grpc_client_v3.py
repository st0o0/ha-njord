"""Tests for the njord v3 gRPC client methods."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.njord.grpc_client import NjordClient
from custom_components.njord.proto.njord import njord_pb2 as v3_pb2


@pytest.fixture
def mock_v3_stub():
    """Create a mock NjordService stub."""
    stub = MagicMock()
    stub.GetManifest = AsyncMock()
    stub.Subscribe = MagicMock()
    stub.GetStatus = AsyncMock()
    stub.TriggerPoll = AsyncMock()
    return stub


@pytest.fixture
def client(mock_v3_stub):
    """Create a NjordClient with mocked stubs (no real connection)."""
    c = NjordClient("localhost", 5001)
    c._channel = MagicMock()
    c._v3_stub = mock_v3_stub
    return c


async def test_get_manifest(client, mock_v3_stub):
    """get_manifest calls GetManifest and returns the response."""
    expected = v3_pb2.ManifestResponse(
        entities=[
            v3_pb2.EntityDefinition(
                entity_id="vienna_frost",
                location="Vienna",
                feature="Frost",
                platform=v3_pb2.ENTITY_PLATFORM_BINARY_SENSOR,
                device_class="safety",
                unit="",
                category="Forecast",
                output_kind=v3_pb2.OUTPUT_KIND_ALERT,
            )
        ]
    )
    mock_v3_stub.GetManifest.return_value = expected

    result = await client.get_manifest()

    mock_v3_stub.GetManifest.assert_awaited_once()
    assert len(result.entities) == 1
    assert result.entities[0].entity_id == "vienna_frost"


async def test_subscribe(client, mock_v3_stub):
    """subscribe returns the stream call object."""
    mock_stream = MagicMock()
    mock_v3_stub.Subscribe.return_value = mock_stream

    result = await client.subscribe("Vienna")

    mock_v3_stub.Subscribe.assert_called_once()
    assert result is mock_stream


async def test_get_status_v3(client, mock_v3_stub):
    """get_status_v3 calls v3 GetStatus."""
    expected = v3_pb2.StatusResponse(version="0.5.0", uptime_seconds=3600)
    mock_v3_stub.GetStatus.return_value = expected

    result = await client.get_status_v3()

    mock_v3_stub.GetStatus.assert_awaited_once()
    assert result.version == "0.5.0"


async def test_trigger_poll_v3(client, mock_v3_stub):
    """trigger_poll_v3 calls v3 TriggerPoll."""
    expected = v3_pb2.TriggerPollResponse(triggered_count=2, targets=["Vienna", "Berlin"])
    mock_v3_stub.TriggerPoll.return_value = expected

    result = await client.trigger_poll_v3("Vienna")

    mock_v3_stub.TriggerPoll.assert_awaited_once()
    assert result.triggered_count == 2
