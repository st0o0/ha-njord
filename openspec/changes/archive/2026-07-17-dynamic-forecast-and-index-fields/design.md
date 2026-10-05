## Context

Weather entities hardcode `_attr_supported_features = FORECAST_DAILY | FORECAST_HOURLY` as a class attribute. Models that only deliver hourly data (e.g., `knmi_harmonie_arome_netherlands`) show an empty forecast section in HA. Separately, the `IndexUpdate` proto has four fields (`hdd`, `cdd`, `frost_hours`, `frost_confidence`) that are never mapped into `IndexData` or exposed as sensors.

## Goals / Non-Goals

**Goals:**
- Weather entities only advertise forecast types they actually have data for
- Complete `IndexData` mapping from proto (all fields)
- Expose HDD, CDD, frost hours, and frost confidence as HA sensors

**Non-Goals:**
- Generating daily forecasts from hourly data (aggregation)
- Making consensus horizons dynamic from config
- Changing existing sensor behavior

## Decisions

### D1: Property-based supported_features

**Choice:** Replace `_attr_supported_features` class attribute with a `supported_features` property that checks `self._forecast_data`:

```python
@property
def supported_features(self) -> WeatherEntityFeature:
    features = WeatherEntityFeature(0)
    data = self._forecast_data
    if data and data.hourly:
        features |= WeatherEntityFeature.FORECAST_HOURLY
    if data and data.daily:
        features |= WeatherEntityFeature.FORECAST_DAILY
    return features
```

**Why property, not computed once at init?** Data arrives via streaming — a model might initially have no daily data, then get some on the next forecast update. The property re-evaluates each time HA asks, so features track reality.

**Alternative considered:** Setting the attribute in `_handle_coordinator_update`. Rejected — more code, same effect, and the coordinator update already triggers entity refresh which reads properties anyway.

### D2: New index sensors follow existing patterns

**Choice:** Add four sensors using the same patterns as existing enrichment sensors:

| Field | Sensor Name | Unit | Icon |
|---|---|---|---|
| `hdd` | Heating Degree Days | °C·d | `mdi:thermometer-chevron-up` |
| `cdd` | Cooling Degree Days | °C·d | `mdi:thermometer-chevron-down` |
| `frost_hours` | Frost Hours | h | `mdi:snowflake-thermometer` |
| `frost_confidence` | Frost Confidence | % | `mdi:snowflake-check` |

HDD and CDD are float values, frost_hours is int, frost_confidence is float (0.0-1.0, displayed as percentage after ×100).

## Risks / Trade-offs

**[supported_features evaluated every state read]** → Negligible cost. It checks two list lengths. HA caches entity state between updates anyway.

**[frost_confidence scale]** → Proto sends 0.0-1.0 but HA percentage sensors expect 0-100. We'll multiply by 100 in the sensor's `native_value`. This matches how alert confidence is stored (0.0-1.0 in the model).

## Open Questions

None.
