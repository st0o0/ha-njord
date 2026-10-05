## Why

njord's `Alert` protobuf message now includes raw trigger values (the actual measured/forecast value that caused the alert, the threshold, peak, timing). ha-njord currently only shows severity and confidence on alert binary sensors — users can't see *what* triggered the alert (e.g. UV index of 8.5 against a threshold of 6.0) or *when* it will occur.

## What Changes

- Update `AlertData` dataclass with new fields: `trigger_value`, `threshold`, `peak_value`, `hours_until`, `duration_hours`
- Update `_to_alert()` converter in `grpc_client.py` to parse the new proto fields
- Extend `NjordAlertEntity.extra_state_attributes` to expose all new values
- Proto stubs already regenerated (proto was updated in prior step)

## Non-goals

- Changing alert on/off logic (still based on severity != none)
- Creating separate sensor entities for trigger values
- Adding unit-of-measurement mapping per alert type (HA doesn't support dynamic UoM on binary sensors)
- Modifying AlertConfig or any write operations

## gRPC Endpoints

- `GetEnrichments` (existing) — Alert messages in response already carry the new fields
- `StreamEnrichments` (existing) — EnrichmentEvent with alerts payload carries same Alert messages

No new endpoints needed. Proto already updated and stubs regenerated.

## Capabilities

### New Capabilities

- `alert-trigger-values`: Expose raw trigger values, thresholds, peak values, and timing on alert binary sensor entities

### Modified Capabilities

- `enrichment-alerts`: AlertData model gains new fields; binary sensor attributes extended

## Impact

- `custom_components/njord/models.py` — `AlertData` dataclass extended
- `custom_components/njord/grpc_client.py` — `_to_alert()` converter updated
- `custom_components/njord/binary_sensor.py` — `extra_state_attributes` extended
- `tests/` — updated tests for converter and entity attributes
