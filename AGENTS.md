# ha-njord

Home Assistant custom integration for the [njord](https://github.com/st0o0/njord)
weather service. Connects via gRPC streaming, creates native weather, sensor,
binary sensor, event, and button entities with real-time updates.

## Architecture

ha-njord is a **pure consumer** - it reads domain data and typed enrichments
from njord via gRPC streaming and presents them as Home Assistant entities.
There is no polling on the HA side; updates arrive in real time.

```
njord (gRPC server)  ──►  ha-njord (HA integration)
  GetManifest()               Entity definitions (manifest-driven)
  Subscribe()                 NjordV3Coordinator (entity stream)
  GetStatus()                 NjordStatusCoordinator (polling)
  TriggerPoll()               weather, sensor, binary_sensor,
                              button entities
```

Entity-first architecture: `GetManifest` returns entity definitions per location x feature, `Subscribe` streams `EntityStateUpdate`s per entity_id. Entities are created from the manifest via `entity_factory.py`; state updates are dispatched by entity_id. Generic per-OutputKind entity classes (`NjordV3AlertBinarySensor`, `NjordV3ScoreSensor`, etc.) replace per-feature entities. Adding a new feature in njord requires no ha-njord changes.

## Tech Stack

- Python 3.12+, grpcio, protobuf
- Proto stubs are generated and committed (no build step for end users)

## Key Commands

Dependency management is uv (`pyproject.toml` + committed `uv.lock`,
`[tool.uv] package = false` since this is a HA custom component, not a
distributable package).

```bash
# Run tests - native pytest fails on Windows (pytest-homeassistant-custom-component's
# event-loop fixtures assume a Unix event loop). On Linux/macOS, uv works directly:
uv sync --locked --all-extras
uv run pytest tests/ -v --tb=short

# Lint
uv run ruff format --check .
uv run ruff check .

# Or, from any platform (Docker: python:3.12-slim + uv):
docker run --rm -v "$PWD:/work" -w /work -e UV_PROJECT_ENVIRONMENT=/opt/venv python:3.12-slim \
  sh -c "pip install --quiet uv && uv sync --locked --all-extras && uv run pytest tests/ -v"

docker run --rm -v "$PWD:/work" -w /work -e UV_PROJECT_ENVIRONMENT=/opt/venv python:3.12-slim \
  sh -c "pip install --quiet uv && uv sync --locked --all-extras && \
  uv run ruff format --check . && uv run ruff check ."

# Generate proto stubs (Docker)
docker run --rm -v "$PWD:/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet 'grpcio-tools>=1.70,<1.79' 'protobuf>=5.0,<6.0' && \
  python -m grpc_tools.protoc \
    -Iprotos \
    --python_out=custom_components/njord/proto \
    --grpc_python_out=custom_components/njord/proto \
    protos/njord/njord.proto"
```

## Project Structure

```
custom_components/njord/
├── __init__.py          # Setup: client, coordinators, platforms, trigger_poll service
├── config_flow.py       # Config flow (host+port) + options flow (status poll interval)
├── coordinator.py       # NjordStatusCoordinator (status polling)
├── v3_coordinator.py    # NjordV3Coordinator (entity stream via Subscribe)
├── v3_entities.py       # Generic entity classes per OutputKind (alert, score, condition, trend, forecast, observation)
├── v3_weather.py        # Weather entity from EntityStateUpdate WeatherValue
├── entity_factory.py    # Manifest-driven entity creation per platform
├── sensor.py            # Server diagnostic sensors + v3 entity factory
├── binary_sensor.py     # v3 entity factory (alert binary sensors)
├── button.py            # Trigger poll button
├── calendar.py          # Calendar entity (stub, needs v3 rewrite)
├── grpc_client.py       # NjordClient: async gRPC wrapper (GetManifest, Subscribe, GetStatus, TriggerPoll)
├── models.py            # Frozen dataclasses (status, ManifestEntity, EntityState)
├── condition_mapper.py  # WMO weather_code + is_day -> HA condition string
├── helpers.py           # Device info, current sample picker
├── diagnostics.py       # HA diagnostics download
├── const.py             # DOMAIN, PollPhase, config constants
├── manifest.json        # HA integration metadata
├── strings.json         # English UI strings
├── translations/de.json # German UI strings
└── proto/               # Generated protobuf/gRPC stubs (njord: NjordService)

protos/njord/            # Source .proto file (synced from njord repo)
tests/                   # pytest tests
brand/                   # HACS brand assets (icon.png, logo.svg)
```

## Proto Management

Proto source files live in `protos/` and are synced from the
[njord](https://github.com/st0o0/njord) repo. When njord's protos change, copy
the files and regenerate stubs (see the proto command above). A GitHub Actions
workflow (`sync-protos.yml`) automates this on njord releases.

## Conventions

- **Git: NEVER `git push`** - the user pushes. Commit messages are Conventional
  Commits (commitlint-enforced).
- Versioning is release-please. Never edit version in `manifest.json` or
  `pyproject.toml` by hand.
- Tests use `pytest-homeassistant-custom-component` for full HA test fixtures.
- Ruff enforces formatting and linting (`pyproject.toml` config: line-length 120,
  rules E/F/I/UP).

## Security-sensitive areas

- `custom_components/njord/grpc_client.py` - gRPC connection to njord server
- `custom_components/njord/proto/` - generated protobuf stubs (synced from njord)
- `custom_components/njord/config_flow.py` - host/port configuration input

## Documentation

Full entity reference, dashboard examples, and automation recipes are in the
[njord docs](https://st0o0.github.io/njord/home-assistant/).
