# ha-njord

Home Assistant custom integration for the njord weather service. Connects via gRPC, creates native `weather` entities with hourly+daily forecast support.

## Architecture

ha-njord is a **pure consumer** — no config logic, no write access to njord. It reads forecasts and config via gRPC and displays them as HA weather entities.

```
njord (gRPC server)  ──►  ha-njord (HA integration)
  GetLocations()              Config Flow (Host+Port)
  GetModels()                 weather.njord_{loc}_{model}
  GetForecast()               DataUpdateCoordinator (5min)
  GetConfig()                 WMO → HA condition mapping
```

## Tech Stack

- Python 3.12+, grpcio, protobuf
- No local Python installed — all commands run via Docker (`python:3.12-slim`)
- Proto stubs are generated and committed (no build step for end users)

## Key Commands

```bash
# Generate proto stubs (Docker)
make proto

# Run tests (Docker)
make test

# Or explicitly:
docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet grpcio protobuf pytest pytest-asyncio voluptuous && python -m pytest tests/ -v"
```

## Project Structure

```
custom_components/njord/
├── __init__.py          # Integration setup (client + coordinator + platform forward)
├── config_flow.py       # Host+Port → gRPC validation → ConfigEntry
├── coordinator.py       # DataUpdateCoordinator (5min polling)
├── weather.py           # NjordWeatherEntity (state, attributes, forecasts)
├── grpc_client.py       # NjordClient — async gRPC wrapper with typed returns
├── models.py            # Frozen dataclasses (ForecastData, NjordConfigData, ...)
├── condition_mapper.py  # WMO weather_code + is_day → HA condition string
├── const.py             # DOMAIN, DEFAULT_PORT
├── manifest.json        # HA integration metadata
├── strings.json         # English UI strings
├── translations/de.json # German UI strings
└── proto/               # Generated protobuf/gRPC stubs
    └── njord/v1/        # forecast_service_pb2*.py, config_service_pb2*.py

protos/njord/v1/         # Source .proto files (copied from njord)
tests/                   # pytest tests (42 total)
```

## Proto Management

Proto files are **manually copied** from `D:\GIT\njord\protos\njord\v1\`. No submodule, no third repo. When njord's protos change, copy the files and run `make proto`.

## Conventions

- Git: commit conventionally, NEVER `git push` — the user pushes
- Tests run via Docker, not local Python
- HA module stubs in `tests/conftest.py` allow testing without homeassistant installed
- Config flow and weather platform tests that need full HA are `@pytest.mark.skip`

## Workflow

Changes go through OpenSpec: `/opsx:explore` to think, `/opsx:propose` to create a change (proposal/design/specs/tasks), `/opsx:apply` to implement, `/opsx:archive`.
