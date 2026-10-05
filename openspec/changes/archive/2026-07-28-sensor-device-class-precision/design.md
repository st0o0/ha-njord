## Context

ha-njord's sensor entities use raw unit strings (`"°C"`, `"km/h"`, `"hPa"`) without `device_class`. Home Assistant only activates automatic unit conversion for sensor entities that have a recognized `device_class` paired with a `native_unit_of_measurement` from HA's unit constants. Without this, imperial/custom unit system users see metric values with no conversion.

The weather entity already works correctly — it uses `_attr_native_temperature_unit` etc., which HA converts automatically regardless of device_class.

## Goals / Non-Goals

**Goals:**
- Enable HA's automatic unit conversion for all sensor entities that report values in convertible units
- Set `suggested_display_precision` on all numeric sensors for consistent decimal formatting
- Use HA `UnitOf*` constants instead of raw strings for maintainability

**Non-Goals:**
- No config flow or options flow for unit selection — HA handles this globally
- No server-side changes to njord
- No changes to the weather entity
- No conversion for domain-specific units without HA device_class (°C·d, J/kg, UV index)

## Decisions

### 1. Use `SensorDeviceClass` + `UnitOf*` constants for convertible sensors

**Decision**: Set `device_class` and use HA unit constants on every sensor whose unit has a matching HA device class.

**Rationale**: This is HA's standard mechanism. Every major weather integration (met.no, OpenWeatherMap, AccuWeather) relies on this. Adding a custom config flow for units would be an anti-pattern.

**Alternative considered**: Custom unit conversion in ha-njord — rejected because it duplicates HA core functionality and risks double-conversion bugs.

### 2. Device class mapping

| Sensor type | device_class | native_unit |
|---|---|---|
| Alert: frost, heat | `TEMPERATURE` | `UnitOfTemperature.CELSIUS` |
| Alert: storm | `WIND_SPEED` | `UnitOfSpeed.KILOMETERS_PER_HOUR` |
| Alert: heavy_rain | `PRECIPITATION_INTENSITY` | — see Decision 4 |
| Alert: pressure_drop | `PRESSURE` | `UnitOfPressure.HPA` |
| Alert: fog | `DISTANCE` | `UnitOfLength.METERS` |
| Alert: snow | `DISTANCE` | `UnitOfLength.CENTIMETERS` |
| Diurnal amplitude | `TEMPERATURE` | `UnitOfTemperature.CELSIUS` |
| History (weighted temp) | `TEMPERATURE` | `UnitOfTemperature.CELSIUS` |
| VPD | `PRESSURE` | `UnitOfPressure.KPA` |

**No device_class** (domain-specific, no HA equivalent):
- Alert: uv (`"UV"` — no device class)
- Alert: thunderstorm (`"J/kg"` — no device class)
- HDD/CDD (`"°C·d"` — degree-days, no device class)
- Frost hours (`"h"` — duration, could use `DURATION` but hours are universal)
- All index sensors (`"%"` — 0-100 score, not a true percentage measurement)
- API Budget, Uptime, COP estimate — diagnostic/dimensionless

### 3. Precision defaults

| Value type | Precision | Rationale |
|---|---|---|
| Temperature (°C/°F) | 1 | Standard for weather display |
| Pressure (hPa/inHg) | 0 | Whole numbers standard |
| Wind speed (m/s, km/h, mph) | 1 | One decimal common |
| Distance (m, km) | 0 | Visibility is coarse |
| Precipitation (mm, in) | 1 | One decimal standard |
| VPD (kPa) | 2 | Small values (0.4–2.5) need precision |
| Percentage (%) | 0 | Whole numbers for scores |
| Degree-days (°C·d) | 1 | One decimal standard |
| Hours | 0 | Whole hours |
| COP | 1 | Values like 3.5 |

### 4. Alert precipitation unit

**Decision**: Use `SensorDeviceClass.PRECIPITATION_INTENSITY` if available in the HA version, otherwise keep raw `"mm"` string as fallback. The heavy_rain alert trigger_value represents a threshold in mm, which is a precipitation amount rather than intensity — but HA's `PRECIPITATION` device class expects cumulative values with `state_class`. Since alert sensors are stateless point-in-time values, using raw `"mm"` is acceptable.

**Revised decision**: Keep `"mm"` as raw string for heavy_rain alert. The alert value is a threshold, not a measurement that needs conversion.

### 5. Frost hours — use DURATION device class

**Decision**: Set `device_class=SensorDeviceClass.DURATION` with `UnitOfTime.HOURS`. This enables HA to display in the user's preferred time format while keeping the semantic meaning clear.

## Risks / Trade-offs

- **[Entity history discontinuity]** → Adding `device_class` may cause HA to re-interpret historical sensor data with unit conversion. Mitigation: This is a one-time visual shift, no data loss. Users who notice can clear entity history.
- **[VPD as PRESSURE]** → VPD is technically a pressure deficit, not atmospheric pressure. Using `PRESSURE` device class means HA might convert it to inHg for imperial users, which is semantically wrong for VPD. → Mitigation: Keep VPD without device_class, use raw `"kPa"` string. VPD is always discussed in kPa regardless of unit system.

## Open Questions

None — the approach follows established HA patterns used by all major weather integrations.
