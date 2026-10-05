## 1. Project Configuration

- [x] 1.1 Create `pyproject.toml` with project metadata, `hatchling` build backend, runtime dependencies (`grpcio>=1.60.0`, `protobuf>=4.25.0`), and dev extras (`pytest`, `grpcio-tools`)
- [x] 1.2 Create `.gitignore` with Python defaults (`__pycache__/`, `*.pyc`, `.venv/`, `*.egg-info/`, `.pytest_cache/`, IDE files)
- [x] 1.3 Create `hacs.json` with name, HACS compatibility flags, and content_in_root set to false

## 2. HA Integration Skeleton

- [x] 2.1 Create `custom_components/njord/manifest.json` with domain `njord`, name `njord Weather`, version `0.1.0`, iot_class `local_push`, codeowners `["@st0o0"]`, requirements `["grpcio>=1.60.0", "protobuf>=4.25.0"]`
- [x] 2.2 Create `custom_components/njord/__init__.py` with minimal HA integration entry point (`async_setup_entry`, `async_unload_entry` as stubs returning True)
- [x] 2.3 Create `custom_components/njord/const.py` with `DOMAIN = "njord"` and default constants

## 3. Proto Files & Codegen

- [x] 3.1 Copy proto source files from `D:\GIT\njord\protos\njord\v1\` to `protos/njord/v1/` (both `forecast_service.proto` and `config_service.proto`)
- [x] 3.2 Create `Makefile` with `proto` target that runs `python -m grpc_tools.protoc` to generate stubs into `custom_components/njord/proto/njord/v1/`
- [x] 3.3 Create `custom_components/njord/proto/__init__.py` and `custom_components/njord/proto/njord/__init__.py` and `custom_components/njord/proto/njord/v1/__init__.py` (package init files)
- [x] 3.4 Run `make proto` and verify generated `_pb2.py` / `_pb2_grpc.py` files are present and importable

## 4. Test Infrastructure

- [x] 4.1 Create `tests/__init__.py` and `tests/conftest.py` with basic pytest configuration
- [x] 4.2 Create `tests/test_proto_import.py` — verify that generated proto modules are importable and contain expected message classes (`GetLocationsRequest`, `GetForecastResponse`, `HourlyForecast`, `NjordConfig`)

## Validation

```bash
# Verify proto codegen works
make proto

# Verify imports work
python -c "from custom_components.njord.proto.njord.v1 import forecast_service_pb2; print('OK')"
python -c "from custom_components.njord.proto.njord.v1 import config_service_pb2; print('OK')"

# Run tests
pytest tests/ -v
```
