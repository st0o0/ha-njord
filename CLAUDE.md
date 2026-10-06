# ha-njord

Home Assistant custom integration for the [njord](https://github.com/st0o0/njord)
weather service. Connects via gRPC streaming, creates native weather, sensor,
binary sensor, event, and button entities with real-time updates.

## Architecture

ha-njord is a **pure consumer** — it reads forecasts, enrichments, and config
from njord via gRPC streaming and presents them as Home Assistant entities.
There is no polling on the HA side; updates arrive in real time.

```
njord (gRPC server)  ──►  ha-njord (HA integration)
  StreamForecasts()           NjordCoordinator (streaming)
  StreamEnrichments()         weather, sensor, binary_sensor,
  StreamConfig()              event, button entities
  GetStatus()                 NjordStatusCoordinator (polling)
  Push() (sensors)            Sensor push (state listener)
```

## Tech Stack

- Python 3.12+, grpcio, protobuf
- Proto stubs are generated and committed (no build step for end users)

## Key Commands

Dependency management is uv (`pyproject.toml` + committed `uv.lock`,
`[tool.uv] package = false` since this is a HA custom component, not a
distributable package).

```bash
# Run tests — native pytest fails on Windows (pytest-homeassistant-custom-component's
# event-loop fixtures assume a Unix event loop), so this project runs tests via
# `make test` (Docker: python:3.12-slim + uv) on Windows. On Linux/macOS, uv works directly:
uv sync --locked --all-extras
uv run pytest tests/ -v --tb=short

# Lint
uv run ruff format --check .
uv run ruff check .

# Or, from any platform:
make test
make lint

# Generate proto stubs (Docker)
make proto
```

## Project Structure

```
custom_components/njord/
├── __init__.py          # Setup: client, coordinators, platforms, sensor push, options listener
├── config_flow.py       # Config flow (host+port) + options flow (enrichments, sensor push, poll interval)
├── coordinator.py       # NjordCoordinator (streaming) + NjordStatusCoordinator (polling)
├── weather.py           # Weather entities (per-model + consensus with horizon advance)
├── sensor.py            # Sensors: alerts, indices, VPD, frost, trend, derived, model perf, server diag
├── binary_sensor.py     # Binary sensors: inversion, stream connectivity
├── event.py             # Alert event entity (started, escalated, deescalated, cleared)
├── button.py            # Trigger poll button
├── grpc_client.py       # NjordClient — async gRPC wrapper (unary + streaming)
├── models.py            # Frozen dataclasses (ForecastData, EnrichmentData, ...)
├── condition_mapper.py  # WMO weather_code + is_day → HA condition string
├── horizon.py           # Horizon offset helper
├── helpers.py           # Device info helper
├── diagnostics.py       # HA diagnostics download
├── const.py             # DOMAIN, DEFAULT_PORT
├── manifest.json        # HA integration metadata
├── strings.json         # English UI strings
├── translations/de.json # German UI strings
└── proto/               # Generated protobuf/gRPC stubs (njord v2)

protos/njord/v2/         # Source .proto files (synced from njord repo)
tests/                   # pytest tests (223 total, 18 skipped without gRPC server)
brand/                   # HACS brand assets (icon.png, logo.svg)
```

## Proto Management

Proto source files live in `protos/` and are synced from the
[njord](https://github.com/st0o0/njord) repo. When njord's protos change, copy
the files and run `make proto`. A GitHub Actions workflow (`sync-protos.yml`)
automates this on njord releases.

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
