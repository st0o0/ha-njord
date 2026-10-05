## Context

The integration groups entities into HA devices by `DeviceInfo.identifiers`. Currently three identifier schemes exist:

| Device          | Identifier                         | Entities                     |
|-----------------|------------------------------------|------------------------------|
| `<Location>`    | `(DOMAIN, "{entry_id}_{location}")` | Weather entities, location sensors |
| Server          | `(DOMAIN, "{entry_id}_server")`     | API budget sensor, uptime sensor   |
| njord (host)    | `(DOMAIN, "{entry_id}")`            | Trigger poll button (orphan)       |

The third device is unintentional — the button was added before the Server device existed.

## Goals / Non-Goals

**Goals:**
- Consolidate the trigger poll button into the Server device so all server-scoped entities live together.

**Non-Goals:**
- Refactoring device assignment for location-scoped entities.
- Extracting a shared `_server_device_info()` helper across modules (sensor.py already has one; button.py can just inline the same identifiers — extracting to a shared module is premature for two call sites).

## Decisions

### Use the same identifier tuple, not import the helper

**Decision**: Duplicate the `DeviceInfo(identifiers={(DOMAIN, f"{entry.entry_id}_server")})` pattern in button.py rather than importing `_server_device_info` from sensor.py.

**Why**: The helper is module-private (`_` prefix) and coupling button.py to sensor.py's internals adds a cross-module dependency for a one-liner. If a third module needs it later, extract then.

**Alternative considered**: Import or extract to `const.py` — rejected as premature abstraction for two call sites.

### Remove name/manufacturer from button's DeviceInfo

**Decision**: Only set `identifiers` in the button's `DeviceInfo`. HA merges device info across entities — the Server device's name and manufacturer are already set by sensor.py.

**Why**: Avoids conflicting device names if sensor.py changes the Server device name later.

## Risks / Trade-offs

- **[Orphan device cleanup]** → HA automatically removes devices with no entities. Users who had the old `njord (host)` device will see it disappear after restart. No manual cleanup needed.
- **[Unique ID stability]** → The button's `unique_id` stays unchanged (`{entry_id}_trigger_poll`), so HA won't create a duplicate entity. Only the device assignment moves.
