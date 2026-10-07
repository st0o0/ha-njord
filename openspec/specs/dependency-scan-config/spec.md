### Requirement: Trivy scans only the shipped dependency footprint
The ha-njord CI SHALL scan a dependency manifest that reflects only the
packages `custom_components/njord/manifest.json` requires at runtime, not
the full `uv.lock` resolution (which also includes the `dev` extra's
`pytest-homeassistant-custom-component` closure).

`requirements.txt` is never committed (see `.gitignore`): it exists only as
an ephemeral build artifact, generated fresh inside the `security` workflow
run before Trivy scans, so it can never drift from `uv.lock` and there is no
separate sync check to fail.

#### Scenario: Security workflow scans requirements.txt instead of uv.lock
- **WHEN** the `security` workflow's `scan` job runs
- **THEN** it generates `requirements.txt` via
  `uv export --no-hashes --no-header -o requirements.txt` right before
  invoking Trivy, scans it as the production-only footprint, and skips
  `uv.lock` via `trivy.yaml`'s `scan.skip-files`

#### Scenario: Generated requirements.txt matches the manifest's declared requirements
- **WHEN** the `security` workflow generates `requirements.txt` from the
  current `uv.lock`
- **THEN** it lists exactly the packages needed to satisfy
  `custom_components/njord/manifest.json`'s `requirements` (`grpcio`,
  `protobuf`) plus their own transitive dependencies, and nothing from the
  `dev` extra
