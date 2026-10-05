## Context

ha-njord currently polls njord every 5 minutes using HA's `DataUpdateCoordinator`. Each poll cycle calls `GetConfig`, then `GetForecast` for every location×model pair, then `GetEnrichments` per location. The gRPC client already has `stream_forecasts()`, `stream_enrichments()`, and `stream_config()` with reconnect+backoff — they're just never called.

The coordinator pattern works well as a data store and entity notification hub. The change replaces the poll trigger with three stream listeners that push data in.

## Goals / Non-Goals

**Goals:**
- Real-time forecast, enrichment, and config updates via gRPC server streams
- Granular enrichment merge (partial events don't clobber unrelated fields)
- Dynamic entity creation when njord adds new locations
- Clean lifecycle management (start on setup, cancel on unload)

**Non-Goals:**
- Entity removal when locations are deleted in njord
- Falling back to polling on stream failure
- Config flow changes
- New entity types or enrichment categories

## Decisions

### D1: Keep DataUpdateCoordinator as data store, disable polling

**Choice:** Set `update_interval=None` on the coordinator. Stream listeners call `coordinator.async_set_updated_data()` to push updates.

**Why not replace the coordinator entirely?** `CoordinatorEntity` is the standard HA pattern. Entities already subclass it and rely on `_handle_coordinator_update` for state refresh. Replacing it would mean reimplementing entity notification. Keeping it with no poll interval gives us the best of both: push-driven updates with standard HA entity lifecycle.

**Alternative considered:** Custom event bus. Rejected — reinventing what the coordinator already provides.

### D2: One stream per type, all locations

**Choice:** Open one `StreamForecasts(location="")` and one `StreamEnrichments(location="")` stream each, receiving updates for all locations. Plus one `StreamConfig()` stream.

**Why not per-location streams?** More connections, more reconnect logic, more complexity. The all-locations stream is a single connection that multiplexes. If njord ever has hundreds of locations this could be revisited, but for a home weather setup this is clearly better.

### D3: Enrichment merge via dataclasses.replace()

**Choice:** When a `StreamEnrichments` event arrives with e.g. only `alerts`, build a new `EnrichmentData` by taking the existing one and replacing only the `alerts` field:

```python
existing = coordinator.data.enrichments[location]
updated = dataclasses.replace(existing, alerts=new_alerts)
```

**Why not mutable dataclasses?** Frozen dataclasses are used everywhere in the codebase. Switching to mutable would be a larger refactor and loses the safety guarantees. `replace()` is one line per merge.

### D4: Stream tasks as asyncio.Task stored on coordinator

**Choice:** The coordinator owns a `_stream_tasks: list[asyncio.Task]` created in a new `start_streams()` method. `__init__.py` calls `coordinator.start_streams()` after first refresh. On unload, tasks are cancelled.

**Why on the coordinator?** It already owns the client and the data. Adding stream management there keeps everything in one place. The alternative — a separate `StreamManager` class — adds indirection without value at this scale.

### D5: Dynamic entity creation via stored callbacks

**Choice:** Each platform setup (`weather.py`, `sensor.py`, `binary_sensor.py`) stores its `async_add_entities` callback on the coordinator. When `StreamConfig` delivers a new location, the coordinator calls these callbacks with new entities.

```
coordinator.register_entity_factory("weather", async_add_entities, factory_fn)
```

The factory function takes a location (and optionally model list) and returns the entities to add. This keeps entity construction logic in the platform files where it belongs.

**How to detect "new":** Coordinator tracks `_known_locations: set[str]`. On each config event, diff against known set. New entries trigger entity creation. Removed entries are ignored (per decision).

### D6: Startup sequence

```
1. client.connect()
2. coordinator = NjordDataCoordinator(hass, client)
3. coordinator.async_config_entry_first_refresh()    ← unary calls, blocks
4. forward_entry_setups(PLATFORMS)                    ← entities created
5. coordinator.start_streams()                        ← background tasks begin
```

Steps 3-4 must complete before 5 because:
- Entities need initial data (step 3)
- Platform setups register entity factories on the coordinator (step 4)
- Streams can then push updates and create new entities (step 5)

## Risks / Trade-offs

**[Stale data on long disconnect]** → Accepted. Last known state is shown. Entities could expose a "last updated" attribute so dashboards can show staleness. Not in scope for this change but easy to add later.

**[Race between stream events and entity creation]** → Mitigated by startup sequence. First refresh provides complete initial state. Stream events arriving before `start_streams()` are impossible. Events arriving between `start_streams()` and entity factory registration cannot happen because `forward_entry_setups` completes before `start_streams`.

**[Enrichment merge with missing initial data]** → If `get_enrichments()` fails for a location during first refresh but the enrichment stream later delivers a partial event, the merge needs a base object. Solution: create a default `EnrichmentData(location=loc)` as the base when no existing data exists.

**[Three concurrent stream tasks]** → Minimal overhead. Each task is mostly idle (awaiting the next gRPC message). No thread pool needed — pure asyncio.

## Open Questions

None — all decisions were made during exploration.
