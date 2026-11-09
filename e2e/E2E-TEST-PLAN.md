# E2E Test Plan -- njord + ha-njord

Agent-orchestrated end-to-end test against a real Docker stack.
gRPC path only (no MQTT). Real Open-Meteo API.

## Section Index

| Section | Name | Steps | Agent |
|---------|------|-------|-------|
| S0 | Stack Setup | 5 | Opus |
| S1 | HA Onboarding + Token | 8 | Opus |
| S2 | Integration Setup | 6 | Opus |
| S3 | Entity Registration | 5 | Opus |
| S4 | NjordService: GetManifest | 6 | Haiku #1 |
| S5 | NjordService: Subscribe (Entity Stream) | 5 | Haiku #1 |
| S6 | Entity Attribute Depth | 15 | Haiku #1 |
| S7 | Server Entities | 7 | Haiku #2 |
| S8 | NjordService: GetStatus | 6 | Haiku #2 |
| S9 | gRPC + REST Error Handling | 5 | Haiku #2 |
| S10 | HA Browser: Weather + Entity Cards | 8 | Haiku #3 |
| S11 | Multi-Cycle: TriggerPoll x 2 | 6 | Opus |
| S12 | Budget Tracking Across Cycles | 4 | Opus |
| S13 | Resilience: Container Restart | 7 | Opus |
| S14 | Teardown: Integration Removal | 5 | Opus |
| | **Total** | **~91** | |

---

## Stack

| Service | Image | Ports | Notes |
|---------|-------|-------|-------|
| njord | Built from repo Dockerfile | 8080 (HTTP), 8081 (gRPC) | 1 location, all features |
| homeassistant | ghcr.io/home-assistant/home-assistant:stable | 8123 | ha-njord mounted as custom_component |

### Configuration

- **Location:** lucerne (47.05, 8.31)
- **Features:** all enabled (alerts, scores, conditions, trends, forecasts, observations, weather)
- **Poll interval:** 3600 s (default)
- **Forecast days:** 4

### Expected Entities

Derived from manifest: 1 location x enabled features.
Entity count depends on the njord manifest (GetManifest response).

| Platform | Pattern | Notes |
|----------|---------|-------|
| weather | `weather.lucerne_weather` + per-model | From WeatherValue entities |
| binary_sensor | `binary_sensor.lucerne_*` | From AlertValue entities (severity-based on/off) |
| sensor | `sensor.lucerne_*` | From ScoreValue, ObservationValue entities |
| sensor (server) | `sensor.version`, `sensor.uptime`, `sensor.monthly_usage`, `sensor.daily_usage` | From GetStatus |
| button | `button.trigger_poll` | TriggerPoll RPC |

---

## S0 -- Stack Setup

**Agent:** Opus (main)

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 0.1 | `docker compose -f e2e/docker-compose.e2e.yml down -v` | No errors |
| 0.2 | `docker compose -f e2e/docker-compose.e2e.yml up -d --build` | Both containers start |
| 0.3 | Poll `http://localhost:8080/alive` until HTTP 200 (timeout: 60s) | njord healthy |
| 0.4 | Poll `http://localhost:8123/` until HTTP 200 or 302 (timeout: 120s) | HA healthy |
| 0.5 | Record startup duration (time from 0.2 to 0.4 complete) | Documented |

---

## S1 -- HA Onboarding + Token

**Agent:** Opus (main), using claude-in-chrome

### S1A -- HA Onboarding (first run only)

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 1.1 | Open `http://localhost:8123` in browser | Onboarding page loads |
| 1.2 | Create user account (name: "njord-e2e", username: "njord", password: "e2e-test-2026") | Account created |
| 1.3 | Complete onboarding wizard (location, timezone, telemetry opt-out) | Dashboard appears |

### S1B -- Create Long-Lived Access Token

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 1.4 | Navigate to user profile (click user icon -> profile) | Profile page loads |
| 1.5 | Scroll to "Long-Lived Access Tokens" section | Section visible |
| 1.6 | Click "Create Token", name: "e2e-test" | Token displayed |
| 1.7 | Copy token value, store for REST API calls | Token captured |
| 1.8 | All subsequent REST calls use `Authorization: Bearer <token>` | -- |

---

## S2 -- Integration Setup

