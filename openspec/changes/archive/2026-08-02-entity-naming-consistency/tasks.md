## 1. Create shared DeviceInfo helpers

- [x] 1.1 Create `custom_components/njord/helpers.py` with `device_info(entry, location, sw_version)` and `server_device_info(entry, sw_version)` extracted from `custom_components/njord/sensor.py`
- [x] 1.2 Update `custom_components/njord/sensor.py` to import and use helpers from `helpers.py`, remove the local `_device_info` and `_server_device_info` functions
- [x] 1.3 Update `custom_components/njord/weather.py` to import and use `device_info` from `helpers.py`, remove inline DeviceInfo construction
- [x] 1.4 Update `custom_components/njord/binary_sensor.py` to import and use `device_info` and `server_device_info` from `helpers.py`, remove inline DeviceInfo construction
- [x] 1.5 Update `custom_components/njord/event.py` to import and use `device_info` from `helpers.py`, remove inline DeviceInfo construction
- [x] 1.6 Update `custom_components/njord/button.py` to import and use `server_device_info` from `helpers.py`, remove inline DeviceInfo construction
- [x] 1.7 Write tests in `tests/test_device_info.py` verifying both helper functions produce correct DeviceInfo for location and server devices

## 2. Rename NjordHistorySensor to NjordModelPerformanceSensor

- [x] 2.1 Rename class `NjordHistorySensor` → `NjordModelPerformanceSensor` in `custom_components/njord/sensor.py`
- [x] 2.2 Update instantiation reference in `async_setup_entry` in `custom_components/njord/sensor.py`
- [x] 2.3 Update any test references to `NjordHistorySensor` in `tests/` (none found — no-op)

## 3. Add `_energy` suffix to energy sensor slugs

- [x] 3.1 Change slug in `NjordEnergySensor.__init__` from `f"{location}_{energy_key}"` to `f"{location}_{energy_key}_energy"` in `custom_components/njord/sensor.py`
- [x] 3.2 Update tests that assert energy sensor unique_ids in `tests/`

## 4. Fix NjordTargetSensor display name

- [x] 4.1 Change `_attr_name` in `NjordTargetSensor.__init__` from `f"{location.title()} {model} Poll"` to `f"{model} Target"` in `custom_components/njord/sensor.py`
- [x] 4.2 Update tests that assert target sensor names in `tests/` (no direct references found — no-op)

## 5. Normalize NjordSunshineSensor slug

- [x] 5.1 Change slug in `NjordSunshineSensor.__init__` from `f"{location}_sunshine_pct"` to `f"{location}_sunshine"` in `custom_components/njord/sensor.py`
- [x] 5.2 Update tests that assert sunshine sensor unique_ids in `tests/` (test uses entity_id from name, not slug — no-op)

## 6. Validation

- [x] 6.1 Run full test suite: `make test` — all 187 tests pass
