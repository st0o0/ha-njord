## MODIFIED Requirements

### Requirement: Nearest-future horizon lookup

The horizon lookup function SHALL find the entry whose hour value is the smallest ≥ the computed offset. If no horizon is ≥ the offset, it SHALL return the last (largest) entry. The function SHALL be renamed from `get_horizon_entry` to `find_nearest_horizon`.

#### Scenario: Offset before first available horizon
- **WHEN** the offset is 0 and horizons are `[h3, h6, h12, h24]`
- **THEN** the lookup returns the `h3` entry

#### Scenario: Exact match still works
- **WHEN** the offset is 6 and horizons are `[h3, h6, h12, h24]`
- **THEN** the lookup returns the `h6` entry

#### Scenario: Offset between horizons
- **WHEN** the offset is 4 and horizons are `[h3, h6, h12, h24]`
- **THEN** the lookup returns the `h6` entry (next available ≥ offset)

#### Scenario: Offset beyond all horizons clamps to last
- **WHEN** the offset is 100 and horizons are `[h3, h6, h12, h24]`
- **THEN** the lookup returns the `h24` entry

#### Scenario: Consensus horizons starting at h0 unchanged
- **WHEN** the offset is 0 and horizons are `[h0, h1, h2, h3]`
- **THEN** the lookup returns the `h0` entry

#### Scenario: Empty list returns None
- **WHEN** horizons is an empty list
- **THEN** the lookup returns None
