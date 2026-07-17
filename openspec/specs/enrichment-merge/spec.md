## Purpose

Defines how partial enrichment events from the streaming pipeline are merged into the coordinator's enrichment state, preserving fields not included in the update.

## Requirements

### Requirement: Partial enrichment events are merged
When a streaming `EnrichmentEvent` contains only a subset of enrichment fields, the merge SHALL update only the delivered fields and preserve all others from the existing `EnrichmentData`.

#### Scenario: Alert event preserves indices
- **WHEN** an enrichment event with only `alerts` arrives for a location that already has `indices` data
- **THEN** the resulting `EnrichmentData` has the new `alerts` and the previous `indices` unchanged

#### Scenario: Index event preserves alerts
- **WHEN** an enrichment event with only `indices` arrives for a location that already has `alerts`
- **THEN** the resulting `EnrichmentData` has the new `indices` and the previous `alerts` unchanged

#### Scenario: All enrichment types can be merged independently
- **WHEN** enrichment events arrive for alerts, indices, trends, energy, derived, history, or consensus individually
- **THEN** each is merged independently without affecting the other fields

### Requirement: Merge uses immutable replacement
The merge SHALL produce a new `EnrichmentData` via `dataclasses.replace()`, not by mutating the existing object.

#### Scenario: Original object is unchanged
- **WHEN** a merge produces an updated `EnrichmentData`
- **THEN** the original `EnrichmentData` object is not modified (frozen dataclass guarantee)

### Requirement: Merge handles missing base data
When an enrichment event arrives for a location with no prior enrichment data, the merge SHALL create a new `EnrichmentData` with the event's payload as the only populated field.

#### Scenario: First enrichment for a location
- **WHEN** an alert event arrives for location "zurich" and no enrichment data exists for "zurich"
- **THEN** a new `EnrichmentData(location="zurich", alerts=[...])` is created with all other fields at defaults
