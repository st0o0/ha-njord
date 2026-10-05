## Capability: enrichment-alerts

Weather alert binary_sensor entities derived from njord's enrichment alert data.

### Entities

9 `binary_sensor` entities per location, one per alert type:

| Entity ID | Alert Type | device_class |
|-----------|-----------|--------------|
| `binary_sensor.njord_{loc}_frost_alert` | FROST | safety |
| `binary_sensor.njord_{loc}_heat_alert` | HEAT | safety |
| `binary_sensor.njord_{loc}_storm_alert` | STORM | safety |
| `binary_sensor.njord_{loc}_heavy_rain_alert` | HEAVY_RAIN | safety |
| `binary_sensor.njord_{loc}_uv_alert` | UV | safety |
| `binary_sensor.njord_{loc}_fog_alert` | FOG | safety |
| `binary_sensor.njord_{loc}_snow_alert` | SNOW | safety |
| `binary_sensor.njord_{loc}_pressure_drop_alert` | PRESSURE_DROP | safety |
| `binary_sensor.njord_{loc}_thunderstorm_alert` | THUNDERSTORM | safety |

### State

- `on` when `severity != NONE` (i.e., yellow, orange, or red)
- `off` when `severity == NONE`

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `severity` | str | `"none"`, `"yellow"`, `"orange"`, `"red"` |
| `confidence` | float | 0.0–1.0, how confident njord is in the alert |

### Data Source

- gRPC: `ForecastService.GetEnrichments(location)` → `AlertUpdate.alerts[]`
- Each `Alert` message has `type` (enum), `severity` (enum), `confidence` (double)
- Protobuf enums map: `ALERT_SEVERITY_NONE`→"none", `ALERT_SEVERITY_YELLOW`→"yellow", etc.
- `ALERT_TYPE_FROST`→"frost", `ALERT_TYPE_HEAT`→"heat", etc.

### Files

- `custom_components/njord/binary_sensor.py` — platform setup + `NjordAlertEntity`
- `tests/test_binary_sensor.py` — entity state, attribute mapping, unavailability
