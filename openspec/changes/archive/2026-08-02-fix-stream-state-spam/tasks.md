## 1. Refactor `_stream_with_reconnect` state tracking

- [x] 1.1 Add `connected: bool = False` local variable to `_stream_with_reconnect` in `custom_components/njord/grpc_client.py`
- [x] 1.2 Fire `on_reconnect` only when `connected` is `False` and the new gRPC call is created — then set `connected = True`
- [x] 1.3 Fire `on_disconnect` only when `connected` is `True` and a `grpc.aio.AioRpcError` (non-CANCELLED) occurs — then set `connected = False`
- [x] 1.4 On normal stream end (iterator exhaustion), do NOT call `on_disconnect` — just reconnect silently

## 2. Tests

- [x] 2.1 Add test: normal stream end + reconnect does not fire `on_disconnect`/`on_reconnect` again (`tests/test_grpc_client.py`)
- [x] 2.2 Add test: gRPC error fires `on_disconnect` exactly once, reconnect fires `on_reconnect` (`tests/test_grpc_client.py`)
- [x] 2.3 Add test: repeated gRPC errors do not spam `on_disconnect` (`tests/test_grpc_client.py`)
- [x] 2.4 Verify existing stream health tests still pass (`tests/test_stream_health.py`)

## 3. Validation

- [x] 3.1 Run `make test` — all tests pass
