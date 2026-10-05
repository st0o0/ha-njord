## MODIFIED Requirements

### Requirement: Partial enrichment events are merged
When a streaming `EnrichmentEvent` contains only a subset of enrichment fields, the merge SHALL update only the delivered fields and preserve all others from the existing `EnrichmentData`. The merge SHALL also track `derived_updated_at` from the event's `updated_at` timestamp when a derived payload is present, analogous to how `consensus_updated_at` is tracked.

#### Scenario: Alert event preserves indices
- **WHEN** an enrichment event with only `alerts` arrives for a location that already has `indices` data
- **THEN** the resulting `EnrichmentData` has the new `alerts` and the previous `indices` unchanged

#### Scenario: Index event preserves alerts
- **WHEN** an enrichment event with only `indices` arrives for a location that already has `alerts`
- **THEN** the resulting `EnrichmentData` has the new `indices` and the previous `alerts` unchanged

#### Scenario: All enrichment types can be merged independently
- **WHEN** enrichment events arrive for alerts, indices, trends, energy, derived, history, or consensus individually
- **THEN** each is merged independently without affecting the other fields

#### Scenario: Derived event sets derived_updated_at
- **WHEN** an enrichment event with a derived payload arrives with `updated_at = 2025-01-15T12:00:00Z`
- **THEN** the resulting `EnrichmentData` has `derived_updated_at = 2025-01-15T12:00:00Z`

#### Scenario: Non-derived event preserves derived_updated_at
- **WHEN** an enrichment event with only alerts arrives for a location that has `derived_updated_at` set
- **THEN** the `derived_updated_at` is preserved unchanged
