## Why

The same closed sets are spelled as string literals across many modules: enrichment groups in eight places, the 14 alert types in six parallel dicts, severity names plus a rank dict, stream names, option keys, sensor kinds. Typos fail silently and adding a value means touching every copy. njord's companion change `typed-wire-enums` turns six more string fields on the wire into proto enums (breaking, released together with ha-njord as 0.5.0), so the client has to consume enums anyway.

## What Changes

- **BREAKING (wire, via njord 0.5.0)**: sync `protos/njord/v2/{common,ops,admin}.proto` and regenerate stubs. `phase`, `direction`, `stability_label`, `dewpoint_comfort`, VPD `category` and consensus `method` arrive as proto enums. `grpc_client.py` maps them to Python enums; `UNSPECIFIED` and unknown numbers fall back to a safe default instead of failing.
- Add `StrEnum`s: `EnrichmentGroup`, `AlertType`, `AlertSeverity` (with `.rank`), `StreamName`, `SensorKind`, optionally `AlertEvent`, plus enums for the typed wire values (poll phase, trend direction, stability, dew point comfort, VPD category). All values stay identical to today's strings.
- `group_enabled(group, active, disabled)` helper replaces the repeated enablement gate in `sensor.py`, `event.py`, `binary_sensor.py`, `weather.py`.
- One metadata structure per `AlertType` replaces `ALERT_TYPES`, `ALERT_NAMES`, `ALERT_UNITS`, `ALERT_DEVICE_CLASSES`, `ALERT_PRECISION`, `ALERT_ICONS` and `_ALERT_TYPE_MAP`.
- `CONF_*` constants for option and config-entry keys (HA's `CONF_HOST` / `CONF_PORT` where they exist).
- `condition_mapper.py` uses HA's `ATTR_CONDITION_*` constants.
- A stored sensor-push kind that no longer exists is skipped instead of raising.

## Non-goals

- No change to entity ids, unique ids, translation keys, device identifiers or the stored options format (stored values stay plain strings, no migration).
- No enums for unique-id suffixes or translation keys (risk of orphaning registry entries, little gain).
- No new entities or attributes; sensors may declare `SensorDeviceClass.ENUM` options only where the value set is now closed.

## Capabilities

### New Capabilities

- `typed-domain-values`: closed value sets are typed, existing entity identity and states are unchanged, unknown wire values are tolerated, stale stored sensor kinds are skipped.

### Modified Capabilities

- `grpc-client`: maps the proto enums for poll phase, trend direction, stability, dew point comfort and VPD category (the consensus method enum is synced but not read by ha-njord).

## Impact

- `custom_components/njord/`: `const.py`, `helpers.py`, `models.py`, `grpc_client.py`, `coordinator.py`, `config_flow.py`, `sensor.py`, `event.py`, `binary_sensor.py`, `weather.py`, `diagnostics.py`, `condition_mapper.py`, `__init__.py`, `proto/` (regenerated).
- `protos/njord/v2/`, `tests/` (new `test_typed_values.py`, adjusted fixtures), `openspec/specs`.
- Depends on njord `typed-wire-enums` being implemented and its protos copied here; the two releases ship together as 0.5.0.

## gRPC Endpoints

No new RPCs. Existing and required: `WeatherService.GetForecast/StreamForecasts/StreamEnrichments/GetEnrichments`, `AdminService.GetConfig/StreamConfig`, `OpsService.GetStatus/GetTargets/TriggerPoll`, `SensorService.Push`. Changed messages: `ModelStatus`, `TriggerTarget`, `ParameterTrend`, trend/derived/VPD payloads and `ConsensusConfig` (string fields replaced by enums).
