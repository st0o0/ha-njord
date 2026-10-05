## Context

The Consensus weather entity reads horizon `h0` for current state and `h1..hN` for forecasts. These horizons are relative to when njord computed the consensus — `h0` means "now at computation time", `h3` means "3 hours after computation". But the entity always reads `h0` regardless of how much real time has passed since the computation, causing stale values.

The `EnrichmentEvent` proto has an `updated_at` field that both converters (`_to_enrichment_data` and `_to_enrichment_event`) currently ignore. This timestamp is the key to computing which horizon represents "now".

## Goals / Non-Goals

**Goals:**
- Consensus entity shows the horizon that matches the current time, not always `h0`
- Forecast horizons shift accordingly
- Extra state attributes (agreement, spread, reliable_hours) reflect the current horizon

**Non-Goals:**
- Tracking `updated_at` for non-consensus enrichment types
- Changing the unary `GetEnrichments` response — it has no top-level `updated_at`, so we use `datetime.now(UTC)` as a reasonable approximation (the response is fresh)
- Handling the case where elapsed hours exceeds available horizons (entity becomes unavailable, same as no data)

## Decisions

### 1. Store `consensus_updated_at` on `EnrichmentData`

**Decision:** Add `consensus_updated_at: datetime | None = None` to `EnrichmentData`.

**Why not a separate tracking dict in the coordinator?** Keeping it on the model is simpler — `merge_enrichment` already handles field-level merges, and the timestamp naturally travels with the consensus data.

**Why only for consensus?** Other enrichment types (alerts, indices, trends, energy) don't use relative horizons. Their values are absolute and don't shift with time.

### 2. Populate from both code paths

**Stream path (`_to_enrichment_event`):** Use `pb.updated_at` from the `EnrichmentEvent` proto — this is the authoritative computation timestamp.

**Unary path (`_to_enrichment_data`):** Use `datetime.now(UTC)` since `GetEnrichmentsResponse` has no top-level `updated_at`. The response is fetched fresh, so "now" is a close enough approximation.

### 3. `merge_enrichment` carries forward the timestamp

**Decision:** When a consensus event is merged, its `consensus_updated_at` replaces the existing one. For non-consensus events, the existing `consensus_updated_at` is preserved.

This works naturally with the current merge logic: `consensus_updated_at` is only set when the event carries consensus data (non-default), and `_ENRICHMENT_MERGE_FIELDS` + `_ENRICHMENT_DEFAULTS` already handle selective field merging. We add `consensus_updated_at` to both.

### 4. Horizon offset calculation

**Decision:** A helper method `_current_horizon_offset()` calculates `int((now - consensus_updated_at).total_seconds() // 3600)`, clamped to 0.

The entity then uses:
- Current state: `h{offset}` instead of `h0`
- Extra attributes: agreement/spread from `h{offset}`
- Hourly forecast: starts at `h{offset+1}` instead of `h1`
- Daily forecast: same shift applied
- Reliable hours: counted from `h{offset}` instead of `h0`

### 5. Graceful degradation when offset exceeds available horizons

**Decision:** If `h{offset}` doesn't exist in the consensus data, `_get_horizon_value` returns `None` and the entity shows "Unknown". This is correct — the consensus data is too old to be useful.

## Risks / Trade-offs

- **[Risk] Clock skew between njord and ha-njord** → Minor issue. Even with 1-2 minutes skew, `// 3600` (floor division) means the horizon only shifts at full hour boundaries. Acceptable.

- **[Risk] `GetEnrichmentsResponse` has no `updated_at`** → Using `datetime.now(UTC)` is slightly inaccurate if the response is cached or delayed. In practice, the unary call only happens at startup; after that, the stream provides authoritative timestamps.

- **[Trade-off] Single timestamp vs per-enrichment-type timestamps** → We only track consensus because it's the only type with relative horizons. If future enrichment types need timestamps, extend then.
