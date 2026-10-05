## Context

ha-njord is a read-only HA integration consuming njord's v2 gRPC API. Core functionality (weather entities, enrichments, streaming) is complete. This change addresses polish and diagnostics gaps before 1.0: incomplete DeviceInfo, missing OptionsFlow, no diagnostics download, invisible stream health, and unused `GetTargets()` endpoint.

Current state:
- DeviceInfo sets `manufacturer="njord"` everywhere but omits `sw_version` and `model`
- `button.py` has a minimal DeviceInfo that doesn't match `sensor.py`'s `_server_device_info` helper
- No OptionsFlow — only host+port at setup time
- No `diagnostics.py` — "Download Diagnostics" button is absent
- Stream failures are silent — no sensors, no HA repairs
- `GetTargets()` proto stubs exist but client method does not

## Goals / Non-Goals

**Goals:**
- Every HA device entry shows server version and model type
- Users can tune status poll interval and toggle enrichment groups after setup
- "Download Diagnostics" works and produces a useful debug snapshot
- Stream disconnects are visible via binary sensors and HA repair issues
- Per-model poll state from `GetTargets()` is available as diagnostic sensors

**Non-Goals:**
- AdminService write mutations
- Streaming reconnect strategy changes (exponential backoff stays as-is)
- Custom Lovelace cards or dashboards

## Decisions

### D1: DeviceInfo — pull sw_version from StatusCoordinator at entity init

The `NjordStatusCoordinator` already polls `GetStatus()` every 30s and has `server_version`. Rather than piping version through coordinator data events, entities read `status_coordinator.data.version` once during `__init__` and set it on `_attr_device_info`. This means version updates require an HA restart — acceptable since server upgrades are rare and restarting HA after upgrading njord is expected.

**Alternative considered**: Dynamic version update via `_handle_coordinator_update` — adds complexity for a field that changes once per deployment. Not worth it.

### D2: OptionsFlow — store options in ConfigEntry.options, apply on change

Two options:
1. `status_poll_interval` (int, seconds, default 30, range 10–300)
2. `disabled_enrichment_groups` (list of enrichment type strings, default empty)

The status coordinator reads poll interval from `entry.options`. Enrichment group toggles filter at entity creation time — disabled groups simply don't create entities. Changing enrichment toggles triggers a config entry reload to add/remove entities cleanly.

**Alternative considered**: Live entity add/remove without reload — complex and error-prone with HA's entity lifecycle. Reload is the standard HA pattern for this.

### D3: diagnostics.py — async_get_config_entry_diagnostics only

HA diagnostics supports two levels: config entry and device. Config entry level is sufficient — it can include all coordinator data, stream states, and server status in one dump. Device-level would duplicate most of the same data per location.

Sensitive fields: `host` is redacted via `async_redact_data`. Port is kept (not sensitive).

### D4: Stream health — coordinator tracks per-stream state, binary sensors observe it

Add a `stream_states: dict[str, bool]` to the coordinator (keys: `"forecast"`, `"enrichment"`, `"config"`). Each `_stream_with_reconnect` wrapper updates this dict on connect/disconnect. Binary sensors are `CoordinatorEntity` instances that read from `coordinator.stream_states`.

HA Repair issues: Created on disconnect (after a grace period of 60s to avoid flapping), dismissed on reconnect. Uses `homeassistant.helpers.issue_registry`.

### D5: GetTargets — new diagnostic sensors under server device

`GetTargets()` returns per-location/model poll state. Map each target to a diagnostic sensor showing last poll time, with status (ok/error/pending) as an attribute. These group under the server device alongside budget/uptime sensors. Fetched by the status coordinator alongside `GetStatus()`.

**Alternative considered**: Separate coordinator for targets — unnecessary overhead, status coordinator already polls on a suitable interval.

## Risks / Trade-offs

- **[OptionsFlow reload on enrichment toggle]** → Users see a brief "loading" state. Acceptable — this is standard HA behavior and happens only on explicit user action.
- **[Stream health binary sensors add entity count]** → 3 extra binary sensors per config entry (not per location). Minimal overhead. Marked as diagnostic category.
- **[GetTargets adds N sensors per location×model]** → Could be many sensors with many models. Mitigated by `entity_registry_enabled_default = False` — created but disabled by default, user enables what they need.
- **[sw_version static at entity init]** → Version shown in HA may lag after njord upgrade until HA restart. Low risk — users restart HA regularly and njord upgrades are infrequent.

## Open Questions

None — all decisions are straightforward applications of HA integration patterns.
