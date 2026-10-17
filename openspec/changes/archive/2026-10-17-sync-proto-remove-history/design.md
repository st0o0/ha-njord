## Context

njord is the source of truth for the protos; ha-njord vendors them and commits generated stubs. The diff between the two repos is exactly: history messages/fields removed (field numbers reserved, so wire-compatible with older stubs) and two new `StatusResponse` bools (`budget_partial=7`, `models_partial=8`).

## Goals / Non-Goals

**Goals:** ha-njord matches njord's current proto; no dead History code or UI; no misleading budget values; no orphaned entities.

**Non-Goals:** see proposal.

## Decisions

1. **Remove History outright, no compatibility shim.** Matches the repo rule for entity-naming (no aliases). Alternative (keep the sensor but permanently unavailable) rejected: it can never become available.
2. **Registry cleanup at setup.** In `async_setup_entry` (before platforms are forwarded) iterate `er.async_entries_for_config_entry` and `async_remove` sensor entities whose `unique_id` ends with `_model_performance` (unique id is `{entry_id}_{location}_model_performance`). Alternative (leave it to the user) rejected: leaves permanent "unavailable" clutter.
3. **Stale `history` in `disabled_enrichment_groups`** is harmless for the platforms (they only test membership), but the options-flow default is intersected with the valid groups so the multi-select does not reject an unknown default value.
4. **Partial flags live on `ServerStatusData`** (`budget_partial: bool = False`, `models_partial: bool = False`), set in `_to_server_status`. `budget_partial` makes `NjordMonthlyUsageSensor` / `NjordDailyUsageSensor` unavailable (njord reports zero usage then, which is not a real measurement). `models_partial` only goes to diagnostics: targets come from `GetTargets`, not from `StatusResponse.models`, so entity creation is unaffected.
5. **Regenerate stubs with the documented Docker command** from `CLAUDE.md`; protos are copied from njord with LF line endings (the njord working copy has CRLF).

## Risks / Trade-offs

- Users with automations/dashboards on `sensor.*_model_performance` or the `model_*` weather attributes break → marked **BREAKING**, commit type `feat!:` so release-please notes it.
- The registry scan on each setup is negligible and becomes a no-op once cleaned.
- Older njord servers still sending history data: unknown fields are ignored by protobuf, so no crash.
