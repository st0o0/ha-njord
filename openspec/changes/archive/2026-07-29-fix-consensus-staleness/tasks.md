## 1. Add freshness attributes to consensus entity

- [x] 1.1 Add `current_horizon` and `consensus_age_hours` to `NjordConsensusWeatherEntity.extra_state_attributes` in `custom_components/njord/weather.py`. `current_horizon` = `f"h{self._current_horizon_offset()}"`. `consensus_age_hours` = offset value (only if `consensus_updated_at` is not None).
- [x] 1.2 Add tests for the new attributes in `tests/test_weather.py`: verify `current_horizon` changes with offset, `consensus_age_hours` tracks elapsed time, and `consensus_age_hours` is absent when `consensus_updated_at` is None.

## 2. Update spec

- [x] 2.1 Merge delta spec into `openspec/specs/consensus-weather/spec.md` — add `current_horizon` and `consensus_age_hours` rows to the Extra State Attributes table, and add the new scenarios to the reliability requirement.

## 3. Validation

- [x] 3.1 Run `make test` and verify all tests pass, including new consensus attribute tests.
