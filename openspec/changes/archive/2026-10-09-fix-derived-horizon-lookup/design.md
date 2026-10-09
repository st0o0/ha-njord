## Context

`horizon.py` provides two functions used by derived and consensus sensors:

```python
def current_horizon_offset(updated_at) -> int:
    # Returns elapsed hours since updated_at (0 if just received)

def get_horizon_entry(horizons, offset) -> T | None:
    # Looks for exact match on f"h{offset}"
```

The consensus weather entity uses horizons starting at `h0` (consensus computes for every hour). The derived sensors use horizons matching the configured forecast horizons — typically `[h3, h6, h12, h24, h48, h72]`. The exact-match lookup fails for derived because there's no `h0`, `h1`, or `h2` entry.

## Goals / Non-Goals

**Goals:**
- Derived horizon sensors show a value immediately after data arrives (offset=0 → nearest horizon)
- Consensus entity behavior unchanged (its horizons start at h0, so nearest-match still picks h0)
- Clean, testable lookup logic

**Non-goals:**
- Changing `current_horizon_offset()` — it correctly computes elapsed hours
- Adding interpolation between horizons

## Decisions

### Decision: Nearest-future-or-equal horizon match

Change `get_horizon_entry` to find the entry whose hour value is the smallest `≥ offset`, falling back to the last entry if offset exceeds all.

```
offset=0, horizons=[h3,h6,h12,h24]  →  h3   (nearest future)
offset=3, horizons=[h3,h6,h12,h24]  →  h3   (exact match)
offset=4, horizons=[h3,h6,h12,h24]  →  h6   (next available)
offset=30, horizons=[h3,h6,h12,h24] →  h24  (clamp to last)
offset=0, horizons=[h0,h1,h2,h3]    →  h0   (consensus: unchanged)
```

**Why nearest-future instead of nearest-past:** A derived sensor at offset=0 should show the soonest forecast (h3 = 3 hours out), not no data. At offset=4 (4 hours elapsed), the h3 forecast is stale (it was for 3h out, now 1h past), so h6 (still 2h in the future) is more useful.

**Why clamp to last instead of None:** At offset=30 with horizons up to h24, the h24 value is the best available. Returning None would make the sensor "unknown" when it could show the longest-range forecast. If truly stale data is a concern, the sensor's `available` property already gates on `enrichment.derived is not None`.

### Decision: Parse horizon string to int for comparison

Extract the integer from `h{N}` strings to enable numeric comparison. This is a safe assumption — njord always formats horizons as `h{int}`.

### Decision: Rename for clarity

Rename `get_horizon_entry` → `find_nearest_horizon` to signal the new behavior. Update all call sites (consensus weather + derived sensors).

## Data Flow (unchanged)

```
njord gRPC                    ha-njord
┌──────────────┐              ┌──────────────────────────┐
│ GetEnrichments│──────────►  │ _to_enrichment_data()    │
│ StreamEnrich. │              │   derived.by_horizon:    │
│               │              │   [h3, h6, h12, h24, …] │
└──────────────┘              └──────────┬───────────────┘
                                         │
                              ┌──────────▼───────────────┐
                              │ _NjordDerivedHorizonSensor│
                              │  _current_derived_horizon()│
                              │   offset = elapsed_hours   │
                              │   find_nearest_horizon()   │
                              │     offset=0 → h3 ✓       │
                              └──────────────────────────┘
```

## Affected Files

| File | Change |
|------|--------|
| `custom_components/njord/horizon.py` | Rewrite `get_horizon_entry` → `find_nearest_horizon` with nearest-future logic |
| `custom_components/njord/sensor.py` | Update import (rename) |
| `custom_components/njord/weather.py` | Update import (rename) |
| `tests/test_horizon.py` | Rewrite tests for nearest-match behavior, add tests with h3+ horizon sets |
| `tests/test_sensor.py` | Update derived sensor tests to verify non-None with h3+ horizons |
