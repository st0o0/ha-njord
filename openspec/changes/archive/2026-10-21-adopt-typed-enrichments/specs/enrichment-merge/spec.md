## REMOVED Requirements

### Requirement: Partial enrichment events are merged
**Reason**: Each feature result is complete; a newer result replaces the old one.
**Migration**: See `typed-enrichments`.

### Requirement: Merge uses immutable replacement
**Reason**: `EnrichmentData` no longer exists.
**Migration**: See `typed-enrichments`.

### Requirement: Merge handles missing base data
**Reason**: No merge is performed.
**Migration**: See `typed-enrichments`.
