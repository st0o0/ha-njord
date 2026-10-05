## 1. Rebuild Consensus Entity

- [x] 1.1 In `custom_components/njord/weather.py`, change `NjordConsensusWeatherEntity` default horizon from `"h3"` to `"h0"` for all current-state properties (`_get_horizon_value` and `_get_horizon_data` default parameter).
- [x] 1.2 Add `_sorted_horizons()` helper that returns all horizons sorted by hours as `list[str]`. Add `_horizon_values(horizon)` helper that returns `dict[str, float | None]` with all parameter medians for a given horizon in one pass.
- [x] 1.3 Implement `async_forecast_hourly()`: iterate h1..hN, convert to timestamps (`now.replace(minute=0, ...) + timedelta(hours=N)`), build `Forecast` entries with temperature, precipitation, humidity, wind_speed, wind_bearing, cloud_cover, condition (via nearest WMO mapping).
- [x] 1.4 Rewrite `async_forecast_daily()`: group horizons by calendar day (UTC), skip today, aggregate per day (max temp, min temp, sum precip, max wind, midday condition from horizon nearest 12:00 UTC).
- [x] 1.5 Update `extra_state_attributes`: source from h0 instead of h3, add `reliable_hours` — count consecutive hours from h0 where temperature_2m agreement >= 0.5.
- [x] 1.6 Update `supported_features` init: set `FORECAST_HOURLY | FORECAST_DAILY` when consensus has >= 2 horizons, otherwise `0`.
- [x] 1.7 Remove `_daily_horizons()` and `_condition_for_horizon()` — no longer needed after rewrite.

## 2. Update Tests

- [x] 2.1 Update test fixtures in `tests/conftest.py`: expand consensus `by_horizon` to include hourly entries (h0, h1, h2, ..., h48) instead of just h3.
- [x] 2.2 Update `tests/test_weather.py` consensus tests: verify current state from h0, hourly forecast count and timestamps, daily aggregation (max/min temp, precip sum, midday condition), reliable_hours attribute.

## 3. Validation

- [x] 3.1 Run full test suite: `make test` — all tests pass.
- [x] 3.2 Run `ruff format --check .` — all files formatted.
