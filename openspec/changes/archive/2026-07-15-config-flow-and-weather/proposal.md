## Why

ha-njord has a working gRPC client but no way to use it from Home Assistant. Without a config flow, the integration doesn't appear in HA's UI. Without weather entities, there's nothing to display. This change connects the dots — after it, a user can add njord as an integration and see weather data in HA.

## What Changes

- Create `config_flow.py` — two-step setup: enter host+port, validate via `get_locations()`, show summary, create ConfigEntry
- Create `strings.json` and `translations/de.json` — UI text for the config flow
- Create `condition_mapper.py` — WMO weather_code + is_day → HA condition strings (`sunny`, `cloudy`, `rainy`, ...)
- Create `weather.py` — `NjordWeatherEntity` per location×model with state, attributes, and hourly+daily forecast support
- Rewrite `__init__.py` — real `async_setup_entry` that creates a `NjordClient`, fetches initial state, starts background streaming tasks, and forwards to the weather platform

## Non-goals

- No Options Flow — njord controls the config, ha-njord just reflects it
- No enrichment entities (alerts, indices, energy) — Phase 2
- No streaming updates in this change — initial implementation uses polling via `DataUpdateCoordinator` for simplicity, streaming upgrade follows
- No Zeroconf/SSDP discovery
- No diagnostics platform

## Capabilities

### New Capabilities
- `config-flow`: HA config flow for adding the njord integration (host+port input, gRPC validation, ConfigEntry creation)
- `weather-entities`: Weather platform with native HA weather entities per location×model, WMO condition mapping, hourly+daily forecast
- `condition-mapping`: WMO weather_code + is_day to HA condition string translation

### Modified Capabilities

(none)

## Impact

- **New files**: `config_flow.py`, `weather.py`, `condition_mapper.py`, `strings.json`, `translations/de.json`
- **Modified files**: `__init__.py` (stub → real setup), `manifest.json` (add `config_flow: true`)
- **gRPC endpoints required**: `GetLocations` (validation), `GetModels` (discovery), `GetForecast` (data), `GetConfig` (location details) — all exist in njord's protos
- **HA platforms**: `weather`
