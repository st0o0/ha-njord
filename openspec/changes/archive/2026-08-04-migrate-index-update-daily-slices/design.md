## Context

ha-njord parses `IndexUpdate` as a flat protobuf message with 8 activity scores and optional frost/VPD fields. njord v2 restructures this into daily slices (`repeated DayScoreSet days`), separate `FrostInfo`/`VpdInfo` sub-messages, and optional `ScoreEnvelope` confidence data per score. The field `ventilation` is renamed to `night_ventilation`.

The current data flow: `common_pb2.IndexUpdate` → `_to_index_data()` → `IndexData` dataclass → sensor entities read individual fields.

## Goals / Non-Goals

**Goals:**
- Parse the new `DayScoreSet`-based `IndexUpdate` correctly
- Expose multi-day scores on activity sensors using the DWD-Pollenflug pattern
- Adapt frost/VPD sensors to read from sub-messages
- Rename ventilation → night_ventilation across the stack

**Non-Goals:**
- Separate sensors per forecast day (entity explosion)
- ScoreEnvelope as standalone sensors (attributes only)
- Changes to coordinator architecture or stream lifecycle
- IndexConfig changes (ha-njord is read-only)

## Decisions

### 1. IndexData stays flat with a forecast list

**Decision**: Keep `IndexData` as a single-level dataclass representing today's scores, and add a `forecast: list[DayScoreData]` field for future days. `FrostData` and `VpdData` become small frozen dataclasses replacing the old flat optional fields.

**Why**: The coordinator's merge logic (`merge_enrichment`) compares `IndexData` against defaults. A nested per-day structure would complicate default detection. Flattening `days[0]` into the top-level fields preserves the existing merge pattern.

**Alternative considered**: Make `IndexData` contain only `days: list[DayScoreData]` — rejected because it forces every sensor to index into `days[0]`, adding boilerplate and breaking the existing attribute access pattern.

**Resulting model**:
```python
@dataclass(frozen=True)
class DayScoreData:
    day_offset: int = 0
    laundry: int = 0
    outdoor: int = 0
    running: int = 0
    cycling: int = 0
    bbq: int = 0
    solar: int = 0
    night_ventilation: int = 0
    hours_included: int = 0

@dataclass(frozen=True)
class FrostData:
    hours_until: int = 0
    confidence: float = 0.0

@dataclass(frozen=True)
class VpdData:
    kpa: float = 0.0
    category: str = ""

@dataclass(frozen=True)
class IndexData:
    laundry: int = 0
    outdoor: int = 0
    running: int = 0
    cycling: int = 0
    bbq: int = 0
    irrigation: int = 0
    solar: int = 0
    night_ventilation: int = 0
    frost: FrostData | None = None
    vpd: VpdData | None = None
    forecast: list[DayScoreData] = field(default_factory=list)
```

### 2. _to_index_data() extracts days[0] as top-level, days[1..N] as forecast

**Decision**: The parser reads `pb.days[0]` into the top-level score fields. `pb.days[1:]` become `DayScoreData` entries in `forecast`. `pb.frost` and `pb.vpd` are parsed into `FrostData`/`VpdData` if present.

**Why**: Keeps the sensor side simple — sensors read `indices.laundry` for today's value, same as before. The forecast list is only consumed by sensors that want to expose it.

### 3. Activity sensors expose forecast as extra_state_attributes

**Decision**: Each `NjordActivitySensor` adds a `forecast` attribute containing a list of dicts: `[{"day_offset": 1, "score": 72}, {"day_offset": 2, "score": 60}]`. The attribute key name within each forecast entry matches the activity type.

**Why**: Follows the DWD-Pollenflug pattern. HA does not natively render forecast attributes on sensors, but they're accessible via templates and custom cards. The attribute is a list of dicts, not a flat key per day, because the number of forecast days is variable.

### 4. Frost/VPD sensors use sub-model accessors

**Decision**: `NjordFrostHoursSensor` reads `enrichment.indices.frost.hours_until` (was `enrichment.indices.frost_hours`). `NjordFrostConfidenceSensor` reads `enrichment.indices.frost.confidence`. `NjordVpdSensor` reads `enrichment.indices.vpd.kpa` / `enrichment.indices.vpd.category`.

**Why**: Direct mapping to the new sub-messages. Null-safety via `indices.frost is None` check, same pattern as before.

### 5. ventilation → night_ventilation is a clean rename

**Decision**: Rename everywhere — model field, sensor INDEX_TYPES tuple, translation keys, entity IDs. No backwards-compatibility shim.

**Why**: ha-njord is installed via HACS with no persistent state keyed by field name. HA entity IDs are derived from the tuple name in INDEX_TYPES, so the entity ID will change from `sensor.{loc}_ventilation_index` to `sensor.{loc}_night_ventilation_index`. This is acceptable — it's a pre-1.0 integration, and the old entity will simply disappear and the new one appear.

### 6. irrigation stays despite not being in DayScoreSet

**Decision**: `irrigation` is not present in the new `DayScoreSet` message. Remove it from `IndexData` and `INDEX_TYPES`. It was in the flat format but dropped in the redesign.

**Why**: The proto is the source of truth. Keeping a field that never gets populated creates dead sensors.

## Risks / Trade-offs

- **Entity ID change for ventilation** → Users who have automations referencing `sensor.*_ventilation_index` will need to update them. Acceptable for a pre-1.0 integration. Risk is low — enrichment sensors are disabled by default.
- **irrigation removal** → Same as above, but the sensor was never populated if njord didn't send the field. Low risk.
- **Empty forecast list** → If njord sends only `days[0]` (single day), `forecast` will be empty. Sensors handle this gracefully — the attribute is just an empty list.
- **Proto copy timing** → The new proto must be copied from njord before stubs can be regenerated. If the njord branch isn't finalized, the proto could change again. Mitigation: copy once the njord branch is merged.

## Open Questions

- Should `hours_included` from `DayScoreSet` be exposed as a sensor attribute? It indicates how many hours of data went into the score calculation. Could be useful for transparency but adds clutter.
