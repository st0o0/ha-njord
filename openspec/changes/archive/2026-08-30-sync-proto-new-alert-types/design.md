## Context

ha-njord creates alert sensor entities for each alert type njord supports. The alert type registry is a set of parallel dicts in `sensor.py` (ALERT_TYPES, ALERT_NAMES, ALERT_UNITS, etc.) that map string type keys to HA metadata. njord upstream added 5 new AlertType enum values and expanded AlertConfig — ha-njord needs to sync the protos and extend the registry.

## Goals / Non-Goals

**Goals:**
- Sync proto files so generated stubs match njord's current API
- Add all 5 new alert types with correct HA metadata so they appear as sensor entities

**Non-Goals:**
- Refactoring the alert registry pattern (parallel dicts work fine for 14 types)
- Exposing or reading AlertConfig threshold values (ha-njord reads alerts from forecast data)
- Adding translations for new alert types beyond English (German can follow later)

## Decisions

### 1. New alert type metadata

| Type | Unit | Device Class | Icon | Precision |
|------|------|-------------|------|-----------|
| `ice` | `°C` | `TEMPERATURE` | `mdi:snowflake-thermometer` | 1 |
| `wind_chill` | `°C` | `TEMPERATURE` | `mdi:thermometer-minus` | 1 |
| `visibility` | `m` | `DISTANCE` | `mdi:eye-off` | 0 |
| `tropical_night` | `°C` | `TEMPERATURE` | `mdi:weather-night` | 1 |
| `humidity` | `%` | `HUMIDITY` | `mdi:water-percent` | 0 |

**Rationale:** Units and device classes match what njord reports. Icons chosen from MDI set to be visually distinct and semantically clear.

### 2. Proto sync: full file copy

Copy `admin.proto` and `common.proto` from `D:\GIT\njord\protos\njord\v2\` and regenerate stubs with `make proto`. No cherry-picking of individual fields — keep protos identical to upstream.

**Alternative considered:** Patching only the changed lines. Rejected because partial sync creates drift risk.

### 3. ops.proto whitespace normalization

The diff shows ops.proto differs only in line endings/whitespace. Copy it too for consistency — the generated stubs won't change.

## Risks / Trade-offs

- [New alert types arrive with no data] → Sensors show `0.0` (native_value from trigger_value=0.0) which is the existing behavior for inactive alerts. No special handling needed.
- [Proto field number conflicts] → Not a risk since we copy upstream protos verbatim. Field numbers are managed by njord.
