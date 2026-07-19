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

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=st0o0&repository=ha-njord&category=integration)

1. Click the button above — or open HACS → three dots → **Custom repositories** → add `https://github.com/st0o0/ha-njord` as **Integration**
2. Search for "njord Weather" and install
3. Restart Home Assistant

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
| `binary_sensor` | 1 inversion | Temperature inversion detection |
| `sensor` | 9 alerts | Weather alerts with trigger values (UV, temp, wind, etc.) |
| `sensor` | 8 indices + 1 VPD | Activity suitability scores (0–100%) |
| `sensor` | 5 energy | Heating, COP, shading, battery, night cooling |
| `sensor` | 1 trend | Weather stability and precipitation timing |
| `sensor` | 2 derived | Sunshine percentage, diurnal amplitude |
| `sensor` | 1 diagnostic | Model performance (weighted temperature) |

## Entity Reference

### Weather Entities (`weather.*`)

Each location×model combination creates a `weather.njord_{location}_{model}` entity (e.g. `weather.njord_home_icon_d2`). Additionally, a `weather.njord_{location}_consensus` entity aggregates all models.

#### State (current conditions from first hourly entry)

| Attribute | Unit | Description |
|-----------|------|-------------|
| `state` | — | HA condition string mapped from WMO weather code (sunny, cloudy, rainy, etc.) |
| `temperature` | °C | Air temperature at 2m height |
| `apparent_temperature` | °C | Feels-like temperature accounting for wind and humidity |
| `humidity` | % | Relative humidity at 2m height |
| `pressure` | hPa | Mean sea level pressure |
| `wind_speed` | m/s | Wind speed at 10m height (displayed in km/h by HA unit conversion) |
| `wind_bearing` | ° | Wind direction in degrees (0=N, 90=E, 180=S, 270=W) |
| `cloud_cover` | % | Total cloud cover percentage |

#### Extra State Attributes (dynamic, from njord's extra parameters)

Any additional forecast parameters configured in njord appear as extra attributes on the entity. These are model- and configuration-dependent and may include values like `cape`, `uv_index`, `soil_moisture_0_to_10cm`, etc. They are passed through as-is from njord without transformation.

#### Hourly Forecast (via `weather.get_forecasts` service)

| Field | Unit | Description |
|-------|------|-------------|
| `datetime` | ISO 8601 | Forecast valid time |
| `native_temperature` | °C | Forecast temperature |
| `precipitation` | mm | Expected precipitation for this hour |
| `humidity` | % | Forecast relative humidity |
| `native_wind_speed` | m/s | Forecast wind speed |
| `wind_bearing` | ° | Forecast wind direction |
| `cloud_cover` | % | Forecast cloud cover |
| `condition` | — | HA condition string from WMO code |
| *(extra parameters)* | varies | Any extra parameters configured in njord (e.g. `cape`, `uv_index`) |

#### Daily Forecast (via `weather.get_forecasts` service)

| Field | Unit | Description |
|-------|------|-------------|
| `datetime` | ISO 8601 | Forecast date (midnight) |
| `native_temperature` | °C | Maximum temperature for the day |
| `native_templow` | °C | Minimum temperature for the day |
| `precipitation` | mm | Total precipitation sum for the day |
| `native_wind_speed` | m/s | Maximum wind speed for the day |
| `condition` | — | HA condition (from daily WMO code or midday fallback) |
| *(extra parameters)* | varies | Any extra parameters configured in njord |

#### Consensus Entity Attributes (`weather.njord_{location}_consensus`)

The consensus entity uses multi-model median values instead of a single model.

| Attribute | Unit | Description |
|-----------|------|-------------|
| `agreement` | 0–1 | Fraction of models that agree on the temperature direction (1.0 = perfect consensus) |
| `available_models` | count | Number of weather models contributing to the consensus |
| `spread` | °C | Temperature spread between models (lower = more agreement) |
| `reliable_hours` | h | Number of forecast hours where model agreement stays above 50% |

---

### Binary Sensor Entities (`binary_sensor.*`)

#### Temperature Inversion (`binary_sensor.njord_{location}_inversion`)

| Attribute | Description |
|-----------|-------------|
| `state` | `on` when a temperature inversion is detected (warm air above cold air) |

*Disabled by default — enable via entity registry if needed.*

---

### Sensor Entities (`sensor.*`)

#### Weather Alerts (`sensor.njord_{location}_{type}_alert`)

Nine alert sensors showing the actual trigger value as state. **Enabled by default.**

| Alert Type | Unit | What it measures |
|------------|------|-----------------|
| `frost_alert` | °C | Minimum forecast temperature (negative = frost) |
| `heat_alert` | °C | Maximum forecast temperature |
| `storm_alert` | km/h | Maximum wind gust speed |
| `heavy_rain_alert` | mm | Precipitation amount (hourly or daily) |
| `uv_alert` | UV | Maximum UV index |
| `fog_alert` | m | Minimum visibility |
| `snow_alert` | cm | Snowfall depth |
| `pressure_drop_alert` | hPa | Pressure change (3h) |
| `thunderstorm_alert` | J/kg | CAPE (convective available potential energy) |

State is `0.0` when no alert is active. The actual value (e.g. UV 8.5) is shown when the threshold is exceeded.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `severity` | string | Alert level: `none`, `yellow`, `orange`, `red` |
| `confidence` | 0–1 | How certain njord is about this alert |
| `threshold` | float | The configured threshold above which the alert fires |
| `peak_value` | float | Maximum forecast value if higher than current (only present when set) |
| `hours_until` | int | Hours until the condition occurs — 0 means now (only present when set) |
| `duration_hours` | int | How many hours the condition is expected to last (only present when set) |

