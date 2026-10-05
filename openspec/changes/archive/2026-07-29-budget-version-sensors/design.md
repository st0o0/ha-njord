## Context

`NjordApiBudgetSensor` shows `usage_percent` with monthly+daily limits/usage as attributes. `NjordUptimeSensor` carries the version as an attribute. Both use `NjordStatusCoordinator` (30s polling).

## Goals / Non-Goals

**Goals:**
- Monthly and daily usage as separate sensors for independent automations/dashboards
- Version as its own sensor for visibility
- All three on the Server device, diagnostic category

**Non-Goals:**
- Update platform integration
- Keeping the old combined budget sensor

## Decisions

### 1. Percentage as state, absolutes as attributes

**Decision:** Each usage sensor computes `used / limit * 100` as state. Attributes carry `limit` and `used` for context.

**Why percentage?** Consistent with the old sensor, and more useful for automations ("trigger when daily usage > 80%") than raw counts.

**Edge case:** If `limit` is 0 (unconfigured), state is `None` (unavailable).

### 2. Daily usage needs computation

**Decision:** `daily_used / daily_limit * 100`. The `BudgetStatus` proto already provides both fields. No server-side change needed.

### 3. Version as text sensor

**Decision:** Simple sensor with `native_value = status.version`, no device class. Same Server device, diagnostic category.

### 4. Remove version from uptime sensor

**Decision:** `NjordUptimeSensor.extra_state_attributes` returns `None` instead of `{"version": ...}`. The version has its own entity now.

## Risks / Trade-offs

- **[Risk] Breaking change** → Users with automations on `sensor.server_api_budget` will need to update. Acceptable — the entity is diagnostic and unlikely to be widely automated.
