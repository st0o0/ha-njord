# Tasks

## 1. Proto + client foundation (Phase 1)

- [x] 1.1 Copy `protos/njord/v3/njord.proto` from njord repo (`D:\GIT\njord\protos\njord\v3\njord.proto`) to `protos/njord/v3/njord.proto`. Generate Python stubs with grpcio-tools into `custom_components/njord/proto/`. Add `__init__.py` if needed.

- [x] 1.2 Add v3 methods to `custom_components/njord/grpc_client.py`: `get_manifest()`, `subscribe()` (async iterator), `get_status_v3()`, `trigger_poll_v3()`. Keep v2 methods intact for now. Add v3 stub initialization in constructor.

- [x] 1.3 Add v3 models to `custom_components/njord/models.py`: `ManifestEntity` (entity_id, platform, device_class, unit, output_kind, name), `EntityState` (entity_id, value, updated_at, available). Parse from proto messages.

- [x] 1.4 Tests: `tests/test_grpc_client_v3.py` — test v3 client methods with mock stubs. `tests/test_models_v3.py` — test v3 model parsing.

**Validation:** `uv run pytest tests/test_grpc_client_v3.py tests/test_models_v3.py -v --tb=short` (Docker on Windows)

## 2. Manifest-driven entity factory (Phase 2)

- [x] 2.1 Create `custom_components/njord/entity_factory.py`: given a list of `ManifestEntity`, create HA entity descriptions grouped by platform. Generic entity class per OutputKind: `NjordAlertSensor`, `NjordScoreSensor`, `NjordConditionSensor`, `NjordTrendSensor`, `NjordForecastSensor`, `NjordObservationSensor`.

- [x] 2.2 Create `custom_components/njord/v3_entities.py`: the 6 generic entity classes (excluding weather). Each takes a `ManifestEntity` and implements `_handle_coordinator_update` to extract state from v3 EntityStateUpdate.

- [x] 2.3 Tests: `tests/test_entity_factory.py` — manifest to entity descriptions. `tests/test_v3_entities.py` — state extraction from mock EntityStateUpdate per OutputKind.

**Validation:** `uv run pytest tests/test_entity_factory.py tests/test_v3_entities.py -v --tb=short`

## 3. Coordinator v3 (Phase 3)

- [ ] 3.1 Add `NjordV3Coordinator` to `custom_components/njord/coordinator.py` (or new file `v3_coordinator.py`): calls `get_manifest()` on setup, `subscribe()` for streaming. Processes EntityStateUpdate (dispatches to entities by entity_id), EntityUnavailable/EntityAvailable (marks entities). Snapshot-on-connect populates initial state.

- [ ] 3.2 Wire v3 coordinator into `custom_components/njord/__init__.py`: replace NjordDataCoordinator with NjordV3Coordinator. Wire entity factory to create entities from manifest. Keep status coordinator (uses v3 GetStatus).

- [ ] 3.3 Update `custom_components/njord/weather.py`: feed from v3 WeatherValue instead of v2 DomainDataUpdate. Map WeatherValue fields to HA weather attributes.

- [ ] 3.4 Tests: `tests/test_v3_coordinator.py` — stream processing, snapshot, availability. Update `tests/test_weather.py` for v3 data path.

**Validation:** `uv run pytest tests/ -v --tb=short` (full suite)

## 4. Cleanup (Phase 4)

- [ ] 4.1 Remove v2 code: `protos/njord/v2/`, v2 stubs in `custom_components/njord/proto/`, v2 client methods in `grpc_client.py`, v2 models in `models.py`.

- [ ] 4.2 Remove per-feature metadata: `ALERT_META`, `Feature` enum, `FEATURE_KEYS`, `DOMAIN_SENSOR_REGISTRY` from `const.py`. Remove `LIFESTYLE_SENSORS` and per-feature descriptions from `lifestyle.py`. Remove per-feature entity classes from `sensor.py`, `binary_sensor.py`.

- [ ] 4.3 Update remaining files: `config_flow.py` (simplify options), `button.py` (use v3 TriggerPoll), `event.py` (v3 AlertValue events), diagnostics.

- [ ] 4.4 Update all tests to v3 only. Remove v2 test fixtures and mocks. Run full test suite + ruff.

**Validation:**
```bash
uv run pytest tests/ -v --tb=short
uv run ruff format --check .
uv run ruff check .
```