---

#### Activity Indices, Energy, Trends, Derived (disabled by default)

All remaining enrichment sensors are **disabled by default** and must be enabled in the entity registry.

#### Activity Indices (0–100%)

Scores indicating how suitable current/forecast weather is for a given activity.

| Entity | What it measures |
|--------|-----------------|
| `sensor.njord_{loc}_laundry_index` | Suitability for drying laundry outdoors (wind, humidity, rain probability) |
| `sensor.njord_{loc}_outdoor_index` | General outdoor comfort (temperature, wind, precipitation, UV) |
| `sensor.njord_{loc}_running_index` | Running conditions (temperature, humidity, wind, precipitation) |
| `sensor.njord_{loc}_cycling_index` | Cycling conditions (wind, precipitation, temperature) |
| `sensor.njord_{loc}_bbq_index` | Barbecue-friendliness (rain, wind, temperature, cloud cover) |
| `sensor.njord_{loc}_irrigation_index` | Garden irrigation need (precipitation, evapotranspiration, soil moisture) |
| `sensor.njord_{loc}_solar_index` | Solar energy production potential (cloud cover, sunshine hours) |
| `sensor.njord_{loc}_ventilation_index` | Window ventilation benefit (outdoor vs indoor temp, humidity, air quality) |

#### Degree Days & Frost

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.njord_{loc}_hdd` | °C·d | Heating Degree Days — how much heating is needed (higher = colder day relative to base temp) |
| `sensor.njord_{loc}_cdd` | °C·d | Cooling Degree Days — how much cooling is needed (higher = warmer day relative to base temp) |
| `sensor.njord_{loc}_frost_hours` | h | Number of forecast hours with temperature below 0°C |
| `sensor.njord_{loc}_frost_confidence` | % | Confidence (0–100%) that frost will actually occur |

#### VPD (Vapour Pressure Deficit)

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.njord_{loc}_vpd` | kPa | Vapour Pressure Deficit — the drying power of the air. Important for greenhouses and plant health. |

**Attributes:**

| Attribute | Description |
|-----------|-------------|
| `category` | Qualitative label: `low`, `optimal`, `high`, `critical` |

#### Energy Optimization

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.njord_{loc}_heating_demand` | % | Relative heating demand (0–100%). Higher = more heating needed. |
| `sensor.njord_{loc}_cop_estimate` | — | Estimated heat pump Coefficient of Performance at current outdoor temperature. Higher = more efficient. |
| `sensor.njord_{loc}_shading` | % | Recommended shading level (0=none, 100=full shade) based on solar radiation and indoor temperature. |
| `sensor.njord_{loc}_battery_strategy` | — | Recommended home battery action: `charge`, `hold`, or `discharge` based on solar forecast and pricing. |
| `sensor.njord_{loc}_night_cooling` | % | Benefit of night ventilation cooling (0–100%). High values mean opening windows overnight saves energy. |

**COP Estimate extra attributes:**

| Attribute | Description |
|-----------|-------------|
| `cop_optimal` | List of optimal COP hours: `[{hours_from_now, cop}]` — best times to run the heat pump |

#### Weather Trend

| Entity | Value | Description |
|--------|-------|-------------|
| `sensor.njord_{loc}_weather_trend` | string | Stability label: `stable`, `changing`, `volatile` |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `precip_starts_in_hours` | int | Hours until precipitation begins (absent if not expected) |
| `precip_ends_in_hours` | int | Hours until precipitation ends (absent if already dry) |
| `temp_max_in_hours` | int | Hours until daily temperature peak |
| `temp_min_in_hours` | int | Hours until daily temperature minimum |
| `reliable_hours` | int | How many forecast hours ahead are considered reliable |
| `stability_ratio` | float | 0–1 ratio of forecast consistency (1.0 = very stable) |
| `decay_rate` | float | Rate at which forecast reliability decreases over time |
| `parameter_trends` | list | Per-parameter trend info: `[{parameter, direction, delta}]` |

#### Derived Metrics

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.njord_{loc}_sunshine_pct` | % | Estimated sunshine percentage for the forecast period based on cloud cover |
| `sensor.njord_{loc}_diurnal_amplitude` | °C | Temperature difference between daily max and min — large values indicate clear continental weather |

#### Model Performance (Diagnostic)

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.njord_{loc}_model_performance` | °C | Weighted ensemble temperature — the consensus-weighted forecast temperature across all models |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `models` | list | Per-model metrics: `[{model, mae_7d, mae_30d, weight, drift}]` |
| `seasonal_best` | string | Which model performs best for the current season |
| `anomaly` | bool | Whether current conditions are anomalous compared to historical data |
| `anomaly_deviation` | float | How far (°C) current conditions deviate from the historical norm |

**Model metrics explained:**

| Field | Description |
|-------|-------------|
| `mae_7d` | Mean Absolute Error over last 7 days (°C) — recent accuracy |
| `mae_30d` | Mean Absolute Error over last 30 days (°C) — longer-term accuracy |
| `weight` | Ensemble weight (0–1) assigned to this model — higher = more trusted |
| `drift` | Systematic bias (°C) — positive means the model runs too warm |

---

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
