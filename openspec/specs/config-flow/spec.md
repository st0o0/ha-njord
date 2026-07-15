## Purpose

Defines the Home Assistant config flow for adding the njord integration — user input, connection validation, duplicate prevention, and UI translations.

## Requirements

### Requirement: Config flow user step
The integration SHALL provide a config flow with a user step that accepts host and port inputs for connecting to a njord instance.

#### Scenario: User enters valid connection
- **WHEN** a user enters a valid host and port and clicks connect
- **THEN** the flow validates the connection by calling `get_locations()` via gRPC and proceeds to the confirmation step

#### Scenario: User enters invalid connection
- **WHEN** a user enters a host/port where no njord instance is reachable
- **THEN** the flow displays a "cannot_connect" error and stays on the user step

#### Scenario: Default port
- **WHEN** the config flow form is displayed
- **THEN** the port field defaults to 8081

### Requirement: Config flow confirmation
The config flow SHALL show a confirmation step displaying discovered locations and models before creating the config entry.

#### Scenario: Successful setup
- **WHEN** the connection validation succeeds
- **THEN** the flow creates a ConfigEntry with the host and port, and the integration sets up

### Requirement: Prevent duplicate entries
The config flow SHALL prevent adding the same njord instance twice.

#### Scenario: Duplicate detection
- **WHEN** a user tries to add an integration with a host:port that already exists as a ConfigEntry
- **THEN** the flow aborts with an "already_configured" message

### Requirement: Config flow UI strings
The integration SHALL provide `strings.json` with English UI text and `translations/de.json` with German translations for the config flow.

#### Scenario: English text displayed
- **WHEN** HA is set to English
- **THEN** the config flow shows English labels and descriptions

#### Scenario: German text displayed
- **WHEN** HA is set to German
- **THEN** the config flow shows German labels and descriptions
