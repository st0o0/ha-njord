## Context

ha-njord currently talks to njord via gRPC v1 (package `njord.v1`), using two service stubs: `ForecastServiceStub` and `ConfigServiceStub`. njord has shipped a v2 API that reorganizes services into three (`WeatherService`, `AdminService`, `OpsService`), merges the `GetLocations` + `GetModels` RPCs into a single `GetCatalog`, and migrates all temporal fields from `int64` epoch seconds to `google.protobuf.Timestamp`.

The current integration makes 10 of 15 v1 RPCs — all read-only. The v2 migration touches every layer from proto stubs through the gRPC client, coordinator, config flow, and weather entities.

## Goals / Non-Goals

**Goals:**
- Full compatibility with njord gRPC v2 — no v1 fallback
- Simplify initial load: replace N+1 `GetModels` calls with single `GetCatalog`
- Add `TriggerPoll` capability (button entity + HA service)
- Richer `ServerStatusData` with model statuses and active enrichments

**Non-Goals:**
- AdminService write RPCs (SetLocations, SetSettings, etc.)
- GetTargets integration
- New enrichment sensor types
- Backward compatibility with njord v1

## Decisions

### D1: Three stubs, one channel

Use a single gRPC channel with three service stubs attached. The channel management (`connect`/`close`/context manager) stays unchanged — stubs are just typed views over the same channel.

**Alternative**: Separate channels per service. Rejected — unnecessary complexity, all three services run on the same port.

### D2: GetCatalog replaces GetLocations + GetModels + get_model_info

`get_catalog()` returns `CatalogData` containing `list[LocationInfo]` (with model ID lists) and `dict[str, ModelInfoData]` (deduplicated). This single call replaces:
- `get_locations()` → `[loc.name for loc in catalog.locations]`
- `get_models(location)` → `loc.models` from the matching LocationInfo
- `get_model_info(location)` → `catalog.model_info` (global, not per-location)

The coordinator calls `get_catalog()` once during initial load. Config flow also uses it for validation.

**Alternative**: Keep separate `get_locations` + `get_models` methods that internally call GetCatalog. Rejected — leaky abstraction over a merged API.

### D3: Timestamp conversion strategy

`google.protobuf.Timestamp` fields are converted to `datetime` at the converter boundary in `grpc_client.py`:
- `pb.valid_at.ToDatetime()` → `datetime` (UTC, replaces `datetime.fromtimestamp(pb.timestamp, tz=UTC)`)
- `pb.updated_at.ToDatetime()` → `datetime` (replaces raw int64)

`ForecastData.updated_at` changes from `int` to `datetime`. `HourlyForecastData.timestamp` is renamed to `valid_at`.

Downstream code (weather.py, tests) adjusts to datetime comparisons instead of epoch int comparisons. The stub `ForecastData(updated_at=0)` for failed fetches becomes `ForecastData(updated_at=datetime.min.replace(tzinfo=UTC))`.

### D4: NjordConfigData sourcing

`GetConfig` (now AdminService) still provides settings: `default_models`, `horizons`, `forecast_days`, `poll_interval_seconds`. But locations now come from `GetCatalog` — `NjordConfig.locations` in AdminService is the authoritative list but `GetCatalog` provides the same `LocationInfo` plus deduplicated `ModelInfo`.

The coordinator uses `GetCatalog` as the primary source during initial load (it has everything needed), and `GetConfig` only for settings fields. The config stream (`StreamConfig` on AdminService) continues to detect new locations — `NjordConfig.locations` still carries the full location list.

### D5: TriggerPoll — button + service

**Button entity**: One `NjordTriggerPollButton` per config entry. Pressing it calls `TriggerPoll("", "")` (all locations, all models). Extra state attributes expose `triggered_count` and `last_triggered`.

**HA service**: `njord.trigger_poll` with optional `location` and `model` string fields (both default to empty = wildcard). Registered in `services.yaml` and handled in `__init__.py` via `hass.services.async_register`. The service targets no entity — it's a domain-level service that finds the client from `hass.data[DOMAIN]`.

**Alternative**: Per-location buttons. Rejected — combinatorial explosion, service call covers fine-grained use cases.

### D6: Proto file layout

v2 uses 4 proto files (`common.proto`, `weather.proto`, `admin.proto`, `ops.proto`) instead of v1's 2 (`forecast_service.proto`, `config_service.proto`). The `common.proto` file contains shared messages/enums imported by the other three.

Source protos: `protos/njord/v2/`
Generated stubs: `custom_components/njord/proto/njord/v2/`

The `__init__.py` in `proto/` updates its `sys.path` setup for v2 imports. The Makefile generates stubs for all 4 files with correct include paths for `common.proto` resolution.

## Risks / Trade-offs

**[Hard cutover]** → No v1/v2 negotiation. ha-njord and njord must be updated together. Acceptable since both are controlled by the same user and njord will drop v1.

**[Timestamp sentinel change]** → `updated_at=0` (int) becomes `updated_at=datetime.min` (datetime). Any test or code comparing against `0` must be updated. Mitigation: grep for `updated_at` usages and update systematically.

**[Config stream location source]** → AdminService's `StreamConfig` still provides `NjordConfig.locations`, which should match `GetCatalog`'s locations. If they diverge, config stream could trigger entity creation for locations not in the catalog. Mitigation: This can't happen — both read from the same njord state.

## Migration Plan

1. Copy v2 protos, regenerate stubs, delete v1
2. Update models.py (field renames, new dataclasses)
3. Rewrite grpc_client.py (3 stubs, GetCatalog, timestamp converters)
4. Update coordinator.py (GetCatalog flow, AdminService/OpsService routing)
5. Update config_flow.py (GetCatalog validation)
6. Update weather.py (field access changes)
7. Add button.py + services.yaml + wire in __init__.py
8. Update all tests

No rollback strategy — this is a clean v1→v2 cutover. If njord v2 has issues, fix forward.

## Open Questions

None — v2 proto files are finalized, all RPCs are available in njord.
