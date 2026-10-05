## MODIFIED Requirements

### Requirement: Typed data models
All public API methods SHALL return typed Python dataclasses, never raw protobuf message objects.

#### Scenario: IndexData includes all proto fields
- **WHEN** `IndexData` is returned as part of enrichment data
- **THEN** it contains `hdd`, `cdd`, `frost_hours`, and `frost_confidence` fields in addition to existing activity index fields and VPD fields
