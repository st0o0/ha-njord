## MODIFIED Requirements

### Requirement: Alert entities have type-specific icons
Each alert binary_sensor entity SHALL have an icon matching its alert type (e.g., frost → snowflake, UV → sun).

#### Scenario: UV alert shows sun icon
- **WHEN** the UV Alert entity is displayed in the HA dashboard
- **THEN** it shows the `mdi:sun-wireless` icon

#### Scenario: Frost alert shows snowflake icon
- **WHEN** the Frost Alert entity is displayed
- **THEN** it shows the `mdi:snowflake-alert` icon

### Requirement: Alert entities have translation keys
Each alert binary_sensor SHALL have a `_attr_translation_key` and corresponding translations.

#### Scenario: Alert name is translatable
- **WHEN** HA language is set to German
- **THEN** the Frost Alert shows as "Frost-Warnung"

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
