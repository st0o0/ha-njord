## Context

Server status (API budget, uptime) is currently fetched by a custom `_run_status_poll()` loop inside `NjordDataCoordinator` every 30 minutes. This is the only non-stream data path in the coordinator. All other data arrives via gRPC streams (forecasts, enrichments, config). The custom loop lacks HA's built-in error handling, backoff, and logging.

## Goals / Non-Goals

**Goals:**
- HA-idiomatic polling for status data via `DataUpdateCoordinator`
- 30-second update interval for near-real-time budget monitoring
- Clean separation: stream coordinator for weather data, polling coordinator for ops data

**Non-Goals:**
- Streaming status from njord (would require proto changes)
- Dynamic polling intervals
- Moving non-sensor status data (model statuses) — they stay on the main coordinator's initial fetch for now

## Decisions

### 1. Separate coordinator class

**Decision:** New `NjordStatusCoordinator(DataUpdateCoordinator[ServerStatusData])` with `update_interval=timedelta(seconds=30)`.

**Why not reuse the main coordinator?** The main coordinator has `update_interval=None` (stream-driven). Setting an interval would re-fetch all data (catalog, forecasts, enrichments) every 30s — wasteful and conflicting with the stream architecture.

**Why 30 seconds?** Fast enough for monitoring, light payload (single unary call returning a small protobuf). The `GetStatus` RPC is cheap on the server side.

### 2. Remove status from main coordinator

**Decision:** Remove `server_status` from `NjordCoordinatorData`, remove `_run_status_poll()` task, and remove the status fetch from `_async_update_data()`.

**Why remove from initial fetch too?** The status coordinator does its own first refresh. Having it in two places creates a race condition on startup and duplicate data.

### 3. Sensor wiring

**Decision:** `NjordApiBudgetSensor` and `NjordUptimeSensor` change their base from `CoordinatorEntity[NjordDataCoordinator]` to `CoordinatorEntity[NjordStatusCoordinator]`. They read directly from `self.coordinator.data` which is now `ServerStatusData` (not `NjordCoordinatorData.server_status`).

This simplifies the sensor code — no more `self.coordinator.data.server_status` nesting.

### 4. Integration setup

**Decision:** `__init__.py` creates the status coordinator, calls `async_config_entry_first_refresh()`, and stores it under `hass.data[DOMAIN][entry.entry_id]["status_coordinator"]`. The sensor platform reads it from there.

No changes to `async_unload_entry` needed — `DataUpdateCoordinator` cleanup is automatic when the config entry is unloaded.

## Risks / Trade-offs

- **[Trade-off] 30s polling vs stream** → Slightly more traffic than a stream, but `GetStatus` is tiny and avoids a njord proto change. Acceptable for diagnostic data.

- **[Risk] Status coordinator fails on startup** → `async_config_entry_first_refresh()` would raise `ConfigEntryNotReady`, blocking the entire integration. Mitigation: catch the error and let the status coordinator retry independently, so weather entities still load.
