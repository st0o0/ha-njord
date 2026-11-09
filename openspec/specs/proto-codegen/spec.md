## Purpose

Defines how njord's protobuf/gRPC definitions are managed, compiled to Python stubs, and shipped with the integration.

## Requirements

### Requirement: Proto source files present
The project SHALL contain a copy of njord's proto definition at `protos/njord/njord.proto`.

#### Scenario: Proto file is present
- **WHEN** a developer inspects the `protos/njord/` directory
- **THEN** `njord.proto` is present and matches njord's current definition (package `njord`)

### Requirement: Python stub generation
The project SHALL document a reproducible command (Docker-based, see AGENTS.md) that generates Python gRPC stubs from the proto source file using `grpcio-tools`. `sync-protos.yml` runs the equivalent `protoc` invocation directly in CI.

#### Scenario: Successful codegen
- **WHEN** a developer runs the documented proto codegen command from the project root
- **THEN** `custom_components/njord/proto/njord/` contains `njord_pb2.py` and `njord_pb2_grpc.py`

#### Scenario: Generated stubs are importable
- **WHEN** a Python script imports `custom_components.njord.proto.njord.njord_pb2`
- **THEN** the import succeeds and the module contains the expected message classes (`ManifestRequest`, `EntityEvent`, `StatusRequest`, etc.)

### Requirement: Generated stubs committed
The generated Python stubs SHALL be committed to git so that end users installing via HACS do not need `grpcio-tools` or a build step.

#### Scenario: Clean install without build tools
- **WHEN** a user installs ha-njord via HACS (copies `custom_components/njord/` to their HA instance)
- **THEN** all proto-generated modules are present and importable without running codegen
