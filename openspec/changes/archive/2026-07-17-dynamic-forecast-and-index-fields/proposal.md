## Why

Weather entities always claim `FORECAST_DAILY | FORECAST_HOURLY` regardless of whether the model actually provides daily data. Models like `knmi_harmonie_arome_netherlands` deliver only hourly forecasts, causing HA to show an empty "Forecast:" section. Additionally, four fields from the `IndexUpdate` proto (`hdd`, `cdd`, `frost_hours`, `frost_confidence`) are never mapped into the data model or exposed as sensors.

## What Changes

- **Dynamic `supported_features` on weather entities.** Replace the static class attribute with a property that checks whether the model's forecast data actually contains hourly and/or daily entries. Models without daily data won't advertise `FORECAST_DAILY`.
- **Add missing index fields to `IndexData`.** Map `hdd` (Heating Degree Days), `cdd` (Cooling Degree Days), `frost_hours`, and `frost_confidence` from the proto into the `IndexData` dataclass.
- **Expose new index fields as sensors.** Create sensor entities for HDD, CDD, frost hours, and frost confidence with appropriate units and icons.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `weather-entities`: `supported_features` becomes dynamic based on actual data availability instead of static class attribute.
- `enrichment-sensors`: Add HDD, CDD, frost hours, and frost confidence sensors.
- `grpc-client`: Map `hdd`, `cdd`, `frost_hours`, `frost_confidence` from `IndexUpdate` proto into `IndexData`.

## Non-goals

- Aggregating daily forecasts from hourly data for models that lack them.
- Dynamic consensus horizons from config (separate concern).
- Changing how existing index sensors (laundry, outdoor, etc.) work.

## gRPC Endpoints Required

| Endpoint | Status | Notes |
|---|---|---|
| `GetForecast` | Exists, already used | No changes needed |
| `StreamForecasts` | Exists, already used | No changes needed |
| `GetEnrichments` | Exists, already used | Already returns `IndexUpdate` with hdd/cdd/frost fields |
| `StreamEnrichments` | Exists, already used | Already streams `IndexUpdate` with hdd/cdd/frost fields |

All fields already exist in the proto — they're just not mapped on the ha-njord side.

## Impact

- **`custom_components/njord/models.py`** — Add `hdd`, `cdd`, `frost_hours`, `frost_confidence` to `IndexData`.
- **`custom_components/njord/grpc_client.py`** — Map the four new fields in `_to_index_data()`.
- **`custom_components/njord/weather.py`** — Change `_attr_supported_features` to a `supported_features` property.
- **`custom_components/njord/sensor.py`** — Add four new sensor entity types.
- **`custom_components/njord/strings.json`** / **`translations/de.json`** — Add translation keys for new sensors.
- **Tests** — Update model tests, add sensor tests for new fields.
