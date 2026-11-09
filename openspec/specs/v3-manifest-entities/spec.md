# v3-manifest-entities Specification

## Purpose
Defines how HA entities are created from the njord manifest and how generic per-OutputKind entity classes work.

## Requirements

### Requirement: Entity creation driven by server manifest
The integration SHALL create HA entities from the njord `GetManifest` response. Each manifest entry defines an entity with `entity_id`, `platform`, `device_class`, `unit`, and `output_kind`. No hardcoded entity metadata (ALERT_META, FEATURE_KEYS, DOMAIN_SENSOR_REGISTRY) SHALL be required.

#### Scenario: Manifest defines a sensor entity
- **WHEN** the manifest contains an entity with platform=sensor, device_class=pm25, unit=ug/m3
- **THEN** the integration SHALL create a sensor entity with the matching device class and unit

#### Scenario: New feature added server-side
- **WHEN** njord adds a new Observation feature and the manifest includes its entity definition
- **THEN** ha-njord SHALL create the corresponding entity without code changes

### Requirement: Generic entity classes per OutputKind
The integration SHALL use one entity class per OutputKind (Alert, Score, Condition, Trend, Forecast, Observation, Weather) instead of per-feature classes. Each class SHALL extract its state from the corresponding value type.

#### Scenario: Alert entity from AlertValue
- **WHEN** an EntityStateUpdate arrives with an AlertValue for entity vienna_frost
- **THEN** the alert binary sensor SHALL update with severity, confidence, and active state from the AlertValue

#### Scenario: Observation entity from ObservationValue
- **WHEN** an EntityStateUpdate arrives with an ObservationValue for entity vienna_pm25_observation
- **THEN** the observation sensor SHALL update with the numeric value

### Requirement: Entity ID preservation
Entity unique IDs SHALL follow the pattern `njord_{location_slug}_{feature_snake_case}` to match existing entity IDs. Existing entities SHALL not require migration in the HA entity registry.

#### Scenario: Existing entity keeps its ID
- **WHEN** a user upgrades to the manifest-driven entity system
- **THEN** the frost alert entity for Vienna SHALL keep the same entity_id and unique_id
