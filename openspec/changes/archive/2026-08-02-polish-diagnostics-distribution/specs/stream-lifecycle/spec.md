## MODIFIED Requirements

### Requirement: Stream tasks are started after first refresh
The coordinator SHALL start three background asyncio tasks (forecast stream, enrichment stream, config stream) via a `start_streams()` method called after initial data load and platform setup. Forecast and enrichment streams use `WeatherServiceStub`. Config stream uses `AdminServiceStub`. Each stream wrapper SHALL update `coordinator.stream_states` on connect and disconnect.

#### Scenario: Streams start on integration setup
- **WHEN** the integration entry is set up and platforms are forwarded
- **THEN** `coordinator.start_streams()` creates three streaming tasks consuming `stream_forecasts()` (WeatherService), `stream_enrichments()` (WeatherService), and `stream_config()` (AdminService)

#### Scenario: Initial data is available before streams start
- **WHEN** `start_streams()` is called
- **THEN** `coordinator.data` already contains forecast and enrichment data from the unary first refresh

#### Scenario: Stream states initialized before streams start
- **WHEN** `start_streams()` is called
- **THEN** `coordinator.stream_states` is `{"forecast": False, "enrichment": False, "config": False}`

### Requirement: Stream reconnect wrapper tracks connection state
The `_stream_with_reconnect` method SHALL update `stream_states[name]` to `True` when a stream connection is established and to `False` when it disconnects or errors. On state change, it SHALL call `async_set_updated_data` to notify binary sensor entities.

#### Scenario: Stream connects successfully
- **WHEN** a stream establishes its gRPC connection
- **THEN** `stream_states[name]` is set to `True` and entities are notified

#### Scenario: Stream disconnects
- **WHEN** a stream raises an exception or the iterator ends
- **THEN** `stream_states[name]` is set to `False` and entities are notified

### Requirement: Stream reconnect wrapper manages repair issues
The stream wrapper SHALL create an HA repair issue if a stream remains disconnected for more than 60 seconds. The issue SHALL be dismissed when the stream reconnects.

#### Scenario: Prolonged disconnect creates repair issue
- **WHEN** a stream has been disconnected for over 60 seconds during reconnect backoff
- **THEN** an HA repair issue is created with identifier `njord_stream_{name}_disconnected`

#### Scenario: Reconnect dismisses repair issue
- **WHEN** a stream reconnects and a repair issue exists for it
- **THEN** the repair issue is dismissed via `async_delete_issue`
