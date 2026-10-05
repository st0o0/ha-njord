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
