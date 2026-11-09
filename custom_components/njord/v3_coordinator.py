"""v3 data coordinator for njord — single Subscribe stream with snapshot-on-connect."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .grpc_client import NjordClient
from .models import EntityState, ManifestEntity
from .proto.njord.v3 import njord_pb2 as v3_pb2

_LOGGER = logging.getLogger(__name__)

_BACKOFF_INITIAL = 1.0
_BACKOFF_MAX = 60.0
_BACKOFF_FACTOR = 2.0

_OUTPUT_KIND_NAMES: dict[int, str] = {
    v3_pb2.OUTPUT_KIND_ALERT: "alert",
    v3_pb2.OUTPUT_KIND_SCORE: "score",
    v3_pb2.OUTPUT_KIND_CONDITION: "condition",
    v3_pb2.OUTPUT_KIND_TREND: "trend",
    v3_pb2.OUTPUT_KIND_FORECAST: "forecast",
    v3_pb2.OUTPUT_KIND_WEATHER: "weather",
    v3_pb2.OUTPUT_KIND_OBSERVATION: "observation",
}

_PLATFORM_NAMES: dict[int, str] = {
    v3_pb2.ENTITY_PLATFORM_WEATHER: "weather",
    v3_pb2.ENTITY_PLATFORM_SENSOR: "sensor",
    v3_pb2.ENTITY_PLATFORM_BINARY_SENSOR: "binary_sensor",
}


def _parse_manifest(response: v3_pb2.ManifestResponse) -> list[ManifestEntity]:
    """Convert a protobuf ManifestResponse to a list of ManifestEntity."""
    entities: list[ManifestEntity] = []
    for e in response.entities:
        entities.append(
            ManifestEntity(
                entity_id=e.entity_id,
                location=e.location,
                feature=e.feature,
                platform=_PLATFORM_NAMES.get(e.platform, "sensor"),
                device_class=e.device_class,
                unit=e.unit,
                icon=e.icon,
                category=e.category,
                output_kind=_OUTPUT_KIND_NAMES.get(e.output_kind, "observation"),
            )
        )
    return entities


def _ts_to_iso(ts) -> str | None:
    """Convert a protobuf Timestamp to ISO string, or None if unset."""
    if ts.seconds or ts.nanos:
        return ts.ToDatetime().replace(tzinfo=UTC).isoformat()
    return None


def _extract_value(update: v3_pb2.EntityStateUpdate):
    """Extract the oneof value from an EntityStateUpdate."""
    which = update.WhichOneof("value")
    if which is None:
        return None
    return getattr(update, which)


class NjordV3Coordinator(DataUpdateCoordinator[None]):
    """Stream-driven v3 coordinator: manifest + single Subscribe stream."""

    def __init__(self, hass: HomeAssistant, client: NjordClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="njord_v3",
            update_interval=None,
        )
        self.client = client
        self.manifest: list[ManifestEntity] = []
        self.v3_entity_states: dict[str, EntityState] = {}
        self._stream_task: asyncio.Task | None = None
        self._stream_connected: bool = False

    async def async_setup(self) -> None:
        """Fetch the manifest and populate initial state."""
        try:
            response = await self.client.get_manifest()
        except Exception as err:
            raise UpdateFailed(f"Failed to get njord v3 manifest: {err}") from err
        self.manifest = _parse_manifest(response)

    async def _async_update_data(self) -> None:
        """No polling — the stream pushes updates."""
        return None

    def start_stream(self) -> None:
        """Start the Subscribe stream in the background."""
        if self._stream_task is not None:
            return
        self._stream_task = self.hass.async_create_task(self._run_stream())

    async def stop_stream(self) -> None:
        """Stop the Subscribe stream."""
        if self._stream_task is not None:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
            self._stream_task = None
        self._stream_connected = False

    @property
    def stream_connected(self) -> bool:
        return self._stream_connected

    async def _run_stream(self) -> None:
        """Reconnecting stream loop with exponential backoff."""
        backoff = _BACKOFF_INITIAL
        while True:
            try:
                stream = await self.client.subscribe()
                self._stream_connected = True
                backoff = _BACKOFF_INITIAL
                _LOGGER.debug("v3 Subscribe stream connected")

                async for event in stream:
                    self._process_event(event)
                    self.async_set_updated_data(None)

            except asyncio.CancelledError:
                _LOGGER.debug("v3 Subscribe stream cancelled")
                break
            except Exception:
                _LOGGER.exception("v3 Subscribe stream error, reconnecting in %.0fs", backoff)
            finally:
                self._stream_connected = False

            await asyncio.sleep(backoff)
            backoff = min(backoff * _BACKOFF_FACTOR, _BACKOFF_MAX)

    def _process_event(self, event: v3_pb2.EntityEvent) -> None:
        """Dispatch a single EntityEvent."""
        which = event.WhichOneof("event")
        if which == "snapshot":
            self._apply_snapshot(event.snapshot)
        elif which == "state_update":
            self._apply_state_update(event.state_update)
        elif which == "unavailable":
            self._apply_unavailable(event.unavailable)
        elif which == "available":
            self._apply_available(event.available)

    def _apply_snapshot(self, snapshot: v3_pb2.EntitySnapshot) -> None:
        """Replace all entity states from a snapshot."""
        for update in snapshot.states:
            self._apply_state_update(update)

    def _apply_state_update(self, update: v3_pb2.EntityStateUpdate) -> None:
        """Update a single entity's state."""
        value = _extract_value(update)
        updated_at_iso = _ts_to_iso(update.updated_at)
        existing = self.v3_entity_states.get(update.entity_id)
        self.v3_entity_states[update.entity_id] = EntityState(
            entity_id=update.entity_id,
            value=value,
            updated_at=updated_at_iso,
            available=existing.available if existing else True,
        )

    def _apply_unavailable(self, msg: v3_pb2.EntityUnavailable) -> None:
        """Mark an entity as unavailable."""
        existing = self.v3_entity_states.get(msg.entity_id)
        if existing:
            self.v3_entity_states[msg.entity_id] = EntityState(
                entity_id=msg.entity_id,
                value=existing.value,
                updated_at=existing.updated_at,
                available=False,
            )
        else:
            self.v3_entity_states[msg.entity_id] = EntityState(
                entity_id=msg.entity_id,
                value=None,
                available=False,
            )

    def _apply_available(self, msg: v3_pb2.EntityAvailable) -> None:
        """Mark an entity as available again."""
        existing = self.v3_entity_states.get(msg.entity_id)
        if existing:
            self.v3_entity_states[msg.entity_id] = EntityState(
                entity_id=msg.entity_id,
                value=existing.value,
                updated_at=existing.updated_at,
                available=True,
            )
