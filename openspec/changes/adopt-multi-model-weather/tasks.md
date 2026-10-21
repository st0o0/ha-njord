## 1. Protos

- [x] 1.1 Copy `D:\GIT\njord\protos\njord\v2\common.proto` and `weather.proto` into `protos/njord/v2/` and regenerate the stubs in `custom_components/njord/proto/njord/v2/` with the documented Docker command
- [x] 1.2 `tests/test_proto_import.py`: assert `ModelInfo.enabled`, `GetDomainDataRequest.model`, `DomainDataUpdate.model` and `ModelComparison` exist

## 2. Client and models

- [x] 2.1 `custom_components/njord/models.py`: `ModelInfoData.enabled: bool = True`, `WeatherDomainData.model: str = ""` (test in `tests/test_models.py`)
- [x] 2.2 `custom_components/njord/grpc_client.py`: `_to_model_info` maps `enabled`, `_to_domain_data` maps `model` for weather, `get_domain_data(location, domain, model="")` sets the request `model` when non-empty (tests in `tests/test_grpc_client.py`)
- [x] 2.3 `tests/test_grpc_client.py`: a `model_comparison` event becomes a `FeatureData` for `Feature.MODEL_COMPARISON` with `values["days"]` as a list of dicts

## 3. Coordinator

- [x] 3.1 `custom_components/njord/coordinator.py`: `NjordCoordinatorData.model_domains`, helpers for primary and enabled secondary models, `register_model_factory`
- [x] 3.2 First refresh fetches every secondary model into `model_domains`; a failure leaves the key absent (tests in `tests/test_coordinator.py`)
- [x] 3.3 Domain stream routes weather updates by `model`; first sight of a secondary key calls the model factories (tests in `tests/test_coordinator_streaming.py`, `tests/test_dynamic_entities.py`)

## 4. Weather entities

- [x] 4.1 `custom_components/njord/weather.py`: parametrize the weather entity by model (primary unique id unchanged, model entities `{entry_id}_{slug}_{model_id}_weather`, entity name = display name (entity id follows HA's device + name convention)), create model entities at setup, register the model factory
- [x] 4.2 Model attributes `model`, `model_name`, `provider`, `region`, `resolution_km`, `forecast_hours` on every weather entity (tests in `tests/test_weather.py`)

## 5. ModelComparison sensor

- [x] 5.1 `custom_components/njord/const.py`: `Feature.MODEL_COMPARISON`, `FEATURE_KEYS[...] = "Weather:ModelComparison"`
- [x] 5.2 `custom_components/njord/lifestyle.py`: `Model Temperature Spread` description (spread of the first day's `max_temperature`, °C, precision 1) (tests in `tests/test_sensor.py`)

## 6. Verification

- [x] 6.1 `pytest`, `ruff format --check`, `ruff check` green in the Docker command from CLAUDE.md
