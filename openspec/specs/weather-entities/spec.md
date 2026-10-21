## Purpose
Defines the per-model weather entities and the attributes they expose.

## Requirements

### Requirement: Weather entities expose all standard attributes
Model weather entities SHALL expose `native_apparent_temperature` and `cloud_cover` properties in addition to existing attributes. All current-state properties SHALL read from the time-matched hourly entry (the last entry where `valid_at <= utcnow()`), not from `hourly[0]`.

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
When `GetForecast` fails for a model during first refresh, the coordinator SHALL insert an empty `ForecastData` stub so the entity starts as available. The stub's `updated_at` SHALL be `datetime.min` with UTC timezone.

#### Scenario: Forecast fetch fails during first refresh
- **WHEN** `GetForecast(location, model)` raises an exception during `_async_update_data`
- **THEN** `ForecastData(location=location, model=model, updated_at=datetime.min.replace(tzinfo=UTC))` is inserted into the result

### Requirement: Forecast entries have all required keys
Every `Forecast` dict returned by `async_forecast_hourly` and `async_forecast_daily` SHALL include the `condition` key mapped from WMO weather code, even when the code maps to an unknown condition.

#### Scenario: Hourly forecast includes cloud cover
- **WHEN** `async_forecast_hourly` is called
- **THEN** each forecast entry includes `cloud_cover` when available in the data

#### Scenario: Daily forecast includes condition
- **WHEN** `async_forecast_daily` is called and the daily entry has a weather_code
- **THEN** the forecast entry has a non-None `condition` string

### Requirement: Weather entities support dynamic addition
The weather platform SHALL store its `async_add_entities` callback and a factory function on the coordinator during setup, enabling entity creation for locations discovered after initial setup.

#### Scenario: Late entity creation
- **WHEN** a new location "bern" with models ["icon_d2", "gfs"] is detected via config stream
- **THEN** two new `NjordWeatherEntity` instances are created and registered in HA for "bern"

#### Scenario: Consensus entity for new location
- **WHEN** a new location is detected and enrichment data with consensus is available
- **THEN** a `NjordConsensusWeatherEntity` is also created for that location

### Requirement: Secondary models get their own weather entity
The weather platform SHALL create one weather entity per location for every secondary model, that is every entry of the location's `models` after the first whose catalog entry is enabled (a model missing from the catalog counts as enabled). The entity SHALL have unique id `{entry_id}_{location_slug}_{model_id}_weather`, the model's catalog display name (or its id when missing from the catalog) as entity name on the location device, and read `model_domains[(location, model_id)]`. The primary entity SHALL keep unique id `{entry_id}_{location_slug}_weather`.

#### Scenario: Two models configured
- **WHEN** the catalog lists location "berlin" with models `["ecmwf_ifs025_ensemble_mean", "ukmo_global_ensemble_mean_20km"]` and both are enabled
- **THEN** the location has two weather entities with unique ids `{entry_id}_berlin_weather` and `{entry_id}_berlin_ukmo_global_ensemble_mean_20km_weather`

#### Scenario: Disabled model gets no entity
- **WHEN** a location lists a secondary model whose catalog entry has `enabled = false`
- **THEN** no weather entity is created for that model

#### Scenario: Single model
- **WHEN** a location lists only one model
- **THEN** only the primary weather entity exists

### Requirement: Weather updates are routed by model
The coordinator SHALL store a weather `DomainDataUpdate` whose `model` is empty or equal to the location's primary model in `domains[(location, WEATHER)]`, and any other weather update in `model_domains[(location, model)]`. The first update for an unknown `(location, model)` key SHALL create the model's weather entity through the registered model factory.

#### Scenario: Primary update
- **WHEN** a weather update for "berlin" arrives with `model` empty
- **THEN** `domains[("berlin", WEATHER)]` is replaced and `model_domains` is unchanged

#### Scenario: Secondary update
- **WHEN** a weather update for "berlin" arrives with `model = "ukmo_global_ensemble_mean_20km"`
- **THEN** `model_domains[("berlin", "ukmo_global_ensemble_mean_20km")]` is replaced and the primary entry is unchanged

#### Scenario: New model on the stream
- **WHEN** the first update for a secondary model arrives after setup
- **THEN** the model factory is called with the location and the model id and its entity is added

### Requirement: Secondary models are fetched on the first refresh
During the first refresh the coordinator SHALL call `GetDomainData` with the `model` field set for every secondary model of every location and store the result in `model_domains`. A failed call SHALL leave the key absent.

#### Scenario: Secondary fetch succeeds
- **WHEN** the first refresh runs for a location with one secondary model
- **THEN** `get_domain_data(location, WEATHER, model=<id>)` is called once and its result is in `model_domains`

#### Scenario: Secondary fetch fails
- **WHEN** the secondary fetch raises
- **THEN** the refresh still succeeds and `model_domains` has no entry for that model

### Requirement: Weather entities expose their model
Every weather entity SHALL expose the attributes `model` (the id), `model_name`, `provider`, `region`, `resolution_km` and `forecast_hours` taken from the catalog entry of its model; attributes of a model missing from the catalog are omitted except `model`.

#### Scenario: Primary entity attributes
- **WHEN** the primary model is `ecmwf_ifs025_ensemble_mean` with display name "ECMWF IFS 0.25° Ensemble Mean" and 360 forecast hours
- **THEN** the primary entity has `model = "ecmwf_ifs025_ensemble_mean"`, `model_name` set to the display name and `forecast_hours = 360`
