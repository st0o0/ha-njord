## Why

njord's `forecast_service.proto` now includes a `repeated ParameterValue extra` field on both `HourlyForecast` and `DailyForecast` messages. This allows njord to deliver model-specific or user-configured parameters (e.g. `soil_moisture`, `cape`, `uv_index`) beyond the fixed schema. ha-njord currently ignores these fields — users miss data their njord instance already provides.

## What Changes

- Copy updated proto from njord, regenerate Python stubs
- Add `extra: dict[str, float | str | bool]` to `HourlyForecastData` and `DailyForecastData`
- Parse `ParameterValue` repeated field in `grpc_client.py`
- Expose extras on `NjordWeatherEntity`:
  - As `extra_state_attributes` (current hour's values)
  - As additional keys in hourly/daily `Forecast` dicts returned by `weather.get_forecasts`

## Non-goals

- Filtering or whitelisting specific extra parameter names (pass all through)
- Creating separate sensor entities per extra parameter
- Modifying the ConsensusWeatherEntity (consensus uses its own data path)
- Any write operations back to njord

## gRPC Endpoints

- `GetForecast` (existing) — response already carries the `extra` field, just unused
- `StreamForecasts` (existing) — `ForecastUpdate` carries `extra` via same message types

No new endpoints needed.

## Capabilities

### New Capabilities

- `extra-forecast-parameters`: Parse and expose dynamic extra parameters from njord's forecast proto through the full ha-njord pipeline (models → client → weather entity → HA state/forecasts)

### Modified Capabilities

## Impact

- `protos/njord/v1/forecast_service.proto` — updated from upstream
- `custom_components/njord/proto/njord/v1/` — regenerated stubs
- `custom_components/njord/models.py` — new field on two dataclasses
- `custom_components/njord/grpc_client.py` — new converter logic
- `custom_components/njord/weather.py` — extra_state_attributes + forecast dict keys
- `tests/` — new/updated tests for parsing and entity output
