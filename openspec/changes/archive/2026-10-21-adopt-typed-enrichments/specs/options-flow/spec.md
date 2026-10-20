## REMOVED Requirements

### Requirement: Enrichment group toggles
**Reason**: njord reports the active features in `StatusResponse.active_enrichments`; there are no toggles on the HA side.
**Migration**: The v2 to v3 config entry migration drops stored toggles.

## MODIFIED Requirements

### Requirement: Enrichment toggle triggers reload
Changing the sensor push configuration SHALL trigger a config entry reload. Changing only the poll interval SHALL NOT trigger a reload.

#### Scenario: Only poll interval changed
- **WHEN** the user changes only the poll interval
- **THEN** the status coordinator's `update_interval` is updated in-place without reload

#### Scenario: Sensor push mapping changed
- **WHEN** the user changes the sensor push entity mapping
- **THEN** `async_reload` is called on the config entry

### Requirement: Options flow UI strings
`strings.json` and `translations/de.json` SHALL include option step labels and field descriptions.

#### Scenario: English strings present
- **WHEN** the options flow is rendered in English
- **THEN** all field labels and descriptions are present from `strings.json`

#### Scenario: German strings present
- **WHEN** the options flow is rendered in German
- **THEN** all field labels and descriptions are present from `translations/de.json`
