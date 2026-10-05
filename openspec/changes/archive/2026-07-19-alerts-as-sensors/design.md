## Context

Alerts are currently `binary_sensor` entities (on/off) with severity and trigger values as attributes. Now that njord provides rich numeric values (`trigger_value`, `threshold`, `peak_value`), a sensor with the numeric value as state is more useful — it enables graphing, threshold automations, and glanceable dashboards.

## Goals / Non-Goals

**Goals:**
- Replace alert binary_sensors with sensor entities
- State = `trigger_value` (numeric, graphable)
- Unit per alert type for proper HA display
- Severity and timing info as attributes

**Non-Goals:**
- Keeping binary_sensors alongside sensors (redundant)
- Changing inversion entity (stays binary_sensor)
- Adding device_class (no standard HA device class fits all alert types)

## Decisions

### 1. State = trigger_value

**Decision**: `native_value` returns `alert.trigger_value`. When severity is "none", the value is 0.0.

**Why**: Makes the sensor graphable. A UV sensor showing 0 → 3 → 6 → 8.5 over time tells a story. Users can automate on `states('sensor.njord_home_uv_alert') | float > 6`.

**Alternative**: State = severity string — rejected because not graphable and less useful for automations.

### 2. Unit mapping per alert type

**Decision**: Static map from alert type to unit string:

| Alert Type | Unit | Meaning |
|------------|------|---------|
| frost | °C | Temperature |
| heat | °C | Temperature |
| storm | km/h | Wind gust speed |
| heavy_rain | mm | Precipitation |
| uv | UV | UV index |
| fog | m | Visibility |
| snow | cm | Snow depth |
| pressure_drop | hPa | Pressure change |
| thunderstorm | J/kg | CAPE energy |

**Why**: Proper units make HA display correct labels and enable unit conversion.

### 3. Sensors enabled by default

**Decision**: Alert sensors are enabled by default (unlike other enrichment sensors which are disabled).

**Why**: Alerts are important safety information. Same behavior as the current binary_sensors.

### 4. Icon reuse

**Decision**: Keep the same icon mapping from the current binary_sensor implementation.

### 5. Breaking change approach

**Decision**: Remove binary_sensors entirely in one step. No deprecation period.

**Why**: This is a pre-1.0 integration with likely very few users. Clean break is simpler than maintaining both.

## Risks / Trade-offs

- **Breaking existing automations** → Users with automations on `binary_sensor.njord_*_alert` will need to update them. Mitigation: pre-1.0, documented in changelog.
- **0.0 state when inactive** → Sensor shows 0.0 instead of "no alert". Mitigation: Users can use severity attribute to distinguish "no alert" from "value is literally 0". HA graphs will show a flat 0 line during quiet periods which is fine.
- **Mixed units across alerts** → Each alert sensor has a different unit, which could be confusing in grouped views. Mitigation: Each entity's name and icon clearly identifies what it measures.
