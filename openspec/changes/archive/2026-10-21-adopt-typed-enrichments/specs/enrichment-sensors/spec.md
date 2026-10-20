## REMOVED Requirements

### Requirement: Sensor entities have icons
**Reason**: Sensors are now defined per feature.
**Migration**: See `typed-enrichments`.

### Requirement: Sensor entities have translation keys
**Reason**: Sensors are now defined per feature.
**Migration**: See `typed-enrichments`.

### Requirement: Frost hours sensor
**Reason**: Frost is an alert feature with a binary sensor and event.
**Migration**: See `typed-enrichments`.

### Requirement: Frost confidence sensor
**Reason**: Frost is an alert feature with a binary sensor and event.
**Migration**: See `typed-enrichments`.

### Requirement: New sensors have translation keys
**Reason**: Sensors are now defined per feature.
**Migration**: See `typed-enrichments`.

### Requirement: Enrichment sensors are disabled by default
**Reason**: Availability follows the active enrichments of the server.
**Migration**: See `typed-enrichments`.

### Requirement: Trend sensor shows weather stability
**Reason**: The trend payload was replaced by the ConfidenceTrend and PollenTrend features.
**Migration**: See `typed-enrichments`.

### Requirement: Sensor entities support dynamic addition
**Reason**: Superseded by feature factories gated on active enrichments.
**Migration**: See `typed-enrichments`.
