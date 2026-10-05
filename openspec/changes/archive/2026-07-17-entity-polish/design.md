## Context

After deploying ha-njord to a real HA instance, three categories of polish issues were identified from live testing. The integration functions correctly but presents poorly in the HA dashboard.

## Goals / Non-Goals

**Goals:**
- Every sensor and binary_sensor has a recognizable MDI icon
- Weather entities show forecast cards (hourly + daily) in the HA weather card
- Alert icons visually indicate the alert type
- Entity names are translatable via HA's translation system

**Non-Goals:**
- No EntityDescription dataclass refactor — use `_attr_icon` directly (simpler, fewer entities don't justify the pattern overhead)
- No entity_id changes (would break existing automations)

## Decisions

### 1. Icons via `_attr_icon`, not EntityDescription

The HA EntityDescription pattern is useful when you have many entities with the same class but different descriptions. We already have separate entity classes per type (NjordIndexSensor, NjordEnergySensor, etc.), so adding `_attr_icon` directly is simpler and avoids a refactor.

### 2. Icon mapping

```
Sensors:
  laundry_index    → mdi:tshirt-crew
  outdoor_index    → mdi:pine-tree
  running_index    → mdi:run
  cycling_index    → mdi:bike
  bbq_index        → mdi:grill
  irrigation_index → mdi:sprinkler
  solar_index      → mdi:solar-power
  ventilation_index→ mdi:air-filter
  vpd              → mdi:water-percent
  heating_demand   → mdi:radiator
  cop_estimate     → mdi:heat-pump
  shading          → mdi:blinds
  battery_strategy → mdi:battery-charging
  night_cooling    → mdi:weather-night
  weather_trend    → mdi:trending-up
  sunshine_pct     → mdi:white-balance-sunny
  diurnal_amplitude→ mdi:thermometer-lines
  model_performance→ mdi:chart-line

Alerts:
  frost            → mdi:snowflake-alert
  heat             → mdi:thermometer-alert
  storm            → mdi:weather-hurricane
  heavy_rain       → mdi:weather-pouring
  uv               → mdi:sun-wireless
  fog              → mdi:weather-fog
  snow             → mdi:snowflake
  pressure_drop    → mdi:gauge-low
  thunderstorm     → mdi:weather-lightning
  inversion        → mdi:arrow-collapse-vertical
```

### 3. Weather forecast fix

The forecast methods return valid data, but the issue is likely:
- Missing `condition` key in forecast entries when `weather_code` is None
- The Consensus entity only declares `FORECAST_HOURLY` — should also compute daily from horizon data
- Missing `native_apparent_temperature` and `cloud_cover` on the main weather entity — these are expected by the HA weather card

### 4. Translation keys

Use HA's `translation_key` system with `strings.json` entity section. This allows proper localization without changing entity_id.

```json
{
  "entity": {
    "sensor": {
      "bbq_index": { "name": "BBQ Index" },
      ...
    },
    "binary_sensor": {
      "frost_alert": { "name": "Frost Alert" },
      ...
    }
  }
}
```

## Risks / Trade-offs

**[Icon selection is subjective]** → Using standard MDI icons that match the most obvious meaning. Users can override in HA customize.

**[Translation key change]** → Adding `translation_key` changes how HA resolves entity names. Need to verify existing entity names don't break.
