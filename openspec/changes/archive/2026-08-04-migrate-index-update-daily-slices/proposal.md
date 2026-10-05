## Why

njord v2 redesigns `IndexUpdate` from a flat single-horizon message into daily slices (`repeated DayScoreSet`), moves frost and VPD into dedicated sub-messages (`FrostInfo`, `VpdInfo`), adds per-score confidence envelopes (`ScoreEnvelope`), and renames `ventilation` to `night_ventilation`. ha-njord still parses the old flat format — once njord deploys this branch, enrichment index parsing will break silently (wrong field numbers) or crash.

## What Changes

- **BREAKING**: `IndexData` model restructured — `frost_hours`/`frost_confidence`/`vpd_kpa`/`vpd_category` replaced by `FrostData`/`VpdData` sub-models; `ventilation` renamed to `night_ventilation`
- **BREAKING**: `_to_index_data()` parser rewritten to consume `DayScoreSet` array, `FrostInfo`, `VpdInfo`
- Copy updated `common.proto` from njord (new `DayScoreSet`, `ScoreEnvelope`, `FrostInfo`, `VpdInfo` messages; restructured `IndexUpdate`); regenerate stubs
- Activity index sensors adopt DWD-Pollenflug pattern: `state` = today's score (`days[0]`), `extra_state_attributes.forecast` = list of upcoming days' scores
- Frost/VPD sensors read from new sub-messages instead of flat optional fields
- `ventilation` sensor renamed to `night_ventilation` across entities, translations, and tests
- All enrichment-related tests updated for new IndexData shape

## Non-goals

- No changes to forecast handling, alert system, trend/derived/history/consensus enrichments
- No changes to coordinator architecture (initial poll + stream stays as-is)
- No new entity types — existing sensor entities are adapted, not replaced
- `IndexConfig` changes in admin.proto are irrelevant (ha-njord never calls `SetEnrichment`)
- `ScoreEnvelope` confidence data is exposed as attributes but not surfaced as separate sensors

## gRPC Endpoints

- `WeatherService.GetEnrichments` — existing, no API change (IndexUpdate is embedded in response)
- `WeatherService.StreamEnrichments` — existing, no API change (IndexUpdate arrives via EnrichmentEvent)
- No new endpoints required

## Capabilities

### New Capabilities

- `daily-index-forecast`: Activity index sensors expose multi-day score forecasts via extra_state_attributes, following the DWD-Pollenflug pattern (state = today, forecast attr = upcoming days)

### Modified Capabilities

- `enrichment-sensors`: Frost/VPD sensors read from sub-messages instead of flat fields; ventilation renamed to night_ventilation; activity sensors gain forecast attributes
- `grpc-client`: `_to_index_data()` parser rewritten for DayScoreSet/FrostInfo/VpdInfo structure
- `enrichment-merge`: IndexData shape changes affect merge default detection

## Impact

- **Models**: `IndexData` in `models.py` — fields restructured
- **gRPC client**: `_to_index_data()` in `grpc_client.py` — full rewrite
- **Sensors**: `sensor.py` — activity sensors gain forecast attr, frost/VPD sensor sources change, ventilation rename
- **Proto stubs**: `common_pb2.py` / `common_pb2_grpc.py` — regenerated
- **Tests**: `conftest.py`, `test_grpc_client.py`, `test_enrichment_models.py`, `test_sensor.py`, `test_enrichment_merge.py`, `test_coordinator_streaming.py` — fixture data and assertions updated
- **Translations**: `strings.json`, `translations/de.json` — ventilation → night_ventilation rename
