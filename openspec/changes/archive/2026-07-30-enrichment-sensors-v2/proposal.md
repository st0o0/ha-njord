## Why

The enrichment system delivers rich derived data (Beaufort, wind chill, dewpoint comfort) and alert events that aren't fully surfaced to the user. Derived per-horizon values sit unused in `DerivedData.by_horizon`, alerts are modeled as sensors (static state) rather than events (things that happen), and the trend sensor buries the most user-facing value (`weather_change_description`) in attributes instead of showing it as the primary state.

## What Changes

- **Derived sensors**: Add Beaufort, Wind Chill, and Dewpoint Comfort sensors per location. These read the current horizon from `DerivedData.by_horizon` using a shared horizon-offset helper (extracted from the consensus entity). Requires adding `derived_updated_at` to `EnrichmentData` for accurate offset calculation.
- **Alert events replace alert sensors**: **BREAKING** — Remove the 9 `NjordAlertSensor` entities and replace them with a single `event` entity per location. Events fire when an alert appears, changes severity, or clears (entwarnung). Event data includes type, severity, confidence, trigger_value, threshold, hours_until, duration_hours.
- **Trend sensor redesign**: Change `NjordTrendSensor` state from `stability_label` to `weather_change_description`. Move `stability_label` into extra_state_attributes alongside existing trend attributes.

## Capabilities

### New Capabilities
- `derived-sensors`: Beaufort, Wind Chill, and Dewpoint Comfort sensors sourced from `DerivedData.by_horizon` with horizon-offset tracking.
- `alert-events`: HA `event` platform entity that fires typed events for weather alerts (frost, heat, storm, etc.) with severity transitions.
- `horizon-offset-helper`: Shared utility for calculating the current horizon offset from an enrichment timestamp, reusable across consensus and derived entities.

### Modified Capabilities
- `enrichment-sensors`: Alert sensors removed from sensor platform. Trend sensor state changes from `stability_label` to `weather_change_description`.
- `enrichment-merge`: Must track `derived_updated_at` timestamp on enrichment events (analogous to `consensus_updated_at`).

## Non-goals

- Admin controls (SetSettings, SetBudget, etc.) — ha-njord remains a pure consumer.
- Calendar entity for forecast events.
- WMO Description sensor (redundant with weather entity condition).
- Options flow for enrichment toggling.

## gRPC Endpoints

All required endpoints already exist and are implemented in `grpc_client.py`:
- `GetEnrichments()` — initial fetch (has derived + alerts)
- `StreamEnrichments()` — live updates (pushes derived + alert events)

No new gRPC work needed. The `derived_updated_at` timestamp must be extracted from the `EnrichmentEvent.updated_at` field already present in the stream proto.

## Impact

- **`sensor.py`**: Remove 9 `NjordAlertSensor` classes and factory registrations. Change `NjordTrendSensor` state source.
- **`models.py`**: Add `derived_updated_at: datetime | None` to `EnrichmentData`.
- **`grpc_client.py`**: Populate `derived_updated_at` from stream events.
- **`coordinator.py`**: Merge `derived_updated_at` in enrichment merge logic.
- **`weather.py`**: Extract horizon-offset logic into shared helper.
- **New `event.py`**: Alert event platform (replaces alert sensors).
- **New shared module**: Horizon offset utility.
- **`__init__.py`**: Register `event` platform, remove alert sensor setup adjustments.
- **Tests**: Update/remove alert sensor tests, add derived sensor + event tests.
- **Breaking**: Users with automations on `sensor.njord_*_alert` entities must migrate to `event.njord_*_weather_alert` triggers.
