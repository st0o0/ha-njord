## ADDED Requirements

### Requirement: Entity identity is unchanged
Introducing typed values SHALL NOT change any entity id, unique id, translation key, device identifier or stored option value.

#### Scenario: Entities after the refactor
- **WHEN** the integration is set up with the default fixtures
- **THEN** every alert, index, trend, derived, server, stream and event entity has the same unique id and entity id as before

#### Scenario: Stored options remain valid
- **WHEN** a config entry holds `disabled_enrichment_groups`, `status_poll_interval` and `sensor_push` as written by an earlier version
- **THEN** the entry loads without migration and applies them as before

### Requirement: Enrichment group enablement is evaluated in one place
An enrichment group SHALL be enabled for entity creation exactly when the server reports it active (or reports no active list) and the user has not disabled it. Unknown group names in stored options SHALL be ignored.

#### Scenario: Group active and not disabled
- **WHEN** the server lists `alerts` as active and the user did not disable it
- **THEN** the alert entities are created

#### Scenario: Group disabled by the user
- **WHEN** the user disabled `trends`
- **THEN** no trend entity is created even if the server lists it as active

#### Scenario: Legacy value in options
- **WHEN** `disabled_enrichment_groups` contains an unknown name such as `history`
- **THEN** it has no effect and setup succeeds

### Requirement: Unknown wire values are tolerated
Alert types, alert severities and the closed-set text values delivered by njord (poll phase, trend direction, stability, dew point comfort, VPD category) SHALL map an unspecified or unrecognised value to a safe default instead of raising. An alert of unknown type SHALL NOT create an entity.

#### Scenario: Unknown alert severity
- **WHEN** an alert arrives with a severity number the client does not know
- **THEN** it is treated as severity none

#### Scenario: Unknown alert type
- **WHEN** an alert arrives with an unspecified or unknown type
- **THEN** no entity is created for it and no error is raised

#### Scenario: Unknown dew point comfort
- **WHEN** a derived payload carries an unknown dew point comfort value
- **THEN** the dew point comfort sensor reports unknown/unavailable instead of an invalid state

### Requirement: Alert severity ordering
Alert severity SHALL be ordered none < yellow < orange < red. An escalation event is fired when the severity rank increases and a de-escalation event when it decreases.

#### Scenario: Escalation
- **WHEN** an alert changes from yellow to red
- **THEN** an escalated event is fired

#### Scenario: De-escalation
- **WHEN** an alert changes from orange to yellow
- **THEN** a de-escalated event is fired

### Requirement: Stale stored sensor kinds are skipped
When the sensor push configuration contains a kind that is no longer supported, the integration SHALL skip that entry and continue instead of failing.

#### Scenario: Stored kind removed upstream
- **WHEN** `sensor_push` for a location contains an unsupported kind
- **THEN** setup and the options form still work and the entry is ignored
