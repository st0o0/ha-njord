## Context

ha-njord has a project skeleton with generated proto stubs (`_pb2.py`, `_pb2_grpc.py`) but no client code to talk to njord. This change adds a `NjordClient` class that wraps all gRPC communication behind a typed Python API. It will be used by config flow (validation), weather entities (data), and background tasks (streaming).

All tools run via Docker (`python:3.12-slim`) since no local Python is installed.

## Goals / Non-Goals

**Goals:**
- Typed Python API surface using dataclasses (consumers never touch raw protobuf)
- Channel lifecycle management (create, close, context manager)
- All read-only unary RPCs wrapped
- Server-streaming RPCs with async iteration
- Reconnect logic with exponential backoff for streams
- Testable without a running njord instance (mock gRPC server in tests)

**Non-Goals:**
- No HA-specific code (no `hass` references, no coordinator)
- No mutation RPCs (ha-njord is read-only)
- No enrichment RPCs (Phase 2)
- No connection pooling or advanced channel options

## Decisions

### 1. API surface: Dataclasses, not protobuf messages

Consumers of `NjordClient` receive plain Python dataclasses (`ForecastData`, `LocationConfig`, etc.), not generated `_pb2` objects. This decouples the rest of ha-njord from protobuf internals and makes the code more Pythonic.

Alternative considered: Exposing raw protobuf messages — simpler initially but leaks generated code into the entire codebase. One mapping layer in the client is cleaner than proto awareness everywhere.

### 2. Async-first with grpcio (not grpcio-async)

Use `grpc.aio` (the async API built into `grpcio`) rather than the separate `grpcio-async` package. `grpc.aio` is the officially supported async interface since grpcio 1.32+ and avoids an extra dependency.

The client methods are all `async def` — this matches HA's async architecture.

### 3. Channel management: Explicit create/close

```python
client = NjordClient(host="192.168.1.100", port=8081)
await client.connect()
# ... use client ...
await client.close()
```

Also supports `async with` for clean resource management. The channel is insecure (h2c) — njord runs on the local network.

Alternative considered: Lazy channel creation on first call — hides connection failures. Explicit `connect()` lets config flow fail fast during validation.

### 4. Streaming: AsyncIterator with reconnect callback

Streaming RPCs (`StreamForecasts`, `StreamConfig`) return `AsyncIterator[T]` so callers use `async for`. The client handles reconnection internally:

```
Stream starts → yields updates → stream breaks
                                       ↓
                              wait (exp. backoff)
                                       ↓
                              reconnect → yields updates → ...
```

Backoff: 1s → 2s → 4s → 8s → ... → max 60s. Resets on successful message.

The caller provides a callback for disconnect/reconnect events (so HA can mark entities unavailable/available).

### 5. Models file: `models.py` with frozen dataclasses

All data types in `custom_components/njord/models.py`:
- `NjordLocation` (name, latitude, longitude, models)
- `HourlyForecastData`, `DailyForecastData`
- `ForecastData` (location, model, updated_at, hourly, daily)
- `NjordConfigData` (locations, default_models, horizons, etc.)
- `ServerStatusData` (version, uptime, budget)

Frozen dataclasses for immutability. Conversion from protobuf happens in private `_to_*` methods inside `grpc_client.py`.

### 6. Testing: Mock gRPC server in-process

Tests use `grpc.aio.server()` with a mock servicer that returns canned responses. No Docker needed for the mock server — `grpcio` runs in the test process. Tests themselves run via Docker (`make test`).

Alternative considered: Testing against real njord — good for integration tests later, but unit tests must not depend on external services.

## Risks / Trade-offs

- **[grpc.aio stability]** → `grpc.aio` has had bugs in older versions. Mitigation: pin `grpcio>=1.60.0` where the async API is mature.
- **[Protobuf mapping maintenance]** → When njord's protos change, `_to_*` converters in `grpc_client.py` need updating. Mitigation: proto import tests already catch schema drift; converter failures surface as test failures.
- **[Reconnect complexity]** → Exponential backoff with jitter adds code. Mitigation: keep it simple (no circuit breaker, no health checks), extract to a small helper if needed.