**Agent:** Opus (main), using claude-in-chrome

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 2.1 | Navigate to Settings -> Devices & Services | Integrations page loads |
| 2.2 | Click "Add Integration" | Integration search dialog opens |
| 2.3 | Search for "njord" | njord integration appears |
| 2.4 | Select njord, enter host: `njord`, port: `8081` | Config flow form visible |
| 2.5 | Submit | Success message with entity count |
| 2.6 | Record time from submit to success | Documented |

---

## S3 -- Entity Registration

**Agent:** Opus (main), using HA REST API

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 3.1 | Poll `GET /api/states` until weather entities appear (interval: 5s, timeout: 120s) | At least 1 `weather.*` entity exists |
| 3.2 | Count total entities with `njord` in device identifiers | Entity count matches manifest |
| 3.3 | Verify weather entity exists: `weather.lucerne_weather` | Present |
| 3.4 | Record time from integration setup (2.5) to first entities | Documented |
| 3.5 | Record complete entity ID list | Documented for future reference |

---

## S4 -- NjordService: GetManifest

**Agent:** Haiku #1

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 4.1 | `grpcurl -plaintext localhost:8081 njord.NjordService/GetManifest` | Response received |
| 4.2 | Verify response `entities` array is non-empty | Has entities |
| 4.3 | Verify entities contain `entity_id`, `location`, `feature`, `platform`, `output_kind` fields | Fields populated |
| 4.4 | Verify at least one entity has `output_kind` = `OUTPUT_KIND_ALERT` | Alert entities present |
| 4.5 | Verify at least one entity has `output_kind` = `OUTPUT_KIND_WEATHER` | Weather entities present |
| 4.6 | Verify entity `location` = "lucerne" for all entities | All for configured location |

---

## S5 -- NjordService: Subscribe (Entity Stream)

**Agent:** Haiku #1

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 5.1 | `timeout 30 grpcurl -plaintext localhost:8081 njord.NjordService/Subscribe` | At least 1 EntityEvent received |
| 5.2 | Verify first event is a `snapshot` with `states` array | Snapshot received |
| 5.3 | Verify snapshot states have `entity_id`, `updated_at`, and a value oneof | Fields populated |
| 5.4 | Wait for `state_update` events after snapshot | At least 1 update received |
| 5.5 | Verify state_update has `entity_id` matching a manifest entity | Valid entity_id |

---

## S6 -- Entity Attribute Depth

**Agent:** Haiku #1

### Weather Entities

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 6.1 | `GET /api/states/weather.lucerne_weather` | State is not "unavailable", state is in HA condition list |
| 6.2 | Verify attributes: `temperature` is numeric, `temperature_unit` = "C" | Both correct |
| 6.3 | Verify attributes: `wind_speed` is numeric, `wind_speed_unit` = "m/s" | Both correct |
| 6.4 | Verify attributes: `humidity` is numeric (0-100) | In range |
| 6.5 | `POST /api/services/weather/get_forecasts` with `entity_id: weather.lucerne_weather, type: hourly` | Forecast entries returned |
| 6.6 | Verify forecast entries have `temperature`, `humidity`, `wind_speed` keys | All keys present |

### Alert Sensors

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 6.7 | Find all binary_sensor entities with alert features via manifest | Alert sensors present |
| 6.8 | For each alert binary_sensor: verify state is "on" or "off" | Valid boolean state |
| 6.9 | Verify at least 1 alert binary_sensor has attributes with `severity`, `trigger_value` | Attributes populated |

### Score/Observation Sensors

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 6.10 | Find score sensor entities via manifest | Score sensors present |
| 6.11 | For each score sensor: verify state is numeric | Valid numeric state |
| 6.12 | Find observation sensor entities via manifest | Observation sensors present |
| 6.13 | For each observation sensor: verify state is numeric | Valid numeric state |

### Button Entity

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 6.14 | `GET /api/states/button.trigger_poll` | Entity exists |
| 6.15 | `POST /api/services/button/press` with `entity_id: button.trigger_poll` | No error |

---

## S7 -- Server Entities

**Agent:** Haiku #2

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 7.1 | `GET /api/states/sensor.version` | State matches semver pattern |
| 7.2 | `GET /api/states/sensor.uptime` | State is non-empty |
| 7.3 | `GET /api/states/sensor.monthly_usage` | State is numeric |
| 7.4 | `GET /api/states/sensor.daily_usage` | State is numeric |
| 7.5 | Verify version sensor has `njord` device identifier | Correct device |
| 7.6 | Verify usage percentages are between 0 and 100 | In range |
| 7.7 | Verify uptime is positive | > 0 |

