## MODIFIED Requirements

### Requirement: Frost hours sensor
The integration SHALL expose a Frost Hours sensor per location, sourced from `IndexData.frost.hours_until` (was `IndexData.frost_hours`). The sensor SHALL set `device_class = SensorDeviceClass.DURATION` and `native_unit_of_measurement = UnitOfTime.HOURS` with `suggested_display_precision = 0`.

#### Scenario: Frost hours sensor shows value
- **WHEN** enrichment data contains `frost = FrostData(hours_until=4, confidence=0.85)`
- **THEN** the sensor shows `4` with unit `h` and icon `mdi:snowflake-thermometer`

#### Scenario: Frost hours sensor shows None when not available
- **WHEN** enrichment data has indices but `frost` is None
- **THEN** the sensor shows unknown state

### Requirement: Frost confidence sensor
The integration SHALL expose a Frost Confidence sensor per location, sourced from `IndexData.frost.confidence` (was `IndexData.frost_confidence`), displayed as a percentage (0-100). The sensor SHALL use raw string unit `"%"` and `suggested_display_precision = 0`.

#### Scenario: Frost confidence sensor shows percentage
- **WHEN** enrichment data contains `frost = FrostData(hours_until=4, confidence=0.85)`
- **THEN** the sensor shows `85.0` with unit `%` and icon `mdi:snowflake-check`

#### Scenario: Frost confidence sensor shows None when not available
- **WHEN** enrichment data has indices but `frost` is None
- **THEN** the sensor shows unknown state

## RENAMED Requirements

### Requirement: Ventilation index sensor
- **FROM:** `ventilation` / "Ventilation Index"
- **TO:** `night_ventilation` / "Night Ventilation Index"

## REMOVED Requirements

### Requirement: Irrigation index sensor
**Reason**: The `irrigation` field has been removed from njord v2's `DayScoreSet` message. The proto no longer provides this score.
**Migration**: Users with automations referencing `sensor.*_irrigation_index` should remove them. The sensor was disabled by default, so impact is minimal.
