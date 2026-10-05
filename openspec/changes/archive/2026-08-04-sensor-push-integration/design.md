## Context

ha-njord is a pure consumer of njord's gRPC API. The new SensorService adds a write path: pushing HA sensor readings (indoor temperature, humidity) to njord so enrichment calculations can use real indoor data. The gRPC client layer (`push_sensor`, `stream_push_sensors`, proto stubs) already exists. What's missing is the HA integration layer: configuration UI, automatic forwarding, and a manual service.

The existing Options Flow has one step (`init`) with poll interval and enrichment toggles. We need to add a second step for sensor push configuration.

## Goals / Non-Goals

**Goals:**
- Users configure sensor push entirely within the integration's Options Flow — no blueprints, no YAML
- Per-location mapping of HA entities to njord sensor kinds (indoor_temperature, indoor_humidity)
- Automatic push on every `state_changed` event for configured entities
- Manual `njord.push_sensor` service for power users and automations
- Clean lifecycle: listeners created on setup, removed on unload

**Non-Goals:**
- No use of `StreamPush` — unary `Push` per change is sufficient
- No throttle/debounce — HA sensor frequencies are already reasonable
- No retry/queue on push failure
- No new HA entities created by this feature
- No validation of sensor values against njord's plausibility ranges (njord validates server-side)

## Decisions

### 1. Options Flow: Two-step flow with flat per-location layout

**Decision**: Add `async_step_sensors` as step 2 after the existing `init` step. The form shows entity selectors for each `(location, kind)` pair on a single screen.

**Why**: A flat layout keeps it simple for the common case (1 location) and remains readable for 2-3 locations. Dynamic multi-step (one step per location) adds complexity with no UX benefit given only 2 sensor kinds per location.

**Schema keys**: `{location}_{kind}` (e.g. `home_indoor_temperature`). Stored in options as:
```python
{
    "sensor_push": {
        "home": {
            "indoor_temperature": ["sensor.wz_temp", "sensor.sz_temp"],
            "indoor_humidity": ["sensor.bad_hum"]
        }
    }
}
```

**Alternative considered**: One Options Flow step per location — rejected because HA OptionsFlow dynamic step counts are awkward and the flat approach scales fine for the expected 1-3 locations.

### 2. Listener: EVENT_STATE_CHANGED with reverse map

**Decision**: Build a reverse map `dict[str, tuple[str, str]]` from `entity_id → (location, kind)` at setup. Register a single `async_track_state_change_event` listener for all configured entity IDs. On each event, look up the mapping, parse `float(new_state.state)`, and call `client.push_sensor()`.

**Why**: `async_track_state_change_event` is HA's idiomatic way to watch specific entities. A single listener with a reverse map is more efficient than one listener per entity.

**Error handling**: If `float()` conversion fails (entity reports `unavailable`, `unknown`, non-numeric) or the gRPC call fails, log a warning and drop. No retry — the next state change is seconds away.

### 3. Service: `njord.push_sensor` with auto-resolve location

**Decision**: Expose as a domain service with `kind` (required), `entity_id` (required), `location` (optional), `source` (optional). If `location` is omitted and the catalog has exactly one location, auto-resolve it. Otherwise raise a `ServiceValidationError`.

**Why**: Matches the existing `njord.trigger_poll` service pattern. Auto-resolve reduces friction for the majority of single-location setups.

### 4. Source derivation: entity_id

**Decision**: Always use the entity_id as the `source` field in the gRPC `SensorReading`. For the service, allow an optional override.

**Why**: Entity IDs are stable, unique, and human-readable. njord aggregates by `(location, kind)` via averaging across sources, so the source is primarily for debugging.

### 5. Catalog access for dynamic schema

**Decision**: The Options Flow `async_step_sensors` reads the catalog from the coordinator's cached data (available via `hass.data[DOMAIN][entry.entry_id]["coordinator"].data.catalog`). No extra gRPC call needed.

**Why**: The coordinator already fetches and caches the catalog on first refresh. The Options Flow runs after setup, so data is always available.

## Risks / Trade-offs

- **[Risk] Catalog not available when Options Flow runs** → The coordinator is initialized before the Options Flow is accessible. If for some reason data is None, fall back to showing no sensor fields (graceful degradation).

- **[Risk] Entity removed after configuration** → If a configured entity_id no longer exists, `state_changed` events simply won't fire for it. No crash, no error — it's a no-op. The Options Flow will show it as an unknown entity on next open, prompting the user to fix it.

- **[Risk] High-frequency sensors flooding njord** → Mitigated by njord's server-side staleness handling. Even if a sensor updates every second, the gRPC overhead is negligible. If this ever becomes an issue, a per-entity minimum interval can be added later.

- **[Trade-off] No StreamPush** → We lose batching efficiency but gain simplicity. StreamPush requires managing a persistent client-streaming connection with lifecycle tied to the integration. For the expected 2-10 sensor entities, unary Push is perfectly adequate.