---

## S8 -- NjordService: GetStatus

**Agent:** Haiku #2

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 8.1 | `grpcurl -plaintext localhost:8081 njord.NjordService/GetStatus` | Response contains `version` field |
| 8.2 | Verify response `version` matches semver pattern | Valid version |
| 8.3 | Verify `models` array contains entries with `location: "lucerne"` | Present |
| 8.4 | Verify `activeEnrichments` is non-empty | Features listed |
| 8.5 | Verify `budget` has `monthlyLimit`, `monthlyUsed`, `dailyLimit`, `dailyUsed`, `usagePercent` | All fields present |
| 8.6 | Verify `uptimeSeconds` > 0 | Running |

---

## S9 -- gRPC + REST Error Handling

**Agent:** Haiku #2

### gRPC Errors

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 9.1 | `grpcurl -plaintext -d '{"location":"nonexistent"}' localhost:8081 njord.NjordService/Subscribe` | gRPC error (NOT_FOUND), not a crash |
| 9.2 | `grpcurl -plaintext -d '{}' localhost:8081 njord.NjordService/TriggerPoll` | Success (empty location = trigger all) |

### HA REST API Errors

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 9.3 | `GET /api/states/sensor.nonexistent_njord_entity_xyz` | HTTP 404 or empty/not-found response, no crash |
| 9.4 | `POST /api/services/weather/get_forecasts` with `{"entity_id": "weather.nonexistent_xyz"}` | Error response, HA stays healthy |
| 9.5 | Verify `GET /api/` still responds after error tests | HA healthy |

---

## S10 -- HA Browser: Weather + Entity Cards

**Agent:** Haiku #3, using claude-in-chrome

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 10.1 | Navigate to Developer Tools -> States, filter by `weather.lucerne` | Weather entity visible |
| 10.2 | Click on weather entity to expand | Attributes visible: temperature, humidity, wind_speed, condition |
| 10.3 | Filter states by `binary_sensor.lucerne` | Alert binary sensors visible |
| 10.4 | Click on an alert binary sensor | Attributes visible: severity, trigger_value |
| 10.5 | Filter states by `sensor.lucerne` | Score/observation sensors visible |
| 10.6 | Click on a score sensor | State is numeric |
| 10.7 | Filter states by `sensor.version` | Server entities visible |
| 10.8 | Verify version displays a version string | Value displayed |

---

## S11 -- Multi-Cycle: TriggerPoll x 2

**Agent:** Opus (main)

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 11.1 | Record `last_updated` timestamp for weather entity via `GET /api/states/weather.lucerne_weather` | Timestamp captured |
| 11.2 | `grpcurl -plaintext -d '{}' localhost:8081 njord.NjordService/TriggerPoll` | `triggeredCount` >= 1 |
| 11.3 | Poll weather entity until `last_updated` > captured timestamp (interval: 5s, timeout: 120s) | Timestamp advanced |
| 11.4 | Record new `last_updated`, trigger second poll | `triggeredCount` >= 1 |
| 11.5 | Poll until `last_updated` advances again (timeout: 120s) | Second cycle confirmed |
| 11.6 | Verify a sensor entity `last_updated` also advanced | Entities updated |

---

## S12 -- Budget Tracking Across Cycles

**Agent:** Opus (main)

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 12.1 | Record `sensor.daily_usage` state before cycle | Usage captured |
| 12.2 | After S11 cycles complete, read `sensor.daily_usage` again | Usage > previous value |
| 12.3 | `grpcurl -plaintext localhost:8081 njord.NjordService/GetStatus` and extract `budget.dailyUsed` | Numeric, > 0 |
| 12.4 | Verify gRPC `dailyUsed` is consistent with HA `sensor.daily_usage` (within +/-1) | Consistent |

---

## S13 -- Resilience: Container Restart

**Agent:** Opus (main)

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 13.1 | `docker stop njord-e2e` | Container stopped |
| 13.2 | Wait 10s, verify entity states become stale or unavailable | Reflects downtime |
| 13.3 | `docker start njord-e2e` | Container starts |
| 13.4 | Poll `http://localhost:8080/alive` until HTTP 200 (timeout: 60s) | njord healthy again |
| 13.5 | Wait for entity stream to reconnect (poll weather entity, timeout: 120s) | State not "unavailable" |
| 13.6 | Trigger a poll and verify entities update | Entity recovered |
| 13.7 | Verify entity count matches pre-restart count | No entity loss |

