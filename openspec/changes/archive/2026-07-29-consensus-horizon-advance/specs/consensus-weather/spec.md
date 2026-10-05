## MODIFIED Requirements

### Requirement: Current state uses h0 horizon
The consensus entity's current state (temperature, humidity, wind, condition, etc.) SHALL use the time-adjusted horizon `h{elapsed}` instead of hardcoded `h0`, where `elapsed` is the number of full hours since `consensus_updated_at`. Falls back to `h0` if `consensus_updated_at` is `None`.

#### Scenario: Current temperature from h0
- **WHEN** consensus data has an h0 horizon with temperature_2m median = 22.5
- **AND** consensus was just computed (0 hours elapsed)
- **THEN** the entity's temperature is 22.5

#### Scenario: Current temperature after 3 hours
- **WHEN** consensus data has h3 with temperature_2m median = 25.0
- **AND** 3 hours have elapsed since consensus computation
- **THEN** the entity's temperature is 25.0

#### Scenario: Fallback when adjusted horizon is missing
- **WHEN** elapsed hours exceeds the highest available horizon
- **THEN** the entity shows "Unknown" state

### Requirement: Hourly forecast from consecutive horizons
The consensus entity SHALL support `FORECAST_HOURLY` by building forecast entries from `h{elapsed+1}..hN` consensus horizons, each with a real timestamp.

#### Scenario: Hourly forecast entries after elapsed time
- **WHEN** `async_forecast_hourly` is called and 3 hours have elapsed since consensus computation
- **THEN** forecast entries start from h4 (not h1), each with timestamp = now + (N - elapsed) hours

#### Scenario: h0 through h{elapsed} excluded from hourly forecast
- **WHEN** `async_forecast_hourly` is called and 3 hours have elapsed
- **THEN** horizons h0, h1, h2, h3 are not included

### Requirement: Reliability extra state attributes
The consensus entity SHALL expose reliability information in extra_state_attributes using the time-adjusted horizon.

#### Scenario: Reliable hours attribute after elapsed time
- **WHEN** 2 hours have elapsed and temperature agreement drops below 0.5 at h10
- **THEN** `reliable_hours` is 8 (counting from h2 through h9)

#### Scenario: Agreement and spread from adjusted horizon
- **WHEN** 2 hours have elapsed and h2 temperature has agreement=0.75, spread=2.8, available_models=7
- **THEN** extra_state_attributes contains `agreement=0.75`, `spread=2.8`, `available_models=7`
