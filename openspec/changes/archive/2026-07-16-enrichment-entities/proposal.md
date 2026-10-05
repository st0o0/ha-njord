## Why

njord's gRPC API provides rich enrichment data beyond raw forecasts — weather alerts, activity indices, energy optimization, weather trends, derived metrics, model performance history, and multi-model consensus. ha-njord currently ignores all of this. These enrichments are the high-value features that make njord more than "yet another weather integration": automated alert entities for safety, COP-optimal scheduling for heat pumps, BBQ/laundry indices for lifestyle dashboards, and a consensus weather entity that's more reliable than any single model.

Live-tested on 2026-07-16: all 7 enrichment categories return real data from njord running locally.

## What Changes

### Foundation
- Add enrichment dataclasses to `custom_components/njord/models.py`
- Add `GetEnrichments()` and `StreamEnrichments()` to `custom_components/njord/grpc_client.py`
- Update `custom_components/njord/coordinator.py` to fetch enrichments alongside forecasts
- Fix DEFAULT_PORT from 8080 to 8081 in `custom_components/njord/const.py` (8080 is HTTP/1.1, 8081 is gRPC/HTTP2)

### Alert Entities (binary_sensor platform)
- 9 `binary_sensor` entities per location (frost, heat, storm, heavy_rain, uv, fog, snow, pressure_drop, thunderstorm)
- State: on/off based on severity > NONE
- Attributes: severity (yellow/orange/red), confidence (0.0–1.0)
- device_class: safety

### Sensor Entities (sensor platform)
- **Indices** (8 sensors): laundry, outdoor, running, cycling, bbq, irrigation, solar, ventilation (0–100%)
- **VPD** (1 sensor): value in kPa, category attribute
- **Energy** (5 sensors): heating_demand, cop_estimate, shading, battery_strategy, night_cooling
- **Trends** (1 sensor): stability_label state, timing attributes (precip_starts_in_hours, etc.)
- **Derived scalars** (2 sensors + 1 binary_sensor): sunshine_pct, diurnal_amplitude, inversion
- **History** (1 diagnostic sensor): weighted_temperature, model performance attributes

### Consensus Weather Entity
- 1 `weather` entity per location using multi-model consensus median values
- Hourly + daily forecasts built from consensus data across all available models
- Agreement percentage as extra state attribute

## Non-goals

- No mutation RPCs — ha-njord remains read-only
- No per-horizon derived sensors — horizon data goes as attributes on weather entities
- No configuration UI for enabling/disabling individual enrichment categories (all enabled by default, njord controls which are computed)
- No MQTT integration — enrichments come via gRPC only

## Capabilities

### New Capabilities
- `enrichment-alerts`: Weather alert binary_sensor entities with severity and confidence
- `enrichment-sensors`: Activity indices, energy optimization, trend, derived, and history sensor entities
- `consensus-weather`: Multi-model consensus weather entity

### Modified Capabilities
- `grpc-client`: Add GetEnrichments + StreamEnrichments RPCs and enrichment data model converters
- `weather-entities`: Add per-horizon derived data as attributes (beaufort, dewpoint_comfort, wmo_description)

## Impact

- **Modified files**: `models.py`, `grpc_client.py`, `coordinator.py`, `const.py`, `__init__.py`, `weather.py`, `strings.json`, `translations/de.json`
- **New files**: `binary_sensor.py`, `sensor.py`
- **New tests**: `tests/test_binary_sensor.py`, `tests/test_sensor.py`, `tests/test_enrichment_models.py`
- **gRPC endpoints required**: `GetEnrichments` (exists in njord), `StreamEnrichments` (exists in njord) — both confirmed working via live testing
