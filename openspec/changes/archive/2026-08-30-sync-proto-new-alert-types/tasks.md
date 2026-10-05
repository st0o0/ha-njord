## 1. Proto Sync

- [x] 1.1 Copy `admin.proto`, `common.proto`, and `ops.proto` from `D:\GIT\njord\protos\njord\v2\` to `protos/njord/v2/`
- [x] 1.2 Run `make proto` to regenerate stubs in `custom_components/njord/proto/njord/v2/`
- [x] 1.3 Verify generated `common_pb2.py` contains `ALERT_TYPE_ICE` through `ALERT_TYPE_HUMIDITY`

## 2. Alert Type Registry

- [x] 2.1 Add `ice`, `wind_chill`, `visibility`, `tropical_night`, `humidity` to `ALERT_TYPES` list in `custom_components/njord/sensor.py`
- [x] 2.2 Add display names to `ALERT_NAMES` dict (`"Ice Alert"`, `"Wind Chill Alert"`, `"Visibility Alert"`, `"Tropical Night Alert"`, `"Humidity Alert"`)
- [x] 2.3 Add units to `ALERT_UNITS` dict (°C, °C, m, °C, %)
- [x] 2.4 Add device classes to `ALERT_DEVICE_CLASSES` dict (TEMPERATURE, TEMPERATURE, DISTANCE, TEMPERATURE, HUMIDITY)
- [x] 2.5 Add precision to `ALERT_PRECISION` dict (1, 1, 0, 1, 0)
- [x] 2.6 Add icons to `ALERT_ICONS` dict (`mdi:snowflake-thermometer`, `mdi:thermometer-minus`, `mdi:eye-off`, `mdi:weather-night`, `mdi:water-percent`)

## 3. Tests

- [x] 3.1 Update alert sensor test fixtures in `tests/` to include the 5 new alert types
- [x] 3.2 Verify all alert type metadata (units, icons, device classes, precision) is tested for 14 types
- [x] 3.3 Update any assertions that hard-code the count of 9 alert types to 14

## 4. Validation

- [x] 4.1 Run `make test` and verify all tests pass
