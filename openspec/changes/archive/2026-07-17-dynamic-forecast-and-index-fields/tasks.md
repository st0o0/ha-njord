## 1. Add Missing Index Fields

- [x] 1.1 Add `hdd: float | None`, `cdd: float | None`, `frost_hours: int | None`, `frost_confidence: float | None` to `IndexData` in `custom_components/njord/models.py`.
- [x] 1.2 Map the four new fields in `_to_index_data()` in `custom_components/njord/grpc_client.py` using `HasField()` pattern.
- [x] 1.3 Update `tests/test_enrichment_models.py` to include the new fields in test fixtures. Update `tests/conftest.py` `_default_enrichment()` to include sample values.

## 2. Dynamic Supported Features

- [x] 2.1 In `custom_components/njord/weather.py`, remove `_attr_supported_features` class attribute from `NjordWeatherEntity`. Add a `supported_features` property that checks `self._forecast_data` for hourly/daily entries.
- [x] 2.2 Add tests in `tests/test_weather.py`: model with both hourly+daily has both features, model with only hourly has only `FORECAST_HOURLY`, model with no data has no forecast features.

## 3. New Index Sensors

- [x] 3.1 Add `NjordHddSensor`, `NjordCddSensor`, `NjordFrostHoursSensor`, `NjordFrostConfidenceSensor` classes in `custom_components/njord/sensor.py`. Follow existing `_NjordEnrichmentSensor` pattern. Frost confidence multiplies value by 100 for percentage display.
- [x] 3.2 Register the new sensors in `async_setup_entry` and the sensor factory in `custom_components/njord/sensor.py`.
- [x] 3.3 Add translation keys to `custom_components/njord/strings.json` and `custom_components/njord/translations/de.json`: `hdd` → "Heating Degree Days"/"Heizgradtage", `cdd` → "Cooling Degree Days"/"Kühlgradtage", `frost_hours` → "Frost Hours"/"Froststunden", `frost_confidence` → "Frost Confidence"/"Frostwahrscheinlichkeit".
- [x] 3.4 Add tests in `tests/test_sensor.py` for the four new sensors: correct values, correct units, correct icons, unavailable when no index data.

## 4. Validation

- [x] 4.1 Run full test suite: `make test` — all existing + new tests pass.
