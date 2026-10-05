## Why

ha-njord polls njord every 5 minutes via unary gRPC calls (`GetForecast`, `GetEnrichments`, `GetConfig`). njord already exposes server-streaming RPCs (`StreamForecasts`, `StreamEnrichments`, `StreamConfig`) and the gRPC client in ha-njord already implements them with reconnect logic — but nothing calls them. Switching to streaming gives instant updates (critical for weather alerts), eliminates redundant polling when nothing changed, and enables dynamic entity creation when locations are added in njord.

## What Changes

- **Replace polling coordinator with stream-driven updates.** `NjordDataCoordinator` keeps `update_interval=None` (no polling). Three asyncio background tasks consume the server streams and push data into the coordinator via `async_set_updated_data()`.
- **Enrichment merge logic.** `StreamEnrichments` delivers partial updates (only the changed enrichment type). Incoming events are merged into the existing `EnrichmentData` per location using `dataclasses.replace()` to preserve immutability.
- **Dynamic entity creation from config stream.** `StreamConfig` detects new locations and creates weather + sensor entities on the fly. Removed locations are ignored (entities stay with stale data).
- **Startup sequence: snapshot + subscribe.** First refresh uses unary calls (existing behavior) to populate initial state, then streams are started. Avoids race conditions where entities exist before data arrives.
- **No polling fallback.** On stream disconnect, the client's existing exponential backoff reconnect handles recovery. Last known state is retained.

## Capabilities

### New Capabilities

- `stream-lifecycle`: Management of the three streaming background tasks (start, stop, reconnect coordination, cancellation on unload). Covers the startup sequence (unary first-refresh → stream subscribe) and graceful shutdown.
- `enrichment-merge`: Granular merge of partial `EnrichmentEvent` updates into the coordinator's enrichment data per location, preserving fields not included in the event.
- `dynamic-entity-creation`: Detecting new locations from config stream events and creating weather/sensor entities at runtime without requiring a config entry reload.

### Modified Capabilities

- `grpc-client`: No API changes needed — streaming methods already exist. May need minor adjustments to callback signatures or error propagation.
- `weather-entities`: Entities must accept being added after initial setup. `async_add_entities` callback must be retained for later use.
- `enrichment-sensors`: Same as weather-entities — must support dynamic addition.

## Non-goals

- **Removing locations/entities at runtime.** Entities for removed locations stay; users can manually remove them.
- **Polling fallback.** No automatic switch to polling on stream failure.
- **Config flow changes.** Host + Port entry stays the same.
- **New enrichment entity types.** This change wires up streaming for existing entity types only.

## gRPC Endpoints Required

| Endpoint | Status | Used for |
|---|---|---|
| `StreamForecasts` | Exists in proto + client | Forecast stream listener |
| `StreamEnrichments` | Exists in proto + client | Enrichment stream listener |
| `StreamConfig` | Exists in proto + client | Config change detection |
| `GetForecast` | Exists, already used | Initial state (first refresh) |
| `GetEnrichments` | Exists, already used | Initial state (first refresh) |
| `GetConfig` | Exists, already used | Initial state (first refresh) |

## Impact

- **`coordinator.py`** — Major rewrite: remove `_async_update_data` polling, add stream listener tasks and enrichment merge.
- **`__init__.py`** — Start/stop stream tasks on entry setup/unload.
- **`weather.py`** — Store `async_add_entities` callback; support late entity addition.
- **`sensor.py` / `binary_sensor.py`** — Same pattern as weather.py for dynamic addition.
- **`models.py`** — No changes (frozen dataclasses stay, merge uses `replace()`).
- **`grpc_client.py`** — Minimal or no changes (streaming already implemented).
- **Tests** — New tests for merge logic, stream lifecycle, dynamic entity creation.
