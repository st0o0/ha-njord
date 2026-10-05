## Capability: consensus-weather

A weather entity per location that uses multi-model consensus values instead of a single model's forecast.

### Entity

| Entity ID | Platform | 
|-----------|----------|
| `weather.njord_{loc}_consensus` | weather |

### State Mapping

The entity's current state uses the `h3` horizon consensus values (nearest horizon). Falls back to next available horizon if h3 is missing.

| Weather attribute | Consensus parameter | Field used |
|-------------------|-------------------|------------|
| `temperature` | `temperature_2m` | `median` |
| `humidity` | `relative_humidity_2m` | `median` |
| `pressure` | `pressure_msl` | `median` |
| `wind_speed` | `wind_speed_10m` | `median` |
| `wind_bearing` | `wind_direction_10m` | `median` |
| `cloud_cover` | `cloud_cover` | `median` |
| `condition` | `weather_code` | `median` → WMO mapping |
| `visibility` | `visibility` | `median` |
| `dew_point` | `dew_point_2m` | `median` |
| `apparent_temperature` | `apparent_temperature` | `median` |
| `precipitation` | `precipitation` | `median` |

### Extra State Attributes

| Attribute | Source | Description |
|-----------|--------|-------------|
| `agreement` | consensus h3 temperature `agreement` | How well models agree (0.0–1.0) |
| `available_models` | consensus h3 `available_models` | Number of models contributing |
| `spread` | consensus h3 temperature `spread` | Temperature spread across models (°C) |

### Forecast Support

The consensus entity supports `forecast_hourly` and `forecast_daily` via HA's weather forecast service.

**Hourly forecasts**: Built from consensus data at each horizon (h3, h6, h12, h24, h48, h72, h96). Each entry includes the median values for temperature, precipitation, wind, cloud cover, humidity, and the agreement level.

**Daily forecasts**: Not directly available from consensus (which is horizon-based, not date-based). Options:
- Use the weighted_temperature from history as a summary
- Skip daily forecast support on the consensus entity (users can use per-model entities for daily)
- Derive daily values from horizon data mapping

Decision: Start without daily forecasts on the consensus entity. The per-model weather entities already provide daily forecasts.

### Data Source

- gRPC: `ForecastService.GetEnrichments(location)` → `ConsensusUpdate.parameters[]`
- Each `ParameterConsensus` has `parameter` (name), `unit`, and `by_horizon[]`
- Each `HorizonConsensus` has `horizon`, `median`, `trimmed_mean`, `spread`, `iqr`, `agreement`, `available_models`

### Files

- `custom_components/njord/weather.py` — add `NjordConsensusWeatherEntity` alongside existing `NjordWeatherEntity`
- `tests/test_weather.py` — consensus entity tests (may need separate test file if too large)
