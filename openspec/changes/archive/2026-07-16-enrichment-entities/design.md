## Architecture

```
njord gRPC (port 8081)
  │
  ├─ GetEnrichments(location) ──────► EnrichmentData (dataclass)
  │                                      ├─ alerts: list[AlertData]
  │                                      ├─ indices: IndexData
  │                                      ├─ trends: TrendData
  │                                      ├─ energy: EnergyData
  │                                      ├─ derived: DerivedData
  │                                      ├─ history: HistoryData
  │                                      └─ consensus: ConsensusData
  │
  └─ StreamEnrichments(location) ──► EnrichmentEvent (type_name + payload)
```

### Data Flow

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────────────┐
│              │     │                 │     │                          │
│  NjordClient │────►│  Coordinator    │────►│  Entity Platforms        │
│              │     │                 │     │                          │
│ get_enrichm..│     │ data:           │     │ binary_sensor.py         │
│ stream_enri..│     │  forecasts{}    │     │   → 9 alert entities/loc │
│              │     │  enrichments{}  │     │                          │
│              │     │  config         │     │ sensor.py                │
└──────────────┘     │                 │     │   → indices (8+1)        │
                     │ update cycle:   │     │   → energy (5)           │
                     │  1. get_config  │     │   → trends (1)           │
                     │  2. get_forecast│     │   → derived (2+1 binary) │
                     │  3. get_enrichm.│     │   → history (1 diag)     │
                     │     per loc     │     │                          │
                     └─────────────────┘     │ weather.py               │
                                            │   → consensus entity/loc │
                                            │   → horizon attrs on     │
                                            │     existing model ents  │
                                            └──────────────────────────┘
```

## Key Design Decisions

### 1. Enrichments in the existing coordinator (not a separate one)

Enrichments update on the same cadence as forecasts — njord recomputes them when new forecast data arrives. A single coordinator keeps the update atomic: entities always see consistent forecast + enrichment state.

The coordinator's `data` dict grows from `{forecasts, config}` to `{forecasts, enrichments, config}`. Enrichments are keyed by location (not location+model, since enrichments are per-location).

### 2. Flat entities over nested attributes

Each alert type, index, and energy metric gets its own entity rather than being packed into a single entity with many attributes. Rationale:
- HA automations trigger on entity state changes, not attribute changes
- Entity-level history tracking in recorder
- Users can selectively show/hide entities in dashboards
- Consistent with how other HA integrations model similar data (e.g., air quality indices)

Exception: Trends stay as 1 entity with attributes because the individual values (precip_starts_in_hours, temp_max_in_hours) are contextually coupled and not independently actionable.

### 3. Consensus as a weather entity, not sensors

The consensus data maps perfectly to HA's weather entity model: it has temperature, humidity, wind, precipitation, cloud cover — all per horizon. Building it as a `weather` entity means it works out-of-the-box with weather cards, forecast graphs, and the built-in weather TTS. Agreement percentage is an extra_state_attribute.

The consensus entity uses `h3` horizon data for current state (or falls back to closest available horizon).

### 4. Streaming for enrichments (future)

The initial implementation uses polling via `GetEnrichments()` in the coordinator. The `StreamEnrichments()` RPC is already in the client but will be connected in a follow-up change (same pattern as the existing `StreamForecasts` → coordinator push).

### 5. Entity naming convention

```
{domain}.njord_{location}_{enrichment_type}
```

Examples:
- `binary_sensor.njord_home_uv_alert`
- `sensor.njord_home_bbq_index`
- `sensor.njord_home_heating_demand`
- `sensor.njord_home_weather_trend`
- `weather.njord_home_consensus`

### 6. Default port fix

`DEFAULT_PORT` in `const.py` changes from `8080` to `8081`. This is a breaking change for existing users who relied on the default — but since the integration is pre-release and 8080 never worked for gRPC, this is the right time to fix it.

## Data Models (models.py additions)

```python
@dataclass(frozen=True)
class AlertData:
    type: str          # "frost", "heat", "storm", ...
    severity: str      # "none", "yellow", "orange", "red"
    confidence: float  # 0.0–1.0

@dataclass(frozen=True)
class IndexData:
    laundry: int       # 0–100
    outdoor: int
    running: int
    cycling: int
    bbq: int
    irrigation: int
    solar: int
    ventilation: int
    vpd_kpa: float | None
    vpd_category: str | None

@dataclass(frozen=True)
class TrendData:
    parameter_trends: list[ParameterTrendData]
    weather_change_description: str | None
    precip_starts_in_hours: int | None
    precip_ends_in_hours: int | None
    temp_max_in_hours: int | None
    temp_min_in_hours: int | None
    stability_label: str | None
    stability_ratio: float | None
    decay_rate: float | None
    reliable_hours: int | None

@dataclass(frozen=True)
class EnergyData:
    heating_demand: int       # 0–100
    cop_estimate: float | None
    shading: int              # 0–100
    battery_strategy: str     # "discharge", "charge", "hold"
    night_cooling: int        # 0–100
    cop_optimal: list[CopOptimalHourData]

@dataclass(frozen=True)
class DerivedData:
    by_horizon: list[HorizonDerivedData]
    diurnal_amplitude: float | None
    sunshine_pct: float | None
    inversion: bool | None

@dataclass(frozen=True)
class HistoryData:
    models: list[ModelMetricsData]
    seasonal_best: str | None
    anomaly: bool | None
    anomaly_deviation: float | None
    weighted_temperature: float | None

@dataclass(frozen=True)
class ConsensusData:
    parameters: list[ParameterConsensusData]

@dataclass(frozen=True)
class EnrichmentData:
    location: str
    alerts: list[AlertData]
    indices: IndexData | None
    trends: TrendData | None
    energy: EnergyData | None
    derived: DerivedData | None
    history: HistoryData | None
    consensus: ConsensusData | None
```

## Platform Registration

In `__init__.py`, add `binary_sensor` and `sensor` to `PLATFORMS`:

```python
PLATFORMS = [Platform.WEATHER, Platform.BINARY_SENSOR, Platform.SENSOR]
```

The consensus weather entity is added to the existing `weather.py` platform alongside the per-model entities.
