## Why

njord now accepts external sensor readings (indoor temperature, humidity) via a new gRPC SensorService to improve enrichment calculations. ha-njord should let users configure which HA sensors to forward to njord — per location, directly in the integration's Options Flow — so the feedback loop works without manual automation setup.

## What Changes

- **New Options Flow step** ("Sensor Push") with per-location entity selectors for indoor temperature and humidity sensors
- **State change listener** that automatically pushes configured sensor values to njord on every update via `SensorService.Push`
- **`njord.push_sensor` HA service** for manual/automation-driven pushes
- **UI strings** (EN + DE) for the new options step and service

## Non-goals

- No use of `StreamPush` (client-streaming) — unary `Push` per state change is sufficient given HA sensor update frequencies
- No throttle/debounce — HA sensors naturally report every 30s–5min, and gRPC unary calls are sub-millisecond
- No retry/queue on push failure — warn-log and drop; next reading arrives shortly
- No new entities or sensors created by this change

## Capabilities

### New Capabilities
- `sensor-push-options`: Options Flow step for configuring per-location sensor entity mappings
- `sensor-push-listener`: State change listener that forwards configured HA sensor readings to njord
- `sensor-push-service`: `njord.push_sensor` HA service for manual/automation sensor pushes

### Modified Capabilities
- `options-flow`: Adds a second step to the existing OptionsFlow for sensor push configuration
- `grpc-client`: Adds SensorService stub initialization on connect (Push RPC method already exists)

## Impact

- **config_flow.py**: New `async_step_sensors` in `NjordOptionsFlow`, dynamic schema from catalog locations × sensor kinds
- **__init__.py**: State listener registration/teardown, `push_sensor` service registration
- **grpc_client.py**: Minor — sensor stub already exists, but connect/close must be verified to include it
- **strings.json / translations/de.json**: New keys for sensor push step labels
- **No new dependencies** — uses existing grpcio, protobuf, HA core APIs
- **gRPC endpoints required**: `SensorService.Push` (exists in njord, proto + stubs already in ha-njord)
