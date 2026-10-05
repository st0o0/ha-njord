## Context

Weather entities read `hourly[0]` for current state (temperature, condition, etc.). This entry corresponds to the hour when the forecast was last pushed by njord, not the current hour. Between forecast pushes (which depend on model update cycles), the displayed values go stale — confirmed by HA showing "2 hours ago" / "4 hours ago" on entity cards.

HA's `SingleCoordinatorWeatherEntity` re-evaluates properties only when the coordinator signals new data via `async_set_updated_data`. Since njord uses streaming (not polling), there's no periodic re-evaluation — state only updates when a new forecast arrives on the stream.

Open-Meteo's HA integration solves a similar problem: it filters past entries from hourly forecasts using `if _datetime < today: continue`. However, Open-Meteo polls every 30 minutes, which implicitly triggers re-evaluation. We need an explicit hourly trigger since our data arrives via streams.

## Goals / Non-Goals

**Goals:**
- Entity state shows the forecast value for the current hour, not the hour of the last forecast push
- State advances automatically at each hour boundary without waiting for new forecast data
- Hourly forecast lists only contain future entries

**Non-Goals:**
- Changing njord's gRPC API (no `current` field)
- Modifying the coordinator or streaming architecture
- Sub-hourly granularity (forecasts are hourly resolution)

## Decisions

### 1. Current-hour selection via `_current_hourly()` helper

**Decision:** Add a method that scans `data.hourly` for the last entry where `valid_at <= now`.

**Why not `hourly[0]`?** It assumes the list starts at "now", which is only true immediately after a forecast push.

**Why not bisect?** Hourly lists are typically 48-168 entries. Linear reverse scan is simpler, correct, and fast enough.

```python
def _current_hourly(self) -> HourlyForecastData | None:
    data = self._forecast_data
    if data is None or not data.hourly:
        return None
    now = utcnow()
    best = None
    for h in data.hourly:
        if h.valid_at <= now:
            best = h
    return best
```

### 2. Hourly timer via `async_track_utc_time_change`

**Decision:** Each weather entity registers `async_track_utc_time_change(hass, callback, minute=0, second=0)` in `async_added_to_hass()`, calling `self.async_write_ha_state()`.

**Why entity-level, not coordinator-level?** No new data is being fetched — the entity just needs to re-compute its properties from existing forecast data. `async_write_ha_state()` is the HA-idiomatic way to trigger a state re-read without coordinator involvement.

**Why `async_track_utc_time_change` over `async_track_time_interval`?** Fires exactly at hour boundaries (minute=0, second=0) rather than drifting based on when the entity was created. Aligns with forecast hour boundaries.

**Cleanup:** `self.async_on_remove(cancel)` ensures the timer is cleaned up when the entity is removed.

### 3. Filter past entries from hourly forecast

**Decision:** `_async_forecast_hourly()` skips entries where `valid_at < now` (same pattern as Open-Meteo).

**Why?** HA weather cards show forecasts as future predictions. Displaying past hours is misleading and clutters the forecast view.

### 4. Consensus entity: timer only, no selection logic change

**Decision:** `NjordConsensusWeatherEntity` gets the same hourly timer but keeps its horizon-based value selection (`h0`, `h1`, etc.) unchanged.

**Why?** Horizons are relative ("hours from now" at enrichment computation time). The timer ensures HA refreshes the displayed state, which clears the "2 hours ago" staleness indicator. The horizon values themselves don't shift with clock time — they update when new enrichment data arrives.

## Risks / Trade-offs

- **[Risk] Forecast data too old — no matching hourly entry for current hour** → `_current_hourly()` returns the last available past entry (graceful degradation). If the entire hourly list is in the future (edge case after a forecast push for tomorrow), returns `None` and entity shows "Unknown".

- **[Risk] Timer fires but entity has no coordinator data yet** → `_current_hourly()` returns `None`, properties return `None`, entity shows "Unknown" — same as current behavior for missing data.

- **[Trade-off] One timer per entity vs. one shared timer** → Slightly more overhead with per-entity timers, but HA's event system is designed for this and it keeps the code simple. With ~10-20 weather entities, the overhead is negligible.
