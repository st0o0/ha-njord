## 1. Add Alert Sensor Class

- [x] 1.1 Add `ALERT_UNITS` mapping dict to `custom_components/njord/sensor.py` (alert_type → unit string)
- [x] 1.2 Add `NjordAlertSensor` class to `custom_components/njord/sensor.py` with `native_value=trigger_value`, unit lookup, icon, and `extra_state_attributes` (severity, confidence, threshold, conditional peak_value/hours_until/duration_hours)
- [x] 1.3 Wire `NjordAlertSensor` into `async_setup_entry` and `sensor_factory` in `custom_components/njord/sensor.py` — create one per location × alert type, enabled by default

## 2. Remove Alert Binary Sensors

- [x] 2.1 Remove `NjordAlertEntity` class, `ALERT_TYPES`, `ALERT_NAMES`, `ALERT_ICONS` constants, and alert setup logic from `custom_components/njord/binary_sensor.py` (keep `NjordInversionEntity` and its setup)
- [x] 2.2 Update `binary_sensor_factory` in `custom_components/njord/binary_sensor.py` to only create inversion entities

## 3. Update Tests

- [x] 3.1 Remove alert-related tests from `tests/test_binary_sensor.py` (keep inversion tests)
- [x] 3.2 Add alert sensor tests to `tests/test_sensor.py`: verify state=trigger_value, unit, attributes with full/partial/inactive values, and entity enabled by default

## 4. Update README

- [x] 4.1 Update `README.md` entity reference: move alerts from binary_sensor section to sensor section, update entity table counts

## 5. Validation

- [x] 5.1 Run full test suite: `make test` — all tests pass
