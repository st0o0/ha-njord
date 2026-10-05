## 1. Create NjordStatusCoordinator

- [x] 1.1 Add `NjordStatusCoordinator` class to `custom_components/njord/coordinator.py` — `DataUpdateCoordinator[ServerStatusData]` with `update_interval=timedelta(seconds=30)`, `_async_update_data` calls `client.get_status()` and raises `UpdateFailed` on error
- [x] 1.2 Add test in `tests/test_coordinator.py`: verify status coordinator fetches data and has 30s interval

## 2. Remove status from main coordinator

- [x] 2.1 Remove `server_status: ServerStatusData | None` from `NjordCoordinatorData` in `custom_components/njord/coordinator.py`
- [x] 2.2 Remove `_STATUS_POLL_INTERVAL` constant and `_run_status_poll()` method from `NjordDataCoordinator`
- [x] 2.3 Remove the status poll task from `start_streams()` in `NjordDataCoordinator`
- [x] 2.4 Remove `get_status()` call from `_async_update_data()` in `NjordDataCoordinator`
- [x] 2.5 Update existing tests that reference `server_status` on coordinator data or the status poll task

## 3. Wire up in integration setup

- [x] 3.1 Update `async_setup_entry()` in `custom_components/njord/__init__.py` to create `NjordStatusCoordinator`, call `async_config_entry_first_refresh()` with graceful failure handling, and store under `hass.data[DOMAIN][entry.entry_id]["status_coordinator"]`
- [x] 3.2 Update `tests/test_init.py` and `tests/test_init_streaming.py` if they reference status data

## 4. Update status sensors

- [x] 4.1 Update `NjordApiBudgetSensor` in `custom_components/njord/sensor.py` to take `NjordStatusCoordinator`, change base to `CoordinatorEntity[NjordStatusCoordinator]`, read from `self.coordinator.data` directly (not `.server_status`)
- [x] 4.2 Update `NjordUptimeSensor` similarly
- [x] 4.3 Update `async_setup_entry()` in `custom_components/njord/sensor.py` to read `status_coordinator` from `hass.data` and pass it to the status sensors
- [x] 4.4 Update `tests/test_sensor.py` for the changed sensor coordinator wiring

## 5. Validation

- [x] 5.1 Run full test suite: `make test` — all existing + new tests pass
