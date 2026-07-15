## Purpose

Defines how njord's protobuf/gRPC definitions are managed, compiled to Python stubs, and shipped with the integration.

## Requirements

### Requirement: Proto source files present
The project SHALL contain copies of njord's proto definitions at `protos/njord/v1/forecast_service.proto` and `protos/njord/v1/config_service.proto`.

#### Scenario: Proto files are present
- **WHEN** a developer inspects the `protos/njord/v1/` directory
- **THEN** both `forecast_service.proto` and `config_service.proto` are present and match njord's current definitions

### Requirement: Python stub generation
The project SHALL provide a Makefile target `make proto` that generates Python gRPC stubs from the proto source files using `grpcio-tools`.

#### Scenario: Successful codegen
- **WHEN** a developer runs `make proto` from the project root
- **THEN** `custom_components/njord/proto/njord/v1/` contains `forecast_service_pb2.py`, `forecast_service_pb2_grpc.py`, `config_service_pb2.py`, and `config_service_pb2_grpc.py`

#### Scenario: Generated stubs are importable
- **WHEN** a Python script imports `custom_components.njord.proto.njord.v1.forecast_service_pb2`
- **THEN** the import succeeds and the module contains the expected message classes (`GetLocationsRequest`, `GetForecastResponse`, `HourlyForecast`, etc.)

### Requirement: Generated stubs committed
The generated Python stubs SHALL be committed to git so that end users installing via HACS do not need `grpcio-tools` or a build step.

#### Scenario: Clean install without build tools
- **WHEN** a user installs ha-njord via HACS (copies `custom_components/njord/` to their HA instance)
- **THEN** all proto-generated modules are present and importable without running codegen
