## Purpose

Defines the lifecycle management of gRPC streaming tasks within the coordinator -- starting streams after first refresh, cancelling on unload, and routing stream data to coordinator state.

## Requirements

### Requirement: Stream tasks are started after first refresh
The coordinator SHALL start three background asyncio tasks (forecast stream, enrichment stream, config stream) via a `start_streams()` method called after initial data load and platform setup.

#### Scenario: Streams start on integration setup
- **WHEN** the integration entry is set up and platforms are forwarded
- **THEN** `coordinator.start_streams()` creates three background tasks consuming `stream_forecasts()`, `stream_enrichments()`, and `stream_config()`

#### Scenario: Initial data is available before streams start
- **WHEN** `start_streams()` is called
- **THEN** `coordinator.data` already contains forecast and enrichment data from the unary first refresh

### Requirement: Stream tasks are cancelled on unload
The coordinator SHALL cancel all running stream tasks when the config entry is unloaded.

#### Scenario: Clean shutdown
- **WHEN** `async_unload_entry` is called
- **THEN** all stream tasks are cancelled and awaited before the gRPC client is closed

#### Scenario: Partial unload
- **WHEN** one stream task has already exited (e.g., cancelled stream) and unload is called
- **THEN** the remaining tasks are cancelled without error

### Requirement: Forecast stream pushes data to coordinator
Each `ForecastUpdate` from the forecast stream SHALL update the coordinator's data and notify entities.

#### Scenario: Forecast update received
- **WHEN** a `ForecastData` arrives from `stream_forecasts()`
- **THEN** `coordinator.data.forecasts[(location, model)]` is updated and `async_set_updated_data()` is called

### Requirement: Enrichment stream pushes data to coordinator
Each `EnrichmentEvent` from the enrichment stream SHALL be merged into the coordinator's enrichment data and notify entities.

#### Scenario: Enrichment update received
- **WHEN** an `EnrichmentData` arrives from `stream_enrichments()`
- **THEN** it is merged into `coordinator.data.enrichments[location]` (see enrichment-merge spec) and `async_set_updated_data()` is called

### Requirement: Config stream triggers entity creation
Each config update from the config stream SHALL be checked for new locations.

#### Scenario: Config update with new location
- **WHEN** a `NjordConfigData` arrives from `stream_config()` containing a location not in `coordinator._known_locations`
- **THEN** the dynamic entity creation flow is triggered (see dynamic-entity-creation spec)

#### Scenario: Config update with no new locations
- **WHEN** a `NjordConfigData` arrives but all locations are already known
- **THEN** no entity creation is triggered and no error occurs

### Requirement: No polling fallback
The coordinator SHALL NOT have a poll interval. Data updates come exclusively from streams (after the initial unary refresh).

#### Scenario: Coordinator has no update interval
- **WHEN** the coordinator is instantiated
- **THEN** `update_interval` is `None`

#### Scenario: Stream disconnect retains last state
- **WHEN** a stream disconnects and is reconnecting
- **THEN** `coordinator.data` retains the last known values and entities remain available
