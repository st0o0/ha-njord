## 1. Current-hour selection for NjordWeatherEntity

- [x] 1.1 Add `_current_hourly()` method to `NjordWeatherEntity` in `custom_components/njord/weather.py` — scans `data.hourly` for last entry where `valid_at <= utcnow()`, returns `HourlyForecastData | None`
- [x] 1.2 Replace all `data.hourly[0]` reads in state properties (`condition`, `native_temperature`, `humidity`, `native_pressure`, `native_wind_speed`, `wind_bearing`, `native_apparent_temperature`, `cloud_cover`, `extra_state_attributes`) with `_current_hourly()`
- [x] 1.3 Add tests in `tests/test_weather.py`: forecast with entries at 14:00-18:00, freeze time at 16:30, assert entity returns 16:00 values. Test edge cases: empty hourly, all entries in future

## 2. Hourly timer registration

- [x] 2.1 Add `async_added_to_hass()` to `NjordWeatherEntity` — register `async_track_utc_time_change(hass, callback, minute=0, second=0)`, callback calls `self.async_write_ha_state()`, cancel via `self.async_on_remove()`
- [x] 2.2 Add `async_added_to_hass()` to `NjordConsensusWeatherEntity` with the same timer pattern
- [x] 2.3 Add tests: mock `async_track_utc_time_change`, verify it is registered in `async_added_to_hass()` and cancel is passed to `async_on_remove()`

## 3. Filter past entries from hourly forecast

- [x] 3.1 Update `_async_forecast_hourly()` in `NjordWeatherEntity` to skip entries where `valid_at < utcnow()` (keep current hour, exclude past)
- [x] 3.2 Add tests: freeze time at 16:30 with entries 14:00-20:00, assert only 17:00+ returned. Test all-past returns `None`

## 4. Validation

- [x] 4.1 Run full test suite: `make test` — all existing + new tests pass
