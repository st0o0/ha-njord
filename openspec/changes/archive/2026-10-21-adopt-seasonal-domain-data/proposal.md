## Why

njord now ships a `SeasonalData` payload in the `DomainDataUpdate` oneof (`seasonal = 16`). ha-njord ignores it, so the seasonal outlook inputs never reach Home Assistant state. Consuming it keeps the integration aligned with the server's domain set.

## What Changes

- Sync `common.proto`, `weather.proto`, `ops.proto` from njord and regenerate the Python stubs (same gencode 5.29.0 as before).
- Parse `DomainDataUpdate.seasonal` into `SeasonalDomainData` / `SeasonalSampleData` (unset optional fields become `None`).
- Track the seasonal domain in the coordinator (first refresh and domain stream) so the latest seasonal data per location is kept like the other domains. No new entity.
- Diagnostics list the seasonal domain per location through the existing domain summary.
- CLAUDE.md: seasonal is consumed, satellite is not.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `grpc-client`: seasonal domain data is converted to typed models and tracked by the coordinator.

## Impact

- `protos/njord/v2/weather.proto`, `custom_components/njord/proto/njord/v2/weather_pb2.py`
- `custom_components/njord/models.py`, `grpc_client.py`, `coordinator.py`
- `tests/test_grpc_client.py`, `tests/test_coordinator_streaming.py`, `tests/test_coordinator.py`, `tests/test_diagnostics.py`
- `CLAUDE.md`
