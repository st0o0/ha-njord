## 1. Fix DEFAULT_PORT and add enrichment data models

- [x] 1.1 Change `DEFAULT_PORT` from `8080` to `8081` in `custom_components/njord/const.py`
- [x] 1.2 Add enrichment dataclasses to `custom_components/njord/models.py`: `AlertData`, `IndexData`, `TrendData`, `ParameterTrendData`, `EnergyData`, `CopOptimalHourData`, `DerivedData`, `HorizonDerivedData`, `HistoryData`, `ModelMetricsData`, `ConsensusData`, `ParameterConsensusData`, `HorizonConsensusData`, `EnrichmentData`
- [x] 1.3 Create `tests/test_enrichment_models.py` — verify dataclass creation, frozen behavior, default values

## 2. Add enrichment RPCs to gRPC client

- [x] 2.1 Add protobuf → dataclass converter functions for all enrichment types in `custom_components/njord/grpc_client.py`
- [x] 2.2 Map protobuf enums to lowercase strings: `ALERT_TYPE_FROST` → `"frost"`, `ALERT_SEVERITY_YELLOW` → `"yellow"`, etc.
- [x] 2.3 Add `get_enrichments(location: str) -> EnrichmentData` unary RPC method
- [x] 2.4 Add `stream_enrichments(location, *, on_disconnect, on_reconnect) -> AsyncIterator[EnrichmentData]` streaming RPC method
- [x] 2.5 Add enrichment tests to `tests/test_grpc_client.py`

## 3. Update coordinator to fetch enrichments

- [x] 3.1 Extend `_async_update_data()` in `custom_components/njord/coordinator.py` to call `client.get_enrichments(location)` for each location
- [x] 3.2 Handle enrichment fetch failures gracefully — log warning, don't fail the entire update cycle
- [x] 3.3 Update `custom_components/njord/__init__.py` to add `Platform.BINARY_SENSOR` and `Platform.SENSOR` to `PLATFORMS`
- [x] 3.4 Update `tests/test_coordinator.py` with enrichment fetch tests

## 4. Alert binary_sensor platform

- [x] 4.1 Create `custom_components/njord/binary_sensor.py` with `async_setup_entry()` and `NjordAlertEntity` — 9 alert entities per location
- [x] 4.2 Create `tests/test_binary_sensor.py` — entity state, attribute mapping, unavailability

## 5. Sensor platform (indices, energy, trends, derived, history)

- [x] 5.1 Create `custom_components/njord/sensor.py` with all sensor entity classes
- [x] 5.2 Add `NjordInversionEntity` binary_sensor to `custom_components/njord/binary_sensor.py`
- [x] 5.3 Create `tests/test_sensor.py` — state, attributes, unavailability for all sensor types

## 6. Consensus weather entity

- [x] 6.1 Add `NjordConsensusWeatherEntity` to `custom_components/njord/weather.py`
- [x] 6.2 Add consensus weather tests to `tests/test_weather.py`

## 7. Translations and final integration

- [x] 7.1 Add entity name translations to `custom_components/njord/strings.json` and `custom_components/njord/translations/de.json`
- [x] 7.2 Run full test suite, verify no regressions

## Validation

```bash
docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet grpcio protobuf pytest pytest-asyncio voluptuous && python -m pytest tests/ -v"
```
