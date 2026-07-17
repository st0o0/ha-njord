## Capability: consensus-weather

A weather entity per location that uses multi-model consensus values instead of a single model's forecast.

### Entity

| Entity ID | Platform | 
|-----------|----------|
| `weather.njord_{loc}_consensus` | weather |

### State Mapping

The entity's current state uses the `h0` horizon consensus values. Falls back to first available horizon if h0 is missing.

| Weather attribute | Consensus parameter | Field used |
|-------------------|-------------------|------------|
| `temperature` | `temperature_2m` | `median` |
| `humidity` | `relative_humidity_2m` | `median` |
| `pressure` | `pressure_msl` | `median` |
| `wind_speed` | `wind_speed_10m` | `median` |
| `wind_bearing` | `wind_direction_10m` | `median` |
| `cloud_cover` | `cloud_cover` | `median` |
| `condition` | `weather_code` | `median` → WMO mapping |
| `visibility` | `visibility` | `median` |
| `dew_point` | `dew_point_2m` | `median` |
| `apparent_temperature` | `apparent_temperature` | `median` |
| `precipitation` | `precipitation` | `median` |

### Extra State Attributes

| Attribute | Source | Description |
|-----------|--------|-------------|
| `agreement` | consensus h0 temperature `agreement` | How well models agree (0.0–1.0) |
| `available_models` | consensus h0 `available_models` | Number of models contributing |
| `spread` | consensus h0 temperature `spread` | Temperature spread across models (°C) |
| `reliable_hours` | count of consecutive horizons from h0 with temperature agreement >= 0.5 | Number of hours where models reliably agree |

### Forecast Support

The consensus entity supports `forecast_hourly` and `forecast_daily` via HA's weather forecast service.

**Hourly forecasts**: Built from consecutive consensus horizons h1..hN (h0 is excluded as it represents current state). Each entry has timestamp = now + N hours, with median values for temperature, precipitation, wind speed, wind bearing, humidity, cloud cover, and condition (mapped from weather_code median via nearest known WMO code).

**Daily forecasts**: Aggregated from hourly consensus data per calendar day. The current (partial) day is excluded. Each daily entry includes: max temperature, min temperature, precipitation sum, max wind speed, and midday condition (derived from weather_code median at the horizon closest to 12:00 UTC for that day).

### Data Source

- gRPC: `ForecastService.GetEnrichments(location)` → `ConsensusUpdate.parameters[]`
- Each `ParameterConsensus` has `parameter` (name), `unit`, and `by_horizon[]`
- Each `HorizonConsensus` has `horizon`, `median`, `trimmed_mean`, `spread`, `iqr`, `agreement`, `available_models`

### Requirements

#### Requirement: Current state uses h0 horizon
The consensus entity's current state (temperature, humidity, wind, condition, etc.) SHALL use the `h0` horizon instead of `h3`.

##### Scenario: Current temperature from h0
- **WHEN** consensus data has an h0 horizon with temperature_2m median = 22.5
- **THEN** the entity's temperature is 22.5

##### Scenario: Fallback when h0 is missing
- **WHEN** consensus data has no h0 horizon but has h1
- **THEN** the entity uses the first available horizon for current state

#### Requirement: Hourly forecast from consecutive horizons
The consensus entity SHALL support `FORECAST_HOURLY` by building forecast entries from h1..hN consensus horizons, each with a real timestamp.

##### Scenario: Hourly forecast entries
- **WHEN** `async_forecast_hourly` is called and consensus has horizons h0-h72
- **THEN** 72 forecast entries are returned (h1 through h72), each with timestamp = now + N hours, and median values for temperature, precipitation, wind speed, wind bearing, humidity, cloud cover, and condition

##### Scenario: Condition mapped from weather_code median
- **WHEN** an hourly consensus horizon has weather_code median = 1.2
- **THEN** the forecast entry's condition is mapped from WMO code 1 (nearest known code)

##### Scenario: h0 excluded from hourly forecast
- **WHEN** `async_forecast_hourly` is called
- **THEN** h0 is not included (it represents the current state, not a forecast)

#### Requirement: Daily forecast aggregated from hourly
The consensus entity SHALL support `FORECAST_DAILY` by aggregating hourly consensus data per calendar day.

##### Scenario: Daily aggregation
- **WHEN** `async_forecast_daily` is called and consensus has 72 hourly horizons
- **THEN** forecast entries are returned for each full future day with: max temperature, min temperature, precipitation sum, max wind speed, and midday condition

##### Scenario: Today excluded
- **WHEN** `async_forecast_daily` is called
- **THEN** the current (partial) day is not included in the daily forecast

##### Scenario: Midday condition
- **WHEN** a daily forecast entry is built for a future day
- **THEN** condition is derived from the weather_code median at the horizon closest to 12:00 UTC for that day

#### Requirement: Reliability extra state attributes
The consensus entity SHALL expose reliability information in extra_state_attributes.

##### Scenario: Reliable hours attribute
- **WHEN** consensus data has temperature_2m agreement >= 0.5 for h0 through h36, then drops below 0.5 at h37
- **THEN** `reliable_hours` is 37

##### Scenario: Agreement and spread from h0
- **WHEN** consensus data has h0 with temperature_2m agreement=0.8, spread=3.2, available_models=8
- **THEN** extra_state_attributes contains `agreement=0.8`, `spread=3.2`, `available_models=8`

#### Requirement: Supported features set at init
The consensus entity SHALL determine `supported_features` at init based on available consensus data.

##### Scenario: Hourly consensus data available
- **WHEN** consensus data has multiple consecutive horizons (h0, h1, h2, ...)
- **THEN** `_attr_supported_features` includes `FORECAST_HOURLY | FORECAST_DAILY`

##### Scenario: No consensus data
- **WHEN** consensus data is None
- **THEN** `_attr_supported_features` is `0`

### Files

- `custom_components/njord/weather.py` — add `NjordConsensusWeatherEntity` alongside existing `NjordWeatherEntity`
- `tests/test_weather.py` — consensus entity tests (may need separate test file if too large)
