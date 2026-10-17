## MODIFIED Requirements

### Requirement: Enrichment group toggles
The OptionsFlow SHALL include a multi-select field for enrichment groups. Available groups: `alerts`, `indices`, `trends`, `derived`, `consensus`. All groups SHALL be enabled by default. Disabled groups are stored as a list in `entry.options["disabled_enrichment_groups"]`. Unknown stored groups (such as a legacy `history`) SHALL be ignored when the form is shown.

#### Scenario: User re-enables a group
- **WHEN** the user re-selects a previously disabled group and submits
- **THEN** the config entry reloads
- **AND** entities for that group are created

#### Scenario: Legacy history group stored
- **WHEN** `disabled_enrichment_groups` contains `history` and the options form is opened
- **THEN** the form renders without error and does not offer `history`
