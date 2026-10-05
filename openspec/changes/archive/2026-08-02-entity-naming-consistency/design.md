## Context

Entity naming across the five platforms (weather, sensor, binary_sensor, event, button) has grown inconsistently. DeviceInfo is constructed inline in some platforms but via shared helpers in others. Class names, unique_id slugs, and display names don't always align. This is a housekeeping change before first public release — fixing these now avoids breaking changes for users later.

## Goals / Non-Goals

**Goals:**
- Single source of truth for DeviceInfo construction (location-scoped and server-scoped)
- Consistent unique_id slug convention: `{location}_{feature_name}` with a descriptive suffix
- Class names match display names
- Display names don't repeat information already provided by the device context

**Non-Goals:**
- Changing entity behavior, data sources, or state logic
- Adding or removing entities
- Modifying gRPC client or coordinator logic

## Decisions

### D1: Shared DeviceInfo helpers in `helpers.py`

Extract `device_info()` and `server_device_info()` into a new `custom_components/njord/helpers.py` module. All platforms import from there.

**Why not keep them in `sensor.py`?** sensor.py is already the largest file. Cross-platform imports from sensor.py create a confusing dependency direction (weather.py importing from sensor.py). A small helpers module is cleaner.

**Why not `const.py`?** const.py holds string constants, not factory functions with `DeviceInfo` imports.

### D2: Class rename via simple find-and-replace

`NjordHistorySensor` → `NjordModelPerformanceSensor`. The class is only referenced in `sensor.py` (definition + `async_setup_entry` instantiation) and in tests. A straight rename with no alias or deprecation.

### D3: Energy sensor slug gets `_energy` suffix

Current: `{loc}_{key}` (e.g., `innsbruck_solar_gain`)
New: `{loc}_{key}_energy` (e.g., `innsbruck_solar_gain_energy`)

This matches the convention: `_alert`, `_index`, `_stream`. The key alone is ambiguous — `solar_gain` could be anything; `solar_gain_energy` makes the domain clear.

**Breaking**: unique_id changes. Acceptable pre-release.

### D4: Target sensor name simplification

Current: `f"{location.title()} {model} Poll"` → displays as "Server Innsbruck ICON-D2 Poll"
New: `f"{model} Target"` → displays as "Server ICON-D2 Target"

Location is dropped because target sensors sit on the Server device (not a location device), and the model name is sufficient to distinguish multiple targets. "Target" replaces "Poll" to match the slug suffix `_target`.

### D5: Sunshine sensor slug normalization

Current: `{loc}_sunshine_pct`
New: `{loc}_sunshine`

The `_pct` encodes a unit, which no other slug does. The display name is "Sunshine" — the slug should match.

**Breaking**: unique_id changes. Acceptable pre-release.

## Risks / Trade-offs

- **[Breaking unique_ids]** → Mitigated: pre-release, no public users yet. Document in commit message.
- **[New module `helpers.py`]** → Very small file (two functions). Risk of over-abstraction is low — these functions are used in 5+ files.
- **[Target sensor loses location in name]** → If someone has targets across multiple locations, all will show as "ICON-D2 Target" under the same Server device. This is acceptable: the entity_id still contains the location in the slug, and HA's entity list shows the full unique_id.
