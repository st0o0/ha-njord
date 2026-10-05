## 1. Proto Layer

- [x] 1.1 Copy v2 proto files from `D:\GIT\njord\protos\njord\v2\` to `protos/njord/v2/` (common.proto, weather.proto, admin.proto, ops.proto). Remove `protos/njord/v1/` directory.
- [x] 1.2 Update `Makefile` proto target: generate stubs from `protos/njord/v2/` into `custom_components/njord/proto/njord/v2/`, handle `common.proto` import resolution via `-I` include path. Remove v1 output directory.
- [x] 1.3 Run `make proto` and verify stubs are generated at `custom_components/njord/proto/njord/v2/` (common_pb2.py, weather_pb2.py, weather_pb2_grpc.py, admin_pb2.py, admin_pb2_grpc.py, ops_pb2.py, ops_pb2_grpc.py).
- [x] 1.4 Update `custom_components/njord/proto/__init__.py` to set up `sys.path` for `njord.v2` imports. Remove v1 stub directory `custom_components/njord/proto/njord/v1/`.

## 2. Data Models

- [x] 2.1 Update `custom_components/njord/models.py`: rename `HourlyForecastData.timestamp` to `valid_at`. Change `ForecastData.updated_at` type from `int` to `datetime`.
- [x] 2.2 Add `CatalogData` dataclass: `locations: list[LocationInfo]`, `model_info: dict[str, ModelInfoData]` where `LocationInfo` is a new dataclass with `name`, `latitude`, `longitude`, `models: list[str]`.
- [x] 2.3 Add `ModelStatusData` dataclass: `location`, `model`, `phase`, `next_poll: datetime | None`, `last_change: datetime | None`, `miss_count: int`, `cycle_seconds: int | None`.
- [x] 2.4 Expand `ServerStatusData`: add `process_start: datetime | None`, `model_statuses: list[ModelStatusData]`, `active_enrichments: list[str]`.
- [x] 2.5 Update tests in `tests/` that reference `HourlyForecastData.timestamp` → `valid_at` and `ForecastData.updated_at` int → datetime.

## 3. gRPC Client

- [x] 3.1 Rewrite `custom_components/njord/grpc_client.py`: replace `ForecastServiceStub` + `ConfigServiceStub` with `WeatherServiceStub` + `AdminServiceStub` + `OpsServiceStub`. Update all imports from `njord.v2` package.
- [x] 3.2 Replace `get_locations()` and `get_models()`/`get_model_info()` with `get_catalog()` → `CatalogData`. Remove the old methods.
- [x] 3.3 Update timestamp converters: `_to_hourly` uses `pb.valid_at.ToDatetime()` instead of `datetime.fromtimestamp(pb.timestamp)`. `_to_forecast_data` converts `pb.updated_at.ToDatetime()`.
- [x] 3.4 Update `_to_server_status`: map `process_start`, `models[]` → `ModelStatusData`, `active_enrichments[]`.
- [x] 3.5 Route RPCs to correct stubs: `get_config()`/`stream_config()` → `AdminServiceStub`, `get_status()` → `OpsServiceStub`, forecast/enrichment RPCs → `WeatherServiceStub`.
- [x] 3.6 Add `trigger_poll(location="", model="")` method using `OpsServiceStub.TriggerPoll`.
- [x] 3.7 Update `tests/test_grpc_client.py`: mock v2 stubs, test `get_catalog()`, test timestamp conversion, test `trigger_poll()`, remove `get_locations`/`get_models` tests.

## 4. Coordinator

- [x] 4.1 Update `custom_components/njord/coordinator.py` `_async_update_data`: call `get_catalog()` for locations + model info, call `get_config()` for settings only. Replace the N × `get_model_info()` loop.
- [x] 4.2 Store `CatalogData` in coordinator data or extract locations/model_info from it into `NjordCoordinatorData`.
- [x] 4.3 Update stub sentinel in failed forecast fetch: `ForecastData(updated_at=datetime.min.replace(tzinfo=UTC))`.
- [x] 4.4 Update `tests/test_coordinator.py`: mock `get_catalog()` instead of `get_locations`/`get_models`/`get_model_info`, update `updated_at` assertions.

## 5. Config Flow

- [x] 5.1 Update `custom_components/njord/config_flow.py` `_async_validate_connection`: replace `get_locations()` + loop `get_models()` with single `get_catalog()` call. Extract location/model counts from catalog response.
- [x] 5.2 Update `tests/test_config_flow.py`: mock `get_catalog()` instead of `get_locations`/`get_models`.

## 6. Weather Entities

- [x] 6.1 Update `custom_components/njord/weather.py`: access `hourly[0].valid_at` instead of `hourly[0].timestamp` where applicable. Adjust any `updated_at` comparisons from int to datetime.
- [x] 6.2 Update `tests/test_weather.py`: use datetime for `updated_at` and `valid_at` in test fixtures.

## 7. Trigger Poll

- [x] 7.1 Create `custom_components/njord/button.py`: `NjordTriggerPollButton` entity that calls `client.trigger_poll()` on press. Expose `triggered_count` and `last_triggered` as extra state attributes.
- [x] 7.2 Create `custom_components/njord/services.yaml`: define `trigger_poll` service with optional `location` (string) and `model` (string) fields.
- [x] 7.3 Update `custom_components/njord/__init__.py`: add `BUTTON` to platforms list, register `njord.trigger_poll` service on setup, unregister on last entry unload.
- [x] 7.4 Update `custom_components/njord/strings.json` and `custom_components/njord/translations/de.json`: add strings for trigger poll button and service.
- [x] 7.5 Add `tests/test_button.py`: test button press triggers `trigger_poll()`, test attributes reflect response.
- [x] 7.6 Add `tests/test_services.py`: test service call with no params, with location only, with location+model.

## 8. Validation

- [x] 8.1 Run full test suite: `make test` — all existing and new tests pass.
- [x] 8.2 Verify proto stubs import correctly: `python -c "from njord.v2 import weather_pb2, admin_pb2, ops_pb2, common_pb2"` inside Docker.
