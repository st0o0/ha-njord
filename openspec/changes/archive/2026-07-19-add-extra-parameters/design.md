## Context

njord's `HourlyForecast` and `DailyForecast` protobuf messages now carry a `repeated ParameterValue extra` field. Each `ParameterValue` has a `name` (string) and a `oneof value { numeric, text, flag }`. ha-njord currently ignores these fields because the proto was not yet updated and the data pipeline has no slot for dynamic parameters.

The existing pipeline is: proto stubs → `_to_hourly()`/`_to_daily()` converters → frozen dataclasses → `NjordWeatherEntity` properties and forecast callbacks.

## Goals / Non-Goals

**Goals:**
- Pass all extra parameters through the full pipeline without filtering
- Expose extras on the HA entity as `extra_state_attributes` (current hour)
- Include extras as additional keys in hourly/daily `Forecast` dicts
- Work transparently with streaming updates (same message types)

**Non-Goals:**
- Filtering, renaming, or transforming parameter names
- Creating dedicated sensor entities per extra parameter
- Modifying the ConsensusWeatherEntity
- Unit conversion on extra values

## Decisions

### 1. Flat dict representation

**Decision**: Represent `extra` as `dict[str, float | str | bool]` on the dataclasses.

**Why**: ParameterValue's oneof collapses to exactly one Python primitive. A flat dict is trivially serializable, iterable, and merges cleanly into HA's attribute/forecast structures.

**Alternative considered**: `list[tuple[str, Any]]` — rejected because duplicate names are not expected and dict is more ergonomic for attribute access.

### 2. No prefix on attribute/forecast keys

**Decision**: Extra parameter names are passed through as-is (e.g. `soil_moisture_0_to_10cm`, not `njord_soil_moisture_0_to_10cm`).

**Why**: njord already uses descriptive, namespaced parameter names. Adding a prefix would make templates/automations more verbose without real collision risk — HA's built-in weather attributes use short names like `temperature` which won't collide with njord's Open-Meteo-style naming.

**Alternative considered**: `njord_` prefix — rejected for verbosity; can be revisited if collisions emerge.

### 3. Current hour extras as extra_state_attributes

**Decision**: `NjordWeatherEntity.extra_state_attributes` returns the `extra` dict from `data.hourly[0]`.

**Why**: Provides immediate template/automation access (`{{ state_attr('weather.njord_x_y', 'cape') }}`). Minimal overhead since the data is already in memory.

### 4. Extras merged into Forecast dicts

**Decision**: In `_async_forecast_hourly` and `_async_forecast_daily`, merge the `extra` dict into each `Forecast` TypedDict.

**Why**: HA's `weather.get_forecasts` service passes through extra keys in the response dict. Custom Lovelace cards and automations can consume them. This is widely used by other integrations (e.g. OpenWeatherMap extras).

## Risks / Trade-offs

- **Untyped attribute explosion** → If njord sends many extras, entity attributes grow large. Mitigation: acceptable since HA handles large attribute dicts fine; no filtering needed now.
- **HA Forecast TypedDict contract** → Extra keys are not officially typed but work in practice. Mitigation: HA has never stripped unknown keys from forecast responses; if they do, extras just disappear gracefully (no crash).
- **Proto field numbering** → `extra` is field 14 (hourly) and 10 (daily). Existing clients that don't know the field simply ignore it (protobuf wire compatibility). No migration needed.
