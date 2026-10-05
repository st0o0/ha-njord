## MODIFIED Requirements

### Requirement: Channel lifecycle
The `NjordClient` SHALL manage a gRPC channel to a njord server specified by host and port, supporting explicit connect, close, and async context manager usage. On connect, it SHALL create four service stubs: `WeatherServiceStub`, `AdminServiceStub`, `OpsServiceStub`, and `SensorServiceStub`.

#### Scenario: Connect and close
- **WHEN** a caller creates a `NjordClient(host, port)` and calls `await client.connect()`
- **THEN** an insecure gRPC channel is opened to `host:port` and four service stubs (WeatherService, AdminService, OpsService, SensorService) are created

#### Scenario: Context manager
- **WHEN** a caller uses `async with NjordClient(host, port) as client:`
- **THEN** the channel is opened on entry and closed on exit

#### Scenario: Close releases resources
- **WHEN** `await client.close()` is called
- **THEN** the gRPC channel is closed and all stubs are set to None
