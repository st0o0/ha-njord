## ADDED Requirements

### Requirement: All DeviceInfo entries include sw_version
Every `DeviceInfo` created by the integration SHALL include `sw_version` populated from the server version obtained via `GetStatus()`. If the status coordinator is unavailable, `sw_version` SHALL be omitted (not set to a placeholder).

#### Scenario: Server version available at entity creation
- **WHEN** entities are created and the status coordinator has data with `version = "2.1.0"`
- **THEN** all DeviceInfo entries include `sw_version="2.1.0"`

#### Scenario: Status coordinator unavailable at entity creation
- **WHEN** entities are created but the status coordinator failed its first refresh
- **THEN** DeviceInfo entries omit `sw_version` (field not set)

### Requirement: All DeviceInfo entries include model
Every `DeviceInfo` SHALL include a `model` field. Location-scoped devices SHALL use `model="Weather Station"`. The server-scoped device SHALL use `model="Weather Service"`.

#### Scenario: Location device model
- **WHEN** a weather or enrichment entity creates its DeviceInfo for location "Innsbruck"
- **THEN** `model="Weather Station"` is set

#### Scenario: Server device model
- **WHEN** a server-level entity (budget, uptime, version, trigger poll) creates its DeviceInfo
- **THEN** `model="Weather Service"` is set

### Requirement: Button entity uses shared server DeviceInfo
The `TriggerPollButton` SHALL use the same DeviceInfo fields as server-scoped sensors (identifiers, name, manufacturer, model, sw_version). A shared helper or consistent construction SHALL be used to prevent drift.

#### Scenario: Button device groups with server sensors
- **WHEN** the trigger poll button and server sensors are registered
- **THEN** they appear under the same device in HA's device registry
- **AND** the device shows manufacturer, model, and sw_version
