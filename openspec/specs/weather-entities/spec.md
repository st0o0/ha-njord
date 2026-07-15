## Purpose

Defines the weather entity platform — entity creation per location×model, state and attributes, forecast support, device grouping, data refresh, and integration lifecycle.

## Requirements

### Requirement: Weather entity per location and model
The integration SHALL create one `WeatherEntity` for each location×model combination reported by njord's config.

#### Scenario: Entities created on setup
- **WHEN** `async_setup_entry` runs and njord reports 2 locations with 4 models each
- **THEN** 8 weather entities are created (e.g., `weather.njord_lucerne_icon_d2`)

### Requirement: Weather entity state
Each weather entity SHALL display the current condition derived from the WMO weather code and is_day flag.

#### Scenario: Sunny day condition
- **WHEN** the latest forecast has weather_code 0 and is_day True
- **THEN** the entity state is `sunny`

#### Scenario: Clear night condition
- **WHEN** the latest forecast has weather_code 0 and is_day False
- **THEN** the entity state is `clear-night`

### Requirement: Weather entity attributes
Each weather entity SHALL expose standard weather attributes from the latest hourly forecast data point.

#### Scenario: Attributes present
- **WHEN** the entity is inspected
- **THEN** it reports temperature, humidity, pressure, wind_speed, and wind_bearing from the first hourly forecast entry

### Requirement: Hourly forecast support
Each weather entity SHALL support the `async_forecast_hourly` method returning hourly forecast data.

#### Scenario: Hourly forecast requested
- **WHEN** HA requests the hourly forecast for a weather entity
- **THEN** the entity returns a list of forecast entries with datetime, temperature, precipitation, humidity, wind_speed, wind_bearing, and condition

### Requirement: Daily forecast support
Each weather entity SHALL support the `async_forecast_daily` method returning daily forecast data.

#### Scenario: Daily forecast requested
- **WHEN** HA requests the daily forecast for a weather entity
- **THEN** the entity returns a list of forecast entries with datetime, temperature_max, temperature_min, precipitation, wind_speed, and condition

### Requirement: Device grouping
Weather entities SHALL be grouped under a device per location.

#### Scenario: Device created
- **WHEN** entities are created for location "lucerne"
- **THEN** all model entities for that location appear under a single device named "njord lucerne"

### Requirement: Data refresh via coordinator
The integration SHALL use a `DataUpdateCoordinator` to refresh forecast data at a regular interval.

#### Scenario: Automatic refresh
- **WHEN** 5 minutes have elapsed since the last update
- **THEN** the coordinator fetches fresh forecasts for all location×model pairs and entities update their state

### Requirement: Integration setup and teardown
The `__init__.py` SHALL create a `NjordClient`, connect it, set up the coordinator, and forward to the weather platform on setup. On unload, it SHALL close the client and clean up.

#### Scenario: Setup entry
- **WHEN** `async_setup_entry` is called
- **THEN** a `NjordClient` is created, connected, the coordinator starts, and the weather platform is loaded

#### Scenario: Unload entry
- **WHEN** `async_unload_entry` is called
- **THEN** the weather platform is unloaded and the gRPC client is closed
