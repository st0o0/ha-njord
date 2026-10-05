## Context

`_stream_with_reconnect` in `grpc_client.py` is a generic reconnecting stream wrapper used by all three gRPC streams (forecast, enrichment, config). It calls `on_reconnect()` unconditionally every time a new gRPC call is created — including after normal stream ends where the server closed the stream after delivering a snapshot. This causes the coordinator's `stream_states` dict to toggle `True → False → True` on every reconnect cycle, producing repeated "Connected" entries in the HA logbook even though the stream never truly disconnected.

Current flow in `_stream_with_reconnect`:
```
while True:
    call = call_factory()
    on_reconnect()              # always fires
    async for msg in call:
        yield msg
    on_disconnect()             # always fires (even on normal end)
    await sleep(backoff)
```

## Goals / Non-Goals

**Goals:**
- Only fire `on_reconnect` when transitioning from disconnected → connected (not on every loop iteration)
- Only fire `on_disconnect` on actual gRPC errors, not on normal stream end + immediate successful reconnect
- Keep the existing backoff/reconnect mechanics unchanged

**Non-Goals:**
- Changing the binary sensor entity implementation
- Changing the coordinator callback logic (`_on_stream_connect` / `_on_stream_disconnect`)
- Changing the HA repair issue grace period logic
- Changing how the server delivers streams (that's njord's concern)

## Decisions

### Decision 1: Track `_connected` state inside `_stream_with_reconnect`

Add a local `connected: bool` variable to the method. Fire `on_reconnect` only when `connected` is `False` and a new call succeeds. Fire `on_disconnect` only when `connected` is `True` and a gRPC error occurs.

**Rationale:** This is the minimal change — one local variable, no new classes or abstractions. The state is scoped to the method lifetime, which matches the stream lifetime.

**Alternative considered:** Moving state-change detection into `_on_stream_connect`/`_on_stream_disconnect` on the coordinator. Rejected because the coordinator shouldn't need to know about reconnect internals — the client should only signal meaningful state changes.

### Decision 2: Normal stream end does not trigger disconnect

When the `async for` iterator exhausts normally (server closed the stream after sending data), this is NOT a disconnect. The method should reconnect silently. Only `grpc.aio.AioRpcError` (excluding `CANCELLED`) counts as a disconnect.

**Rationale:** A server closing a stream after delivering a config snapshot is expected behavior, not an error. The user's logbook should only reflect actual connection problems.

### Decision 3: First connect always fires `on_reconnect`

The initial `connected` state is `False`, so the very first successful call always fires `on_reconnect`. This preserves the existing behavior for initial setup.

## Risks / Trade-offs

- **[Risk] Normal stream end masks a real issue** → If the server starts closing streams due to a bug, the user won't see disconnect/reconnect churn in the logbook. Mitigation: The `_LOGGER.debug` line for normal stream ends is kept, so debug logging still reveals the pattern.
- **[Risk] Long disconnect during backoff not signaled** → If a gRPC error occurs and backoff grows to 60s, the disconnect is signaled immediately on the error. The repair issue logic (60s grace) handles prolonged disconnects. No change needed.
