## Tasks

- [x] ### Task 1: Add `derived_updated_at` to models and merge logic
**Spec:** enrichment-merge
**Files:** `models.py`, `grpc_client.py`, `coordinator.py`

- Add `derived_updated_at: datetime | None = None` field to `EnrichmentData`
- In `_to_enrichment_event()`: set `derived_updated_at = _ts_to_dt(pb.updated_at)` when `payload_field == "derived"`
- In `_to_enrichment_data()` (unary): set `derived_updated_at = datetime.now(UTC)` as approximation for initial load
- Add `"derived_updated_at"` to `_ENRICHMENT_MERGE_FIELDS` and `_ENRICHMENT_DEFAULTS` in `coordinator.py`
- Update existing tests for enrichment merge to verify `derived_updated_at` handling

- [x] ### Task 2: Create horizon offset helper module
**Spec:** horizon-offset-helper
**Files:** new `custom_components/njord/horizon.py`, `weather.py`

- Create `horizon.py` with:
  - `current_horizon_offset(updated_at: datetime | None) -> int` — returns `max(0, floor((now - updated_at) / 3600))`; returns 0 if `updated_at` is None
  - `get_horizon_entry(horizons: list[T], offset: int) -> T | None` — finds entry matching `f"h{offset}"` by `horizon` attribute
- Refactor `NjordConsensusWeatherEntity`:
  - Replace `_current_horizon_offset()` with `current_horizon_offset(enrichment.consensus_updated_at)`
  - Replace inline horizon lookups with `get_horizon_entry()` where applicable
- Verify consensus entity behavior is unchanged
- Add unit tests for `horizon.py`

- [x] ### Task 3: Add derived sensors (Beaufort, Wind Chill, Dewpoint Comfort)
**Spec:** derived-sensors
**Files:** `sensor.py`, `strings.json`, `translations/de.json`

- Add `NjordBeaufortSensor` — reads `beaufort` from current derived horizon, icon `mdi:windsock`, no unit, precision 0
- Add `NjordWindChillSensor` — reads `wind_chill` from current derived horizon, device_class TEMPERATURE, unit °C, precision 1, icon `mdi:snowflake-thermometer`
- Add `NjordDewpointComfortSensor` — reads `dewpoint_comfort` from current derived horizon, icon `mdi:water-thermometer`, string value
- All three: `_attr_entity_registry_enabled_default = False`, proper `translation_key`
- Register in `async_setup_entry` and `sensor_factory`
- Add translation entries for EN and DE
- Add unit tests

- [x] ### Task 4: Create alert event platform
**Spec:** alert-events
**Files:** new `custom_components/njord/event.py`, `__init__.py`

- Create `NjordWeatherAlertEvent(CoordinatorEntity, EventEntity)`:
  - One entity per location, `unique_id = "{entry_id}_{location}_weather_alert"`
  - `_attr_event_types = ["alert_started", "alert_escalated", "alert_deescalated", "alert_cleared"]`
  - Icon `mdi:weather-lightning-rainy`
  - Internal `_previous_alerts: dict[str, str]` tracking type → severity
  - `_handle_coordinator_update()`: diff current alerts against `_previous_alerts`, fire events for transitions
  - First update initializes `_previous_alerts` without firing events
- Add `"event"` to `PLATFORMS` in `__init__.py`
- Register entity factory for dynamic location addition
- Add unit tests for all event types and edge cases

- [x] ### Task 5: Remove alert sensors and update trend sensor
**Spec:** enrichment-sensors
**Files:** `sensor.py`

- Remove `NjordAlertSensor` class and all supporting constants (`ALERT_TYPES`, `ALERT_NAMES`, `ALERT_UNITS`, `ALERT_DEVICE_CLASSES`, `ALERT_PRECISION`, `ALERT_ICONS`)
- Remove alert sensor creation from `async_setup_entry` and `sensor_factory`
- Modify `NjordTrendSensor.native_value` to return `weather_change_description` instead of `stability_label`
- Add `stability_label` to `extra_state_attributes`
- Update existing tests

- [x] ### Task 6: Update tests
**Spec:** all
**Files:** `tests/`

- Remove or update alert sensor tests
- Add tests for derived sensors (beaufort, wind_chill, dewpoint_comfort)
- Add tests for alert event entity (all 4 event types, initial state, edge cases)
- Add tests for trend sensor state change (description as primary, stability_label as attr)
- Add tests for horizon offset helper
- Verify enrichment merge tests cover `derived_updated_at`
