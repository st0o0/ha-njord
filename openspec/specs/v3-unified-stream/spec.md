# v3-unified-stream Specification

## Purpose
Defines the unified entity stream that replaces the dual v2 domain/enrichment streams.

## Requirements

### Requirement: Single Subscribe stream replaces dual streams
The integration SHALL use one `Subscribe` RPC call instead of separate domain and enrichment streams. All entity state updates, availability events, and operational signals SHALL arrive on this single stream.

#### Scenario: All entity types on one stream
- **WHEN** the integration connects to njord
- **THEN** weather data, alert results, scores, conditions, trends, forecasts, and observations SHALL all arrive via the Subscribe stream

### Requirement: Snapshot on connect
When the Subscribe stream opens, the integration SHALL receive the current state of every entity as a batch of EntityStateUpdate messages before live updates. This SHALL replace separate initial fetch calls.

#### Scenario: Reconnect receives fresh state
- **WHEN** the integration reconnects after a disconnect
- **THEN** it SHALL receive a complete snapshot of all entity states before any live events

### Requirement: Availability events replace stale detection
The integration SHALL mark entities as unavailable when the server sends an EntityUnavailable event and available again on EntityAvailable. This SHALL replace client-side stale-detection timers.

#### Scenario: Entity becomes unavailable
- **WHEN** the server sends an EntityUnavailable for vienna_frost
- **THEN** the frost alert entity SHALL be marked as unavailable in HA
