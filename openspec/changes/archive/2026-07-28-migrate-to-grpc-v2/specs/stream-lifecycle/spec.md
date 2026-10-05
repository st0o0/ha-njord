## MODIFIED Requirements

### Requirement: Stream tasks are started after first refresh
The coordinator SHALL start three background asyncio tasks (forecast stream, enrichment stream, config stream) plus a status poll task via a `start_streams()` method called after initial data load and platform setup. Forecast and enrichment streams use `WeatherServiceStub`. Config stream uses `AdminServiceStub`.

#### Scenario: Streams start on integration setup
- **WHEN** the integration entry is set up and platforms are forwarded
- **THEN** `coordinator.start_streams()` creates three streaming tasks consuming `stream_forecasts()` (WeatherService), `stream_enrichments()` (WeatherService), and `stream_config()` (AdminService), plus a status poll task using `get_status()` (OpsService)

#### Scenario: Initial data is available before streams start
- **WHEN** `start_streams()` is called
- **THEN** `coordinator.data` already contains forecast and enrichment data from the unary first refresh
