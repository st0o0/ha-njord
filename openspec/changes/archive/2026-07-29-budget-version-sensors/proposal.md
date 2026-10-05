## Why

The API budget is currently a single sensor (`sensor.server_api_budget`) with `usage_percent` as state and all limits/usage counts buried in attributes. This makes it hard to create HA automations that trigger on daily vs monthly budget separately, and impossible to show them as individual dashboard cards. The server version is hidden as an attribute on the uptime sensor.

## What Changes

- **New `sensor.server_monthly_usage`** — `usage_percent` for monthly budget as state (%), with `limit` and `used` as attributes.
- **New `sensor.server_daily_usage`** — daily equivalent, computed as `daily_used / daily_limit * 100`.
- **New `sensor.server_version`** — text sensor showing the njord container version from `GetStatus().version`.
- **Remove `sensor.server_api_budget`** — replaced by the two usage sensors. **BREAKING** for users with automations referencing this entity.
- **Remove `version` attribute** from `sensor.server_uptime` — moved to its own entity.

## Capabilities

### New Capabilities

- `budget-usage-sensors`: Monthly and daily API usage as separate percentage sensors with limit/used attributes.
- `version-sensor`: njord container version as a standalone text sensor.

### Modified Capabilities

(No existing spec modifications — the old `api_budget` sensor has no dedicated spec, it was part of the initial integration.)

## Impact

- `custom_components/njord/sensor.py`: Remove `NjordApiBudgetSensor`, add `NjordMonthlyUsageSensor`, `NjordDailyUsageSensor`, `NjordVersionSensor`. Update `NjordUptimeSensor` to remove version attribute.
- Tests: Update/add sensor tests for the new entities.

## Non-goals

- Update entity (`update` platform) with latest-version check against Docker Hub/GitHub — just show the running version.
- Keeping `sensor.server_api_budget` for backwards compatibility.

## gRPC Endpoints

All existing, no changes needed:

- `OpsService.GetStatus` — already provides `budget` and `version` fields.
