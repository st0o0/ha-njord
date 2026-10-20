## 1. Protos

- [x] 1.1 Copy `common.proto` and `weather.proto`, remove `admin.proto` and `sensor.proto`, regenerate stubs
- [x] 1.2 Update the generate command in CLAUDE.md

## 2. Model and client

- [x] 2.1 Add `Feature`, `FEATURE_KEYS`, `feature_enabled`, DUST alert, SEASONAL and SATELLITE domains; remove `Enrichment` and lifestyle enums
- [x] 2.2 Add `FeatureData`, `ScoreData`; remove `EnrichmentData`, `LifestyleData`
- [x] 2.3 Map `EnrichmentEvent` and `GetEnrichments` in `grpc_client.py`; ignore satellite domain data

## 3. Coordinator and entities

- [x] 3.1 Store features per (location, feature), register feature factories, gate by `active_enrichments`
- [x] 3.2 Rework alert binary sensors, event entity, lifestyle sensors and binary sensors, diagnostics
- [x] 3.3 Remove enrichment toggles from config and options flow, migrate entries to version 3
- [x] 3.4 Update `strings.json` and `translations/de.json`

## 4. Tests

- [x] 4.1 Adapt the test suite (170 passed, ruff clean)
