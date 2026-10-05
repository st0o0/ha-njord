## Context

ha-njord is a greenfield Home Assistant custom integration. Before any feature work (gRPC client, config flow, weather entities) can begin, the project needs a Python project structure, an HA integration skeleton, proto files copied from njord, and a working codegen pipeline.

The proto definitions already exist in `D:\GIT\njord\protos\njord\v1\` — two files (`forecast_service.proto`, `config_service.proto`). These are manually copied (no submodule, no third repo) since both repos are maintained by the same developer.

## Goals / Non-Goals

**Goals:**
- Working `pyproject.toml` that declares runtime and dev dependencies
- Valid HA integration skeleton that HA Core can discover (manifest.json)
- Proto files present and Python stubs generatable via `grpcio-tools`
- Test infrastructure ready (pytest, conftest.py)
- HACS-installable structure (hacs.json)

**Non-Goals:**
- No functional integration code (no `async_setup_entry`, no entities)
- No CI/CD, no GitHub Actions
- No Docker setup
- No proto modifications — files are copied verbatim from njord

## Decisions

### 1. Project tooling: pyproject.toml only (no setup.py, no setup.cfg)

Modern Python standard. HA custom integrations don't need a build system per se, but `pyproject.toml` is the canonical place for metadata, dependencies, and tool config. Using `hatchling` as build backend since it's lightweight and zero-config.

Alternative considered: `setuptools` — more common historically but `pyproject.toml`-only is cleaner and HA core itself has moved this direction.

### 2. Codegen approach: Makefile target with grpcio-tools

`python -m grpc_tools.protoc` invoked from a simple Makefile target (`make proto`). Generated files go into `custom_components/njord/proto/` as a Python package (with `__init__.py`).

Alternative considered: `buf` (modern proto toolchain) — more powerful but adds a non-Python dependency. `grpcio-tools` is already a dev dependency and sufficient for two proto files.

Alternative considered: Pre-committed generated files vs. gitignored + generate-on-build. Decision: **commit the generated files**. This avoids requiring `grpcio-tools` at install time and matches how most HA custom integrations work (ship everything, no build step for end users).

### 3. Generated code location: `custom_components/njord/proto/`

Generated `_pb2.py` and `_pb2_grpc.py` live inside the integration package so HA can import them directly. The `protos/` directory at project root holds the source `.proto` files.

```
ha-njord/
├── protos/                          ← source .proto files (copied from njord)
│   └── njord/v1/
│       ├── forecast_service.proto
│       └── config_service.proto
├── custom_components/
│   └── njord/
│       ├── proto/                   ← generated Python stubs
│       │   ├── __init__.py
│       │   ├── njord/v1/
│       │   │   ├── forecast_service_pb2.py
│       │   │   ├── forecast_service_pb2_grpc.py
│       │   │   ├── config_service_pb2.py
│       │   │   └── config_service_pb2_grpc.py
│       │   └── ...
│       ├── __init__.py
│       ├── manifest.json
│       └── const.py
└── tests/
    └── conftest.py
```

### 4. Python version: 3.12+

Matches Home Assistant 2024.x+ requirements. Allows use of modern Python features (type hints with `|`, `match` statements).

### 5. manifest.json iot_class: "local_push"

Even though this scaffold doesn't implement streaming yet, the manifest declares the intended `iot_class` from the start. This matches the architectural vision (streaming, not polling).

## Risks / Trade-offs

- **[Proto drift]** → Proto files are manually copied from njord. If njord's protos change and ha-njord isn't updated, the generated stubs won't match the server. Mitigation: single developer controls both repos; codegen failure is an immediate signal.
- **[Generated files in git]** → Adds noise to diffs when protos change. Mitigation: acceptable for two files; keeps end-user install simple (no build step).
- **[grpcio version coupling]** → `grpcio` runtime version must be compatible with `grpcio-tools` version used for codegen. Mitigation: pin both to same major.minor range.
