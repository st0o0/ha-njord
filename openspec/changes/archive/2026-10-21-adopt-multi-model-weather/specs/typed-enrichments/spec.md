## ADDED Requirements

### Requirement: ModelComparison is shown as a temperature spread sensor
The integration SHALL map the `Weather:ModelComparison` feature (`EnrichmentEvent.model_comparison`) to a sensor "Model Temperature Spread" with unique id `{entry_id}_{location_slug}_model_comparison`, device class temperature, unit °C and precision 1. Its state SHALL be the difference between the highest and the lowest `max_temperature` of the first day across the models that report one, or unknown with fewer than two values. Its attributes SHALL include the full `days` list with per-model values.

#### Scenario: Two models disagree
- **WHEN** the first day reports `max_temperature` 21.4 for one model and 19.0 for another
- **THEN** the sensor state is 2.4 and the attribute `days` lists both models

#### Scenario: One model only
- **WHEN** the first day reports a `max_temperature` for a single model
- **THEN** the sensor state is unknown

#### Scenario: Feature not active
- **WHEN** the server's `active_enrichments` do not contain `Weather:ModelComparison`
- **THEN** no Model Temperature Spread sensor is created
