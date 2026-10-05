## Why

The Consensus weather entity always reads horizon `h0` for current state, regardless of how much time has passed since the enrichment data was computed. If njord pushed consensus at 14:00, then at 17:00 the entity still shows `h0` (the 14:00 value) instead of `h3` (the 17:00 value). This is the same stale-data problem that was fixed for model weather entities in the `hourly-state-advance` change, but for consensus the fix requires tracking elapsed time since enrichment computation.

The root cause: `EnrichmentData` has no `updated_at` timestamp. The `EnrichmentEvent` proto carries `updated_at` but the converter discards it.

## What Changes

- `EnrichmentData` model gains a `consensus_updated_at: datetime | None` field to track when consensus data was last computed.
- `_to_enrichment_event()` in `grpc_client.py` preserves `updated_at` from the proto when the payload is a `ConsensusUpdate`.
- `merge_enrichment()` in `coordinator.py` carries forward the timestamp when merging.
- `NjordConsensusWeatherEntity` calculates the elapsed hours since the consensus push and reads `h{elapsed}` instead of hardcoded `h0` for current state.
- Hourly forecast horizons shift accordingly — starting from `h{elapsed+1}` instead of `h1`.

## Capabilities

### New Capabilities

- `consensus-horizon-advance`: Time-aware horizon selection for consensus entity based on elapsed time since enrichment push.

### Modified Capabilities

- `consensus-weather`: Current state reads from time-adjusted horizon instead of `h0`. Forecast starts from adjusted offset.

## Impact

- `custom_components/njord/models.py`: Add `consensus_updated_at` field to `EnrichmentData`.
- `custom_components/njord/grpc_client.py`: `_to_enrichment_event()` and `_to_enrichment_data()` preserve `updated_at` for consensus payloads.
- `custom_components/njord/coordinator.py`: `merge_enrichment()` carries forward `consensus_updated_at`.
- `custom_components/njord/weather.py`: `NjordConsensusWeatherEntity` calculates elapsed hours and adjusts horizon lookups.
- Tests need updating for time-dependent consensus behavior.

## Non-goals

- Tracking `updated_at` for non-consensus enrichment types (alerts, indices, etc.) — only consensus uses horizon-relative data.
- Changing the njord gRPC API — the `updated_at` field already exists in `EnrichmentEvent`.

## gRPC Endpoints

All existing, no changes needed:

- `WeatherService.GetEnrichments` (unary) — already has `updated_at` fields per sub-message; needs investigation whether a top-level timestamp is usable.
- `WeatherService.StreamEnrichments` (server stream) — `EnrichmentEvent.updated_at` is the source.
