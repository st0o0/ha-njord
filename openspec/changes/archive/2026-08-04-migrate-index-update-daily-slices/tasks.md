## 1. Proto Update

- [x] 1.1 Copy updated `common.proto` from `D:\GIT\njord\protos\njord\v2\common.proto` to `protos/njord/v2/common.proto` (contains new `DayScoreSet`, `ScoreEnvelope`, `FrostInfo`, `VpdInfo`, restructured `IndexUpdate`)
- [x] 1.2 Run `make proto` to regenerate stubs in `custom_components/njord/proto/njord/v2/`
- [x] 1.3 Verify generated `common_pb2.py` contains `DayScoreSet`, `FrostInfo`, `VpdInfo` message classes

## 2. Models

- [x] 2.1 Add `DayScoreData`, `FrostData`, `VpdData` frozen dataclasses to `custom_components/njord/models.py`
- [x] 2.2 Restructure `IndexData` in `custom_components/njord/models.py`: replace `ventilation` with `night_ventilation`, replace `frost_hours`/`frost_confidence` with `frost: FrostData | None`, replace `vpd_kpa`/`vpd_category` with `vpd: VpdData | None`, add `forecast: list[DayScoreData]`, remove `irrigation`
- [x] 2.3 Update `tests/test_enrichment_models.py`: fix `IndexData` construction and assertions for new field names and sub-models
- [x] 2.4 Run `docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim sh -c "pip install --quiet grpcio protobuf pytest pytest-asyncio voluptuous && python -m pytest tests/test_enrichment_models.py -v"`

## 3. gRPC Client Parser

- [x] 3.1 Rewrite `_to_index_data()` in `custom_components/njord/grpc_client.py`: parse `pb.days[0]` into top-level fields, `pb.days[1:]` into `forecast` list, `pb.frost`/`pb.vpd` into sub-models
- [x] 3.2 Add `_to_day_score_data()`, `_to_frost_data()`, `_to_vpd_data()` helper functions in `custom_components/njord/grpc_client.py`
- [x] 3.3 Update `tests/test_grpc_client.py`: fix `IndexUpdate` construction in fixtures to use `DayScoreSet`/`FrostInfo`/`VpdInfo`, update assertions for new `IndexData` shape
- [x] 3.4 Run `docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim sh -c "pip install --quiet grpcio protobuf pytest pytest-asyncio voluptuous && python -m pytest tests/test_grpc_client.py -v"`

## 4. Sensors

- [x] 4.1 Rename `ventilation` to `night_ventilation` in `INDEX_TYPES` list in `custom_components/njord/sensor.py`, update label to "Night Ventilation Index"
- [x] 4.2 Keep `irrigation` in `INDEX_TYPES` (still present in njord v2 proto `DayScoreSet`)
- [x] 4.3 Add `forecast` extra state attribute to `NjordIndexSensor` in `custom_components/njord/sensor.py`: read `enrichment.indices.forecast` and build `[{"day_offset": d.day_offset, "score": getattr(d, self._index_key)} for d in forecast]`
- [x] 4.4 Update `NjordFrostHoursSensor` in `custom_components/njord/sensor.py`: read from `enrichment.indices.frost.hours_until` instead of `enrichment.indices.frost_hours`
- [x] 4.5 Update `NjordFrostConfidenceSensor` in `custom_components/njord/sensor.py`: read from `enrichment.indices.frost.confidence` instead of `enrichment.indices.frost_confidence`
- [x] 4.6 Update `NjordVpdSensor` in `custom_components/njord/sensor.py`: read from `enrichment.indices.vpd.kpa` and `enrichment.indices.vpd.category` instead of flat fields
- [x] 4.7 Update `tests/test_sensor.py`: fix `IndexData` fixtures, update ventilation/irrigation references, add test for forecast attribute on activity sensors
- [x] 4.8 Run sensor tests

## 5. Enrichment Merge

- [x] 5.1 No changes needed — `IndexData` construction in merge tests uses only kwargs that still exist in the new model
- [x] 5.2 Run merge tests

## 6. Translations

- [x] 6.1 Rename `ventilation_index` to `night_ventilation_index` in `custom_components/njord/strings.json`, update English label
- [x] 6.2 Rename `ventilation_index` to `night_ventilation_index` in `custom_components/njord/translations/de.json`, update German label to "Nachtlüftungs-Index"
- [x] 6.3 `irrigation_index` kept (proto still has it)

## 7. Remaining Test Fixtures

- [x] 7.1 Update `tests/conftest.py`: fix `IndexData` construction in shared fixtures (`ventilation` → `night_ventilation`, flat frost/vpd → sub-models, add forecast)
- [x] 7.2 No changes needed in `tests/test_coordinator_streaming.py` — uses `IndexData(laundry=80)` which still works
- [x] 7.3 No changes needed in `tests/test_event.py` — doesn't reference IndexData fields directly

## 8. Validation

- [x] 8.1 Run full test suite — 205 passed, 18 skipped
- [x] 8.2 Verify no remaining references to old field names — clean
