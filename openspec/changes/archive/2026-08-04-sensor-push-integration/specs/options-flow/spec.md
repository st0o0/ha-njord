## MODIFIED Requirements

### Requirement: OptionsFlow is available after setup
The integration SHALL provide an `OptionsFlow` accessible from the integration's configuration page in HA. It SHALL present settings across two steps: general settings (init) and sensor push configuration (sensors).

#### Scenario: User opens options
- **WHEN** the user clicks "Configure" on the njord integration entry
- **THEN** an options form is shown with status poll interval and enrichment group toggles
- **AND** after submitting, a second step for sensor push configuration is shown

### Requirement: Enrichment toggle triggers reload
Changing the enrichment group selection or the sensor push configuration SHALL trigger a config entry reload. Changing only the poll interval SHALL NOT trigger a reload.

#### Scenario: Only poll interval changed
- **WHEN** the user changes only the poll interval
- **THEN** the status coordinator's `update_interval` is updated in-place without reload

#### Scenario: Enrichment groups changed
- **WHEN** the user changes the enrichment group selection
- **THEN** `async_reload` is called on the config entry

#### Scenario: Sensor push mapping changed
- **WHEN** the user changes the sensor push entity mapping
- **THEN** `async_reload` is called on the config entry
