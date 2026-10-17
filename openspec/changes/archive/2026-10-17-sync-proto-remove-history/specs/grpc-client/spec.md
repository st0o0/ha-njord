## MODIFIED Requirements

### Requirement: Get enrichments
The client SHALL provide an async method to retrieve enrichment data for a given location, returning typed dataclasses.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_enrichments(location)` is called
- **THEN** an `EnrichmentData` object is returned containing alerts, indices, trends, derived, and consensus data for that location
- **AND** `EnrichmentData` has no `history` field

## ADDED Requirements

### Requirement: Status maps partial flags
`get_status` SHALL map `StatusResponse.budget_partial` and `StatusResponse.models_partial` to `ServerStatusData.budget_partial` and `ServerStatusData.models_partial`.

#### Scenario: Complete status
- **WHEN** the response has `budget_partial = false` and `models_partial = false`
- **THEN** both `ServerStatusData` flags are `False`

#### Scenario: Partial status
- **WHEN** the response has `budget_partial = true` and `models_partial = true`
- **THEN** both `ServerStatusData` flags are `True`
