## Why

Three production issues with entity lifecycle:

1. **Random entities unavailable after HA restart.** When njord hasn't finished loading all models during ha-njord's first refresh, individual `GetForecast` calls fail silently. The entity gets created but `_forecast_data` returns `None`, making it permanently unavailable until a manual integration reload.
2. **`supported_features` caching mismatch.** HA caches `supported_features` at entity registration time. Our dynamic property can't change the cached value, so models without daily data still show an empty "Forecast:" section from a stale registration.
3. **Entity flood.** Every location creates ~30 entities. Most users only care about weather and alerts. Index sensors, energy metrics, derived data, and diagnostic sensors should be opt-in.

## What Changes

- **Weather entity `available` property.** Weather entities get an explicit `available` property that returns `True` when the forecast key exists in coordinator data (even with empty hourly/daily), `False` when missing entirely. Entities degrade gracefully instead of showing "unavailable".
- **Set `supported_features` once at init.** Evaluate hourly/daily data presence at entity construction time and store as `_attr_supported_features`. No dynamic property — HA caches it anyway. If data arrives later via streaming that adds daily, the features won't change mid-session, which is acceptable.
- **Default-disabled enrichment entities.** Set `_attr_entity_registry_enabled_default = False` on all sensor and binary_sensor entities except alert binary sensors. Weather entities and alert sensors remain enabled by default.
- **Resilient first refresh.** When `GetForecast` fails for a specific model during first refresh, log the warning but still register the forecast key with an empty `ForecastData` stub so the entity starts as "available but no data" rather than "unavailable".

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `weather-entities`: Add `available` property, set `supported_features` at init instead of dynamically, handle missing forecast data gracefully.
- `enrichment-sensors`: Set `_attr_entity_registry_enabled_default = False` on all non-alert sensors.
- `enrichment-alerts`: Alert binary sensors remain enabled by default. Inversion binary sensor becomes disabled by default.

## Non-goals

- Aggregating daily forecasts from hourly data.
- Retry logic for failed first-refresh forecasts (streaming will deliver updates).
- Changing config flow or entity naming.

## gRPC Endpoints Required

No new endpoints. All existing endpoints unchanged.

## Impact

- **`custom_components/njord/weather.py`** — Add `available` property, change `supported_features` from property to init-time attribute.
- **`custom_components/njord/coordinator.py`** — On forecast fetch failure, insert empty `ForecastData` stub instead of skipping.
- **`custom_components/njord/sensor.py`** — Add `_attr_entity_registry_enabled_default = False` to base `_NjordEnrichmentSensor` class.
- **`custom_components/njord/binary_sensor.py`** — Add `_attr_entity_registry_enabled_default = False` to `NjordInversionEntity` only. Alerts remain enabled.
- **Tests** — Update weather entity tests for `available` property and init-time features. Add tests for disabled-by-default behavior.
