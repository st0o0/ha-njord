## MODIFIED Requirements

### Requirement: Typed data models
All public API methods SHALL return typed Python dataclasses, never raw protobuf message objects. Temporal fields SHALL be `datetime` objects, not integer epochs.

#### Scenario: IndexData includes daily scores and sub-models
- **WHEN** `IndexData` is returned as part of enrichment data
- **THEN** it contains today's activity scores as top-level int fields, `frost` as `FrostData | None`, `vpd` as `VpdData | None`, and `forecast` as `list[DayScoreData]`

#### Scenario: IndexData parses DayScoreSet array
- **WHEN** the proto `IndexUpdate` contains `days = [{day_offset: 0, laundry: 85, bbq: 70}, {day_offset: 1, laundry: 72, bbq: 55}]`
- **THEN** `IndexData.laundry` is `85`, `IndexData.bbq` is `70`, and `IndexData.forecast` contains one `DayScoreData(day_offset=1, laundry=72, bbq=55)`

#### Scenario: IndexData parses FrostInfo sub-message
- **WHEN** the proto `IndexUpdate` contains `frost = FrostInfo(hours_until_frost=4, confidence=0.85)`
- **THEN** `IndexData.frost` is `FrostData(hours_until=4, confidence=0.85)`

#### Scenario: IndexData parses VpdInfo sub-message
- **WHEN** the proto `IndexUpdate` contains `vpd = VpdInfo(kpa=0.59, category="optimal")`
- **THEN** `IndexData.vpd` is `VpdData(kpa=0.59, category="optimal")`

#### Scenario: IndexData with no frost/vpd
- **WHEN** the proto `IndexUpdate` has no `frost` or `vpd` fields set
- **THEN** `IndexData.frost` is `None` and `IndexData.vpd` is `None`

#### Scenario: IndexData with empty days array
- **WHEN** the proto `IndexUpdate` has an empty `days` array
- **THEN** `IndexData` has all score fields at `0`, `frost`/`vpd` from sub-messages, and `forecast` is `[]`

#### Scenario: No protobuf leakage
- **WHEN** a consumer uses any `NjordClient` method
- **THEN** the return type is a dataclass from `models.py`, not a `_pb2` generated class

#### Scenario: Timestamps are datetime
- **WHEN** a `ForecastData` or `HourlyForecastData` is returned
- **THEN** `updated_at` and `valid_at` are `datetime` objects with UTC timezone, not integers

#### Scenario: ventilation field renamed to night_ventilation
- **WHEN** the proto `DayScoreSet` contains `night_ventilation = 22`
- **THEN** `IndexData.night_ventilation` is `22`
