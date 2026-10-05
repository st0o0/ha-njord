## 1. Add icons to sensor entities

- [x] 1.1 Add `_attr_icon` to `NjordIndexSensor` in `custom_components/njord/sensor.py` — per index type (grill, bike, run, etc.)
- [x] 1.2 Add `_attr_icon` to `NjordVpdSensor`, `NjordEnergySensor`, `NjordTrendSensor`, `NjordSunshineSensor`, `NjordDiurnalAmplitudeSensor`, `NjordHistorySensor`
- [x] 1.3 Add `_attr_icon` to `NjordAlertEntity` in `custom_components/njord/binary_sensor.py` — per alert type (snowflake, thermometer, lightning, etc.)
- [x] 1.4 Add `_attr_icon` to `NjordInversionEntity`

## 2. Add translation keys and translations

- [x] 2.1 Add `_attr_translation_key` to all sensor and binary_sensor entity classes
- [x] 2.2 Add `entity` section to `custom_components/njord/strings.json` with English names for all sensor, binary_sensor entities
- [x] 2.3 Add `entity` section to `custom_components/njord/translations/de.json` with German translations

## 3. Fix weather entity attributes and forecasts

- [x] 3.1 Add `native_apparent_temperature` and `cloud_cover` properties to `NjordWeatherEntity` in `custom_components/njord/weather.py`
- [x] 3.2 Add `cloud_cover` to hourly forecast entries in `async_forecast_hourly`
- [x] 3.3 Verify `async_forecast_daily` includes `condition` for all entries with a weather_code
- [x] 3.4 Add `native_apparent_temperature` and `cloud_cover` to `NjordConsensusWeatherEntity` (from consensus parameters)

## 4. Update tests

- [x] 4.1 Update `tests/test_weather.py` — assert `apparent_temperature` and `cloud_cover` on weather entity state
- [x] 4.2 Update `tests/test_binary_sensor.py` — verify icon attribute exists on alert entities
- [x] 4.3 Update `tests/test_sensor.py` — verify icon attribute exists on sensor entities
- [x] 4.4 Run full test suite, verify all pass

## Validation

```bash
docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet pytest pytest-asyncio \
         pytest-homeassistant-custom-component \
         grpcio protobuf voluptuous && \
         python -m pytest tests/ -v"
```
