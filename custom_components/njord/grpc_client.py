"""gRPC client for communicating with the njord weather service."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import TypeVar

import grpc

# Ensure proto package path is on sys.path before importing generated stubs.
from . import proto as _proto_pkg  # noqa: F401
from .proto.njord import njord_pb2, njord_pb2_grpc

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

_BACKOFF_INITIAL = 1.0
_BACKOFF_MAX = 60.0
_BACKOFF_FACTOR = 2.0


# --- Protobuf helpers ---


def _ts_to_dt(ts) -> datetime:
    return ts.ToDatetime().replace(tzinfo=UTC)


def _optional_ts(ts) -> datetime | None:
    return _ts_to_dt(ts) if ts.seconds or ts.nanos else None


def _opt(pb, name: str):
    return getattr(pb, name) if pb.HasField(name) else None


# --- Client ---


class NjordClient:
    """Async gRPC client for the njord weather service."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._channel: grpc.aio.Channel | None = None
        self._stub: njord_pb2_grpc.NjordServiceStub | None = None

    async def connect(self) -> None:
        """Open an insecure gRPC channel to njord."""
        target = f"{self._host}:{self._port}"
        self._channel = grpc.aio.insecure_channel(target)
        self._stub = njord_pb2_grpc.NjordServiceStub(self._channel)

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def __aenter__(self) -> NjordClient:
        await self.connect()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def _ensure_connected(self) -> None:
        if self._channel is None:
            raise RuntimeError("NjordClient is not connected. Call connect() first.")

    # --- Unary RPCs ---

    async def get_manifest(self) -> njord_pb2.ManifestResponse:
        """Retrieve entity manifest."""
        self._ensure_connected()
        assert self._stub is not None
        return await self._stub.GetManifest(njord_pb2.ManifestRequest())

    async def get_status(self) -> njord_pb2.StatusResponse:
        """Get system status."""
        self._ensure_connected()
        assert self._stub is not None
        return await self._stub.GetStatus(njord_pb2.StatusRequest())

    async def trigger_poll(self, location: str = "") -> njord_pb2.TriggerPollResponse:
        """Trigger a poll (all locations when empty)."""
        self._ensure_connected()
        assert self._stub is not None
        return await self._stub.TriggerPoll(njord_pb2.TriggerPollRequest(location=location))

    # --- Streaming RPCs ---

    async def subscribe(self, location: str = "") -> AsyncIterator[njord_pb2.EntityEvent]:
        """Open a Subscribe stream. Returns an async iterator of EntityEvent."""
        self._ensure_connected()
        assert self._stub is not None
        return self._stub.Subscribe(njord_pb2.SubscribeRequest(location=location))
