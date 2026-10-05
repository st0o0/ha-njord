## Context

The Consensus entity was built when njord delivered consensus only at configured horizons (h3, h6, h12, h24, h48, h72, h96). It used h3 for current state and filtered >= h24 for a sparse daily forecast. njord now delivers hourly consensus (h0, h1, h2, ... hN) as long as >= 2 models cover the time point, using the same proto structure.

## Goals / Non-Goals

**Goals:**
- Consensus entity becomes a first-class weather entity with hourly + daily forecasts
- Current state uses h0 for maximum accuracy
- Daily forecast is properly aggregated from hourly data
- Reliability info (reliable_hours) as extra attribute

**Non-Goals:**
- Per-hour agreement in forecast entries (HA doesn't support it)
- Changing how model weather entities work

## Decisions

### D1: Current state from h0

**Choice:** Change default horizon from `"h3"` to `"h0"` for all current-state properties (temperature, humidity, etc.).

**Why h0?** It's the current hour's consensus. h3 was a reasonable default when h0 didn't exist, but now it's available and more accurate.

**Fallback:** If h0 is missing (shouldn't happen but defensive), fall back to the first available horizon.

### D2: Hourly forecast from consecutive horizons

**Choice:** `async_forecast_hourly` iterates h1, h2, h3, ... hN, converts each to a timestamp (`now + N hours`), and builds a `Forecast` entry with median values.

```python
now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
for horizon in sorted_horizons:
    hours = int(horizon[1:])
    if hours == 0:
        continue  # skip current hour, that's the entity state
    forecast_time = now + timedelta(hours=hours)
    ...
```

### D3: Daily forecast aggregated from hourly

**Choice:** Group hourly horizons by calendar date, then aggregate:

| Daily field | Aggregation |
|---|---|
| `temperature_max` | max of hourly temperature medians |
| `temperature_min` | min of hourly temperature medians |
| `precipitation_sum` | sum of hourly precipitation medians |
| `wind_speed_max` | max of hourly wind_speed medians |
| `condition` | weather_code median at the hour nearest to 12:00 local |

**Today is excluded** from daily forecast (partial day). Only full future days.

**Condition at midday:** Use the horizon closest to 12:00 UTC for each day. Simple, deterministic, and the most representative single-point condition for a day.

### D4: Reliable hours attribute

**Choice:** `reliable_hours` = count of consecutive hours from h0 where `agreement >= 0.5` on temperature_2m. Stops at the first hour below threshold.

```python
reliable = 0
for h in sorted_horizons:
    temp_agreement = get_agreement("temperature_2m", h)
    if temp_agreement is None or temp_agreement < 0.5:
        break
    reliable += 1
```

This gives users a single number: "consensus is reliable for the next N hours."

### D5: Helper method for bulk horizon access

**Choice:** Instead of calling `_get_horizon_value()` per parameter per horizon (O(params × horizons × horizons)), build a lookup dict once:

```python
def _horizon_values(self, horizon: str) -> dict[str, float | None]:
    """Get all parameter medians for a horizon as a dict."""
```

This avoids the nested linear search for every forecast entry.

## Risks / Trade-offs

**[Large forecast arrays]** → With 120+ hourly entries, the forecast response is larger. HA handles this fine — other integrations (Met.no) return similar amounts.

**[UTC vs local for midday condition]** → Using 12:00 UTC is simple but wrong for locations far from UTC. Acceptable for European locations (UTC+1/+2), "midday" is 13:00-14:00 local which is close enough. Proper timezone handling would require knowing the location's timezone, which njord doesn't provide.

**[Agreement threshold 0.5]** → Arbitrary but reasonable. Below 0.5 means models disagree more than they agree. Can be tuned later.

## Open Questions

None.
