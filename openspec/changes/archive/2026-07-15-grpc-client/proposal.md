## Why

ha-njord has a project skeleton and generated proto stubs but no way to actually communicate with njord. A gRPC client module is the foundation for every feature that follows — config flow validation, weather entity data, streaming updates. Without it, nothing connects.

## What Changes

- Create `custom_components/njord/grpc_client.py` — a `NjordClient` class wrapping all gRPC communication
- Unary RPCs: `GetLocations`, `GetModels`, `GetForecast`, `GetConfig`, `GetStatus`
- Server-streaming RPCs: `StreamForecasts`, `StreamConfig`
- Channel lifecycle: create/close insecure gRPC channel (h2c)
- Reconnect logic with exponential backoff on stream failure
- Typed return values using dataclasses (not raw protobuf messages at the API surface)
- Tests against a mock gRPC server running in Docker

## Non-goals

- No Home Assistant integration code (no config flow, no entities, no platforms)
- No `async_setup_entry` changes — the client is a standalone module
- No enrichment RPCs (`GetEnrichments`, `StreamEnrichments`) — those are Phase 2
- No mutation RPCs (`AddLocation`, `UpdateForecastSettings`, etc.) — ha-njord is read-only

## Capabilities

### New Capabilities
- `grpc-client`: Channel management, unary RPCs, server-streaming RPCs, reconnect logic, and typed data models

### Modified Capabilities

(none)

## Impact

- **New file**: `custom_components/njord/grpc_client.py`
- **New file**: `custom_components/njord/models.py` (dataclasses for typed API surface)
- **New tests**: `tests/test_grpc_client.py`
- **No new dependencies**: `grpcio` and `protobuf` are already declared in `manifest.json` and `pyproject.toml`
- **gRPC endpoints required**: `GetLocations`, `GetModels`, `GetForecast` (exist in njord), `GetConfig`, `GetStatus` (exist in proto), `StreamForecasts`, `StreamConfig` (exist in proto). All RPCs are defined in the protos — implementation status in njord is a separate concern.
