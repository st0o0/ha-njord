## Why

njord replaced its enrichment payload with one typed `EnrichmentEvent` per feature (a `feature` oneof with 36 cases: alerts, scores, conditions, trends, forecasts) and dropped the admin and sensor protos and the solar domain. The old `EnrichmentData` merge (alerts, indices, trends, derived, consensus), the lifestyle types and the HA-side enrichment toggles no longer match anything on the wire. njord now reports which features run in `StatusResponse.active_enrichments`, so toggles on the HA side are redundant.

## What Changes

- **BREAKING (wire)**: sync `protos/njord/v2/{common,weather}.proto`, drop `admin.proto` and `sensor.proto`, regenerate stubs. Domains gain SEASONAL and SATELLITE, SOLAR is gone.
- `grpc_client.py` maps each `EnrichmentEvent` to a `FeatureData` (`alert` for alert features, `score` for score features, native-typed `values` for the rest). `GetEnrichments` returns the per-location snapshot.
- The coordinator stores `features[(location, Feature)]` instead of merged `EnrichmentData`; entities are created per feature when it first arrives and is active.
- Entities are gated by `StatusResponse.active_enrichments` (`<Category>:<Name>`, empty = all enabled) through `feature_enabled`.
- 20th alert type DUST; new sensors and binary sensors for the new features; `climate_anomaly` becomes `seasonal_outlook`.
- **BREAKING (config)**: config entry version 3; enrichment toggles removed from config and options flow; the v2 to v3 migration keeps only `status_poll_interval`.

## Non-goals

- No entity for `satellite_radiation`, no consumption of seasonal or satellite domain data.
- Unique ids of surviving features stay unchanged.

## Capabilities

### New Capabilities

- `typed-enrichments`: typed per-feature results, feature gating by the server, entity mapping.

### Modified Capabilities

- `enrichment-merge`, `enrichment-alerts`, `enrichment-sensors`: removed, superseded by `typed-enrichments`.
- `options-flow`: enrichment group toggles removed.
