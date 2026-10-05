## ADDED Requirements

### Requirement: Enrichment sensors are disabled by default
All enrichment sensor entities SHALL have `_attr_entity_registry_enabled_default = False`, so they appear in the entity registry but are disabled until the user explicitly enables them.

#### Scenario: Index sensor is disabled by default
- **WHEN** the integration is set up for the first time
- **THEN** index sensors (laundry, outdoor, cycling, etc.) are registered but disabled

#### Scenario: Energy sensor is disabled by default
- **WHEN** the integration is set up
- **THEN** energy sensors (heating demand, COP, shading, etc.) are registered but disabled

#### Scenario: User enables a sensor
- **WHEN** a user enables a disabled sensor in the HA entity registry
- **THEN** the sensor becomes active and shows its current value
