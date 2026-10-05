## 1. Options Flow: Sensor Push Step

- [x] 1.1 Add `async_step_sensors` to `NjordOptionsFlow` in `custom_components/njord/config_flow.py` — dynamic schema built from catalog locations × sensor kinds (`indoor_temperature`, `indoor_humidity`) using `EntitySelector` with `device_class` filter and `multiple=True`. Schema keys: `{location}_{kind}`. Step 1 (`init`) returns `async_step_sensors` instead of `create_entry`.
- [x] 1.2 Update `async_step_init` to return `self.async_show_form(step_id="sensors", ...)` after processing init data (store init data on `self`, finalize both steps in `async_step_sensors`).
- [x] 1.3 Store sensor push config in `entry.options["sensor_push"]` as `{location: {kind: [entity_id, ...]}}`. Detect changes vs previous config and trigger reload if changed.
- [x] 1.4 Add EN strings in `custom_components/njord/strings.json` for the sensor step: step title, field labels per kind.
- [x] 1.5 Add DE strings in `custom_components/njord/translations/de.json` for the sensor step.
- [x] 1.6 Write tests in `tests/test_options_flow.py`: step navigation (init → sensors → create_entry), sensor config persistence, reload trigger on change, no reload when unchanged.

## 2. State Change Listener

- [x] 2.1 Add sensor push listener setup in `custom_components/njord/__init__.py` `async_setup_entry`: read `sensor_push` from options, build reverse map `entity_id → (location, kind)`, register `async_track_state_change_event` for all entity IDs.
- [x] 2.2 Implement the listener callback: parse `float(new_state.state)`, skip non-numeric states silently, call `client.push_sensor(kind, location, value, source=entity_id)`, catch exceptions and log warning.
- [x] 2.3 Ensure listener is removed on `async_unload_entry` via `entry.async_on_unload`.
- [x] 2.4 Write tests in `tests/test_sensor_push.py`: listener registered with correct entities, push called on state change, non-numeric states skipped, gRPC errors logged and dropped, listener removed on unload, no listener when config empty.

## 3. push_sensor Service

- [x] 3.1 Register `njord.push_sensor` service in `custom_components/njord/__init__.py` with schema: `kind` (required, string), `entity_id` (required, string), `location` (optional, string), `source` (optional, string).
- [x] 3.2 Implement service handler: validate kind against `SENSOR_KIND_MAP`, read entity state, convert to float (raise `ServiceValidationError` on failure), auto-resolve location from catalog if omitted and exactly one location exists, call `client.push_sensor()`.
- [x] 3.3 Remove service on last entry unload (same pattern as `trigger_poll`).
- [x] 3.4 Write tests in `tests/test_sensor_push_service.py`: valid push, source defaults to entity_id, location auto-resolve with single location, error on missing location with multiple locations, error on invalid kind, error on non-existent entity, error on non-numeric state.

## 4. Validation

- [x] 4.1 Run `pytest tests/test_options_flow.py -v` — all existing + new tests pass
- [x] 4.2 Run `pytest tests/test_sensor_push.py -v` — all listener tests pass
- [x] 4.3 Run `pytest tests/test_sensor_push_service.py -v` — all service tests pass
- [x] 4.4 Run `pytest tests/ -v` — full suite passes, no regressions
