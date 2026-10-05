## 1. DeviceInfo Enrichment

- [x] 1.1 Add `model` and `sw_version` params to `_server_device_info()` and `_device_info()` helpers in `custom_components/njord/sensor.py`. Server device gets `model="Weather Service"`, location devices get `model="Weather Station"`. `sw_version` is passed in from the status coordinator data.
- [x] 1.2 Update `NjordWeatherEntity` and `NjordConsensusWeatherEntity` in `custom_components/njord/weather.py` to include `model="Weather Station"` and `sw_version` from the status coordinator.
- [x] 1.3 Update `TriggerPollButton` in `custom_components/njord/button.py` to use matching DeviceInfo fields (name, manufacturer, model, sw_version) consistent with `_server_device_info()`.
- [x] 1.4 Update `binary_sensor.py` and `event.py` to include `model="Weather Station"` and `sw_version` on their DeviceInfo.
- [x] 1.5 Wire status coordinator reference into all platform `async_setup_entry` functions so entities can read `sw_version` at init.
- [x] 1.6 Add tests in `tests/test_device_info.py`: verify `model` and `sw_version` appear on DeviceInfo for weather, sensor, binary_sensor, button, and event entities.

## 2. OptionsFlow

- [x] 2.1 Add `NjordOptionsFlow` class to `custom_components/njord/config_flow.py` with `status_poll_interval` (int, default 30, range 10–300) and `disabled_enrichment_groups` (multi-select from 7 enrichment types, default all enabled).
- [x] 2.2 Register the options flow handler on `NjordConfigFlow` via `async_get_options_flow`.
- [x] 2.3 Add options update listener in `custom_components/njord/__init__.py`: update status coordinator interval in-place if only poll interval changed, trigger reload if enrichment groups changed.
- [x] 2.4 Filter entity creation in sensor/binary_sensor/event platform setup by checking `entry.options.get("disabled_enrichment_groups", [])`.
- [x] 2.5 Read `status_poll_interval` from `entry.options` in `NjordStatusCoordinator.__init__` with fallback to 30.
- [x] 2.6 Add `options` step strings to `custom_components/njord/strings.json` and `custom_components/njord/translations/de.json`.
- [x] 2.7 Add tests in `tests/test_options_flow.py`: default values, custom values, poll-interval-only change (no reload), enrichment toggle change (triggers reload).

## 3. Stream Health Tracking

- [x] 3.1 Add `stream_states: dict[str, bool]` to `NjordDataCoordinator` in `custom_components/njord/coordinator.py`, initialized to `{"forecast": False, "enrichment": False, "config": False}`.
- [x] 3.2 Update `_stream_with_reconnect` to set `stream_states[name] = True` on successful connection and `False` on disconnect/error, calling `async_set_updated_data` on change.
- [x] 3.3 Add repair issue creation after 60s disconnect grace period and auto-dismiss on reconnect using `homeassistant.helpers.issue_registry` (`async_create_issue` / `async_delete_issue`).
- [x] 3.4 Add three `BinarySensorEntity` subclasses in `custom_components/njord/binary_sensor.py` for forecast/enrichment/config stream connectivity with `device_class=CONNECTIVITY`, `entity_category=DIAGNOSTIC`, grouped under server device.
- [x] 3.5 Add tests in `tests/test_stream_health.py`: binary sensor states on connect/disconnect, repair issue creation after grace period, repair dismissal on reconnect.

## 4. GetTargets Integration

- [x] 4.1 Add `TargetData` frozen dataclass to `custom_components/njord/models.py` with fields: `location`, `model`, `last_poll` (datetime | None), `status` (str).
- [x] 4.2 Add `async get_targets()` method to `NjordClient` in `custom_components/njord/grpc_client.py` calling `OpsService.GetTargets()` and returning `list[TargetData]`.
- [x] 4.3 Add `targets: list[TargetData]` field to `ServerStatusData` in `custom_components/njord/models.py`.
- [x] 4.4 Update `NjordStatusCoordinator._async_update_data` to call `get_targets()` alongside `get_status()`, falling back to empty list on error.
- [x] 4.5 Add `NjordTargetSensor` in `custom_components/njord/sensor.py` — one per target, `native_value` = last poll ISO timestamp, extra attributes = `{status, model}`, `entity_category=DIAGNOSTIC`, `entity_registry_enabled_default=False`, grouped under server device.
- [x] 4.6 Add tests in `tests/test_get_targets.py`: client method, status coordinator with targets, target sensor values and attributes.

## 5. Diagnostics Download

- [x] 5.1 Create `custom_components/njord/diagnostics.py` with `async_get_config_entry_diagnostics` returning config (host redacted), coordinator summary (location count, forecast key count, enrichment types per location), stream states, and server status.
- [x] 5.2 Add tests in `tests/test_diagnostics.py`: verify output structure, host redaction, stream states included, server status included, graceful handling when status coordinator is None.

## 6. Validation

- [x] 6.1 Run full test suite: `make test` — all existing + new tests pass.
- [x] 6.2 Verify `strings.json` and `de.json` are structurally consistent (all keys present in both).
