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
