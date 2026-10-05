## MODIFIED Requirements

### Requirement: Unit of measurement per alert type

Each alert sensor SHALL have a `native_unit_of_measurement` based on its type:
- frost: `°C`
- heat: `°C`
- storm: `km/h`
- heavy_rain: `mm`
- uv: `UV`
- fog: `m`
- snow: `cm`
- pressure_drop: `hPa`
- thunderstorm: `J/kg`
- ice: `°C`
- wind_chill: `°C`
- visibility: `m`
- tropical_night: `°C`
- humidity: `%`

#### Scenario: Ice alert shows temperature unit

- **WHEN** the ice alert sensor is registered
- **THEN** its `native_unit_of_measurement` SHALL be `"°C"`

#### Scenario: Wind chill alert shows temperature unit

- **WHEN** the wind_chill alert sensor is registered
- **THEN** its `native_unit_of_measurement` SHALL be `"°C"`

#### Scenario: Visibility alert shows distance unit

- **WHEN** the visibility alert sensor is registered
- **THEN** its `native_unit_of_measurement` SHALL be `"m"`

#### Scenario: Tropical night alert shows temperature unit

- **WHEN** the tropical_night alert sensor is registered
- **THEN** its `native_unit_of_measurement` SHALL be `"°C"`

#### Scenario: Humidity alert shows percentage unit

- **WHEN** the humidity alert sensor is registered
- **THEN** its `native_unit_of_measurement` SHALL be `"%"`

### Requirement: Alert sensors enabled by default

Alert sensor entities SHALL have `_attr_entity_registry_enabled_default = True` (HA default).

#### Scenario: Alert sensors active after setup

- **WHEN** the integration is set up
- **THEN** all 14 alert sensor entities SHALL be registered and enabled
