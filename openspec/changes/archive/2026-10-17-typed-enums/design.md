## Context

HA integrations conventionally use plain `CONF_*` string constants and HA's own enums/constants. Here the closed sets are spread as raw literals. Several are persisted (option keys, unique ids, translation keys) and must not change value.

## Goals / Non-Goals

**Goals:** one definition per closed set; zero change to anything HA persists or users see; wire enums consumed safely.

**Non-Goals:** see proposal.

## Decisions

1. **`StrEnum` with unchanged values.** A `StrEnum` member equals its string, so unique ids built with f-strings, issue ids, translation keys and stored options stay byte-identical. A test pins this for each enum.
2. **Wire-fed enums tolerate unknown values.** `AlertType`, `AlertSeverity` and the typed wire values define `_missing_` (or a mapping default) returning `UNSPECIFIED`/`NONE`. Alert types keep the existing behaviour of ignoring `unspecified`. Rationale: a newer njord must not crash an older ha-njord.
3. **`AlertType` carries its metadata** in one table (`name`, `unit`, `device_class`, `precision`, `icon`) instead of six parallel dicts; sensor creation iterates the table. Alternative (enum with tuple values) rejected: it makes the enum value non-string.
4. **`AlertSeverity` is a `StrEnum` with a `.rank` property** (none 0, yellow 1, orange 2, red 3). The string is exposed as an attribute and used by translations, so an `IntEnum` is not used.
5. **`EnrichmentGroup` + `group_enabled`.** The helper encodes the existing rule: enabled when (`active` is `None` or contains the group) and the group is not in `disabled`. Disabled groups read from options are converted with a tolerant filter so a stored legacy value (such as `history`) is ignored.
6. **Proto enum mapping lives in `grpc_client.py`** next to the other converters, via lookup tables from proto numbers to the Python enums; unknown numbers map to `UNSPECIFIED`.
7. **`SensorKind`** keys `SENSOR_KIND_MAP`; `push_sensor` still accepts strings (service calls) and raises `ServiceValidationError`/`ValueError` for unknown input as today, but stored options with a stale kind are skipped with a debug log.
8. **Conditions** use `ATTR_CONDITION_*`; values are identical, only the source of the literal changes.
9. **Sequencing**: njord implements `typed-wire-enums` first; this change copies the resulting protos and regenerates stubs (documented Docker command). Tasks that need the new stubs come after the proto sync.

## Risks / Trade-offs

- Subtle behaviour drift while refactoring entity creation → the tests assert unique ids, entity ids and states before and after, using the existing fixtures.
- Proto stubs out of step with njord → `test_proto_import.py` plus the explicit sync task; released together.
- `SensorDeviceClass.ENUM` options constrain states; values outside the options would be rejected by HA → options are derived from the same enum that parses the wire value, and unknown values map to `unavailable` rather than an invalid state.
