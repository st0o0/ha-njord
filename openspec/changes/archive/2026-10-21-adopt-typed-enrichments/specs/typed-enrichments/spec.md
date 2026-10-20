## ADDED Requirements

### Requirement: Enrichment events are typed per feature
The client SHALL map every `EnrichmentEvent` and every entry of `GetEnrichmentsResponse.events` to a `FeatureData` keyed by `(location, Feature)`. Alert features SHALL carry an `AlertData`, score features a `ScoreData`, and all other fields SHALL be in `values` with native types. A newer result of a feature SHALL replace the previous one.

#### Scenario: Alert event
- **WHEN** an event with the `frost` case arrives
- **THEN** the coordinator holds a `FeatureData` for `Feature.FROST` with an `AlertData` carrying severity, confidence, trigger value and threshold

#### Scenario: Score event
- **WHEN** an event with the `laundry` case arrives
- **THEN** the `FeatureData` carries a `ScoreData` with score, best start and best hours

#### Scenario: Newer result replaces older
- **WHEN** two events of the same feature and location arrive
- **THEN** only the later one is stored

### Requirement: Features are gated by the active enrichments of the server
Entities for a feature SHALL be created only when `feature_enabled(feature, active)` is true. `active` is `StatusResponse.active_enrichments` (`<Category>:<Name>` keys, matched case-insensitively); an empty or missing list SHALL enable all features.

#### Scenario: Feature not active
- **WHEN** `active_enrichments` is `["Weather:Uv"]` and a frost event arrives
- **THEN** no frost entity is created

#### Scenario: Empty list
- **WHEN** `active_enrichments` is empty
- **THEN** every feature that delivers data gets entities

#### Scenario: Feature becomes active
- **WHEN** the status poll reports a newly active feature that already has data
- **THEN** its entities are created without a reload

### Requirement: Features map to entities
Alert features SHALL map to one alert binary sensor each plus the shared weather alert event entity. Laundry, Bbq, Outdoor and SurfConditions SHALL map to score sensors; CommuteSafety, ExerciseAdvisory, NightVentilation, ConfidenceTrend, PollenTrend, SolarYield, FloodTimeline, ApproachingFront and SeasonalOutlook to sensors; VentilationWindow and Gardening to binary sensors. SatelliteRadiation SHALL have no entity.

#### Scenario: Surf conditions
- **WHEN** a `surf_conditions` event arrives and `Marine:Surf` is active
- **THEN** the `surf_conditions` sensor exists with unique id `{entry_id}_{location}_surf_conditions`

#### Scenario: Satellite radiation
- **WHEN** a `satellite_radiation` event arrives
- **THEN** no entity is created

### Requirement: Entity identity of surviving features is stable
Unique ids SHALL keep the format `{entry_id}_{location}_{key}`. The `climate_anomaly` sensor is renamed `seasonal_outlook`.

#### Scenario: Existing sensor
- **WHEN** the integration is set up after the upgrade
- **THEN** sensors that existed before keep their unique id

### Requirement: Config entries migrate to version 3
The v2 to v3 migration SHALL keep only `status_poll_interval` and drop all enrichment toggles.

#### Scenario: v2 entry with toggles
- **WHEN** a version 2 entry with disabled enrichment groups is loaded
- **THEN** the entry becomes version 3 with only `status_poll_interval` left
