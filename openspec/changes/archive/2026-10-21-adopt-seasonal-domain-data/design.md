## Context

Domains are parsed in `grpc_client._to_domain_data` into frozen dataclasses and stored in `NjordCoordinatorData.domains` keyed by `(location, Domain)`. `TRACKED_DOMAINS` drives both the first-refresh unary calls and the stream subscription.

## Decisions

- Model seasonal like the other domains: `SeasonalSampleData` and `SeasonalDomainData(location, model_run, points, domain=Domain.SEASONAL)`, added to the `DomainData` union. Using the existing shape means the coordinator, stream handling and diagnostics need no special case.
- Add `Domain.SEASONAL` to `TRACKED_DOMAINS`. Sensor and weather factories filter by domain, so no entity appears. Diagnostics already summarize domains per location.
- Stubs are regenerated with the documented Docker command; it resolves to grpcio-tools 1.71 / protobuf 5.29, matching the existing gencode header, so the command needs no change.
- Satellite stays unconsumed.

## Risks

- Older njord servers answer a seasonal `GetDomainData` with an error or nothing; the first refresh already tolerates that per domain.
