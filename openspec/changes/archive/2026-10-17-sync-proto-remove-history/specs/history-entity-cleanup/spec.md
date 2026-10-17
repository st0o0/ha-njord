## ADDED Requirements

### Requirement: Stale model performance entities are removed
On config entry setup the integration SHALL remove every sensor entity of that entry whose unique id ends with `_model_performance` from the entity registry, before platforms are set up. No new entity of that kind SHALL be created.

#### Scenario: Existing model performance sensor is removed
- **WHEN** the entry has a registered `sensor.lucerne_model_performance` from a previous version and the integration is set up
- **THEN** the entity registry no longer contains it

#### Scenario: Other sensors are untouched
- **WHEN** the integration is set up with registered alert, index, trend and derived sensors
- **THEN** those registry entries are preserved

#### Scenario: Clean registry
- **WHEN** no `_model_performance` entity is registered
- **THEN** setup completes without error and removes nothing
