## 1. Proto sync

- [x] 1.1 Copy `admin.proto`, `common.proto`, `ops.proto`, `weather.proto` from `D:\GIT\njord\protos\njord\v2` to `protos/njord/v2/` (LF endings); regenerate stubs in `custom_components/njord/proto/` with the Docker command from `CLAUDE.md`
- [x] 1.2 Run `tests/` to list what breaks on removed `history` symbols (expected: `tests/conftest.py`, `tests/test_enrichment_*`, `tests/test_grpc_client.py`, `tests/test_sensor.py`, `tests/test_options_flow.py`)

## 2. Remove History enrichment

- [x] 2.1 `custom_components/njord/models.py`, `grpc_client.py`: delete `HistoryData`, `ModelMetricsData`, `EnrichmentData.history`, `_to_model_metrics`, `_to_history_data` and the history payload branches; update `tests/test_grpc_client.py`, `tests/test_enrichment_models.py`
- [x] 2.2 `custom_components/njord/coordinator.py`: drop `history` from `_ENRICHMENT_MERGE_FIELDS` / `_ENRICHMENT_DEFAULTS`; update `tests/test_enrichment_merge.py`
- [x] 2.3 `custom_components/njord/sensor.py`: delete `NjordModelPerformanceSensor` and both creation sites; `weather.py`: delete `_model_metrics` and the `model_*` attributes; update `tests/test_sensor.py`, weather tests, `tests/conftest.py`
- [x] 2.4 `custom_components/njord/config_flow.py`: remove `history` from `ENRICHMENT_GROUPS`, intersect stored disabled groups with valid groups; add a legacy-`history` test to `tests/test_options_flow.py`
- [x] 2.5 `diagnostics.py`: remove history from enrichment types; `strings.json` + `translations/de.json`: remove `model_performance`

## 3. Registry cleanup

- [x] 3.1 `custom_components/njord/__init__.py`: before forwarding platforms remove sensor registry entries of the entry whose `unique_id` ends with `_model_performance`; new `tests/test_history_cleanup.py` (removed, other sensors kept, clean registry no-op)

## 4. Partial status flags

- [x] 4.1 `models.py` / `grpc_client.py`: add `budget_partial`, `models_partial` to `ServerStatusData` and `_to_server_status`; tests in `tests/test_grpc_client.py`
- [x] 4.2 `sensor.py`: usage sensors `available` is false when `budget_partial`; tests in `tests/test_sensor.py`
- [x] 4.3 `diagnostics.py`: add both flags to the server section; test in the diagnostics tests

## 5. Docs and infra

- [x] 5.1 Remove `Njord__Enrichment__History__Enabled` from `docker-compose.yml` and `e2e/docker-compose.e2e.yml`; remove history rows from `e2e/E2E-TEST-PLAN.md` (6.6, 7.22, 13.1, entity table, enrichment list); drop "history" from `openspec/config.yaml` context

## 6. Validation

- [x] 6.1 `python -m pytest tests/ -v --tb=short` (Docker command from `CLAUDE.md`) green
- [x] 6.2 `uv run ruff format --check . && uv run ruff check .` clean
- [x] 6.3 `openspec validate --all --no-interactive`; `grep -ri history custom_components tests` shows no leftovers
