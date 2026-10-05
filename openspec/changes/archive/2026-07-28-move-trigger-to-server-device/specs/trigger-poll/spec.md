## MODIFIED Requirements

### Requirement: Trigger poll button entity
The integration SHALL create one `NjordTriggerPollButton` button entity per config entry that triggers a full forecast poll on njord via `OpsService.TriggerPoll("", "")`. The button entity SHALL be assigned to the Server device (identifier `{entry_id}_server`) alongside diagnostic sensors.

#### Scenario: Button press triggers poll
- **WHEN** the user presses the "Trigger Poll" button in the HA UI
- **THEN** the integration calls `OpsService.TriggerPoll(location="", model="")` and the button's `triggered_count` attribute reflects the server's response

#### Scenario: Button shows last trigger result
- **WHEN** a poll has been triggered
- **THEN** the button entity exposes `triggered_count` and `last_triggered` as extra state attributes

#### Scenario: Button available when connected
- **WHEN** the gRPC client is connected
- **THEN** the button entity is available

#### Scenario: Button belongs to Server device
- **WHEN** the button entity is created
- **THEN** its `DeviceInfo.identifiers` SHALL match the Server device `(DOMAIN, "{entry_id}_server")`
- **AND** no standalone device is created for the button
