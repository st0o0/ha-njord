## Why

ha-njord needs a working project foundation before any feature work can begin. There is currently no Python project structure, no HA integration skeleton, no proto files, and no codegen pipeline. Every future change (gRPC client, config flow, weather entities) depends on this scaffold existing.

## What Changes

- Create `pyproject.toml` with project metadata, dependencies (`grpcio`, `protobuf`), and dev dependencies (`pytest`, `grpcio-tools`)
- Create `custom_components/njord/` with HA integration skeleton: `__init__.py`, `manifest.json`, `const.py`
- Copy proto files from njord (`forecast_service.proto`, `config_service.proto`) into `protos/njord/v1/`
- Set up gRPC Python codegen (protoc invocation via script or Makefile) that generates `_pb2.py` / `_pb2_grpc.py` stubs
- Create `tests/` directory with `conftest.py`
- Add `hacs.json` for HACS discoverability
- Add `.gitignore` (Python defaults + generated proto stubs)

## Non-goals

- No functional gRPC client code — that's a separate change
- No config flow, no weather entities, no condition mapping
- No CI/CD pipeline
- No README or documentation beyond what HACS requires
- No proto modifications — files are copied as-is from njord

## Capabilities

### New Capabilities
- `project-structure`: Python project layout, HA integration skeleton, dependency declarations
- `proto-codegen`: Proto file management and Python stub generation from `.proto` definitions

### Modified Capabilities

(none — greenfield project)

## Impact

- **New files**: ~10-12 files establishing the project skeleton
- **Dependencies**: `grpcio>=1.60.0`, `protobuf>=4.25.0` (runtime); `grpcio-tools>=1.60.0`, `pytest` (dev)
- **gRPC endpoints required**: None at this stage (protos are copied but no client code uses them yet). All RPCs from `ForecastService` and `ConfigService` are defined in the proto files.
- **Build**: After this change, `python -m grpc_tools.protoc` produces working Python stubs from the proto files
