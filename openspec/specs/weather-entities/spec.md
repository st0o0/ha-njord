## MODIFIED Requirements

### Requirement: Weather entities expose all standard attributes
Model weather entities SHALL expose `native_apparent_temperature` and `cloud_cover` properties in addition to existing attributes.

#### Scenario: Weather card shows apparent temperature
- **WHEN** the weather entity is displayed in the HA weather card
- **THEN** apparent temperature is available as an attribute

#### Scenario: Weather card shows cloud cover
- **WHEN** the weather entity is displayed
- **THEN** cloud cover percentage is available as an attribute

### Requirement: Forecast entries have all required keys
Every `Forecast` dict returned by `async_forecast_hourly` and `async_forecast_daily` SHALL include the `condition` key mapped from WMO weather code, even when the code maps to an unknown condition.

#### Scenario: Hourly forecast includes cloud cover
- **WHEN** `async_forecast_hourly` is called
- **THEN** each forecast entry includes `cloud_cover` when available in the data

#### Scenario: Daily forecast includes condition
- **WHEN** `async_forecast_daily` is called and the daily entry has a weather_code
- **THEN** the forecast entry has a non-None `condition` string
