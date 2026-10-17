## MODIFIED Requirements

### Requirement: Diagnostics include server status
The server status section SHALL include version, uptime, budget usage, `budget_partial` and `models_partial` if the status coordinator has data. If unavailable, the section SHALL indicate `"unavailable"`. The enrichment types listed in diagnostics SHALL NOT include `history`.

#### Scenario: Server status available
- **WHEN** diagnostics are downloaded and status coordinator has data
- **THEN** the server section shows version, uptime_seconds, budget usage percent, `budget_partial` and `models_partial`

#### Scenario: Server status unavailable
- **WHEN** diagnostics are downloaded but the status coordinator has no data
- **THEN** the server section shows `"unavailable"`
