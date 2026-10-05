## 1. Add new usage sensors

- [x] 1.1 Add `NjordMonthlyUsageSensor` to `custom_components/njord/sensor.py` — `CoordinatorEntity[NjordStatusCoordinator]`, state = `monthly_used / monthly_limit * 100`, attrs = `limit`, `used`. Unavailable if limit is 0 or status is None.
- [x] 1.2 Add `NjordDailyUsageSensor` similarly with daily fields
- [x] 1.3 Add tests for both sensors: normal values, zero limit → unavailable

## 2. Add version sensor

- [x] 2.1 Add `NjordVersionSensor` to `custom_components/njord/sensor.py` — `CoordinatorEntity[NjordStatusCoordinator]`, state = `status.version`, no unit, diagnostic category, Server device
- [x] 2.2 Add test for version sensor

## 3. Remove old sensors and clean up

- [x] 3.1 Remove `NjordApiBudgetSensor` class from `custom_components/njord/sensor.py`
- [x] 3.2 Remove version from `NjordUptimeSensor.extra_state_attributes` (return `None`)
- [x] 3.3 Update `async_setup_entry()` in sensor.py to create the three new sensors instead of `NjordApiBudgetSensor`
- [x] 3.4 Update/remove existing tests referencing `api_budget` or uptime version attribute

## 4. Validation

- [x] 4.1 Run full test suite: `make test` — all tests pass
