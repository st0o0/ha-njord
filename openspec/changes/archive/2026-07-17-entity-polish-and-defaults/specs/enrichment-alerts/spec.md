## ADDED Requirements

### Requirement: Alert sensors remain enabled by default
Alert binary sensor entities SHALL keep the default `_attr_entity_registry_enabled_default = True`, so they are active immediately after setup.

#### Scenario: Alert sensors are enabled after setup
- **WHEN** the integration is set up for the first time
- **THEN** all 9 alert binary sensors (frost, heat, storm, etc.) are registered and enabled

### Requirement: Inversion sensor is disabled by default
The inversion binary sensor SHALL have `_attr_entity_registry_enabled_default = False`.

#### Scenario: Inversion sensor is disabled after setup
- **WHEN** the integration is set up for the first time
- **THEN** the inversion binary sensor is registered but disabled
