## MODIFIED Requirements

### Requirement: Weather entities register in HA
Weather entities SHALL be discoverable via `hass.states` after platform setup. Tests SHALL assert entity state and attributes through the HA state machine rather than by constructing entity instances directly.

#### Scenario: Weather entity appears in hass.states after setup
- **WHEN** `async_setup_entry` completes with a config entry
- **THEN** `hass.states.get("weather.njord_{location}_{model}")` returns a state object with condition, temperature, humidity, wind_speed, and pressure attributes

#### Scenario: Consensus weather entity appears alongside model entities
- **WHEN** `async_setup_entry` completes and enrichment data includes consensus
- **THEN** `hass.states.get("weather.njord_{location}_consensus")` returns a state object

#### Scenario: Alert binary sensors appear in hass.states
- **WHEN** `async_setup_entry` completes and enrichment data includes alerts
- **THEN** `hass.states.get("binary_sensor.njord_{location}_{type}_alert")` returns a state object with severity and confidence attributes

#### Scenario: Sensor entities appear in hass.states
- **WHEN** `async_setup_entry` completes and enrichment data includes indices
- **THEN** `hass.states.get("sensor.njord_{location}_{index}_index")` returns a state object with the index value
