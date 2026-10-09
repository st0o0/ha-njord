## Why

Derived horizon sensors (Beaufort, Wind Chill, Dewpoint Comfort) always show "unknown" in HA despite njord's gRPC `GetEnrichments` returning valid data. The root cause is that `horizon.py`'s `get_horizon_entry()` computes `h{elapsed_hours}` (e.g. `h0` right after a poll), but njord sends horizons starting at the configured minimum — typically `h3` — so no match is ever found until 3+ hours after a poll. The consensus weather entity doesn't have this problem because consensus horizons start at `h0`.

This was discovered during E2E testing (2026-10-09) and confirmed by inspecting the gRPC response: derived `by_horizon` contains `[h3, h6, h12, h24, h48, h72]` while the lookup searches for `h0`.

## What Changes

- **Fix horizon lookup to find the nearest available horizon** instead of requiring an exact `h{elapsed}` match. When the elapsed offset (e.g. 0) falls before the smallest available horizon (e.g. h3), return the smallest horizon entry. When it falls between two horizons, return the nearest one whose hour value is ≥ the elapsed offset.
- **Update the `horizon-offset-helper` spec** to reflect that horizons may not start at h0 and to specify nearest-match behavior.
- **Update the `derived-sensors` spec** to test with realistic horizon sets (h3+ instead of h0+).

## Non-goals

- Changing njord's horizon output format (it correctly sends configured horizons).
- Fixing sunshine sensor — it's null because the Solar parameter group isn't requested (expected behavior, not a bug).
- Fixing trend/history sensors — they require multiple poll cycles to populate (expected behavior).
- Changing target sensor timestamp format — the "locale format" in E2E was a PowerShell `Invoke-RestMethod` display artifact, not a real bug.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `horizon-offset-helper`: The lookup function must handle horizon lists that don't start at h0. Instead of exact `h{offset}` match, use nearest-available-horizon logic.
- `derived-sensors`: Update test scenarios to use realistic horizon sets starting at h3, and verify the sensor shows a value immediately after data arrival (offset=0 → picks h3).

## Impact

- **Code:** `custom_components/njord/horizon.py` (the `get_horizon_entry` function)
- **Tests:** `tests/test_horizon.py`, `tests/test_sensor.py` (derived sensor tests)
- **Specs:** `openspec/specs/horizon-offset-helper/spec.md`, `openspec/specs/derived-sensors/spec.md`
- **gRPC endpoints:** No changes needed — uses existing `StreamEnrichments` / `GetEnrichments` (existing).
