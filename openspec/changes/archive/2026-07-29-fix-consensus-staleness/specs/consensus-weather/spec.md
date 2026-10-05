## MODIFIED Requirements

### Requirement: Reliability extra state attributes
The consensus entity SHALL expose reliability and freshness information in extra_state_attributes using the time-adjusted horizon.

#### Scenario: Agreement and spread from adjusted horizon
- **WHEN** 2 hours have elapsed since consensus computation
- **THEN** `agreement` in extra_state_attributes comes from the `h2` temperature consensus, not `h0`

#### Scenario: Reliable hours counted from adjusted horizon
- **WHEN** 2 hours have elapsed and temperature agreement drops below 0.5 at h10
- **THEN** `reliable_hours` is 8 (counting from h2 through h9)

#### Scenario: Current horizon attribute reflects offset
- **WHEN** 5 hours have elapsed since consensus computation
- **THEN** extra_state_attributes contains `current_horizon = "h5"`

#### Scenario: Current horizon at zero offset
- **WHEN** consensus was just computed (0 hours elapsed)
- **THEN** extra_state_attributes contains `current_horizon = "h0"`

#### Scenario: Consensus age in hours
- **WHEN** consensus was computed 3 hours ago
- **THEN** extra_state_attributes contains `consensus_age_hours = 3`

#### Scenario: Consensus age when no timestamp available
- **WHEN** `consensus_updated_at` is None
- **THEN** extra_state_attributes SHALL NOT contain `consensus_age_hours`

#### Scenario: Attributes change every hour to prevent staleness
- **WHEN** the hourly refresh fires and the horizon offset advances from 4 to 5
- **THEN** `current_horizon` changes from `"h4"` to `"h5"` and `consensus_age_hours` increments
- **AND** HA updates `last_updated` on the entity because attributes changed
