## 1. Update ALERT_UNITS and alert sensor device classes

- [x] 1.1 In `custom_components/njord/sensor.py`: add imports for `SensorDeviceClass`, `UnitOfTemperature`, `UnitOfSpeed`, `UnitOfPressure`, `UnitOfLength` from `homeassistant.components.sensor` and `homeassistant.const`
- [x] 1.2 Replace `ALERT_UNITS` dict values with HA constants where applicable: `frost`/`heat` → `UnitOfTemperature.CELSIUS`, `storm` → `UnitOfSpeed.KILOMETERS_PER_HOUR`, `pressure_drop` → `UnitOfPressure.HPA`, `fog` → `UnitOfLength.METERS`, `snow` → `UnitOfLength.CENTIMETERS`. Keep `heavy_rain` as `"mm"`, `uv` as `"UV"`, `thunderstorm` as `"J/kg"`
- [x] 1.3 Create `ALERT_DEVICE_CLASSES` dict mapping alert types to their `SensorDeviceClass`: `frost`/`heat` → `TEMPERATURE`, `storm` → `WIND_SPEED`, `pressure_drop` → `PRESSURE`, `fog`/`snow` → `DISTANCE`. Omit types without device class
- [x] 1.4 In `NjordAlertSensor.__init__`: set `self._attr_device_class` from `ALERT_DEVICE_CLASSES.get(alert_type)`
- [x] 1.5 Create `ALERT_PRECISION` dict and set `self._attr_suggested_display_precision` in `NjordAlertSensor.__init__`: temperature→1, wind→0, precipitation→1, pressure→0, distance→0, uv→0, thunderstorm→0
- [x] 1.6 Update `tests/test_sensor.py` to assert `device_class` on alert sensors via state attributes

## 2. Add device class and precision to enrichment sensors

- [x] 2.1 In `NjordDiurnalAmplitudeSensor`: set `_attr_device_class = SensorDeviceClass.TEMPERATURE`, change `_attr_native_unit_of_measurement` to `UnitOfTemperature.CELSIUS`, add `_attr_suggested_display_precision = 1`
- [x] 2.2 In `NjordHistorySensor`: set `_attr_device_class = SensorDeviceClass.TEMPERATURE`, change `_attr_native_unit_of_measurement` to `UnitOfTemperature.CELSIUS`, add `_attr_suggested_display_precision = 1`
- [x] 2.3 In `NjordFrostHoursSensor`: set `_attr_device_class = SensorDeviceClass.DURATION`, change `_attr_native_unit_of_measurement` to `UnitOfTime.HOURS`, add `_attr_suggested_display_precision = 0`
- [x] 2.4 In `NjordHddSensor`: add `_attr_suggested_display_precision = 1` (keep raw `"°C·d"` unit, no device class)
- [x] 2.5 In `NjordCddSensor`: add `_attr_suggested_display_precision = 1` (keep raw `"°C·d"` unit, no device class)
- [x] 2.6 In `NjordFrostConfidenceSensor`: add `_attr_suggested_display_precision = 0` (keep raw `"%"` unit, no device class)

## 3. Add precision to remaining sensors

- [x] 3.1 In `NjordIndexSensor`: add `_attr_suggested_display_precision = 0`
- [x] 3.2 In `NjordVpdSensor`: add `_attr_suggested_display_precision = 2` (keep raw `"kPa"` unit, no device class — VPD is always kPa)
- [x] 3.3 In `NjordSunshineSensor`: add `_attr_suggested_display_precision = 0`
- [x] 3.4 In `NjordEnergySensor.__init__`: set `self._attr_suggested_display_precision` based on energy_key: `cop_estimate`→1, sensors with units→0, text sensors (battery_strategy)→none
- [x] 3.5 In `NjordTrendSensor`: no precision needed (text value). Verified — no change required
- [x] 3.6 In `NjordApiBudgetSensor`: add `_attr_suggested_display_precision = 1`
- [x] 3.7 In `NjordUptimeSensor`: add `_attr_suggested_display_precision = 1`, also added `device_class = DURATION` + `UnitOfTime.HOURS`

## 4. Update test stubs and assertions

- [x] 4.1 N/A — `pytest-homeassistant-custom-component` provides real HA modules, no stub changes needed
- [x] 4.2 Added `test_alert_device_classes`, `test_diurnal_amplitude_device_class`, `test_model_performance_device_class`, `test_frost_hours_device_class` to `tests/test_sensor.py`
- [x] 4.3 N/A — `tests/test_dynamic_entities.py` has no unit string assertions

## 5. Validation

- [x] 5.1 Run `make test` — 136 passed, 13 skipped, 0 failed
- [x] 5.2 No regressions in test_services.py, test_dynamic_entities.py, test_init.py — all pass
