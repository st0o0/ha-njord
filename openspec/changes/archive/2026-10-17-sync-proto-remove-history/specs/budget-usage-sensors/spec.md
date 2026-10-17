## ADDED Requirements

### Requirement: Usage sensors are unavailable on partial budget status
While `ServerStatusData.budget_partial` is true, both usage sensors SHALL be unavailable, because njord reports zero usage in that case and it is not a real measurement.

#### Scenario: Budget tracker timed out
- **WHEN** the status response has `budget_partial = true` with `monthly_used=0`
- **THEN** `sensor.server_monthly_usage` and `sensor.server_daily_usage` are unavailable

#### Scenario: Budget status recovers
- **WHEN** the next status response has `budget_partial = false`
- **THEN** both sensors show their computed percentages again
