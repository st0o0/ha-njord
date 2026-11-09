## Purpose

Defines the gRPC client module for communicating with the njord weather service -- channel management, unary RPCs, server-streaming RPCs, and typed data models.

## Requirements

### Requirement: gRPC client wraps njord API
The gRPC client SHALL wrap the njord `NjordService` API. It SHALL provide async methods for `GetManifest`, `Subscribe`, `GetStatus`, and `TriggerPoll`.

#### Scenario: Client connects to API
- **WHEN** the integration starts and connects to njord
- **THEN** the client SHALL use the NjordService stub for all operations

#### Scenario: Subscribe returns an async iterator
- **WHEN** the coordinator calls subscribe
- **THEN** the client SHALL return an async iterator of EntityEvent messages

### Requirement: Channel lifecycle
The `NjordClient` SHALL manage a gRPC channel to a njord server specified by host and port, supporting explicit connect, close, and async context manager usage. On connect, it SHALL create a `NjordServiceStub`.

#### Scenario: Connect and close
- **WHEN** a caller creates a `NjordClient(host, port)` and calls `await client.connect()`
- **THEN** an insecure gRPC channel is opened to `host:port` and the NjordService stub is created

#### Scenario: Context manager
- **WHEN** a caller uses `async with NjordClient(host, port) as client:`
- **THEN** the channel is opened on entry and closed on exit

#### Scenario: Close releases resources
- **WHEN** `await client.close()` is called
- **THEN** the gRPC channel is closed and the stub is set to None

### Requirement: Get manifest
The client SHALL provide an async method to retrieve entity definitions from njord via `NjordService.GetManifest`.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_manifest()` is called
- **THEN** a list of `ManifestEntity` objects is returned, each with entity_id, platform, device_class, unit, output_kind, feature, location, category, and icon

### Requirement: Get status
The client SHALL provide an async method to retrieve njord's server status via `NjordService.GetStatus`.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_status()` is called
- **THEN** a `ServerStatusData` object is returned containing version, uptime_seconds, budget information, process_start, model_statuses, and active_enrichments

### Requirement: Trigger poll
The client SHALL provide an async method to trigger a forecast poll via `NjordService.TriggerPoll`.

#### Scenario: Trigger all locations
- **WHEN** `await client.trigger_poll()` is called with no arguments
- **THEN** `NjordService.TriggerPoll(location="")` is called and the triggered count is returned

#### Scenario: Trigger specific location
- **WHEN** `await client.trigger_poll(location="graz")` is called
- **THEN** `NjordService.TriggerPoll(location="graz")` is called

### Requirement: Subscribe stream
The client SHALL provide an async iterator for the unified entity stream via `NjordService.Subscribe` server-streaming RPC.

#### Scenario: Receive entity events
- **WHEN** `async for event in client.subscribe()` is used
- **THEN** each iteration yields an EntityEvent containing snapshots, state updates, or availability changes

#### Scenario: Filter by location
- **WHEN** `client.subscribe(location="lucerne")` is called
- **THEN** only entity events for that location are received

### Requirement: Reconnect with exponential backoff
The streaming methods SHALL automatically reconnect on stream failure using exponential backoff.

#### Scenario: Stream failure and recovery
- **WHEN** a streaming RPC connection drops
- **THEN** the client waits with exponential backoff (1s, 2s, 4s, ... up to 60s max) and reconnects automatically

#### Scenario: Backoff reset on success
- **WHEN** a message is successfully received after reconnection
- **THEN** the backoff delay resets to the initial value (1s)

### Requirement: Status maps partial flags
`get_status` SHALL map `StatusResponse.budget_partial` and `StatusResponse.models_partial` to `ServerStatusData.budget_partial` and `ServerStatusData.models_partial`.

#### Scenario: Complete status
- **WHEN** the response has `budget_partial = false` and `models_partial = false`
- **THEN** both `ServerStatusData` flags are `False`

#### Scenario: Partial status
- **WHEN** the response has `budget_partial = true` and `models_partial = true`
- **THEN** both `ServerStatusData` flags are `True`

### Requirement: Typed data models
All public API methods SHALL return typed Python dataclasses, never raw protobuf message objects. Temporal fields SHALL be `datetime` objects, not integer epochs.

#### Scenario: No protobuf leakage
- **WHEN** a consumer uses any `NjordClient` method
- **THEN** the return type is a dataclass from `models.py`, not a `_pb2` generated class

#### Scenario: Timestamps are datetime
- **WHEN** status data is returned
- **THEN** `process_start` is a `datetime` object with UTC timezone, not an integer
