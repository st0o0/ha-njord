## Why

njord now serves a v3 entity-first gRPC API (`GetManifest`, `Subscribe`, `GetStatus`, `TriggerPoll`) alongside v2. The v3 API is simpler: entities are defined by the server manifest (no hardcoded ALERT_META/FEATURE_KEYS), state updates arrive on a single unified stream with snapshot-on-connect and availability events, and value types are generic per OutputKind (7 types instead of 65 per-feature oneofs). ha-njord must migrate to v3 to consume the new Observation entities and future features without code changes on each addition.

## What Changes

### Phase 1: Proto + client foundation
- Copy v3 proto from njord, generate Python stubs
- Add v3 `NjordServiceStub` methods to `NjordClient` (alongside v2, not replacing yet)
- Add manifest and v3 models

### Phase 2: Manifest-driven entities
- Replace `ALERT_META`, `Feature` enum, `FEATURE_KEYS`, `DOMAIN_SENSOR_REGISTRY`, `LIFESTYLE_SENSORS` with manifest-driven entity creation
- Entities are created from `GetManifest` response: each entity definition carries platform, device_class, unit, entity_id
- Generic sensor per OutputKind instead of per-feature classes

### Phase 3: Unified stream
- Replace `StreamDomainData` + `StreamEnrichments` with single `Subscribe` stream
- Snapshot-on-connect replaces `GetDomainData` + `GetEnrichments` initial fetch
- Availability events replace stale-detection logic
- Coordinator simplification: one stream, one entity update path

### Phase 4: Cleanup
- Remove v2 proto stubs, v2 client methods, v2 models
- Remove per-feature entity classes, ALERT_META, Feature enum, FEATURE_KEYS
- Update tests to v3 models

## Non-goals

- Changing the weather platform entity (it stays as a composite HA weather entity, fed from v3 WeatherValue)
- Sensor push (stays on v2 or gets its own migration later)
- Options flow changes (feature toggles move server-side; options flow simplifies to connection settings)
- Config flow changes (host/port stays the same)

## Required gRPC endpoints

All exist in njord v3 (`protos/njord/v3/njord.proto`):
- `GetManifest` — entity definitions (existing)
- `Subscribe` — unified entity event stream (existing)
- `GetStatus` — system status (existing)
- `TriggerPoll` — trigger poll (existing)

## Capabilities

### New Capabilities

- `v3-manifest-entities`: Entity creation driven by server manifest instead of hardcoded metadata
- `v3-unified-stream`: Single Subscribe stream replacing dual v2 streams with snapshot-on-connect and availability

### Modified Capabilities

- `grpc-client`: Client adds v3 stub methods, later removes v2
- `stream-lifecycle`: Stream reconnection changes from 2 streams to 1
- `typed-enrichments`: Replaced by generic per-OutputKind value dispatch
- `alert-sensors`: Alert binary sensors driven by manifest + AlertValue instead of ALERT_META
- `weather-entities`: Weather entity fed from v3 WeatherValue instead of v2 DomainDataUpdate

## Impact

- Every file in `custom_components/njord/` is touched
- All tests rewritten for v3 models
- Proto stubs regenerated for v3
- Entity IDs must be preserved for migration (njord uses the same slug pattern)
- **Breaking**: requires njord with v3 API (the version being built in this session)
