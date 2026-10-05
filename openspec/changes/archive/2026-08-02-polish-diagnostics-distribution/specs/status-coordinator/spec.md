## MODIFIED Requirements

### Requirement: Dedicated status coordinator polls server status
A `NjordStatusCoordinator` SHALL poll `OpsService.GetStatus` and `OpsService.GetTargets` using HA's `DataUpdateCoordinator`. Its `update_interval` SHALL default to `timedelta(seconds=30)` but SHALL be configurable via `ConfigEntry.options["status_poll_interval"]`. Its data type SHALL be `ServerStatusData` which includes a `targets: list[TargetData]` field.

#### Scenario: Normal polling cycle
- **WHEN** the configured interval has elapsed since the last update
- **THEN** the coordinator calls both `GetStatus` and `GetTargets` and updates its data

#### Scenario: First refresh on startup
- **WHEN** the integration is set up
- **THEN** the status coordinator performs an initial refresh before entities are created

#### Scenario: Server unreachable
- **WHEN** `GetStatus` raises an exception
- **THEN** the coordinator raises `UpdateFailed` and HA applies exponential backoff automatically

#### Scenario: Custom poll interval from options
- **WHEN** `entry.options["status_poll_interval"]` is 60
- **THEN** the coordinator uses a 60-second update interval

#### Scenario: Poll interval updated without reload
- **WHEN** the user changes the poll interval via OptionsFlow without changing enrichment groups
- **THEN** the coordinator's `update_interval` is updated in-place
