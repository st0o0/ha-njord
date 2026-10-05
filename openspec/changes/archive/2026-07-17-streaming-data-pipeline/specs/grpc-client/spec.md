## ADDED Requirements

### Requirement: Get enrichments
The client SHALL provide an async method to retrieve enrichment data for a given location, returning typed dataclasses.

#### Scenario: Successful retrieval
- **WHEN** `await client.get_enrichments(location)` is called
- **THEN** an `EnrichmentData` object is returned containing alerts, indices, trends, energy, derived, history, and consensus data for that location

### Requirement: Stream enrichments
The client SHALL provide an async iterator for real-time enrichment updates via server-streaming RPC.

#### Scenario: Receive updates
- **WHEN** `async for event in client.stream_enrichments()` is used
- **THEN** each iteration yields an `EnrichmentData` object containing only the changed enrichment type (partial payload)

#### Scenario: Filter by location
- **WHEN** `client.stream_enrichments(location="lucerne")` is called with a location
- **THEN** only enrichment updates for that location are received

#### Scenario: Reconnect on failure
- **WHEN** the enrichment stream disconnects
- **THEN** the client reconnects with exponential backoff, same as other streaming RPCs