---

## S14 -- Teardown: Integration Removal

**Agent:** Opus (main), using claude-in-chrome

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 14.1 | Navigate to Settings -> Devices & Services | Integrations page loads |
| 14.2 | Find njord integration, click "Delete" / remove | Deletion confirmed |
| 14.3 | Poll `GET /api/states` until no njord entities remain (interval: 5s, timeout: 30s) | All njord entities gone |
| 14.4 | Verify 0 entities match `njord` device identifiers | No orphans |
| 14.5 | `docker compose -f e2e/docker-compose.e2e.yml down -v` | Stack torn down |

---

## Orchestration

```
+------------------------------------------------------------------+
|  Opus Main Agent                                                  |
|  S0: Docker up, health poll                                 [SEQ] |
|  S1: Browser -- onboarding, token                           [SEQ] |
|  S2: Browser -- integration setup                           [SEQ] |
|  S3: Entity registration polling                            [SEQ] |
|                                                                   |
|  -- Parallel Block A (after S3) ----------------------------      |
|  +-------------------+  +-------------------+  +-----------+     |
|  |  Haiku #1         |  |  Haiku #2         |  |  Haiku #3 |     |
|  |  S4: GetManifest  |  |  S7: Server       |  |  S10: UI  |     |
|  |  S5: Subscribe    |  |  S8: GetStatus    |  |           |     |
|  |  S6: Attr Depth   |  |  S9: Errors       |  |           |     |
|  +-------------------+  +-------------------+  +-----------+     |
|                                                                   |
|  -- Re-validate any Haiku FAILs ----------------------------      |
|                                                                   |
|  S11: Multi-Cycle TriggerPoll x 2                           [SEQ] |
|  S12: Budget Tracking                                       [SEQ] |
|  S13: Resilience: Container Restart                         [SEQ] |
|  S14: Teardown: Integration Removal                         [SEQ] |
|                                                                   |
|  -- Write Results ------------------------------------------      |
+------------------------------------------------------------------+
```

### Subagent Briefing

Each Haiku subagent receives:
- The HA base URL (`http://localhost:8123`)
- The long-lived access token
- Their assigned sections from this plan (full step tables)
- Instruction to report PASS/FAIL per step with detail

**Haiku #1 -- Manifest + Stream + Entities (S4-S6):**
Verify GetManifest and Subscribe RPCs, then deep entity attribute validation. Use grpcurl for gRPC calls and curl + HA REST API for entity checks.

**Haiku #2 -- Server + Status + Errors (S7-S9):**
Verify server diagnostic entities via HA REST API, GetStatus RPC, and error handling.

**Haiku #3 -- HA Browser (S10):**
Verify entity display in HA UI using claude-in-chrome.

The main agent re-checks any FAIL before accepting it (Haiku may misinterpret API responses).

---

## Results Format

Output: `e2e/results/E2E-TEST-RESULTS-<YYYY-MM-DD>.md`

### Summary Table

| Section | Step | Result | Detail |
|---------|------|--------|--------|
| S0 | 0.1 Clean shutdown | PASS | No errors |
| S0 | 0.2 Stack start | PASS | Both containers running |
| ... | ... | ... | ... |

Rules:
- Every step gets PASS or FAIL -- **no SKIP allowed**
- FAIL includes the reason (error message, unexpected value, timeout)
- Timing observations are recorded in the Detail column

### Timing Baselines

Recorded on first run, used as reference for future runs:

| Metric | Baseline | Notes |
|--------|----------|-------|
| Stack startup (0.2 -> 0.4) | ~9s | njord instant, HA ~5s |
| Integration -> entities (2.5 -> 3.1) | < 1s | gRPC fast |
| Poll cycle (TriggerPoll -> last_updated) | ~30-60s | Depends on Open-Meteo response time |
| Restart -> stream reconnect (13.3 -> 13.5) | ~12s | Entity stream recovery |
| Teardown -> entities gone (14.2 -> 14.3) | < 5s | HA removes entities immediately |
| Full run duration | ~10-15 min | Including multi-cycle waits |
