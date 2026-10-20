# ha-njord

Home Assistant custom integration for the [njord](https://github.com/st0o0/njord)
weather service. Connects via gRPC streaming, creates native weather, sensor,
binary sensor, event, and button entities with real-time updates.

## Architecture

ha-njord is a **pure consumer** — it reads domain data and typed enrichments
from njord via gRPC streaming and presents them as Home Assistant entities.
There is no polling on the HA side; updates arrive in real time.

```
njord (gRPC server)  ──►  ha-njord (HA integration)
  StreamDomainData()          NjordDataCoordinator (streaming)
  StreamEnrichments()         weather, sensor, binary_sensor,
  GetDomainData()             event, button entities
  GetEnrichments()
  GetStatus()                 NjordStatusCoordinator (polling)
```

Domains: weather, air quality, flood, marine are tracked and get entities. The proto also carries seasonal and satellite (`DomainDataUpdate` oneof has weather, air_quality, flood, marine, satellite); they are not consumed.
Enrichments on the wire are typed per-feature `EnrichmentEvent`s (oneof `feature`: alerts, scores, conditions, trends, forecasts). Which features get entities follows `StatusResponse.active_enrichments` (`<Category>:<Name>` keys, see `FEATURE_KEYS` in `const.py`); an empty list means all enabled. There are no enrichment toggles on the HA side.

## Tech Stack

- Python 3.12+, grpcio, protobuf
- Proto stubs are generated and committed (no build step for end users)

## Key Commands

Dependency management is uv (`pyproject.toml` + committed `uv.lock`,
`[tool.uv] package = false` since this is a HA custom component, not a
distributable package).

```bash
# Run tests — native pytest fails on Windows (pytest-homeassistant-custom-component's
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
    protos/njord/v2/common.proto \
    protos/njord/v2/weather.proto \
    protos/njord/v2/ops.proto"
```

## Project Structure

```
custom_components/njord/
├── __init__.py          # Setup: client, coordinators, platforms, v1->v2->v3 migration, trigger_poll service
├── config_flow.py       # Config flow (host+port) + options flow (status poll interval)
├── coordinator.py       # NjordDataCoordinator (domain + typed feature streams) + NjordStatusCoordinator (polling)
├── weather.py           # One weather entity per location (weather domain, hourly forecast)
├── sensor.py            # Domain sensors (air quality, flood, marine) + server diagnostics
├── lifestyle.py         # Feature-keyed sensor and binary sensor descriptions (scores, conditions, trends, forecasts)
├── binary_sensor.py     # Feature binary sensors, alert binary sensors (one per active alert feature), stream connectivity
├── event.py             # Alert event entity (started, escalated, deescalated, cleared)
├── button.py            # Trigger poll button
├── grpc_client.py       # NjordClient: async gRPC wrapper (unary + reconnecting streams)
├── models.py            # Frozen dataclasses (domain data, alerts, FeatureData/ScoreData, status, catalog)
├── condition_mapper.py  # WMO weather_code + is_day -> HA condition string
├── helpers.py           # Device info, current sample picker
├── diagnostics.py       # HA diagnostics download
├── const.py             # DOMAIN, Domain, Feature/FEATURE_KEYS, AlertType (20), ALERT_META
├── manifest.json        # HA integration metadata
├── strings.json         # English UI strings
├── translations/de.json # German UI strings
└── proto/               # Generated protobuf/gRPC stubs (njord v2: common, weather, ops)

protos/njord/v2/         # Source .proto files (synced from njord repo)
tests/                   # pytest tests
brand/                   # HACS brand assets (icon.png, logo.svg)
```

## Proto Management

Proto source files live in `protos/` and are synced from the
[njord](https://github.com/st0o0/njord) repo. When njord's protos change, copy
the files and regenerate stubs (see the proto command above). A GitHub Actions
workflow (`sync-protos.yml`) automates this on njord releases.

## Conventions

- **Git: NEVER `git push`** — the user pushes. Commit messages are Conventional
  Commits (commitlint-enforced).
- Versioning is release-please. Never edit version in `manifest.json` or
  `pyproject.toml` by hand.
- Tests use `pytest-homeassistant-custom-component` for full HA test fixtures.
- Ruff enforces formatting and linting (`pyproject.toml` config: line-length 120,
  rules E/F/I/UP).

## Workflow

Changes go through OpenSpec: `/opsx:explore` to think → `/opsx:propose` to create
a change (proposal/design/specs/tasks) → `/opsx:apply` to implement → `/opsx:archive`.

## Documentation

Full entity reference, dashboard examples, and automation recipes are in the
[njord docs](https://st0o0.github.io/njord/home-assistant/).
