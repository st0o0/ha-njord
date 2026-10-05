## 1. Condition Mapper

- [x] 1.1 Create `custom_components/njord/condition_mapper.py` with `WMO_TO_HA` dictionary and `map_condition(weather_code: int, is_day: bool) -> str` function covering WMO codes 0–99
- [x] 1.2 Create `tests/test_condition_mapper.py` — test clear sky day/night, overcast, rain, thunderstorm, unknown code fallback to "exceptional"

## 2. Config Flow

- [x] 2.1 Add `"config_flow": true` to `custom_components/njord/manifest.json`
- [x] 2.2 Create `custom_components/njord/config_flow.py` — `NjordConfigFlow` with user step (host+port form, default port 8081), gRPC validation via `get_locations()`, unique_id `{host}:{port}`, abort on duplicate, create ConfigEntry
- [x] 2.3 Create `custom_components/njord/strings.json` with English text for config flow steps and errors
- [x] 2.4 Create `custom_components/njord/translations/de.json` with German translations
- [x] 2.5 Create `tests/test_config_flow.py` — test successful flow, connection error, duplicate abort

## 3. Integration Setup

- [x] 3.1 Rewrite `custom_components/njord/__init__.py` — `async_setup_entry` creates `NjordClient`, connects, creates `DataUpdateCoordinator` with 5min interval, stores in `hass.data[DOMAIN]`, forwards to weather platform. `async_unload_entry` unloads platforms and closes client.
- [x] 3.2 Create `custom_components/njord/coordinator.py` — `NjordDataCoordinator(DataUpdateCoordinator)` that calls `get_config()` + `get_forecast()` for each location×model pair, stores results as `dict[tuple[str, str], ForecastData]`

## 4. Weather Platform

- [x] 4.1 Create `custom_components/njord/weather.py` — `NjordWeatherEntity(CoordinatorEntity, WeatherEntity)` with state from condition mapper, attributes (temperature, humidity, pressure, wind_speed, wind_bearing), `async_forecast_hourly`, `async_forecast_daily`, device info grouped by location
- [x] 4.2 Create `tests/test_weather.py` — test entity state from WMO code, attributes from hourly data, forecast methods return correct structure

## Validation

```bash
# Run all tests via Docker
docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet grpcio protobuf pytest pytest-asyncio && python -m pytest tests/ -v"
```
