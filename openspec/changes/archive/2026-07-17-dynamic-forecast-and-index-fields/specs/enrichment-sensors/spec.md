## ADDED Requirements

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
