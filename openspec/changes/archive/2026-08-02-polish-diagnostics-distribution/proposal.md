## Why

ha-njord's core integration is functionally complete — all v2 WeatherService endpoints are consumed, all 7 enrichment types are mapped, and streaming is operational. However, several standard HA integration qualities are missing: device registry entries lack server version and model info, there's no `diagnostics.py` for troubleshooting, stream health is invisible to users, the `GetTargets()` endpoint isn't consumed, and there's no OptionsFlow for post-setup configuration. These gaps prevent a confident 1.0 release.

## What Changes

**Polish:**
- Populate `sw_version` (from `GetStatus()`) and `model` on all `DeviceInfo` entries
- Unify `button.py`'s DeviceInfo to use the same helper as `sensor.py`
- Add `OptionsFlow` with two settings: status poll interval and enrichment group toggles (client-side enable/disable per enrichment type)

**Diagnostics:**
- Add `diagnostics.py` (HA standard "Download Diagnostics" support) dumping config, coordinator state, stream status, and server status
- Add stream health tracking: `binary_sensor` per stream (forecast/enrichment/config) showing connected/disconnected + HA Repair issue on prolonged disconnect
- Implement `GetTargets()` client method and expose per-location/model poll state as diagnostic sensors

**Distribution:**
- No changes needed — hacs.json, README, CI, release automation, and CHANGELOG are already in place

## Capabilities

### New Capabilities
- `device-info-enrichment`: Populate `sw_version` and `model` on all DeviceInfo entries, unify button.py device info
- `options-flow`: Post-setup OptionsFlow with status poll interval and enrichment group toggles
- `diagnostics-download`: HA-standard `diagnostics.py` for config entry and device diagnostics
- `stream-health`: Binary sensors for stream connection state + HA Repair issues on disconnect
- `get-targets`: Consume `OpsService.GetTargets()` and expose poll state as diagnostic sensors

### Modified Capabilities
- `status-coordinator`: Needs to expose `sw_version` for DeviceInfo consumption
- `stream-lifecycle`: Needs to track and expose per-stream connection state

## Impact

- **Files modified**: `__init__.py`, `coordinator.py`, `config_flow.py`, `weather.py`, `sensor.py`, `binary_sensor.py`, `button.py`, `grpc_client.py`, `models.py`, `strings.json`, `translations/de.json`
- **Files added**: `diagnostics.py`, `repairs.py` (or inline in coordinator)
- **gRPC endpoints**: `GetTargets()` (new), `GetStatus()` (already consumed, data reused for DeviceInfo)
- **HA APIs**: `OptionsFlowHandler`, `diagnostics` platform, `repairs` integration, `BinarySensorEntity`
- **No breaking changes**

## Non-goals

- AdminService write mutations (SetLocations, SetSettings, SetEnrichment, SetBudget) — ha-njord remains read-only
- Additional language translations beyond EN/DE
- UI dashboards or Lovelace cards
- Server-side configuration from HA
