<p align="center">
  <img src="brand/logo.svg" width="120" alt="njord" />
</p>

<h1 align="center">ha-njord</h1>

<p align="center">
  Home Assistant custom integration for the <a href="https://github.com/st0o0/njord">njord</a> weather intelligence service
</p>

<p align="center">
  <a href="https://github.com/st0o0/ha-njord/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.12+-3776ab" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/HACS-custom-41bdf5" alt="HACS" />
</p>

---

Connects to a [njord](https://github.com/st0o0/njord) instance via gRPC streaming and creates native Home Assistant entities for multi-domain weather intelligence. Data arrives in real time, with no polling delay on the HA side.

## Features

- **Multi-domain weather data.** Weather (Ensemble), Air Quality, Flood and Marine data as sensor entities per location
- **19 weather alerts.** Frost, heat, storm, UV, fog, pollen, PM2.5, flood risk, swimming conditions and more as `binary_sensor` entities with severity and trigger value
- **Lifestyle enrichments.** Laundry drying score, commute safety, ventilation window, exercise advisory, BBQ score, outdoor score and more as `sensor` entities
- **Alert events.** Event entity that fires on alert state changes
- **Air quality sensors.** PM2.5, PM10, ozone, birch/grass/alder/mugwort pollen per location
- **Flood monitoring.** River discharge sensor with flood risk alerts
- **Marine conditions.** Wave height, wave period, wave direction, water temperature
- **Server diagnostics.** API usage, poll state per location, gRPC stream connectivity
- **Manual poll trigger.** Button entity to trigger an immediate poll for a location
- **Enrichment-driven config.** Toggle individual enrichments in HA; njord derives which API domains to fetch

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
4. Choose which enrichments to enable (weather alerts, pollen, flood risk, lifestyle scores, etc.)

Entities appear immediately after setup. Locations are auto-discovered from the njord configuration. Coordinates are resolved automatically via geocoding.

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
    protos/njord/v2/ops.proto"
```

## License

MIT
