## MODIFIED Requirements

### Requirement: gRPC client wraps njord API
The gRPC client SHALL wrap the njord v3 `NjordService` API. It SHALL provide async methods for `GetManifest`, `Subscribe`, `GetStatus`, and `TriggerPoll`. The v2 `WeatherService` and `OpsService` stubs SHALL be removed after migration.

#### Scenario: Client connects to v3 API
- **WHEN** the integration starts and connects to njord
- **THEN** the client SHALL use the v3 NjordService stub for all operations

#### Scenario: Subscribe returns an async iterator
- **WHEN** the coordinator calls subscribe
- **THEN** the client SHALL return an async iterator of EntityEvent messages
