## 1. Resilient First Refresh

- [x] 1.1 In `custom_components/njord/coordinator.py` `_async_update_data()`, when `get_forecast()` fails for a model, insert `ForecastData(location=location.name, model=model, updated_at=0)` into the result instead of just logging and skipping.
- [x] 1.2 Add test in `tests/test_coordinator.py`: when `get_forecast` fails for one model, that model's key still exists in `coordinator.data.forecasts` with `updated_at=0`.

## 2. Weather Entity Availability and Features

- [x] 2.1 In `custom_components/njord/weather.py` `NjordWeatherEntity`, add an `available` property that returns `True` when `(self._location, self._model)` exists in `coordinator.data.forecasts`, `False` otherwise.
- [x] 2.2 Replace the `supported_features` property with init-time `_attr_supported_features` in `NjordWeatherEntity.__init__`: check `coordinator.data.forecasts.get((location, model))` and set features based on whether hourly/daily are non-empty.
- [x] 2.3 Update tests in `tests/test_weather.py`: entity with stub data is available but has unknown state, entity with no key is unavailable, features are set at init (hourly+daily, hourly-only, stub).

## 3. Default-Disabled Entities

- [x] 3.1 In `custom_components/njord/sensor.py`, add `_attr_entity_registry_enabled_default = False` to the `_NjordEnrichmentSensor` base class.
- [x] 3.2 In `custom_components/njord/binary_sensor.py`, add `_attr_entity_registry_enabled_default = False` to `NjordInversionEntity`. Verify `NjordAlertEntity` does NOT have this attribute (stays default `True`).
- [x] 3.3 Add tests: verify alert entities are enabled by default, verify index/energy/inversion entities are disabled by default.

## 4. Validation

- [x] 4.1 Run full test suite: `make test` — all existing + new tests pass.
- [x] 4.2 Run `ruff format --check .` — all files formatted.
