## 1. Enrichment Merge Logic

- [x] 1.1 Add `merge_enrichment(existing: EnrichmentData | None, event: EnrichmentData) -> EnrichmentData` function in `custom_components/njord/coordinator.py` that uses `dataclasses.replace()` to update only non-None/non-default fields from the event onto the existing object. Creates a default `EnrichmentData(location=...)` if no existing data.
- [x] 1.2 Add pytest tests in `tests/test_enrichment_merge.py`: partial alert merge preserves indices, partial index merge preserves alerts, all 7 enrichment types merge independently, merge with no existing base creates new object.

## 2. Coordinator Streaming Infrastructure

- [x] 2.1 Refactor `NjordDataCoordinator` in `custom_components/njord/coordinator.py`: set `update_interval=None`, remove `_async_update_data` polling logic. Add `_known_locations: set[str]`, `_stream_tasks: list[asyncio.Task]`, and `_entity_factories: dict[str, tuple[AddEntitiesCallback, Callable]]`.
- [x] 2.2 Add `start_streams()` method that creates three asyncio tasks: `_run_forecast_stream()`, `_run_enrichment_stream()`, `_run_config_stream()`. Store tasks in `_stream_tasks`.
- [x] 2.3 Implement `_run_forecast_stream()`: iterate `client.stream_forecasts(location="")`, update `self.data.forecasts[(update.location, update.model)]`, call `self.async_set_updated_data(self.data)`.
- [x] 2.4 Implement `_run_enrichment_stream()`: iterate `client.stream_enrichments(location="")`, merge via `merge_enrichment()`, update `self.data.enrichments[location]`, call `self.async_set_updated_data(self.data)`.
- [x] 2.5 Implement `_run_config_stream()`: iterate `client.stream_config()`, diff locations against `_known_locations`, call `_create_entities_for_location()` for new ones. Fetch initial forecast+enrichment data for new locations via unary calls before creating entities.
- [x] 2.6 Add `stop_streams()` method that cancels all tasks in `_stream_tasks` and awaits them.
- [x] 2.7 Add `register_entity_factory(platform: str, add_entities: AddEntitiesCallback, factory: Callable)` and `_create_entities_for_location(location: NjordLocation)` methods.
- [x] 2.8 Keep `_async_update_data()` as a minimal method that does the unary-call-based first refresh (called once via `async_config_entry_first_refresh()`), populates `_known_locations` from config response.
- [x] 2.9 Add pytest tests in `tests/test_coordinator_streaming.py`: forecast stream updates coordinator data, enrichment stream merges correctly, config stream detects new locations, `stop_streams()` cancels tasks, no-op on config with only known locations.

## 3. Integration Setup/Teardown

- [x] 3.1 Update `custom_components/njord/__init__.py`: call `coordinator.start_streams()` after `forward_entry_setups()`. In `async_unload_entry`, call `coordinator.stop_streams()` before `client.close()`.
- [x] 3.2 Add pytest tests in `tests/test_init_streaming.py`: verify streams start after setup, verify streams stop and client closes on unload.

## 4. Dynamic Entity Creation

- [x] 4.1 Update `custom_components/njord/weather.py` `async_setup_entry`: after creating initial entities, call `coordinator.register_entity_factory("weather", async_add_entities, weather_factory_fn)` where the factory creates `NjordWeatherEntity` (per model) and optionally `NjordConsensusWeatherEntity` for a given location.
- [x] 4.2 Update `custom_components/njord/sensor.py` `async_setup_entry`: register entity factory on coordinator for sensor entities.
- [x] 4.3 Update `custom_components/njord/binary_sensor.py` `async_setup_entry`: register entity factory on coordinator for binary sensor entities.
- [x] 4.4 Add pytest tests in `tests/test_dynamic_entities.py`: new location triggers entity factory calls, factory creates correct entity types, duplicate location does not create duplicates.

## 5. Validation

- [x] 5.1 Run full test suite: `make test` — all existing + new tests pass.
- [x] 5.2 Verify no regressions: existing weather entity tests, enrichment sensor tests, config flow tests still pass.
