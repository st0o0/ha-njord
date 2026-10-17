## Why

njord removed the History enrichment (`HistoryConfig`, `HistoryUpdate`, `ModelMetrics`, and the `history` fields in `ForecastUpdate` / `EnrichmentUpdate`; the freed field numbers are now `reserved`) and added `budget_partial` / `models_partial` flags to `StatusResponse`. ha-njord still ships the old protos, a "Model Performance" sensor and per-model MAE/drift weather attributes that can never be populated again, and it would show a misleading 0 % budget when njord's `BudgetTracker` times out.

## What Changes

- Sync `protos/njord/v2/{admin,common,ops,weather}.proto` from njord and regenerate the committed stubs.
- **BREAKING**: Remove the History enrichment: `HistoryData`, `ModelMetricsData`, `EnrichmentData.history`, the history branch in `grpc_client.py`, the merge field/default in `coordinator.py`, `NjordModelPerformanceSensor` (`sensor.*_model_performance`), the `model_mae_7d` / `model_mae_30d` / `model_weight` / `model_drift` weather attributes, `history` in the diagnostics enrichment list, and the `model_performance` translation strings.
- Remove `history` from the options-flow enrichment groups; ignore a stale `history` entry in a saved `disabled_enrichment_groups`.
- Remove already-registered `*_model_performance` sensor entities from the entity registry on setup so users are not left with permanently unavailable entities.
- Expose `budget_partial` and `models_partial` on `ServerStatusData`; make the monthly/daily usage sensors unavailable while `budget_partial` is true and report both flags in diagnostics.
- Drop `Njord__Enrichment__History__Enabled` from `docker-compose.yml`, the e2e compose file, `e2e/E2E-TEST-PLAN.md` and `openspec/config.yaml`; update tests accordingly.

## Non-goals

- Replacing model-quality metrics with anything else (njord has no equivalent).
- A new UI/sensor for the partial flags beyond availability of the usage sensors and diagnostics.
- Changing how `GetTargets` or the model/target sensors are created.
- Config-entry version migration (`disabled_enrichment_groups` is tolerated, not rewritten).

## Capabilities

### New Capabilities

- `history-entity-cleanup`: Stale History-derived entities (`model_performance` sensors) are removed from the entity registry on setup.

### Modified Capabilities

- `enrichment-merge`: `history` is no longer a mergeable enrichment field.
- `entity-naming-convention`: the "Class names match display names" requirement (only about the Model Performance sensor) is removed.
- `grpc-client`: `EnrichmentData` no longer carries history; `StatusResponse` partial flags are mapped.
- `options-flow`: `history` is no longer an enrichment group.
- `budget-usage-sensors`: usage sensors are unavailable when `budget_partial` is set.
- `diagnostics-download`: server section reports the partial flags.

## Impact

- `protos/njord/v2/*.proto`, `custom_components/njord/proto/` (regenerated).
- `custom_components/njord/`: `grpc_client.py`, `models.py`, `coordinator.py`, `config_flow.py`, `sensor.py`, `weather.py`, `diagnostics.py`, `__init__.py`, `strings.json`, `translations/de.json`.
- `tests/`: `conftest.py`, `test_enrichment_*`, `test_grpc_client.py`, `test_options_flow.py`, `test_sensor.py`, plus new tests.
- `docker-compose.yml`, `e2e/`, `openspec/config.yaml`.

## gRPC Endpoints

No new RPCs. Existing and still required: `WeatherService.GetForecast/StreamForecasts/StreamEnrichments/GetEnrichments`, `AdminService.GetConfig/StreamConfig`, `OpsService.GetStatus/GetTargets/TriggerPoll`, `SensorService.Push`. Changed messages: `StatusResponse` (+2 fields), `EnrichmentUpdate` / `ForecastUpdate` / `DetailedEnrichmentConfig` (history removed).
