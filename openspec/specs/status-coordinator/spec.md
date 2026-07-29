## Purpose

Defines a dedicated status coordinator that polls server status independently from the main data coordinator, providing faster status updates and fault isolation.

## Requirements

### Requirement: Dedicated status coordinator polls server status
A `NjordStatusCoordinator` SHALL poll `OpsService.GetStatus` every 30 seconds using HA's `DataUpdateCoordinator` with `update_interval=timedelta(seconds=30)`. Its data type SHALL be `ServerStatusData`.

#### Scenario: Normal polling cycle
- **WHEN** 30 seconds have elapsed since the last update
- **THEN** the coordinator calls `OpsService.GetStatus` and updates its data

#### Scenario: First refresh on startup
- **WHEN** the integration is set up
- **THEN** the status coordinator performs an initial refresh before entities are created

#### Scenario: Server unreachable
- **WHEN** `GetStatus` raises an exception
- **THEN** the coordinator raises `UpdateFailed` and HA applies exponential backoff automatically

### Requirement: Status coordinator failure does not block integration setup
If the status coordinator's first refresh fails, the integration SHALL still load. Weather entities and the data coordinator SHALL function independently.

#### Scenario: Status unreachable at startup
- **WHEN** `GetStatus` fails during `async_config_entry_first_refresh`
- **THEN** the integration continues setup with a `None` status coordinator
- **AND** status sensors show as unavailable
- **AND** weather entities function normally

### Requirement: Status sensors use the status coordinator
`NjordApiBudgetSensor` and `NjordUptimeSensor` SHALL be `CoordinatorEntity[NjordStatusCoordinator]` and read directly from `self.coordinator.data` (which is `ServerStatusData`).

#### Scenario: Budget sensor reads from status coordinator
- **WHEN** the status coordinator has data with `budget.usage_percent = 25.0`
- **THEN** the API Budget sensor's `native_value` is `25.0`

#### Scenario: Uptime sensor reads from status coordinator
- **WHEN** the status coordinator has data with `uptime_seconds = 7200`
- **THEN** the Uptime sensor's `native_value` is `2.0` (hours)

#### Scenario: Status coordinator has no data
- **WHEN** the status coordinator's data is `None`
- **THEN** both sensors report as unavailable

### Requirement: Main coordinator has no status polling
`NjordDataCoordinator` SHALL NOT fetch or store server status data. The `_run_status_poll()` background task, `_STATUS_POLL_INTERVAL`, and `server_status` field on `NjordCoordinatorData` SHALL be removed.

#### Scenario: Main coordinator streams only
- **WHEN** the data coordinator starts streams
- **THEN** no status poll task is created

#### Scenario: NjordCoordinatorData has no server_status
- **WHEN** `NjordCoordinatorData` is instantiated
- **THEN** it has no `server_status` field
