## 1. Typed values without wire changes

- [x] 1.1 `custom_components/njord/const.py`: `EnrichmentGroup`, `StreamName`, `SensorKind` StrEnums and `CONF_*` constants; `helpers.py`: `group_enabled`; tests in new `tests/test_typed_values.py` (values equal today's strings, tolerant parsing of stored groups, helper truth table)
- [x] 1.2 Replace the enablement gates and group literals in `sensor.py`, `event.py`, `binary_sensor.py`, `weather.py`, `config_flow.py`, `coordinator.py`, `diagnostics.py`; tests in `tests/test_enrichment_filtering.py` and `tests/test_typed_values.py` asserting unchanged unique ids/entity ids
- [x] 1.3 `AlertType` with one metadata table and `AlertSeverity` with `.rank` in `models.py`/`const.py`; replace the parallel ALERT_* dicts in `sensor.py`, `_ALERT_TYPE_MAP` / `_ALERT_SEVERITY_MAP` in `grpc_client.py`, the rank dict in `event.py`; update `tests/test_sensor.py`, `tests/test_event.py` (all 14 types keep unit, device class, precision, icon)
- [x] 1.4 `StreamName` in `coordinator.py`, `binary_sensor.py`, `diagnostics.py`; tests in `tests/test_stream_health.py` (unique ids, issue ids unchanged)
- [x] 1.5 `SensorKind` keyed `SENSOR_KIND_MAP`; skip stale stored kinds in `__init__.py` and `config_flow.py`; tests in `tests/test_sensor_push.py`, `tests/test_options_flow.py`
- [x] 1.6 `condition_mapper.py` with `ATTR_CONDITION_*`; `tests/test_condition_mapper.py` unchanged results
- [x] 1.7 Optional: `AlertEvent` StrEnum in `event.py` with unchanged values

## 2. Proto enums (after njord `typed-wire-enums` is implemented)

- [x] 2.1 Copy `common.proto`, `ops.proto`, `admin.proto` from njord (LF endings) and regenerate stubs with the Docker command from `CLAUDE.md`
- [x] 2.2 `models.py`: typed fields for phase, direction, stability, dewpoint_comfort, VPD category; `grpc_client.py`: lookup tables from proto numbers, unknown/UNSPECIFIED to the unspecified value; update `tests/conftest.py`, `tests/test_grpc_client.py`, `tests/test_enrichment_models.py`, `tests/test_get_targets.py`
- [x] 2.3 `sensor.py`: sensors with closed value sets (trend, dew point comfort, VPD category) use the enum for state and optionally `SensorDeviceClass.ENUM` options; unknown value yields unavailable; tests in `tests/test_sensor.py`

## 3. Validation

- [ ] 3.1 `python -m pytest tests/ -v --tb=short` (Docker command from `CLAUDE.md`) green
- [ ] 3.2 `uv run ruff format --check . && uv run ruff check .` clean
- [ ] 3.3 `openspec validate --all --no-interactive`; `grep -rn '"disabled_enrichment_groups"\|"alerts"' custom_components` shows only the constant definitions
- [ ] 3.4 Final commit carries the footer `Release-As: 0.5.0` (user-approved exception to the single-line rule; release together with njord)
