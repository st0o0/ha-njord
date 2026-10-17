## ADDED Requirements

### Requirement: Closed-set wire values are mapped from proto enums
The client SHALL map the proto enums for poll phase, trend direction, stability, dew point comfort and VPD category to typed Python values. `UNSPECIFIED` and unknown numbers SHALL map to an unspecified value, not raise.

#### Scenario: Target phase
- **WHEN** `GetTargets` returns a target with phase steady
- **THEN** the resulting `TargetData` has the steady phase value

#### Scenario: Optional comfort absent
- **WHEN** a horizon has no dew point comfort
- **THEN** the resulting `HorizonDerivedData.dewpoint_comfort` is `None`

#### Scenario: Unknown number
- **WHEN** a response carries an enum number the client does not know
- **THEN** it is mapped to the unspecified value without raising
