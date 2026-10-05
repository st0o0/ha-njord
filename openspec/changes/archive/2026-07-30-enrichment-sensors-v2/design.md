## Context

ha-njord exposes njord enrichment data via sensor and binary_sensor platforms. The current implementation has three gaps:
1. `DerivedData.by_horizon` per-hour values (beaufort, wind_chill, dewpoint_comfort) are unused
2. Weather alerts are modeled as sensors (continuous state) rather than events (transitions)
3. The trend sensor's most user-facing value (`weather_change_description`) is buried in attributes

The integration already has streaming, enrichment merge, and a horizon-offset pattern in the consensus entity.

## Goals / Non-Goals

**Goals:**
- Surface derived per-horizon data as sensors with proper time-tracking
- Replace alert sensors with event entities that fire on alert transitions
- Make weather change description the primary trend sensor value

**Non-Goals:**
- Admin controls or write access to njord
- Options flow for enrichment toggling
- Calendar entity

## Decisions

### D1: Shared horizon offset module

**Choice:** Extract horizon offset logic into `custom_components/njord/horizon.py` with two functions:
- `current_horizon_offset(updated_at: datetime) -> int`
- `get_horizon_value(horizons: list, offset: int, attr: str) -> T | None`

**Why:** Both the consensus weather entity and derived sensors need the same offset calculation. Duplicating is error-prone. A small utility module is the right granularity — no class, no abstraction layer, just two pure functions.

**Alternative:** Mixin or base class. Rejected — the consumers are different entity types (`WeatherEntity` vs `SensorEntity`), so a shared base doesn't fit cleanly.

### D2: `derived_updated_at` timestamp

**Choice:** Add `derived_updated_at: datetime | None` to `EnrichmentData`. Populate it from `EnrichmentEvent.updated_at` when the payload is `derived`. Update `_to_enrichment_event()` and `merge_enrichment()` to handle it.

**Why:** Without knowing when derived data was computed, the horizon offset drifts. The stream proto already carries `updated_at` on every event — we just need to capture it for the derived case (like we already do for consensus).

**Alternative:** Use the coordinator's `last_update_success_time`. Rejected — that timestamp reflects the last *any* update, not specifically when derived data was refreshed.

### D3: Alert events replace sensors entirely

**Choice:** Remove all 9 `NjordAlertSensor` classes. Add a single `NjordWeatherAlertEvent` entity per location using HA's `event` platform. The entity tracks previous alert state internally to detect transitions.

**Why:** Alerts are inherently event-like — they start, change severity, and clear. Sensors force a continuous-state model that doesn't match. One event entity per location (instead of 9 per alert type) reduces entity count from 9×N to 1×N.

**Alternative:** Keep sensors alongside events. Rejected — the user explicitly wants replacement, and maintaining both is pointless complexity.

### D4: Event state tracking

**Choice:** The event entity maintains a `dict[str, str]` mapping `alert_type → severity`. On each enrichment update, it diffs current alerts against this map to determine which events to fire. The map is initialized on first update (no events fired for initial state).

**Why:** The enrichment stream delivers full alert snapshots per event. Diffing against previous state is the only way to detect transitions. Initializing without firing prevents spurious events on integration restart.

### D5: Trend sensor state swap

**Choice:** Change `NjordTrendSensor.native_value` from `stability_label` to `weather_change_description`. Add `stability_label` to `extra_state_attributes`.

**Why:** The weather change description is natural language ("Rain starting in 3h") — much more useful as a dashboard card primary value than a technical label like "stable".

## Risks / Trade-offs

- **Breaking change (alert sensors)** → Users with automations on alert sensors must migrate. Mitigation: clear documentation in release notes. The event model is strictly more capable (can trigger on start/clear/escalation separately).
- **`derived_updated_at` not in proto response** → The unary `GetEnrichments()` response doesn't carry a per-field timestamp. Mitigation: for initial load, use `datetime.now(UTC)` as approximation (data is fresh from the server). Stream events carry `updated_at`.
- **Trend sensor returns None more often** → `weather_change_description` may be None when `stability_label` is set. Mitigation: acceptable — unknown state is correct when there's no description to show.

## Open Questions

None — all decisions are settled from the explore session.
