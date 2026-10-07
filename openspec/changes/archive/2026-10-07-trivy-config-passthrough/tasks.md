## 1. github-workflows: generic trivy-config passthrough

- [x] 1.1 In `github-workflows/.github/workflows/security.yml`, remove the
  `skip-dirs` input (default `'docs'`) and the `skip-files` input (added for
  ha-njord but not yet merged) from `workflow_call.inputs`.
- [x] 1.2 Add a new `trivy-config` input (`type: string`, `default: ''`),
  documented as: "Path to a trivy.yaml in the consumer repo for scan tuning
  (skip-files, skip-dirs, severity overrides that aren't already hardcoded
  below, etc.). Severity/scanners/ignore-unfixed stay hardcoded here and
  always win over trivy.yaml (Trivy/Viper precedence) — only keys this
  workflow doesn't already set explicitly take effect from the config file."
- [x] 1.3 Pass `trivy-config: ${{ inputs.trivy-config }}` to the
  `aquasecurity/trivy-action` step in the `trivy-image` job.
- [x] 1.4 Pass `trivy-config: ${{ inputs.trivy-config }}` to the
  `aquasecurity/trivy-action` step in the `trivy-fs` job, removing the
  `skip-dirs`/`skip-files` lines that referenced the removed inputs.
- [x] 1.5 Confirm the other 12 consumers' `security.yml` files need no
  changes (they don't set `skip-dirs`/`skip-files`): Flickr.Net,
  FunkArr, FunkCrawlArr, OpenTraverse, WebSocket.Rx, bifrost, eir, forseti,
  mjolnir, njord, ran, shutterfall, var.

## 2. Signal.Bot: migrate off the skip-dirs default

- [x] 2.1 Add `Signal.Bot/trivy.yaml`:
  ```yaml
  scan:
    skip-dirs:
      - docs
  ```
- [x] 2.2 Update `Signal.Bot/.github/workflows/security.yml`'s `with:` block
  to add `trivy-config: trivy.yaml` (keep `scan-type: fs`).

## 3. ha-njord: scope the scan to the shipped footprint

- [x] 3.1 Replace the already-drafted, uncommitted `skip-files: 'uv.lock'`
  line in `ha-njord/.github/workflows/security.yml` with
  `trivy-config: trivy.yaml` (don't layer both).
- [x] 3.2 Add `ha-njord/trivy.yaml`:
  ```yaml
  scan:
    skip-files:
      - uv.lock
  ```
- [x] 3.3 Keep/commit the already-exported `ha-njord/requirements.txt`
  (`uv export --no-hashes --no-header -o requirements.txt`, no extras —
  currently `grpcio`, `protobuf`, `typing-extensions`). Switched to
  `--no-header` after discovering the header comment embeds the `-o` target
  path, which would make `requirements-sync` (task 3.5) always fail since it
  exports to a different temp path than the committed file's original path.
- [x] 3.4 Keep the already-drafted `make requirements` target in
  `ha-njord/Makefile` (`uv export --no-hashes --no-header -o requirements.txt`);
  comment already referenced `trivy.yaml` rather than the removed
  `skip-files` input.
- [x] 3.5 Keep the already-drafted `requirements-sync` job in
  `ha-njord/.github/workflows/ci.yml` (checkout, `astral-sh/setup-uv`,
  `uv export --no-hashes --no-header -o /tmp/requirements.txt`, diff against
  the committed `requirements.txt`, fail with a pointer to `make requirements`
  on mismatch).

## 4. Validation

- [x] 4.1 `cd ha-njord && uv export --no-hashes --no-header -o /tmp/requirements.txt && diff requirements.txt /tmp/requirements.txt`
  — confirmed the committed `requirements.txt` is current (no diff).
- [x] 4.2 Linted all three changed workflow YAML files with `actionlint`
  (`github-workflows/.github/workflows/security.yml`,
  `Signal.Bot/.github/workflows/security.yml`,
  `ha-njord/.github/workflows/security.yml`, `ha-njord/.github/workflows/ci.yml`)
  — all exit 0. Visually checked the two new `trivy.yaml` files (trivial
  3-line configs, no linter available for Trivy's own config schema).
- [ ] 4.3 Open PRs in dependency order — `github-workflows` first (additive,
  safe to merge alone since `trivy-config` defaults to a no-op for the other
  12 consumers), then `Signal.Bot` and `ha-njord` referencing
  `security.yml@main` once the shared workflow change is merged — and
  confirm each repo's `security` workflow run (manual `workflow_dispatch` or
  the `pull_request` trigger) completes without the removed-input error and
  without the dev-dependency-tree noise reappearing in Code Scanning.
- [ ] 4.4 Confirm ha-njord's `ci.yml` `requirements-sync` job passes on the PR.
