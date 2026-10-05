## REMOVED Requirements

### Requirement: Alert sensors show trigger values
**Reason**: Replaced by the `alert-events` event platform. Alert data is better modeled as events (things that happen) than as sensors (continuous state). The event entity fires typed events on alert transitions.
**Migration**: Users with automations on `sensor.njord_*_alert` entities must migrate to `event.njord_*_weather_alert` entity triggers using event types `alert_started`, `alert_escalated`, `alert_deescalated`, `alert_cleared`.

#### Scenario: Alert sensor no longer exists
- **WHEN** the integration is set up
- **THEN** no `NjordAlertSensor` entities are created

## MODIFIED Requirements

### Requirement: Trend sensor shows weather stability
The integration SHALL expose a Weather Trend sensor per location. The sensor's primary state SHALL be `weather_change_description` from `TrendData`. The `stability_label` SHALL be included as an extra state attribute alongside existing trend attributes (`precip_starts_in_hours`, `precip_ends_in_hours`, `temp_max_in_hours`, `temp_min_in_hours`, `reliable_hours`, `stability_ratio`, `decay_rate`, `parameter_trends`).

#### Scenario: Trend sensor shows weather description
- **WHEN** enrichment data contains `weather_change_description = "Rain starting in 3 hours, temperature dropping"`
- **THEN** the sensor state is `"Rain starting in 3 hours, temperature dropping"`

#### Scenario: Trend sensor shows stability label as attribute
- **WHEN** enrichment data contains `stability_label = "stable"` and `weather_change_description = "No significant changes expected"`
- **THEN** the sensor state is `"No significant changes expected"` and `extra_state_attributes` includes `{"stability_label": "stable"}`

#### Scenario: Trend sensor shows None when no description
- **WHEN** enrichment data has trends but `weather_change_description` is None
- **THEN** the sensor state is unknown

#### Scenario: Trend sensor unavailable without trend data
- **WHEN** enrichment data has no trends
- **THEN** the trend sensor is unavailable
