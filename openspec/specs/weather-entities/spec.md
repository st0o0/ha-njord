## Purpose
Defines the weather entities and the attributes they expose.

## Requirements

### Requirement: Weather entity per location
The integration SHALL create one HA weather entity per location. The weather entity SHALL be fed from WeatherValue (via EntityStateUpdate on the Subscribe stream). It SHALL map WeatherValue fields to HA weather attributes (temperature, humidity, wind_speed, wind_bearing, pressure, condition).

#### Scenario: Weather entity updates from stream
- **WHEN** an EntityStateUpdate with a WeatherValue arrives for location Vienna
- **THEN** the weather entity SHALL update its state attributes from the WeatherValue fields

#### Scenario: Hourly forecast from weather entity
- **WHEN** the weather entity provides an hourly forecast
- **THEN** it SHALL derive the forecast from the WeatherValue hourly data

### Requirement: Weather entities expose all standard attributes
Weather entities SHALL expose `native_apparent_temperature` and `cloud_cover` properties in addition to existing attributes. All current-state properties SHALL read from the time-matched hourly entry (the last entry where `valid_at <= utcnow()`), not from `hourly[0]`.

#### Scenario: Weather card shows apparent temperature
- **WHEN** the weather entity is displayed in the HA weather card
- **THEN** apparent temperature is available as an attribute, sourced from the current-hour entry

#### Scenario: Weather card shows cloud cover
- **WHEN** the weather entity is displayed
- **THEN** cloud cover percentage is available as an attribute, sourced from the current-hour entry

#### Scenario: Current hour differs from first hourly entry
- **WHEN** the forecast was pushed at 14:00 and the current time is 17:00
- **THEN** temperature, condition, humidity, pressure, wind, and cloud cover reflect the 17:00 hourly entry

### Requirement: Weather entities advertise supported forecast types
Weather entities SHALL determine `supported_features` once at construction time based on the initial data, stored as `_attr_supported_features`.

#### Scenario: Entity with hourly and daily data at init
- **WHEN** a weather entity is created and the data contains both hourly and daily entries
- **THEN** `_attr_supported_features` includes `FORECAST_HOURLY | FORECAST_DAILY`

#### Scenario: Entity with only hourly data at init
- **WHEN** a weather entity is created and the data contains hourly entries but no daily entries
- **THEN** `_attr_supported_features` includes only `FORECAST_HOURLY`

### Requirement: Weather entities report availability from coordinator
Weather entities SHALL return `available = True` when their entity state exists in the coordinator, and `available = False` when the coordinator reports the entity as unavailable.

#### Scenario: Entity state exists
- **WHEN** the coordinator has state for the weather entity
- **THEN** the entity is available and shows current condition/temperature

#### Scenario: Entity marked unavailable
- **WHEN** the coordinator marks the entity as unavailable
- **THEN** the entity is unavailable in HA

### Requirement: Forecast entries have all required keys
Every `Forecast` dict returned by `async_forecast_hourly` and `async_forecast_daily` SHALL include the `condition` key mapped from WMO weather code, even when the code maps to an unknown condition.

#### Scenario: Hourly forecast includes cloud cover
- **WHEN** `async_forecast_hourly` is called
- **THEN** each forecast entry includes `cloud_cover` when available in the data

#### Scenario: Daily forecast includes condition
- **WHEN** `async_forecast_daily` is called and the daily entry has a weather_code
- **THEN** the forecast entry has a non-None `condition` string
