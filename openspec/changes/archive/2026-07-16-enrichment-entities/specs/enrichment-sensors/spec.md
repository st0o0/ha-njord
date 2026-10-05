## Capability: enrichment-sensors

Sensor entities for njord enrichment data: indices, energy, trends, derived metrics, and model history.

### Index Sensors (8 per location)

| Entity ID | State | Unit | 
|-----------|-------|------|
| `sensor.njord_{loc}_laundry_index` | 0–100 | % |
| `sensor.njord_{loc}_outdoor_index` | 0–100 | % |
| `sensor.njord_{loc}_running_index` | 0–100 | % |
| `sensor.njord_{loc}_cycling_index` | 0–100 | % |
| `sensor.njord_{loc}_bbq_index` | 0–100 | % |
| `sensor.njord_{loc}_irrigation_index` | 0–100 | % |
| `sensor.njord_{loc}_solar_index` | 0–100 | % |
| `sensor.njord_{loc}_ventilation_index` | 0–100 | % |

### VPD Sensor (1 per location)

| Entity ID | State | Unit | Attributes |
|-----------|-------|------|------------|
| `sensor.njord_{loc}_vpd` | float (kPa) | kPa | `category` ("optimal", "low", "high") |

### Energy Sensors (5 per location)

| Entity ID | State | Unit | Attributes |
|-----------|-------|------|------------|
| `sensor.njord_{loc}_heating_demand` | 0–100 | % | — |
| `sensor.njord_{loc}_cop_estimate` | float | — | `cop_optimal` (list of {hours_from_now, cop}) |
| `sensor.njord_{loc}_shading` | 0–100 | % | — |
| `sensor.njord_{loc}_battery_strategy` | string | — | — |
| `sensor.njord_{loc}_night_cooling` | 0–100 | % | — |

`battery_strategy` values: `"discharge"`, `"charge"`, `"hold"`

### Trend Sensor (1 per location)

| Entity ID | State | Attributes |
|-----------|-------|------------|
| `sensor.njord_{loc}_weather_trend` | `stability_label` (string) | `precip_starts_in_hours`, `precip_ends_in_hours`, `temp_max_in_hours`, `temp_min_in_hours`, `reliable_hours`, `stability_ratio`, `decay_rate`, `parameter_trends` |

### Derived Sensors (2 sensors + 1 binary_sensor per location)

| Entity ID | Type | State | Unit |
|-----------|------|-------|------|
| `sensor.njord_{loc}_sunshine_pct` | sensor | float | % |
| `sensor.njord_{loc}_diurnal_amplitude` | sensor | float | °C |
| `binary_sensor.njord_{loc}_inversion` | binary_sensor | on/off | — |

Per-horizon derived data (beaufort, dewpoint_comfort, wmo_description) is exposed as attributes on the corresponding weather entities, not as separate sensors.

### History Sensor (1 diagnostic per location)

| Entity ID | State | entity_category | Attributes |
|-----------|-------|----------------|------------|
| `sensor.njord_{loc}_model_performance` | `weighted_temperature` (float, °C) | diagnostic | `models` (list of {model, mae_7d, mae_30d, weight, drift}), `seasonal_best`, `anomaly`, `anomaly_deviation` |

### Data Sources

All data comes from `ForecastService.GetEnrichments(location)`:
- Indices: `GetEnrichmentsResponse.indices` → `IndexUpdate`
- Energy: `GetEnrichmentsResponse.energy` → `EnergyUpdate`
- Trends: `GetEnrichmentsResponse.trends` → `TrendUpdate`
- Derived: `GetEnrichmentsResponse.derived` → `DerivedUpdate`
- History: `GetEnrichmentsResponse.history` → `HistoryUpdate`

### Files

- `custom_components/njord/sensor.py` — platform setup + entity classes
- `custom_components/njord/binary_sensor.py` — inversion entity added alongside alerts
- `tests/test_sensor.py` — state, attributes, unavailability, edge cases
