# ha-njord

[![Release](https://img.shields.io/github/v/release/st0o0/ha-njord?sort=semver&style=flat-square)](https://github.com/st0o0/ha-njord/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776ab?style=flat-square)](https://www.python.org/)
[![HACS](https://img.shields.io/badge/HACS-custom-41bdf5?style=flat-square)](https://hacs.xyz/)

Home Assistant custom integration for the [njord](https://github.com/st0o0/njord) weather intelligence service. Connects via gRPC streaming and creates native Home Assistant entities for multi-domain weather intelligence. Data arrives in real time with no polling delay on the HA side.

## Features

- **89 features across 6 domains.** Forecast, Ensemble, Air Quality, Flood, Marine, and Seasonal data as native HA entities per location
- **30 weather alerts.** Frost, heat, storm, UV, fog, pollen, PM2.5, flood risk, swimming conditions, dust, fire risk, migraine risk, and more as `binary_sensor` entities with severity and trigger value
- **23 observation sensors.** PM2.5, PM10, ozone, pollen (birch/grass/alder/mugwort), UV index, flood discharge, wave height/period/direction, water temperature, soil moisture/temperature, snow depth, and more
- **23 condition sensors.** Commute safety, ventilation window, exercise advisory, gardening, atmospheric stability, heat pump COP, solar yield, irrigation need, and more
- **7 activity scores.** Laundry drying, BBQ, outdoor, sleep quality, allergy severity, asthma risk, spray window as `sensor` entities
- **4 forecast sensors.** Ensemble and forecast model comparison, seasonal outlook, growing degree days
- **Weather entity.** Native `weather` platform entity per location with hourly forecasts
- **Server diagnostics.** API usage, poll state per location, gRPC stream connectivity
- **Manual poll trigger.** Button entity to trigger an immediate poll for a location

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

Entities appear immediately after setup. Locations are auto-discovered from the njord configuration. Feature toggles are configured server-side in njord (environment variables or config file).

## Documentation

For the complete entity reference, dashboard examples, automation recipes, and configuration details, see the **[njord documentation](https://njord.st0o0.net/home-assistant/)**.

## Development

```bash
# Run tests (Docker, no local Python needed)
docker run --rm -v "$PWD:/work" -w /work -e UV_PROJECT_ENVIRONMENT=/opt/venv python:3.12-slim \
  sh -c "pip install --quiet uv && uv sync --locked --all-extras && uv run pytest tests/ -v"

# Regenerate proto stubs
docker run --rm -v "$PWD:/work" -w /work python:3.12-slim \
  sh -c "pip install --quiet 'grpcio-tools>=1.68.0' 'protobuf>=5.0,<6.0' && \
  python -m grpc_tools.protoc \
    -Iprotos \
    --python_out=custom_components/njord/proto \
    --grpc_python_out=custom_components/njord/proto \
    protos/njord/njord.proto"
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org/); releases are cut automatically by release-please.

## License

[MIT](LICENSE). Weather data from [Open-Meteo](https://open-meteo.com/) is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The data is enriched and transformed by [njord](https://github.com/st0o0/njord) before being displayed. Open-Meteo aggregates data from national weather services (DWD, ECMWF, NOAA, and [others](https://open-meteo.com/en/licence)) under their respective licences.
