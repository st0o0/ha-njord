## ADDED Requirements

### Requirement: Seasonal domain data is converted
The client SHALL convert a `DomainDataUpdate` whose payload is `seasonal` into a `SeasonalDomainData` holding one `SeasonalSampleData` per point (`valid_at`, `temperature_anomaly`, `precipitation_anomaly`, `precipitation_mean`). Optional fields that are not set SHALL become `None`.

#### Scenario: Full seasonal sample
- **WHEN** a seasonal update arrives with all sample fields set
- **THEN** the result is a `SeasonalDomainData` for that location whose sample carries the same values

#### Scenario: Unset optional fields
- **WHEN** a seasonal sample arrives without `precipitation_anomaly` and `precipitation_mean`
- **THEN** those fields are `None` and the temperature anomaly is kept

#### Scenario: Empty seasonal payload
- **WHEN** a seasonal update arrives with no points
- **THEN** the result is a `SeasonalDomainData` with an empty point list

### Requirement: Coordinator keeps the latest seasonal data
The data coordinator SHALL request the seasonal domain on first refresh and on the domain stream and SHALL store the latest `SeasonalDomainData` per location. No entity is created for it.

#### Scenario: Seasonal update on the stream
- **WHEN** a seasonal update for a location arrives on the domain stream
- **THEN** the coordinator stores it under that location and the seasonal domain

#### Scenario: Seasonal domain requested
- **WHEN** the coordinator starts the domain stream
- **THEN** the seasonal domain is among the requested domains
