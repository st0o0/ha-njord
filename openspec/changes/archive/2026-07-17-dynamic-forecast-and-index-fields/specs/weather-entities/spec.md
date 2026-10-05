## MODIFIED Requirements

### Requirement: Weather entities advertise supported forecast types
Model weather entities SHALL dynamically determine `supported_features` based on whether the model's current forecast data contains hourly and/or daily entries, instead of statically claiming both.

#### Scenario: Model with hourly and daily data
- **WHEN** a model's forecast data contains both hourly and daily entries
- **THEN** `supported_features` includes `FORECAST_HOURLY | FORECAST_DAILY`

#### Scenario: Model with only hourly data
- **WHEN** a model's forecast data contains hourly entries but no daily entries
- **THEN** `supported_features` includes only `FORECAST_HOURLY`
- **AND** the HA weather card does not show an empty daily forecast section

#### Scenario: Model with no data yet
- **WHEN** the forecast data is None or empty
- **THEN** `supported_features` returns no forecast features

#### Scenario: Features update when data changes
- **WHEN** a model initially has no daily data and later receives daily forecasts via streaming
- **THEN** `supported_features` dynamically includes `FORECAST_DAILY` on the next state read
