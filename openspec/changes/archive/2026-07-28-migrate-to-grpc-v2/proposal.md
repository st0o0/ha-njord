## Why

njord has moved its gRPC API from v1 to v2. The v2 API reorganizes services (ForecastService + ConfigService → WeatherService + AdminService + OpsService), merges `GetLocations` + `GetModels` into a single `GetCatalog` RPC, and switches temporal fields from `int64` epoch to `google.protobuf.Timestamp`. ha-njord must migrate to stay compatible — v1 will be removed from njord.

## What Changes

- **BREAKING**: Replace all v1 proto files and generated stubs with v2 (new package `njord.v2`, 4 proto files: `common.proto`, `weather.proto`, `admin.proto`, `ops.proto`)
- **BREAKING**: gRPC client switches from 2 stubs (`ForecastServiceStub`, `ConfigServiceStub`) to 3 stubs (`WeatherServiceStub`, `AdminServiceStub`, `OpsServiceStub`)
- Replace `get_locations()` + `get_models(location)` + `get_model_info(location)` with single `get_catalog()` call — eliminates N+1 queries during initial load and config validation
- Timestamp conversion: `HourlyForecast.valid_at` (Timestamp) replaces `.timestamp` (int64); `updated_at` fields become Timestamp
- `GetConfig` moves to AdminService, `GetStatus` moves to OpsService
- `ServerStatusData` gains `process_start`, `model_statuses[]`, `active_enrichments[]`
- New button entity: global "Trigger Poll" button calling `OpsService.TriggerPoll("", "")`
- New HA service: `njord.trigger_poll(location, model)` for fine-grained poll triggering from automations

## Non-goals

- No AdminService write RPCs (SetLocations, SetSettings, SetEnrichment, SetBudget) — ha-njord remains a pure consumer
- No new enrichment sensor types in this change — existing sensors continue to work unchanged
- No GetTargets integration — model status data from GetStatus is sufficient for now

## Required gRPC Endpoints

| Endpoint | Service | Status |
|----------|---------|--------|
| GetCatalog | WeatherService | Existing in njord v2 |
| GetForecast | WeatherService | Existing (same shape) |
| GetEnrichments | WeatherService | Existing (same shape) |
| StreamForecasts | WeatherService | Existing (same shape) |
| StreamEnrichments | WeatherService | Existing (same shape) |
| GetConfig | AdminService | Existing (moved from ConfigService) |
| StreamConfig | AdminService | Existing (moved from ConfigService) |
| GetStatus | OpsService | Existing (moved, expanded response) |
| TriggerPoll | OpsService | Existing (new usage from ha-njord) |

## Capabilities

### New Capabilities
- `trigger-poll`: Button entity + HA service for manually triggering njord forecast polls via OpsService.TriggerPoll

### Modified Capabilities
- `grpc-client`: Service stubs change (2→3), GetLocations+GetModels→GetCatalog, timestamp type changes
- `config-flow`: Validation uses GetCatalog instead of GetLocations+GetModels loop
- `proto-codegen`: v1→v2 proto source path, 4 files instead of 2, common.proto import handling
- `weather-entities`: ForecastData.updated_at becomes datetime, HourlyForecastData field rename timestamp→valid_at
- `stream-lifecycle`: StreamConfig moves to AdminService stub, forecast/enrichment streams move to WeatherService stub

## Impact

- **Proto stubs**: Complete regeneration — all generated `_pb2.py` / `_pb2_grpc.py` files replaced
- **grpc_client.py**: Major rewrite — new stubs, new methods, updated converters
- **coordinator.py**: Initial load flow changes (GetCatalog replaces multi-call pattern)
- **config_flow.py**: Validation logic simplified (single GetCatalog call)
- **models.py**: Dataclass field changes (timestamps, new ModelStatusData)
- **weather.py**: Minor field access updates
- **__init__.py**: New platform (button), new service registration
- **New files**: `button.py`, `services.yaml`
- **Tests**: All fixtures and mocks need v2 updates
- **Makefile**: Proto generation path update
