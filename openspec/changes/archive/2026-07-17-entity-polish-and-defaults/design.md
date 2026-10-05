## Context

After switching to streaming, entities that fail to load during first refresh stay permanently unavailable until manual reload. HA caches `supported_features` at registration, making our dynamic property ineffective. And the integration creates ~30 entities per location, overwhelming users who only want weather data and alerts.

## Goals / Non-Goals

**Goals:**
- Entities never show "unavailable" just because first refresh was slow
- `supported_features` accurately reflects the model's data from the start
- Users see only weather + alerts by default; everything else is opt-in

**Non-Goals:**
- Retry logic or polling fallback for failed fetches
- Dynamic feature changes mid-session
- Per-entity enable/disable in config flow

## Decisions

### D1: Empty ForecastData stub on fetch failure

**Choice:** When `GetForecast` fails during first refresh, insert `ForecastData(location=loc, model=model, updated_at=0)` with empty hourly/daily lists. The entity starts as "available" with no current condition/temperature (shows "Unknown" state). When streaming delivers the real data, the entity updates normally.

**Why not keep it unavailable?** "Unavailable" in HA means "broken" — users file bugs. "Unknown" means "no data yet" — users wait. The streaming pipeline will deliver data within seconds.

### D2: Set supported_features at __init__ time

**Choice:** In `NjordWeatherEntity.__init__`, check the forecast data that was just loaded (from first refresh) and set `_attr_supported_features` based on whether `data.hourly` and `data.daily` are non-empty.

```python
def __init__(self, coordinator, entry, location, model):
    ...
    data = coordinator.data.forecasts.get((location, model))
    features = WeatherEntityFeature(0)
    if data and data.hourly:
        features |= WeatherEntityFeature.FORECAST_HOURLY
    if data and data.daily:
        features |= WeatherEntityFeature.FORECAST_DAILY
    self._attr_supported_features = features
```

**Why not keep the property?** HA's entity registry caches `supported_features` once. A property that returns different values confuses the cache. Setting it once at init aligns with HA's design.

### D3: Default-disabled via base class

**Choice:** Set `_attr_entity_registry_enabled_default = False` on `_NjordEnrichmentSensor` (base for all sensor entities). This disables all enrichment sensors by default. Alert binary sensors (`NjordAlertEntity`) keep the default `True`. `NjordInversionEntity` gets explicit `False`.

**Result:**

| Entity Type | Default Enabled |
|---|---|
| Weather (per model) | Yes |
| Weather Consensus | Yes |
| Alert Binary Sensors (9 types) | Yes |
| Inversion Binary Sensor | No |
| All Index Sensors (8 + VPD) | No |
| All Energy Sensors (5) | No |
| Trend, Sunshine, Diurnal, History | No |
| HDD, CDD, Frost Hours, Frost Confidence | No |

### D4: Weather entity `available` property

**Choice:** Add `available` property to `NjordWeatherEntity`:

```python
@property
def available(self) -> bool:
    return (
        self.coordinator.data is not None
        and (self._location, self._model) in self.coordinator.data.forecasts
    )
```

This returns `True` even when the forecast has empty hourly/daily (the stub case). The entity shows "Unknown" state instead of "unavailable".

## Risks / Trade-offs

**[Empty stub means "Unknown" state]** → Acceptable. HA shows "Unknown" which is honest — data hasn't arrived yet. Better than "unavailable" which implies a broken integration.

**[supported_features frozen at init]** → If a model starts with no daily data but later gets some via streaming, the entity won't offer daily forecasts until next HA restart. This is an edge case (models don't change their data shape mid-run) and acceptable.

## Open Questions

None.
