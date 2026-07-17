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

Connects to a [njord](https://github.com/st0o0/njord) instance via gRPC and creates native Home Assistant entities — weather forecasts, weather alerts, activity indices, energy optimization, and more.

## Features

- **Multi-model weather entities** — one `weather` entity per model (ICON, ECMWF, GFS, UKMO, Arpege, KNMI, DMI, MeteoSwiss, ...) with hourly + daily forecasts
- **Consensus entity** — multi-model median with agreement score and daily forecast
- **Weather alerts** — 9 alert types (frost, heat, storm, UV, fog, ...) as `binary_sensor` entities with severity and confidence
- **Activity indices** — BBQ, outdoor, running, cycling, laundry, irrigation, solar, ventilation (0–100%)
- **Energy optimization** — heating demand, COP estimate, battery strategy, shading, night cooling
- **Weather trends** — stability label, precipitation timing, reliable forecast hours
- **Derived metrics** — sunshine percentage, diurnal amplitude, temperature inversion
- **Model performance** — weighted temperature, per-model MAE and drift (diagnostic)

## Prerequisites

A running [njord](https://github.com/st0o0/njord) instance accessible via gRPC (default port 8081).

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/st0o0/ha-njord` as **Integration**
4. Search for "njord Weather" and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/njord` directory to your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **njord Weather**
3. Enter the host and gRPC port (default: 8081) of your njord instance
4. The integration auto-discovers all locations and models

## Entities

For each configured location, the integration creates:

| Platform | Entities | Description |
|----------|----------|-------------|
| `weather` | 1 per model + 1 consensus | Forecasts with hourly + daily views |
| `binary_sensor` | 9 alerts + 1 inversion | Weather warnings with severity/confidence |
| `sensor` | 8 indices + 1 VPD | Activity suitability scores (0–100%) |
| `sensor` | 5 energy | Heating, COP, shading, battery, night cooling |
| `sensor` | 1 trend | Weather stability and precipitation timing |
| `sensor` | 2 derived | Sunshine percentage, diurnal amplitude |
| `sensor` | 1 diagnostic | Model performance (weighted temperature) |

## Development

```bash
# Run tests (Docker, no local Python needed)
make test

# Regenerate proto stubs
make proto
```

## Architecture

```
njord (gRPC server, port 8081)
  │
  ├─ GetLocations / GetModels / GetForecast
  ├─ GetEnrichments (alerts, indices, trends, energy, derived, history, consensus)
  └─ StreamForecasts / StreamEnrichments
        │
        ▼
ha-njord (HA custom integration)
  ├─ Config Flow (host + port → gRPC validation)
  ├─ DataUpdateCoordinator (5 min polling)
  ├─ weather.* entities (per model + consensus)
  ├─ binary_sensor.* entities (alerts + inversion)
  └─ sensor.* entities (indices, energy, trends, derived, history)
```

## License

MIT
