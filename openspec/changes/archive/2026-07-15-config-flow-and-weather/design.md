## Context

ha-njord has a project skeleton, generated proto stubs, and a working `NjordClient` with typed models. What's missing is the HA-facing layer: config flow for setup, weather entities for display, and the glue in `__init__.py` that ties the client to HA's lifecycle. After this change, a user can install ha-njord and see weather data.

## Goals / Non-Goals

**Goals:**
- User can add njord via HA's "Add Integration" UI
- Weather entities appear for every location×model combination
- Current conditions, temperature, humidity, wind, and hourly+daily forecasts display correctly
- Data refreshes automatically via `DataUpdateCoordinator`

**Non-Goals:**
- No streaming (uses polling coordinator initially — streaming upgrade is a follow-up)
- No enrichment entities
- No options flow
- No diagnostics

## Decisions

### 1. Data refresh: DataUpdateCoordinator with polling (not streaming yet)

Use HA's standard `DataUpdateCoordinator` with a 5-minute poll interval. Each update calls `get_config()` + `get_forecast()` for all location×model pairs.

Rationale: `DataUpdateCoordinator` is HA's blessed pattern for data refresh. It handles error counting, logging, and entity availability automatically. Streaming is the architectural vision, but starting with polling lets us validate the entity layer first without mixing concerns.

Alternative considered: Jump straight to streaming — more aligned with the vision but adds complexity (background tasks, reconnect handling, manual availability management) before the basic entity layer is proven. Streaming upgrade is the logical next change.

### 2. Config Flow: Two steps (connect → confirm)

Step 1 (`user`): User enters host + port. Flow validates by calling `get_locations()` via `NjordClient`. If it fails, show error.

Step 2 (abort or create): On success, show the number of locations and models discovered. Create `ConfigEntry` with host+port. No model selection — ha-njord shows everything njord provides.

Unique ID: `{host}:{port}` — prevents duplicate entries for the same njord instance.

### 3. Entity naming: `weather.njord_{location}_{model}`

Entity IDs follow the pattern `weather.njord_{location}_{model}` with underscores replacing hyphens and spaces. The friendly name is `njord {Location} {Model}`.

Device grouping: One device per location (`njord {location}`), with all model entities grouped under it.

### 4. Condition mapping: Static dictionary in `condition_mapper.py`

A simple `WMO_TO_HA` dictionary maps WMO weather codes to HA condition strings. Tuple values `(day_condition, night_condition)` handle day/night variants (e.g., WMO 0 → `"sunny"` by day, `"clear-night"` at night).

### 5. Weather entity: WeatherEntity with native forecast support

Use HA's `WeatherEntity` base class with `Forecast` support (the modern `async_forecast_daily` / `async_forecast_hourly` methods, not the deprecated `forecast` attribute). This requires `supported_features` to declare `FORECAST_DAILY | FORECAST_HOURLY`.

### 6. Coordinator data structure

The coordinator stores a dict keyed by `(location, model)` tuples, with `ForecastData` values. On each update cycle:

1. `get_config()` → discover current locations and their models
2. `get_forecast(loc, model)` for each combination
3. Store results in `coordinator.data`

Entities read from this shared data on each coordinator update.

## Risks / Trade-offs

- **[Polling overhead]** → Each poll calls `get_forecast()` N times (locations × models). For 2 locations × 8 models = 16 RPCs per cycle. At 5min intervals this is fine. Mitigation: streaming upgrade eliminates this.
- **[No dynamic entity add/remove]** → If njord's config changes (new location added), the coordinator won't create new entities until HA restart. Mitigation: acceptable for MVP; streaming config change will handle this later.
- **[WMO mapping gaps]** → Some WMO codes may not have HA equivalents. Mitigation: unmapped codes fall back to `"exceptional"`.
