"""Tests for the njord gRPC client methods."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.njord.grpc_client import NjordClient
from custom_components.njord.proto.njord import njord_pb2


@pytest.fixture
def mock_stub():
    """Create a mock NjordService stub."""
    stub = MagicMock()
    stub.GetManifest = AsyncMock()
    stub.Subscribe = MagicMock()
    stub.GetStatus = AsyncMock()
    stub.TriggerPoll = AsyncMock()
    return stub


@pytest.fixture
def client(mock_stub):
    """Create a NjordClient with mocked stubs (no real connection)."""
    c = NjordClient("localhost", 5001)
    c._channel = MagicMock()
    c._stub = mock_stub
    return c


async def test_get_manifest(client, mock_stub):
    """get_manifest calls GetManifest and returns the response."""
    expected = njord_pb2.ManifestResponse(
        entities=[
            njord_pb2.EntityDefinition(
                entity_id="vienna_frost",
                location="Vienna",
                feature="Frost",
                platform=njord_pb2.ENTITY_PLATFORM_BINARY_SENSOR,
                device_class="safety",
                unit="",
                category="Forecast",
                output_kind=njord_pb2.OUTPUT_KIND_ALERT,
            )
        ]
    )
    mock_stub.GetManifest.return_value = expected

    result = await client.get_manifest()

    mock_stub.GetManifest.assert_awaited_once()
    assert len(result.entities) == 1
    assert result.entities[0].entity_id == "vienna_frost"


async def test_subscribe(client, mock_stub):
    """subscribe returns the stream call object."""
    mock_stream = MagicMock()
    mock_stub.Subscribe.return_value = mock_stream

    result = await client.subscribe("Vienna")

    mock_stub.Subscribe.assert_called_once()
    assert result is mock_stream


async def test_get_status(client, mock_stub):
    """get_status calls GetStatus."""
    expected = njord_pb2.StatusResponse(version="0.5.0", uptime_seconds=3600)
    mock_stub.GetStatus.return_value = expected

    result = await client.get_status()

    mock_stub.GetStatus.assert_awaited_once()
    assert result.version == "0.5.0"


async def test_trigger_poll(client, mock_stub):
    """trigger_poll calls TriggerPoll."""
    expected = njord_pb2.TriggerPollResponse(triggered_count=2, targets=["Vienna", "Berlin"])
    mock_stub.TriggerPoll.return_value = expected

    result = await client.trigger_poll("Vienna")

    mock_stub.TriggerPoll.assert_awaited_once()
    assert result.triggered_count == 2
