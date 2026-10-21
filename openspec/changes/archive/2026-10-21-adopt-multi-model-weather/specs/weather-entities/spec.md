## ADDED Requirements

### Requirement: Secondary models get their own weather entity
The weather platform SHALL create one weather entity per location for every secondary model, that is every entry of the location's `models` after the first whose catalog entry is enabled (a model missing from the catalog counts as enabled). The entity SHALL have unique id `{entry_id}_{location_slug}_{model_id}_weather`, the model's catalog display name (or its id when missing from the catalog) as entity name on the location device, and read `model_domains[(location, model_id)]`. The primary entity SHALL keep unique id `{entry_id}_{location_slug}_weather`.

#### Scenario: Two models configured
- **WHEN** the catalog lists location "berlin" with models `["ecmwf_ifs025_ensemble_mean", "ukmo_global_ensemble_mean_20km"]` and both are enabled
- **THEN** the location has two weather entities with unique ids `{entry_id}_berlin_weather` and `{entry_id}_berlin_ukmo_global_ensemble_mean_20km_weather`

#### Scenario: Disabled model gets no entity
- **WHEN** a location lists a secondary model whose catalog entry has `enabled = false`
- **THEN** no weather entity is created for that model

#### Scenario: Single model
- **WHEN** a location lists only one model
- **THEN** only the primary weather entity exists

### Requirement: Weather updates are routed by model
The coordinator SHALL store a weather `DomainDataUpdate` whose `model` is empty or equal to the location's primary model in `domains[(location, WEATHER)]`, and any other weather update in `model_domains[(location, model)]`. The first update for an unknown `(location, model)` key SHALL create the model's weather entity through the registered model factory.

#### Scenario: Primary update
- **WHEN** a weather update for "berlin" arrives with `model` empty
- **THEN** `domains[("berlin", WEATHER)]` is replaced and `model_domains` is unchanged

#### Scenario: Secondary update
- **WHEN** a weather update for "berlin" arrives with `model = "ukmo_global_ensemble_mean_20km"`
- **THEN** `model_domains[("berlin", "ukmo_global_ensemble_mean_20km")]` is replaced and the primary entry is unchanged

#### Scenario: New model on the stream
- **WHEN** the first update for a secondary model arrives after setup
- **THEN** the model factory is called with the location and the model id and its entity is added

### Requirement: Secondary models are fetched on the first refresh
During the first refresh the coordinator SHALL call `GetDomainData` with the `model` field set for every secondary model of every location and store the result in `model_domains`. A failed call SHALL leave the key absent.

#### Scenario: Secondary fetch succeeds
- **WHEN** the first refresh runs for a location with one secondary model
- **THEN** `get_domain_data(location, WEATHER, model=<id>)` is called once and its result is in `model_domains`

#### Scenario: Secondary fetch fails
- **WHEN** the secondary fetch raises
- **THEN** the refresh still succeeds and `model_domains` has no entry for that model

### Requirement: Weather entities expose their model
Every weather entity SHALL expose the attributes `model` (the id), `model_name`, `provider`, `region`, `resolution_km` and `forecast_hours` taken from the catalog entry of its model; attributes of a model missing from the catalog are omitted except `model`.

#### Scenario: Primary entity attributes
- **WHEN** the primary model is `ecmwf_ifs025_ensemble_mean` with display name "ECMWF IFS 0.25° Ensemble Mean" and 360 forecast hours
- **THEN** the primary entity has `model = "ecmwf_ifs025_ensemble_mean"`, `model_name` set to the display name and `forecast_hours = 360`
