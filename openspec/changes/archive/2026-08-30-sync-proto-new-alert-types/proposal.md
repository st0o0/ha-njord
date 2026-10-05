## Why

njord upstream added 5 new weather alert types (ice, wind chill, visibility, tropical night, humidity) and expanded AlertConfig to support multi-threshold alerts. ha-njord's proto stubs and alert sensor registry are out of sync and miss these new alert types entirely.

## What Changes

- Copy updated `admin.proto` and `common.proto` from njord and regenerate gRPC stubs
- Register 5 new alert types in `sensor.py` with correct units, device classes, icons, and precision
- Update the existing `alert-sensors` spec to reflect 14 total alert types (was 9)
- Update tests to cover the new alert types

## Non-goals

- Exposing AlertConfig thresholds in HA (ha-njord reads alerts from forecasts, not config)
- Adding UI for configuring alert thresholds (that's njord's domain)
- Changing how existing 9 alert types work

## Capabilities

### New Capabilities

_(none — this extends an existing capability)_

### Modified Capabilities

- `alert-sensors`: Add 5 new alert types (ice, wind_chill, visibility, tropical_night, humidity) with their units, device classes, icons, and precision values

## Impact

- `protos/njord/v2/admin.proto` — replaced with upstream version
- `protos/njord/v2/common.proto` — replaced with upstream version
- `custom_components/njord/proto/njord/v2/` — regenerated stubs (admin_pb2.py, common_pb2.py)
- `custom_components/njord/sensor.py` — 5 new entries in ALERT_TYPES, ALERT_NAMES, ALERT_UNITS, ALERT_DEVICE_CLASSES, ALERT_PRECISION, ALERT_ICONS
- `tests/` — updated alert test fixtures and assertions

## gRPC Endpoints

All endpoints already exist in njord v2 — no new RPCs needed. The new alert types flow through the existing `GetForecast` / streaming responses that already carry `Alert` messages with `AlertType` enum values.
