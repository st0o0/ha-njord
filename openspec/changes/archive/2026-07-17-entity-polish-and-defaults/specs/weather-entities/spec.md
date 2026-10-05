## ADDED Requirements

### Requirement: Weather entities report availability based on forecast key
Weather entities SHALL return `available = True` when their forecast key exists in coordinator data, even if hourly/daily lists are empty. They SHALL return `available = False` only when the key is entirely missing.

#### Scenario: Forecast key exists with data
- **WHEN** `coordinator.data.forecasts[(location, model)]` exists with hourly entries
- **THEN** the entity is available and shows current condition/temperature

#### Scenario: Forecast key exists but empty (stub)
- **WHEN** `coordinator.data.forecasts[(location, model)]` exists but has empty hourly and daily
- **THEN** the entity is available but shows "Unknown" state

#### Scenario: Forecast key missing
- **WHEN** `(location, model)` is not in `coordinator.data.forecasts`
- **THEN** the entity is unavailable

### Requirement: First refresh inserts stub on failure
When `GetForecast` fails for a model during first refresh, the coordinator SHALL insert an empty `ForecastData` stub so the entity starts as available.

#### Scenario: Forecast fetch fails during first refresh
- **WHEN** `GetForecast(location, model)` raises an exception during `_async_update_data`
- **THEN** `ForecastData(location=location, model=model, updated_at=0)` is inserted into the result

## MODIFIED Requirements

### Requirement: Weather entities advertise supported forecast types
Model weather entities SHALL determine `supported_features` once at construction time based on the initial forecast data, stored as `_attr_supported_features`.

#### Scenario: Model with hourly and daily data at init
- **WHEN** a weather entity is created and the forecast data contains both hourly and daily entries
- **THEN** `_attr_supported_features` includes `FORECAST_HOURLY | FORECAST_DAILY`

#### Scenario: Model with only hourly data at init
- **WHEN** a weather entity is created and the forecast data contains hourly entries but no daily entries
- **THEN** `_attr_supported_features` includes only `FORECAST_HOURLY`

#### Scenario: Model with no data at init (stub)
- **WHEN** a weather entity is created and the forecast data has empty hourly and daily
- **THEN** `_attr_supported_features` is `0` (no forecast features)
