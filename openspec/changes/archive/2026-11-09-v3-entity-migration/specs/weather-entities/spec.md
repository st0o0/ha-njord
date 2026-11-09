## MODIFIED Requirements

### Requirement: Weather entity per location
The integration SHALL create one HA weather entity per location. The weather entity SHALL be fed from v3 WeatherValue (via EntityStateUpdate on the Subscribe stream) instead of v2 DomainDataUpdate. It SHALL map WeatherValue fields to HA weather attributes (temperature, humidity, wind_speed, wind_bearing, pressure, condition).

#### Scenario: Weather entity updates from v3 stream
- **WHEN** an EntityStateUpdate with a WeatherValue arrives for location Vienna
- **THEN** the weather entity SHALL update its state attributes from the WeatherValue fields

#### Scenario: Hourly forecast from weather entity
- **WHEN** the weather entity provides an hourly forecast
- **THEN** it SHALL derive the forecast from the WeatherValue hourly data
