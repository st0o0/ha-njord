## 1. Protos

- [x] 1.1 Copy common/weather/ops protos from njord and regenerate stubs

## 2. Models and parsing

- [x] 2.1 Write failing tests for seasonal parsing (full, unset optionals, empty)
- [x] 2.2 Add `SeasonalSampleData`, `SeasonalDomainData`, parse `seasonal` in `_to_domain_data`

## 3. Coordinator

- [x] 3.1 Write failing tests for seasonal storage and tracked domains
- [x] 3.2 Add `Domain.SEASONAL` to `TRACKED_DOMAINS`

## 4. Docs and verification

- [x] 4.1 Update CLAUDE.md domain line
- [x] 4.2 Run pytest, ruff, `openspec validate --all`
