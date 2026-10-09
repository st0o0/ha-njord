## Purpose

Defines shared utility functions for calculating horizon offsets from timestamps and looking up values from horizon-indexed data structures.

## Requirements

### Requirement: Shared horizon offset calculation
The integration SHALL provide a shared utility function that calculates the current horizon offset from a given timestamp. The offset SHALL be `max(0, floor((now_utc - timestamp).total_seconds() / 3600))`.

#### Scenario: Offset after 2.5 hours
- **WHEN** the timestamp is 2.5 hours ago
- **THEN** the offset is 2

#### Scenario: Offset at exactly 0
- **WHEN** the timestamp is less than 1 hour ago
- **THEN** the offset is 0

#### Scenario: Offset never goes negative
- **WHEN** the timestamp is in the future (clock skew)
- **THEN** the offset is 0

### Requirement: Nearest-future horizon lookup
The utility SHALL provide a `find_nearest_horizon` function that finds the entry whose hour value is the smallest ≥ the computed offset. If no horizon is ≥ the offset, it SHALL return the last (largest) entry. Horizon lists may not start at h0 (e.g. derived horizons start at h3).

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

### Requirement: Consensus entity uses shared helper
The `NjordConsensusWeatherEntity` SHALL be refactored to use the shared horizon-offset helper instead of its inline `_current_horizon_offset()` method.

#### Scenario: Consensus behavior unchanged
- **WHEN** the consensus entity calculates its current state after refactoring
- **THEN** results are identical to the previous inline implementation
