## Why

`_stream_with_reconnect` fires `on_reconnect()` every time it opens a new gRPC call — including after normal stream ends (server sends snapshot, closes). This causes the stream health binary sensors to toggle `True → False → True` on every reconnect cycle, spamming the HA logbook with repeated "Connected" entries even though the stream is healthy and never truly disconnected.

## What Changes

- Refactor `_stream_with_reconnect` to track internal connected state and only fire `on_reconnect`/`on_disconnect` callbacks on **actual state transitions** (disconnected→connected, connected→disconnected)
- Normal stream end + immediate reconnect no longer toggles the binary sensor — only gRPC errors that persist through the backoff cycle count as a real disconnect
- First successful connect still fires `on_reconnect` as before

## Non-goals

- Changing the reconnect/backoff logic itself — that stays as-is
- Changing the binary sensor entity or coordinator callback logic — the fix is isolated to `_stream_with_reconnect`
- Changing the HA repair issue timing (60s grace period) — that behavior is correct

## gRPC Endpoints

All existing streaming RPCs are affected (no new endpoints needed):
- `WeatherService.StreamForecasts` (existing)
- `WeatherService.StreamEnrichments` (existing)
- `AdminService.StreamConfig` (existing)

## Capabilities

### New Capabilities

_None — this is a behavioral fix to an existing capability._

### Modified Capabilities

- `stream-health`: The requirement "Stream reconnect wrapper tracks connection state" needs refinement — state transitions should only fire on actual connect/disconnect, not on every reconnect cycle.

## Impact

- `custom_components/njord/grpc_client.py` — `_stream_with_reconnect` method
- Stream health binary sensors will show fewer state changes (only meaningful ones)
- HA logbook will no longer be spammed with repeated "Connected" entries
