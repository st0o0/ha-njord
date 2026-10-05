## 1. Data Models

- [x] 1.1 Create `custom_components/njord/models.py` with frozen dataclasses: `HourlyForecastData`, `DailyForecastData`, `ForecastData`, `NjordLocation`, `NjordConfigData`, `ServerStatusData`, `BudgetStatusData`
- [x] 1.2 Create `tests/test_models.py` — verify dataclass construction, frozen immutability, optional fields default to None

## 2. Client Core — Channel & Unary RPCs

- [x] 2.1 Create `custom_components/njord/grpc_client.py` with `NjordClient` class: `__init__(host, port)`, `async connect()`, `async close()`, `__aenter__`/`__aexit__` context manager
- [x] 2.2 Implement protobuf-to-dataclass converters as private `_to_*` functions in `grpc_client.py` (e.g., `_to_forecast_data`, `_to_config_data`, `_to_location`)
- [x] 2.3 Implement unary RPCs: `get_locations() -> list[str]`, `get_models(location) -> list[str]`, `get_forecast(location, model) -> ForecastData`
- [x] 2.4 Implement unary RPCs: `get_config() -> NjordConfigData`, `get_status() -> ServerStatusData`
- [x] 2.5 Create `tests/test_grpc_client.py` with mock gRPC server (in-process `grpc.aio.server()` with a mock servicer). Test all 5 unary RPCs with canned responses.

## 3. Streaming RPCs

- [x] 3.1 Implement `stream_forecasts(location: str | None = None) -> AsyncIterator[ForecastData]` in `grpc_client.py`
- [x] 3.2 Implement `stream_config() -> AsyncIterator[NjordConfigData]` in `grpc_client.py`
- [x] 3.3 Add streaming tests to `tests/test_grpc_client.py` — mock servicer yields multiple updates, verify async iteration produces correct dataclasses

## 4. Reconnect Logic

- [x] 4.1 Implement exponential backoff reconnect wrapper for streaming RPCs: retry on `grpc.RpcError`, backoff 1s→2s→4s→...→60s max, reset on successful message, invoke `on_disconnect`/`on_reconnect` callbacks
- [x] 4.2 Add reconnect tests to `tests/test_grpc_client.py` — mock server drops connection, verify client reconnects with backoff and callbacks are invoked

## Validation

```bash
# Run all tests via Docker
make test

# Or explicitly:
docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet grpcio protobuf pytest && python -m pytest tests/ -v"
```
