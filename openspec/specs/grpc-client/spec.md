## Purpose

Defines the gRPC client module for communicating with the njord weather service — channel management, unary RPCs, server-streaming RPCs, reconnect logic, and typed data models.

## Requirements

### Requirement: Channel lifecycle
The `NjordClient` SHALL manage a gRPC channel to a njord server specified by host and port, supporting explicit connect, close, and async context manager usage.

#### Scenario: Connect and close
- **WHEN** a caller creates a `NjordClient(host, port)` and calls `await client.connect()`
- **THEN** an insecure gRPC channel is opened to `host:port` and the client is ready for RPC calls

#### Scenario: Context manager
- **WHEN** a caller uses `async with NjordClient(host, port) as client:`
- **THEN** the channel is opened on entry and closed on exit

#### Scenario: Close releases resources
- **WHEN** `await client.close()` is called
- **THEN** the gRPC channel is closed and subsequent RPC calls raise an error

### Requirement: Get locations
The client SHALL provide an async method to retrieve all configured locations from njord.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_locations()` is called
- **THEN** a list of location name strings is returned

### Requirement: Get models
The client SHALL provide an async method to retrieve available weather models for a given location.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_models(location)` is called with a valid location name
- **THEN** a list of model name strings for that location is returned

### Requirement: Get forecast
The client SHALL provide an async method to retrieve the current forecast for a given location and model, returning typed dataclasses.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_forecast(location, model)` is called
- **THEN** a `ForecastData` object is returned containing location, model, updated_at timestamp, hourly forecasts, and daily forecasts

#### Scenario: Hourly forecast fields
- **WHEN** a `HourlyForecastData` is inspected
- **THEN** it contains timestamp, temperature, apparent_temperature, precipitation, humidity, wind_speed, wind_bearing, cloud_cover, weather_code, is_day, rain, wind_gusts, and pressure_msl as optional fields

### Requirement: Get config
The client SHALL provide an async method to retrieve njord's current configuration.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_config()` is called
- **THEN** a `NjordConfigData` object is returned containing locations (with coordinates and models), default_models, horizons, forecast_days, and poll_interval_seconds

### Requirement: Get status
The client SHALL provide an async method to retrieve njord's server status.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_status()` is called
- **THEN** a `ServerStatusData` object is returned containing version, uptime_seconds, and budget information

### Requirement: Stream forecasts
The client SHALL provide an async iterator for real-time forecast updates via server-streaming RPC.

#### Scenario: Receive updates
- **WHEN** `async for update in client.stream_forecasts()` is used
- **THEN** each iteration yields a `ForecastData` object when njord pushes a forecast update

#### Scenario: Filter by location
- **WHEN** `client.stream_forecasts(location="lucerne")` is called with a location
- **THEN** only forecast updates for that location are received

### Requirement: Stream config
The client SHALL provide an async iterator for real-time config change notifications via server-streaming RPC.

#### Scenario: Receive config changes
- **WHEN** `async for config in client.stream_config()` is used
- **THEN** each iteration yields an `NjordConfigData` object when njord's configuration changes

### Requirement: Reconnect with exponential backoff
The streaming methods SHALL automatically reconnect on stream failure using exponential backoff.

#### Scenario: Stream failure and recovery
- **WHEN** a streaming RPC connection drops
- **THEN** the client waits with exponential backoff (1s, 2s, 4s, ... up to 60s max) and reconnects automatically, resuming the async iterator

#### Scenario: Backoff reset on success
- **WHEN** a message is successfully received after reconnection
- **THEN** the backoff delay resets to the initial value (1s)

#### Scenario: Disconnect callback
- **WHEN** a stream disconnects or reconnects
- **THEN** the provided `on_disconnect` and `on_reconnect` callbacks are invoked so callers can react (e.g., mark entities unavailable)

### Requirement: Get enrichments
The client SHALL provide an async method to retrieve enrichment data for a given location, returning typed dataclasses.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_enrichments(location)` is called
- **THEN** an `EnrichmentData` object is returned containing alerts, indices, trends, energy, derived, history, and consensus data for that location

### Requirement: Stream enrichments
The client SHALL provide an async iterator for real-time enrichment updates via server-streaming RPC.

#### Scenario: Receive updates
- **WHEN** `async for event in client.stream_enrichments()` is used
- **THEN** each iteration yields an `EnrichmentData` object containing only the changed enrichment type (partial payload)

#### Scenario: Filter by location
- **WHEN** `client.stream_enrichments(location="lucerne")` is called with a location
- **THEN** only enrichment updates for that location are received

#### Scenario: Reconnect on failure
- **WHEN** the enrichment stream disconnects
- **THEN** the client reconnects with exponential backoff, same as other streaming RPCs

### Requirement: Typed data models
All public API methods SHALL return typed Python dataclasses, never raw protobuf message objects.

#### Scenario: IndexData includes all proto fields
- **WHEN** `IndexData` is returned as part of enrichment data
- **THEN** it contains `hdd`, `cdd`, `frost_hours`, and `frost_confidence` fields in addition to existing activity index fields and VPD fields

#### Scenario: No protobuf leakage
- **WHEN** a consumer uses any `NjordClient` method
- **THEN** the return type is a dataclass from `models.py`, not a `_pb2` generated class
