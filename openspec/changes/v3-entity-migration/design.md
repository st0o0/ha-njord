## Context

ha-njord currently uses v2 gRPC API with 2 streams (domain data + enrichments), per-feature entity classes, and ~300 lines of hardcoded metadata (ALERT_META, FEATURE_KEYS, DOMAIN_SENSOR_REGISTRY). Adding a new feature in njord requires matching changes in ha-njord. The v3 API eliminates this coupling.

## Goals / Non-Goals

**Goals:**
- Manifest-driven entity creation (zero ha-njord changes when njord adds features)
- Single unified stream with snapshot-on-connect
- Preserve existing HA entity IDs for seamless migration
- Simplify coordinator from 2 stream paths to 1

**Non-Goals:**
- Sensor push migration
- Options flow redesign
- Calendar entity changes

## Decisions

### Decision 1: Phased migration with v2/v3 coexistence

Implement v3 alongside v2, then cut over. This avoids a big-bang rewrite and lets us test incrementally.

**Phase 1**: Add v3 proto + client methods. Both v2 and v3 stubs exist.
**Phase 2**: Manifest-driven entity factory replaces hardcoded metadata. Entities still fed by v2 streams.
**Phase 3**: Subscribe stream replaces v2 streams. Full v3 data path.
**Phase 4**: Remove all v2 code.

### Decision 2: Generic entity classes per OutputKind

Replace per-feature entity classes with 7 generic classes (one per OutputKind): `NjordAlertSensor`, `NjordScoreSensor`, `NjordConditionSensor`, `NjordTrendSensor`, `NjordForecastSensor`, `NjordObservationSensor`, `NjordWeatherSensor`. Each knows how to extract its state from the corresponding v3 value type.

**Alternative considered:** Single generic `NjordEntitySensor` for all types. Rejected because OutputKinds have different state attributes (alerts have severity + active, scores have numeric value, conditions have state string).

### Decision 3: Entity ID preservation

njord v3 uses `{slug}_{snake_case_name}` for entity IDs (e.g. `vienna_frost`, `vienna_pm25_observation`). ha-njord v2 uses the same pattern. Entity IDs are preserved by construction -- no migration needed for existing features. New Observation entities get new IDs that never existed in v2.

### Decision 4: Weather entity stays composite

The HA `weather` platform entity is a composite (temperature, humidity, wind, etc. in one entity). It cannot be replaced by individual v3 entities. Instead, it will consume `WeatherValue` from the v3 stream and map fields to HA weather attributes.

## Risks / Trade-offs

- **[Large change]** Every file touched. Mitigation: phased approach, each phase independently testable.
- **[Test rewrite]** 3300 lines of tests coupled to v2 models. Mitigation: rewrite alongside each phase, not as a separate task.
- **[Entity registry]** HA entity registry may need cleanup if entity unique_ids change. Mitigation: keep unique_id format consistent (`njord_{location}_{feature_snake_case}`).

## Open Questions

- Should sensor push stay on v2 or get a separate v3 endpoint?
