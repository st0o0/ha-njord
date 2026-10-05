## Context

The `NjordConsensusWeatherEntity` uses a horizon-offset mechanism: as hours pass since `consensus_updated_at`, it reads from progressively later horizons (h0→h1→h2...). An hourly refresh timer calls `async_write_ha_state()` at each hour boundary. However, in newer HA versions, if the resulting state and attributes are identical to the previous write, HA does not update `last_updated`. On stable weather days, temperature, condition, and the existing attributes (agreement, spread, available_models) can be identical across adjacent horizons, causing the entity to appear stale for hours.

## Goals / Non-Goals

**Goals:**
- Guarantee `last_updated` advances every hour by including at least one attribute that changes with the horizon offset
- Give users visibility into consensus freshness via explicit age/horizon attributes

**Non-Goals:**
- Changing njord's consensus computation frequency (server-side)
- Fixing independent-median inconsistencies (Sunny + precipitation)
- Adding new gRPC endpoints

## Decisions

### Decision: Add `current_horizon` and `consensus_age_hours` to extra_state_attributes

**Choice:** Two new attributes in `extra_state_attributes`:
- `current_horizon` (str, e.g. `"h5"`) — the horizon currently being read
- `consensus_age_hours` (int) — hours since consensus was computed

**Why:** `current_horizon` changes every hour by definition (it's derived from the offset), guaranteeing HA sees a state change. `consensus_age_hours` provides user-facing freshness information.

**Alternative considered:** Using `_attr_force_update = True` on the entity. This would force HA to always update `last_updated`, but it's a blunt instrument — it disables HA's deduplication optimization entirely and doesn't add useful information for the user.

**Alternative considered:** Adding only `current_horizon`. This solves staleness but doesn't tell the user *how old* the consensus data is. Both attributes are cheap and informative.

## Risks / Trade-offs

- [Minimal state bloat] → Two small attributes added to every consensus entity state. Negligible impact.
- [Horizon string format coupling] → `current_horizon` mirrors the internal `h{N}` format. If njord changes horizon naming, this attribute changes too. Acceptable since it's informational only.
