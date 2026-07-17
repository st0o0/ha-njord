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

### Requirement: HDD sensor
The integration SHALL expose a Heating Degree Days sensor per location, sourced from `IndexData.hdd`.

#### Scenario: HDD sensor shows value
- **WHEN** enrichment data contains `hdd = 5.2`
- **THEN** the sensor shows `5.2` with unit `°C·d` and icon `mdi:thermometer-chevron-up`

#### Scenario: HDD sensor unavailable without index data
- **WHEN** enrichment data has no indices
- **THEN** the HDD sensor is unavailable

### Requirement: CDD sensor
The integration SHALL expose a Cooling Degree Days sensor per location, sourced from `IndexData.cdd`.

#### Scenario: CDD sensor shows value
- **WHEN** enrichment data contains `cdd = 3.1`
- **THEN** the sensor shows `3.1` with unit `°C·d` and icon `mdi:thermometer-chevron-down`

### Requirement: Frost hours sensor
The integration SHALL expose a Frost Hours sensor per location, sourced from `IndexData.frost_hours`.

#### Scenario: Frost hours sensor shows value
- **WHEN** enrichment data contains `frost_hours = 4`
- **THEN** the sensor shows `4` with unit `h` and icon `mdi:snowflake-thermometer`

#### Scenario: Frost hours sensor shows None when not available
- **WHEN** enrichment data has indices but `frost_hours` is None
- **THEN** the sensor shows unknown state

### Requirement: Frost confidence sensor
The integration SHALL expose a Frost Confidence sensor per location, sourced from `IndexData.frost_confidence`, displayed as a percentage (0-100).

#### Scenario: Frost confidence sensor shows percentage
- **WHEN** enrichment data contains `frost_confidence = 0.85`
- **THEN** the sensor shows `85.0` with unit `%` and icon `mdi:snowflake-check`

#### Scenario: Frost confidence sensor shows None when not available
- **WHEN** enrichment data has indices but `frost_confidence` is None
- **THEN** the sensor shows unknown state

### Requirement: New sensors have translation keys
All new sensors SHALL have `_attr_translation_key` set and corresponding entries in `strings.json` and `translations/de.json`.

#### Scenario: German translations exist
- **WHEN** HA language is set to German
- **THEN** HDD shows as "Heizgradtage", CDD as "Kühlgradtage", Frost Hours as "Froststunden", Frost Confidence as "Frostwahrscheinlichkeit"

### Requirement: Sensor entities support dynamic addition
The sensor and binary_sensor platforms SHALL store their `async_add_entities` callbacks and factory functions on the coordinator during setup, enabling entity creation for locations discovered after initial setup.

#### Scenario: Late sensor creation
- **WHEN** a new location "bern" is detected via config stream and enrichment data arrives for it
- **THEN** sensor and binary_sensor entities are created for "bern" matching the same patterns as initially created locations

#### Scenario: No duplicate sensors on repeated config events
- **WHEN** the config stream sends multiple events containing "bern" after it was already added
- **THEN** no duplicate sensor entities are created
