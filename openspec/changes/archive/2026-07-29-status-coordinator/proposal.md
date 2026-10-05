## Why

Server status data (API budget, uptime, model statuses) is fetched via a custom `_run_status_poll()` background loop every 30 minutes. This bypasses HA's `DataUpdateCoordinator` infrastructure — no automatic retry with backoff, no HA logging, no adaptive polling. The 30-minute interval is also too slow for monitoring API usage. A separate lightweight coordinator with `update_interval=30s` is the HA-idiomatic solution.

## What Changes

- New `NjordStatusCoordinator` — a standard `DataUpdateCoordinator[ServerStatusData]` with `update_interval=timedelta(seconds=30)` that only calls `OpsService.GetStatus`.
- Remove `_run_status_poll()` background task and `server_status` field from `NjordDataCoordinator` / `NjordCoordinatorData`.
- Remove status fetch from `_async_update_data()` in the main coordinator (it was part of the initial unary load).
- `NjordApiBudgetSensor` and `NjordUptimeSensor` switch from `CoordinatorEntity[NjordDataCoordinator]` to `CoordinatorEntity[NjordStatusCoordinator]`.
- `__init__.py` creates and stores the status coordinator alongside the data coordinator.

## Capabilities

### New Capabilities

- `status-coordinator`: Dedicated polling coordinator for server status data with 30s interval.

### Modified Capabilities

(No existing spec changes — the sensor behavior is unchanged, only the data source coordinator changes.)

## Impact

- `custom_components/njord/coordinator.py`: New `NjordStatusCoordinator` class. Remove `_run_status_poll()`, `_STATUS_POLL_INTERVAL`, `server_status` from `NjordCoordinatorData`, and status fetch from `_async_update_data()`.
- `custom_components/njord/__init__.py`: Create and store `NjordStatusCoordinator`, pass it to sensor platform.
- `custom_components/njord/sensor.py`: `NjordApiBudgetSensor` and `NjordUptimeSensor` take `NjordStatusCoordinator` instead of `NjordDataCoordinator`.
- `custom_components/njord/button.py`: Check if trigger poll button references status — if so, update.
- Tests: Update status-related tests, add coordinator tests for the new class.

## Non-goals

- Adding a `StreamStatus` RPC to njord — the unary `GetStatus` with 30s polling is sufficient for diagnostic data.
- Changing the polling interval dynamically based on budget thresholds.
- Moving model status sensors to the new coordinator (they don't exist as entities yet).

## gRPC Endpoints

All existing, no changes needed:

- `OpsService.GetStatus` (unary) — used by the new status coordinator.
