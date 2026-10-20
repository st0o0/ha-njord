## Context

The server now sends one result per feature. A feature result replaces the previous result of the same feature, so no field-level merge is needed.

## Decisions

- **`Feature` StrEnum** with 36 members whose values are the proto oneof case names; `FEATURE_KEYS` maps each to the server key `<Category>:<Name>` (verified against njord `docs/data/features.json`). Alert features share their value with `AlertType`.
- **`FeatureData`** holds `location`, `feature`, `updated_at`, an optional `alert` (`AlertData`), an optional `score` (`ScoreData`) and `values` with native types. Platforms read `values` by key.
- **Gating**: `feature_enabled(feature, active)` is true when `active` is empty or None and otherwise compares case-insensitively with `FEATURE_KEYS`. The status coordinator feeds `active_enrichments` into the data coordinator and a change re-evaluates entity creation.
- **No toggles on the HA side**: the server decides; v2 entries migrate to v3 keeping `status_poll_interval`.
- **First refresh** uses `GetEnrichments(location)` as authoritative snapshot, the stream applies later events.
- **Alert clearing**: the server emits no severity-NONE event, so a cleared alert is only noticed on the next snapshot; accepted for now.
- **Unique ids** keep the format `{entry_id}_{location}_{key}`; `climate_anomaly` is renamed `seasonal_outlook`.

## Risks

- Stale alert state after a clear until reconnect or refresh.
- Extra per-feature attributes (frost expected low, gardening watering, seasonal months) are not exposed yet.
