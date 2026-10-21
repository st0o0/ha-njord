## Context

njord (`b77f8368`) returns, per location, `models` = effective model ids with the primary first, and the catalog
`models` with every known model and `enabled`. Secondary models are only effective while `Weather:ModelComparison`
is enabled. `DomainDataUpdate.model` is set for weather only; an empty `GetDomainDataRequest.model` means the primary
model, an unknown or disabled one answers NOT_FOUND.

## Decisions

### Separate store for secondary models

`NjordCoordinatorData.domains` stays keyed by `(location, domain)` and holds the primary model, so every existing
consumer (weather entity, derived sensors, alerts) is untouched. Secondary weather goes to a new
`model_domains: dict[tuple[str, str], WeatherDomainData]` keyed by `(location, model_id)`.

Routing of a streamed weather update: `update.model` empty or equal to the location's primary
(`location.models[0]`) goes to `domains`; anything else goes to `model_domains`.

### Which models get entities

Secondary models = `location.models[1:]` whose catalog entry is `enabled` (a model missing from the catalog counts as
enabled, the location list is authoritative). The first refresh calls `get_domain_data(location, WEATHER, model=id)`
for each; a failure leaves the key absent and the entity unavailable until the stream delivers data.

### Entity naming

The primary entity keeps unique id `{entry_id}_{slug}_weather` so existing installations keep their history. Model
entities use `{entry_id}_{slug}_{model_id}_weather`; the entity name is the catalog display name and HA derives the
entity id from device name + entity name (`has_entity_name`), like every other njord entity. A custom object id is
not forced: `suggested_object_id` is read-only in the supported HA version and would break the naming convention. A model first seen on the stream creates its entity through a model factory
registered on the coordinator (`register_model_factory`), mirroring the domain and feature factories.

### ModelComparison sensor

`_to_feature` already flattens repeated messages into lists of dicts, so `values["days"]` is
`[{year, month, day, models: [{model, max_temperature, min_temperature, precipitation}]}]`. The sensor state is the
spread (max - min) of the first day's `max_temperature` across the models that report it (None with fewer than two);
attributes are the generic feature attributes, so the whole table is visible.

## Risks

- A config with secondary models but ModelComparison disabled: njord reports only the primary in `models`, so no
  extra entities appear. Correct by construction.
