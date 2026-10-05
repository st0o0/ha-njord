## Why

Live testing in HA revealed three usability issues: sensors have no icons or descriptions so users can't tell what "COP Estimate" or "Shading" means at a glance; some weather entities don't show forecast cards (hourly/daily) in the HA dashboard; and alert binary sensors show "Unsafe/Safe" with no visual differentiation. These are polish issues that make the integration feel unfinished.

## What Changes

- Add MDI icons to all sensor and binary_sensor entities via `_attr_icon`
- Add `translation_key` and entity translations so HA can localize entity names
- Fix weather entity forecast rendering — ensure `async_forecast_daily` and `async_forecast_hourly` return proper `Forecast` dicts with all required keys
- Add missing weather attributes (`native_apparent_temperature`, `cloud_cover`) to model weather entities
- Improve alert binary sensor icons per alert type (e.g., `mdi:snowflake-alert` for frost, `mdi:weather-sunny-alert` for UV)

## Non-goals

- No new entities or enrichment types
- No changes to gRPC client or data models
- No new gRPC endpoints needed

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `enrichment-sensors`: Adding icons, translation keys, and entity descriptions to all sensor entities
- `enrichment-alerts`: Adding per-type icons and translation keys to alert binary sensors
- `weather-entities`: Fixing forecast rendering, adding missing attributes (apparent_temperature, cloud_cover)

## Impact

- **Modified**: `custom_components/njord/sensor.py` — add icons and translation_key to all sensors
- **Modified**: `custom_components/njord/binary_sensor.py` — add per-type icons and translation_key
- **Modified**: `custom_components/njord/weather.py` — add missing attributes, verify forecast output
- **Modified**: `custom_components/njord/strings.json` — add entity translations
- **Modified**: `custom_components/njord/translations/de.json` — German entity translations
- **Modified**: Tests — update assertions for new attributes
