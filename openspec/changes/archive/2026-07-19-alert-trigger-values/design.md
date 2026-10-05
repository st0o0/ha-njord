## Context

njord's `Alert` message was extended with 5 new fields:
```protobuf
message Alert {
  AlertType type = 1;
  AlertSeverity severity = 2;
  double confidence = 3;
  double trigger_value = 4;       // always set when alert active
  double threshold = 5;           // always set when alert active
  optional double peak_value = 6; // only if different from trigger
  optional int32 hours_until = 7; // 0 = now, >0 = future
  optional int32 duration_hours = 8;
}
```

ha-njord's `AlertData` currently only has `type`, `severity`, `confidence`. The `NjordAlertEntity` binary sensor exposes severity and confidence as `extra_state_attributes`.

## Goals / Non-Goals

**Goals:**
- Parse all new alert fields into `AlertData`
- Expose them as `extra_state_attributes` on the binary sensor
- Enable HA templates/automations like `{{ state_attr('binary_sensor.njord_home_uv_alert', 'trigger_value') }}`

**Non-Goals:**
- Unit labels per alert type (would require alert-type-aware logic; keep it simple)
- Separate sensor entities per value
- Changing the is_on logic

## Decisions

### 1. All fields on AlertData, no filtering

**Decision**: Add all 5 fields directly to `AlertData`. `trigger_value` and `threshold` are non-optional (default 0.0 when alert is inactive/severity=none). `peak_value`, `hours_until`, `duration_hours` are optional.

**Why**: Matches the proto exactly. When severity is "none", trigger_value/threshold will be 0.0 — this is fine because the binary sensor is off anyway and attributes are informational.

### 2. Flat extra_state_attributes

**Decision**: Add all new fields directly to the existing `extra_state_attributes` dict alongside severity and confidence.

**Why**: Keeps it simple, all alert info in one place. Users already access attributes via `state_attr()`. No nesting needed.

### 3. Omit None values from attributes

**Decision**: Only include optional fields (peak_value, hours_until, duration_hours) in attributes when they have a value. Don't show `"peak_value": null`.

**Why**: Cleaner attribute display in HA UI. Automations can use `state_attr(..., 'peak_value') | default` pattern.

## Risks / Trade-offs

- **0.0 values when alert inactive** → `trigger_value` and `threshold` will be 0.0 from proto defaults when no alert is firing. Acceptable because the binary sensor is off and attributes are secondary.
- **No unit context** → User sees `trigger_value: 8.5` but doesn't know it's UV index vs °C without checking the alert type. Mitigation: Users know which entity they're looking at (e.g. `uv_alert`). Could add unit mapping later if needed.
