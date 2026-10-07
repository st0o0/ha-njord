<p align="center">
  <img src="brand/logo.svg" width="120" alt="njord" />
</p>

<h1 align="center">ha-njord</h1>

<p align="center">
  Home Assistant custom integration for the <a href="https://github.com/st0o0/njord">njord</a> weather service
</p>

<p align="center">
  <a href="https://github.com/st0o0/ha-njord/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.12+-3776ab" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/HACS-custom-41bdf5" alt="HACS" />
</p>

---

Connects to a [njord](https://github.com/st0o0/njord) instance via gRPC streaming and creates native Home Assistant entities: weather forecasts, alerts, activity indices, trends, derived metrics, and more. Data arrives in real time, with no polling delay on the HA side.

## Features

- **Multi-model weather entities.** One `weather` entity per model (ICON, ECMWF, GFS, UKMO, MeteoSwiss, ...) with hourly and daily forecasts
- **Consensus entity.** Multi-model median with agreement score and daily forecast
- **14 weather alerts.** Frost, heat, storm, UV, fog, ice, wind chill, humidity, and more as `sensor` entities with severity and confidence
- **Alert events.** Event entity that fires on alert state changes (started, escalated, deescalated, cleared)
- **8 activity indices.** BBQ, outdoor, running, cycling, laundry, irrigation, solar, night ventilation (0 to 100%)
- **Derived metrics.** Sunshine percentage, diurnal amplitude, Beaufort scale, wind chill, dewpoint comfort, temperature inversion
- **Weather trends.** Stability label, precipitation timing, reliable forecast hours
- **Model performance.** Weighted temperature, per-model MAE and drift (diagnostic)
- **Server diagnostics.** API usage, version, uptime, per-target poll state, gRPC stream connectivity
- **Manual poll trigger.** Button entity to trigger an immediate forecast poll

## Prerequisites

A running [njord](https://github.com/st0o0/njord) instance accessible via gRPC (default port 8081).

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=st0o0&repository=ha-njord&category=integration)

1. Click the button above, or open HACS > three dots > **Custom repositories** > add `https://github.com/st0o0/ha-njord` as **Integration**
2. Search for "njord Weather" and install
3. Restart Home Assistant

### Manual

Copy the `custom_components/njord` directory to your Home Assistant `config/custom_components/` directory and restart.

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **njord Weather**
3. Enter the host and gRPC port (default: 8081) of your njord instance
4. The integration auto-discovers all locations and models

Entities appear immediately after setup. Many enrichment sensors are disabled by default; enable them via the entity registry.

## Documentation

For the complete entity reference, dashboard examples, automation recipes, and configuration details, see the **[njord documentation](https://st0o0.github.io/njord/home-assistant)**.

## Development

```bash
# Run tests (Docker, no local Python needed)
docker run --rm -v "$PWD:/work" -w /work -e UV_PROJECT_ENVIRONMENT=/opt/venv python:3.12-slim \
  sh -c "pip install --quiet uv && uv sync --locked --all-extras && uv run pytest tests/ -v"

# Regenerate proto stubs
docker run --rm -v "$PWD:/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet 'grpcio-tools>=1.70,<1.79' 'protobuf>=5.0,<6.0' && \
  python -m grpc_tools.protoc \
    -Iprotos \
    --python_out=custom_components/njord/proto \
    --grpc_python_out=custom_components/njord/proto \
    protos/njord/v2/common.proto \
    protos/njord/v2/weather.proto \
    protos/njord/v2/admin.proto \
    protos/njord/v2/ops.proto \
    protos/njord/v2/sensor.proto"
```

## License

MIT
