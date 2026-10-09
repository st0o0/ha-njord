## Tasks

### Chunk 1: Fix horizon lookup function

**Files:** `custom_components/njord/horizon.py`, `tests/test_horizon.py`

- [x] Rename `get_horizon_entry` → `find_nearest_horizon` in `custom_components/njord/horizon.py`
- [x] Implement nearest-future-or-equal logic: parse `h{N}` to int, find smallest entry where N ≥ offset, fall back to last entry if all are < offset
- [x] Rewrite `tests/test_horizon.py`:
  - Test offset=0 with `[h3, h6, h12, h24]` → returns h3
  - Test offset=3 with `[h3, h6, h12, h24]` → returns h3 (exact)
  - Test offset=4 with `[h3, h6, h12, h24]` → returns h6
  - Test offset=100 with `[h3, h6, h12, h24]` → returns h24 (clamp)
  - Test offset=0 with `[h0, h1, h2, h3]` → returns h0 (consensus unchanged)
  - Test empty list → returns None

**Validation:** `python -m pytest tests/test_horizon.py -v --tb=short`

### Chunk 2: Update call sites and derived sensor tests

**Files:** `custom_components/njord/sensor.py`, `custom_components/njord/weather.py`, `tests/test_sensor.py`

- [x] Update import in `custom_components/njord/sensor.py`: `get_horizon_entry` → `find_nearest_horizon`
- [x] Update import in `custom_components/njord/weather.py`: `get_horizon_entry` → `find_nearest_horizon` (not needed — weather.py doesn't use `get_horizon_entry`)
- [x] Add/update derived sensor tests in `tests/test_sensor.py` to use h3+ horizon fixtures and verify non-None values at offset=0

**Validation:** `python -m pytest tests/test_sensor.py -v --tb=short -k "derived or beaufort or wind_chill or dewpoint"` and `python -m pytest tests/test_weather.py -v --tb=short`

### Chunk 3: Sync delta specs to main specs

- [x] Run `openspec sync --change fix-derived-horizon-lookup` to merge delta specs into main specs
