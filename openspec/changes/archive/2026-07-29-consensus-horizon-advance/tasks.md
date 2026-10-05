## 1. Track consensus timestamp in EnrichmentData

- [x] 1.1 Add `consensus_updated_at: datetime | None = None` field to `EnrichmentData` in `custom_components/njord/models.py`
- [x] 1.2 Update `_to_enrichment_event()` in `custom_components/njord/grpc_client.py` to set `consensus_updated_at=_ts_to_dt(pb.updated_at)` when payload is `consensus`
- [x] 1.3 Update `_to_enrichment_data()` in `custom_components/njord/grpc_client.py` to set `consensus_updated_at=datetime.now(UTC)` when consensus is present
- [x] 1.4 Update `merge_enrichment()` in `custom_components/njord/coordinator.py`: add `consensus_updated_at` to `_ENRICHMENT_MERGE_FIELDS` and `_ENRICHMENT_DEFAULTS` so it merges correctly
- [x] 1.5 Add tests in `tests/test_enrichment_merge.py`: verify timestamp preserved on non-consensus merge, updated on consensus merge

## 2. Adjust consensus entity horizon selection

- [x] 2.1 Add `_current_horizon_offset()` method to `NjordConsensusWeatherEntity` in `custom_components/njord/weather.py` — calculates `int((now - consensus_updated_at).total_seconds() // 3600)`, clamped to 0, falls back to 0 if `consensus_updated_at` is None
- [x] 2.2 Update `_get_horizon_value()` and `_get_horizon_data()` to use `h{offset}` as default instead of `h0`
- [x] 2.3 Update `extra_state_attributes` to use offset-adjusted horizon for agreement/spread/available_models
- [x] 2.4 Update `_reliable_hours()` to count from `h{offset}` instead of `h0`
- [x] 2.5 Add tests in `tests/test_weather.py`: freeze time at 3h after consensus push, verify entity reads h3 values for state. Test elapsed exceeds horizons → unknown. Test no timestamp → falls back to h0

## 3. Adjust consensus forecast horizons

- [x] 3.1 Update `_async_forecast_hourly()` in consensus entity to start from `h{offset+1}` instead of `h1`, and compute forecast timestamps relative to actual current time
- [x] 3.2 Update `_async_forecast_daily()` to apply same offset when grouping horizons into calendar days
- [x] 3.3 Add tests: freeze time at 3h elapsed, verify hourly forecast starts from h4 values, daily forecast excludes consumed horizons

## 4. Validation

- [x] 4.1 Run full test suite: `make test` — all existing + new tests pass
