## MODIFIED Requirements

### Requirement: Sensor entities have icons
Every sensor entity SHALL have an `_attr_icon` set to an appropriate MDI icon.

#### Scenario: Index sensors show activity icons
- **WHEN** the BBQ Index sensor is displayed in the HA dashboard
- **THEN** it shows the `mdi:grill` icon

#### Scenario: Energy sensors show energy-related icons
- **WHEN** the Heating Demand sensor is displayed
- **THEN** it shows the `mdi:radiator` icon

### Requirement: Sensor entities have translation keys
Every sensor entity SHALL have a `_attr_translation_key` set, and corresponding entries in `strings.json` and `translations/de.json`.

#### Scenario: Sensor name is translatable
- **WHEN** HA language is set to German
- **THEN** the BBQ Index sensor shows as "Grillwetter-Index"

### Requirement: Sensor entities support dynamic addition
The sensor and binary_sensor platforms SHALL store their `async_add_entities` callbacks and factory functions on the coordinator during setup, enabling entity creation for locations discovered after initial setup.

#### Scenario: Late sensor creation
- **WHEN** a new location "bern" is detected via config stream and enrichment data arrives for it
- **THEN** sensor and binary_sensor entities are created for "bern" matching the same patterns as initially created locations

#### Scenario: No duplicate sensors on repeated config events
- **WHEN** the config stream sends multiple events containing "bern" after it was already added
- **THEN** no duplicate sensor entities are created
