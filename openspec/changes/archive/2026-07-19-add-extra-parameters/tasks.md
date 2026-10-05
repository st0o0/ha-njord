## 1. Proto Update & Stub Regeneration

- [x] 1.1 Copy `forecast_service.proto` from `D:\GIT\njord\protos\njord\v1\` to `protos/njord/v1/`
- [x] 1.2 Run `make proto` to regenerate Python stubs in `custom_components/njord/proto/njord/v1/`

## 2. Data Models

- [x] 2.1 Add `extra: dict[str, float | str | bool] = field(default_factory=dict)` to `HourlyForecastData` in `custom_components/njord/models.py`
- [x] 2.2 Add `extra: dict[str, float | str | bool] = field(default_factory=dict)` to `DailyForecastData` in `custom_components/njord/models.py`

## 3. gRPC Client Parsing

- [x] 3.1 Add `_parse_extra(pb_extra)` helper in `custom_components/njord/grpc_client.py` that converts `repeated ParameterValue` to `dict[str, float | str | bool]`
- [x] 3.2 Wire `_parse_extra` into `_to_hourly()` to populate `HourlyForecastData.extra`
- [x] 3.3 Wire `_parse_extra` into `_to_daily()` to populate `DailyForecastData.extra`
- [x] 3.4 Add tests in `tests/` for `_parse_extra` covering numeric, text, flag, empty, and unset-value cases

## 4. Weather Entity — State Attributes

- [x] 4.1 Add `extra_state_attributes` property to `NjordWeatherEntity` in `custom_components/njord/weather.py` returning current hour's `extra` dict (or `None` if empty/unavailable)
- [x] 4.2 Add tests for `extra_state_attributes` with extras present, empty extras, and no forecast data

## 5. Weather Entity — Forecast Responses

- [x] 5.1 Update `_async_forecast_hourly` in `custom_components/njord/weather.py` to merge each hour's `extra` into the `Forecast` dict
- [x] 5.2 Update `_async_forecast_daily` in `custom_components/njord/weather.py` to merge each day's `extra` into the `Forecast` dict
- [x] 5.3 Add tests for hourly/daily forecast responses verifying extra keys appear and empty extras add nothing

## 6. Validation

- [x] 6.1 Run full test suite: `make test` — all tests pass
