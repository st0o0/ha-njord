## Why

The consensus weather entity appears stale in HA ("5 hours ago") even though the hourly refresh fires every hour. In newer HA versions, `async_write_ha_state()` only updates `last_updated` when the state or attributes actually change. On stable summer days where the condition stays "Sunny" and consensus attribute values (agreement, spread, available_models) are identical across adjacent horizons, the state write is a no-op and HA never advances the timestamp.

## What Changes

- Add `current_horizon` extra state attribute (e.g. `"h5"`) — changes every hour as the horizon offset advances, guaranteeing HA sees a state change
- Add `consensus_age_hours` extra state attribute — integer showing how many hours since njord computed the consensus, giving users visibility into data freshness

## Non-goals

- Changing how often njord computes consensus (server-side concern)
- Fixing the independent-median physical inconsistency (e.g. Sunny + 0.6mm) — that's a separate design question
- Adding new gRPC endpoints — no server changes needed

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `consensus-weather`: Add `current_horizon` and `consensus_age_hours` to extra state attributes

## Impact

- `custom_components/njord/weather.py` — `NjordConsensusWeatherEntity.extra_state_attributes`
- `tests/test_weather.py` — consensus attribute tests
- `openspec/specs/consensus-weather/spec.md` — add new attributes to spec
