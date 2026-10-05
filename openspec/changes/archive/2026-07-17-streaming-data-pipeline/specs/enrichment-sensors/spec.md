## ADDED Requirements

### Requirement: Sensor entities support dynamic addition
The sensor and binary_sensor platforms SHALL store their `async_add_entities` callbacks and factory functions on the coordinator during setup, enabling entity creation for locations discovered after initial setup.

#### Scenario: Late sensor creation
- **WHEN** a new location "bern" is detected via config stream and enrichment data arrives for it
- **THEN** sensor and binary_sensor entities are created for "bern" matching the same patterns as initially created locations

#### Scenario: No duplicate sensors on repeated config events
- **WHEN** the config stream sends multiple events containing "bern" after it was already added
- **THEN** no duplicate sensor entities are created
