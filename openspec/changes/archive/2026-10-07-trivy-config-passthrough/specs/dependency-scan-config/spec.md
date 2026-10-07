## ADDED Requirements

### Requirement: Trivy scans only the shipped dependency footprint
The ha-njord CI SHALL scan a dependency manifest that reflects only the
packages `custom_components/njord/manifest.json` requires at runtime, not
the full `uv.lock` resolution (which also includes the `dev` extra's
`pytest-homeassistant-custom-component` closure).

#### Scenario: Security workflow scans requirements.txt instead of uv.lock
- **WHEN** the `security` workflow runs its filesystem scan
- **THEN** it scans `requirements.txt` (the production-only export) and
  skips `uv.lock` via `trivy.yaml`'s `scan.skip-files`

#### Scenario: requirements.txt matches the manifest's declared requirements
- **WHEN** `requirements.txt` is regenerated via `make requirements`
  (`uv export --no-hashes -o requirements.txt`, no extras)
- **THEN** it lists exactly the packages needed to satisfy
  `custom_components/njord/manifest.json`'s `requirements` (`grpcio`,
  `protobuf`) plus their own transitive dependencies, and nothing from the
  `dev` extra

### Requirement: requirements.txt cannot silently drift from uv.lock
CI SHALL fail a pull request if `requirements.txt` no longer matches what
`uv export --no-hashes` would produce from the current `uv.lock`.

#### Scenario: Stale requirements.txt fails CI
- **WHEN** `pyproject.toml`'s `[project.dependencies]` changes and
  `requirements.txt` is not regenerated to match
- **THEN** the `requirements-sync` CI job's diff check fails the pull request
  with a message pointing to `make requirements`

#### Scenario: In-sync requirements.txt passes CI
- **WHEN** `requirements.txt` was regenerated via `make requirements` after
  the last dependency change and committed
- **THEN** the `requirements-sync` CI job passes
