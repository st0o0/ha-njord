## Why

Entity naming across platforms (weather, sensor, binary_sensor, event, button) has diverged — inline DeviceInfo duplicates shared helpers, class names don't match their display names, and unique_id slugs use inconsistent suffix conventions. Cleaning this up now (before first public release) prevents breaking changes later and makes the entity registry predictable.

## What Changes

- **Consolidate DeviceInfo construction**: Move `_device_info()` and `_server_device_info()` to a shared module so all platforms reuse them instead of building DeviceInfo inline.
- **Rename `NjordHistorySensor` → `NjordModelPerformanceSensor`**: Align class name with its display name ("Model Performance") and slug (`model_performance`).
- **Add `_energy` suffix to energy sensor slugs**: Change `{loc}_{key}` → `{loc}_{key}_energy` to match the convention of other enrichment sensors (`_alert`, `_index`). **BREAKING** unique_id change.
- **Fix `NjordTargetSensor._attr_name`**: Remove redundant location/model prefix — use `"{Model} Target"` since the Server device already provides context, and multiple targets are distinguished by model name.
- **Normalize `NjordSunshineSensor` slug**: Change `{loc}_sunshine_pct` → `{loc}_sunshine` to remove unit info from the identifier. **BREAKING** unique_id change.

## Non-goals

- Changing any entity's functional behavior or data source.
- Adding new entities or removing existing ones.
- Modifying gRPC endpoints — all existing endpoints are sufficient.

## Capabilities

### New Capabilities
- `entity-naming-convention`: Defines the naming rules for entity unique_ids, display names, and class names across all platforms.

### Modified Capabilities
- `device-info-enrichment`: Requirement for shared DeviceInfo helpers extends from "button uses shared server DeviceInfo" to "ALL platforms use shared helpers for both location and server devices."

## Impact

- `custom_components/njord/sensor.py` — class rename, slug changes, name fix
- `custom_components/njord/binary_sensor.py` — replace inline DeviceInfo with shared helper
- `custom_components/njord/event.py` — replace inline DeviceInfo with shared helper
- `custom_components/njord/button.py` — replace inline DeviceInfo with shared helper
- `custom_components/njord/weather.py` — replace inline DeviceInfo with shared helper
- New shared module for DeviceInfo helpers (e.g. `helpers.py`)
- Tests referencing `NjordHistorySensor` or changed slugs
- Two **BREAKING** unique_id changes (energy suffix, sunshine slug) — acceptable pre-release

## gRPC Endpoints

No new endpoints required. All existing endpoints (`GetForecast`, `GetConfig`, `GetStatus`, `GetLocations`, `GetModels`) are sufficient.
