## Why

njord now fetches the weather domain for several ensemble-mean models when the operator lists more than one in
`Njord:Weather:Models` and enables `Weather:ModelComparison`. The catalog carries every known model with an
`enabled` flag, `GetDomainData`/`StreamDomainData` carry the weather model, and a new `ModelComparison` enrichment
compares the daily values of all models. ha-njord still treats weather as one series per location, so secondary
model data overwrites the primary entity and the comparison is invisible in Home Assistant.

## What Changes

- Sync `common.proto` and `weather.proto` from njord and regenerate the stubs (`ModelInfo.enabled`,
  `GetDomainDataRequest.model`, `DomainDataUpdate.model`, `EnrichmentEvent.model_comparison`).
- `ModelInfoData.enabled` and `WeatherDomainData.model`; `get_domain_data(..., model=...)` requests a specific model.
- The coordinator keeps secondary-model weather in `model_domains[(location, model_id)]`, fetches it on the first
  refresh and routes streamed weather updates by their `model` (empty or primary goes to `domains` as before).
- One extra weather entity per enabled secondary model on the location device, named after the model's display name
  (entity id follows HA's device + name convention), unique id `{entry_id}_{location}_{model_id}_weather`. The primary
  entity keeps its unique id.
- Every weather entity exposes `model`, `model_name`, `provider`, `region`, `resolution_km` and `forecast_hours`
  from the catalog.
- New feature `Weather:ModelComparison`: sensor `Model Temperature Spread` (spread of the first day's maximum
  temperature across models, in °C) with the full per-day, per-model table as attributes.
- Fix the stale proto-codegen spec (no `admin.proto`, current message names).

## Non-goals

- No consensus/blended weather entity; njord does not deliver one.
- Secondary models do not drive alerts, scores or other sensors; rules on the server run on the primary model.
- No entity removal when a model is disabled later; the registry cleanup that already exists for stale entities applies.
- No change to air quality, flood, marine, seasonal or satellite handling.

## njord endpoints used

All exist; only fields are new: `GetCatalog` (`models[].enabled`), `GetDomainData` (request `model`),
`StreamDomainData` (update `model`), `GetEnrichments`/`StreamEnrichments` (`model_comparison` case), `GetStatus`
(`active_enrichments` lists `Weather:ModelComparison`).

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `weather-entities`: per-model weather entities, model routing, model attributes.
- `typed-enrichments`: the ModelComparison sensor.
- `proto-codegen`: three proto files and current message names.
