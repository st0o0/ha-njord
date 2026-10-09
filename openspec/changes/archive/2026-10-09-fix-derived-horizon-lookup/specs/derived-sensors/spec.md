## MODIFIED Requirements

### Requirement: Derived sensors show values immediately after data arrival

Derived sensors (Beaufort, Wind Chill, Dewpoint Comfort) SHALL show a value immediately when enrichment data arrives, even when the smallest available horizon is h3 or greater. The sensor SHALL use `find_nearest_horizon` to select the nearest future horizon entry.

#### Scenario: Beaufort shows value at offset 0 with h3+ horizons
- **WHEN** derived data contains `by_horizon` with `[h3, h6, h12, h24]` where h3 has `beaufort = 4`
- **AND** the data was just received (offset = 0)
- **THEN** the Beaufort sensor shows `4` (picked h3 as nearest available)

#### Scenario: Wind Chill advances through horizons
- **WHEN** derived data has h3 with `wind_chill = -1.0` and h6 with `wind_chill = -2.5`
- **AND** 4 hours have passed since data arrival (offset = 4)
- **THEN** the Wind Chill sensor shows `-2.5` (picked h6 as nearest ≥ 4)

#### Scenario: Dewpoint Comfort clamps to last horizon
- **WHEN** derived data has horizons up to h24 with `dewpoint_comfort = "humid"`
- **AND** 30 hours have passed since data arrival (offset = 30)
- **THEN** the Dewpoint Comfort sensor shows `"humid"` (clamped to h24)
