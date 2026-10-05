## ADDED Requirements

### Requirement: Weather entities support dynamic addition
The weather platform SHALL store its `async_add_entities` callback and a factory function on the coordinator during setup, enabling entity creation for locations discovered after initial setup.

#### Scenario: Late entity creation
- **WHEN** a new location "bern" with models ["icon_d2", "gfs"] is detected via config stream
- **THEN** two new `NjordWeatherEntity` instances are created and registered in HA for "bern"

#### Scenario: Consensus entity for new location
- **WHEN** a new location is detected and enrichment data with consensus is available
- **THEN** a `NjordConsensusWeatherEntity` is also created for that location
