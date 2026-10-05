## MODIFIED Requirements

### Requirement: Weather entities expose all standard attributes
Model weather entities SHALL expose `native_apparent_temperature` and `cloud_cover` properties in addition to existing attributes. All current-state properties SHALL read from the time-matched hourly entry (the last entry where `valid_at <= utcnow()`), not from `hourly[0]`.

#### Scenario: Weather card shows apparent temperature
- **WHEN** the weather entity is displayed in the HA weather card
- **THEN** apparent temperature is available as an attribute, sourced from the current-hour entry

#### Scenario: Weather card shows cloud cover
- **WHEN** the weather entity is displayed
- **THEN** cloud cover percentage is available as an attribute, sourced from the current-hour entry

#### Scenario: Current hour differs from first hourly entry
- **WHEN** the forecast was pushed at 14:00 and the current time is 17:00
- **THEN** temperature, condition, humidity, pressure, wind, and cloud cover reflect the 17:00 hourly entry
