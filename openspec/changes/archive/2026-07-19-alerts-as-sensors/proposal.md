## Why

With the addition of `trigger_value` and `threshold` to alerts, binary sensors (on/off) no longer serve alerts well. A sensor entity with the actual trigger value as state (e.g. UV index 8.5, temperature 38.2°C) enables HA history graphs, threshold-based automations, and is more informative at a glance. The binary sensor only answered "is there an alert?" — the sensor answers "what is the value and how bad is it?"

## What Changes

- **BREAKING**: Remove `NjordAlertEntity` (binary_sensor) for all 9 alert types
- Add `NjordAlertSensor` (sensor) with `trigger_value` as native state
- Map unit-of-measurement per alert type (°C, km/h, UV index, mm, hPa)
- Expose severity, confidence, threshold, peak_value, hours_until, duration_hours as attributes
- State is `0` when alert is inactive (severity=none), allowing graphs to show baseline
- Keep inversion binary_sensor unchanged (it's boolean by nature)

## Non-goals

- Adding alert history/tracking over time (HA recorder handles this)
- Combining alerts into a single summary sensor
- Modifying njord's alert generation logic
- Adding notification/automation scaffolding

## gRPC Endpoints

- `GetEnrichments` (existing) — same Alert messages, no change
- `StreamEnrichments` (existing) — same payload

No new endpoints needed.

## Capabilities

### New Capabilities

- `alert-sensors`: Sensor entities for weather alerts with numeric trigger values as state

### Modified Capabilities

- `enrichment-alerts`: Alert platform changes from binary_sensor to sensor (breaking)

## Impact

- `custom_components/njord/binary_sensor.py` — remove `NjordAlertEntity` class and alert setup logic (keep `NjordInversionEntity`)
- `custom_components/njord/sensor.py` — add `NjordAlertSensor` class with unit mapping
- `tests/test_binary_sensor.py` — remove alert tests, keep inversion tests
- `tests/test_sensor.py` — add alert sensor tests
- `README.md` — update entity reference
