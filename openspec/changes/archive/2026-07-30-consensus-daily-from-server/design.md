# Design: Consensus Daily from Server

## Proto Change

```protobuf
// OLD
message ConsensusUpdate {
  repeated ParameterConsensus parameters = 1;
}

// NEW (from njord)
message ConsensusUpdate {
  repeated ParameterConsensus hourly_parameters = 1;  // field 1 renamed
  repeated ParameterConsensus daily_parameters = 2;   // field 2 new
}
```

Wire-compatible: field number 1 stays the same, so existing stubs continue reading hourly data. Field 2 is simply ignored until stubs are regenerated.

## Data Flow

```
njord ConsensusSnapshot
├── hourly_parameters[]
│   └── ParameterConsensus("temperature_2m")
│       └── by_horizon: [h0, h1, h2, ... h72]
│
└── daily_parameters[]
    └── ParameterConsensus("temperature_2m_max")
        └── by_horizon: [d0, d1, d2, ... d7]
```

## Model Change (models.py)

```python
# OLD
@dataclass(frozen=True)
class ConsensusData:
    parameters: list[ParameterConsensusData]

# NEW
@dataclass(frozen=True)
class ConsensusData:
    hourly_parameters: list[ParameterConsensusData]
    daily_parameters: list[ParameterConsensusData]
```

## Daily Forecast Mapping

```
Daily Consensus Parameter  →  HA Forecast Field
───────────────────────────────────────────────
temperature_2m_max         →  native_temperature
temperature_2m_min         →  native_templow
precipitation_sum          →  precipitation
wind_speed_10m_max         →  native_wind_speed
weather_code               →  condition (via map_condition)
```

## What Changes in weather.py

### NjordConsensusWeatherEntity

1. **All methods reading `consensus.parameters`** → read `consensus.hourly_parameters` instead (rename only)
   - `_sorted_horizons()`
   - `_horizon_values()`
   - `_get_horizon_value()`
   - `_get_horizon_data()`
   - `_reliable_hours()`

2. **`_async_forecast_daily()`** — replace self-aggregation with:
   - Read `daily_parameters` from consensus
   - Sort horizons `d0, d1, ...`
   - For each horizon, extract the mapped fields
   - Build `Forecast` entries with proper date calculation (today + N days)

3. **`_async_forecast_hourly()`** — no logic change, just uses `hourly_parameters` instead of `parameters`

## Date Calculation for Daily Horizons

`d0` = today (UTC), `d1` = tomorrow, etc. Straightforward — no offset calculation needed like hourly, since daily horizons always start from "today" at compute time.

## What Does NOT Change

- Current state properties (native_temperature, condition, etc.) — still from hourly h0 + offset
- Hourly forecast logic — rename only
- Sunrise/sunset — not in consensus, stays per-model
- `NjordWeatherEntity` — completely untouched
