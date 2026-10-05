## 1. Add test dependency and update Docker command

- [x] 1.1 Add `pytest-homeassistant-custom-component` to `[project.optional-dependencies].dev` in `pyproject.toml`
- [x] 1.2 Update `Makefile` test target to install `pytest-homeassistant-custom-component` in the Docker command
- [x] 1.3 Verify the Docker test command installs successfully (may need system deps like `gcc` for some HA transitive deps)

## 2. Rewrite conftest.py

- [x] 2.1 Delete all HA module stub code from `tests/conftest.py` (the `_HA_STUBS` dict, all fake classes, `sys.modules` manipulation)
- [x] 2.2 Add `mock_client` fixture that patches `custom_components.njord.NjordClient` with an `AsyncMock` returning canned `NjordConfigData`, `ForecastData`, `EnrichmentData` responses
- [x] 2.3 Add `mock_config_entry` fixture returning a `MockConfigEntry(domain=DOMAIN, data={"host": "localhost", "port": 8081})`
- [x] 2.4 Add `init_integration(hass, mock_config_entry)` helper that adds the entry to hass, calls `async_setup`, and returns the entry
- [x] 2.5 Verify `conftest.py` imports work: `from pytest_homeassistant_custom_component.common import MockConfigEntry`

## 3. Adapt existing unit tests

- [x] 3.1 Update `tests/test_models.py` and `tests/test_enrichment_models.py` — these should work unchanged (pure Python, no HA imports)
- [x] 3.2 Update `tests/test_condition_mapper.py` — should work unchanged (pure Python)
- [x] 3.3 Update `tests/test_grpc_client.py` — should work unchanged (uses real mock gRPC server, no HA)
- [x] 3.4 Update `tests/test_coordinator.py` — adapt to use real `DataUpdateCoordinator` instead of stub; may need `hass` fixture for coordinator construction
- [x] 3.5 Update `tests/test_weather.py` — replace direct entity construction with `hass.states` assertions via `init_integration`
- [x] 3.6 Update `tests/test_binary_sensor.py` — replace direct entity construction with `hass.states` assertions
- [x] 3.7 Update `tests/test_sensor.py` — replace direct entity construction with `hass.states` assertions

## 4. Activate config flow tests

- [x] 4.1 Rewrite `tests/test_config_flow.py` — remove `@pytest.mark.skip`, implement `test_config_flow_success` using `hass.config_entries.flow.async_init` and `async_configure`
- [x] 4.2 Implement `test_config_flow_cannot_connect` — set `mock_client.get_locations.side_effect` to gRPC error
- [x] 4.3 Implement `test_config_flow_duplicate_abort` — create existing entry first, then attempt duplicate

## 5. Add integration lifecycle tests

- [x] 5.1 Create `tests/test_init.py` with `test_setup_entry` — verify `async_setup_entry` creates coordinator, forwards platforms, entities appear in `hass.states`
- [x] 5.2 Add `test_unload_entry` — verify `async_unload_entry` calls `client.close()` and unloads platforms
- [x] 5.3 Add `test_setup_entry_connection_failure` — verify setup fails gracefully when NjordClient raises on connect

## 6. Final validation

- [x] 6.1 Run full test suite via Docker, verify all tests pass with zero skips
- [x] 6.2 Verify test count is >= previous count (126 passed) — no tests lost in migration

## Validation

```bash
docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet pytest pytest-asyncio \
         pytest-homeassistant-custom-component \
         grpcio protobuf voluptuous && \
         python -m pytest tests/ -v"
```
