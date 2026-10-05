## Why

njord now delivers consensus data with hourly granularity (h0, h1, h2, ... hN) instead of only the configured horizons (h3, h6, h12, h24, h48, h72, h96). Each hour is included as long as >= 2 models cover that time point. This is the same proto type (`ConsensusUpdate`), just more entries in `by_horizon`. The current ha-njord Consensus entity uses h3 for current state and filters >= h24 for daily forecast — with hourly data it should become a full weather entity with proper hourly and aggregated daily forecasts.

## What Changes

- **Current state from h0.** Use h0 (current hour) instead of h3 for the entity's live state (temperature, humidity, condition, etc.).
- **Hourly forecast.** Build `async_forecast_hourly` from h1..hN consensus horizons. Each entry gets a real timestamp and median values for temperature, precipitation, wind, humidity, condition.
- **Aggregated daily forecast.** Build `async_forecast_daily` by grouping hourly horizons per calendar day: max/min temperature, precipitation sum, midday condition, max wind speed.
- **Reliability attributes.** Add `reliable_hours` to extra_state_attributes — the number of hours where agreement stays above a threshold (0.5). Keep existing `agreement`, `available_models`, `spread` from h0.
- **supported_features.** Set `FORECAST_HOURLY | FORECAST_DAILY` at init when hourly consensus data exists.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `consensus-weather`: Rebuild to use hourly consensus data for current state (h0), hourly forecast, aggregated daily forecast, and reliability attributes.

## Non-goals

- Changing the consensus proto or njord-side logic.
- Adding consensus hourly data as separate sensor entities.
- Exposing per-hour agreement/spread in forecast entries (HA Forecast TypedDict doesn't support custom fields).

## gRPC Endpoints Required

| Endpoint | Status | Notes |
|---|---|---|
| `GetEnrichments` | Exists, unchanged | Returns ConsensusUpdate with more by_horizon entries |
| `StreamEnrichments` | Exists, unchanged | Streams ConsensusUpdate with more entries |

No proto or client changes needed — same types, just more data.

## Impact

- **`custom_components/njord/weather.py`** — Full rewrite of `NjordConsensusWeatherEntity`: current state from h0, new `async_forecast_hourly`, rewrite `async_forecast_daily` as aggregation, updated `extra_state_attributes`.
- **Tests** — Update consensus weather tests for hourly forecasts, daily aggregation, reliability attributes.
