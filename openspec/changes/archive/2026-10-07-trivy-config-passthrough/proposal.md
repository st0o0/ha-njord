## Why

ha-njord's GitHub Dependabot alerts (112 open, now disabled in repo settings)
came almost entirely from `uv.lock` resolving the `dev` extra: pytest-homeassistant-custom-component`
pulls in the full `homeassistant` core package and its entire dependency
closure (Pillow, cryptography, urllib3, aiohttp, orjson, PyJWT, pyOpenSSL,
...) for testing only. None of it ships — `custom_components/njord/manifest.json`
only requires `grpcio` and `protobuf`. Scanning the combined lockfile with
any tool (Dependabot or Trivy) reproduces the same noise.

ha-njord already runs a Trivy filesystem scan via the shared
`st0o0/github-workflows/.github/workflows/security.yml` reusable workflow.
That workflow only exposes two narrow, repo-specific inputs (`skip-dirs`,
default `'docs'`; `skip-files`, just added and not yet merged) for tuning the
scan. Every future tuning need (a new skip pattern, a severity override) would
otherwise require another round-trip through the shared repo. Since only one
other consumer (Signal.Bot, which relies on the `skip-dirs: 'docs'` default
for its VitePress doc site's own lockfile) is actually affected by the fs-scan
inputs today, replacing them with a single generic config passthrough is a
small, low-risk change that benefits every current and future consumer.

## What Changes

- **BREAKING** (shared workflow consumers only): `github-workflows/.github/workflows/security.yml`
  removes the `skip-dirs` and `skip-files` inputs from the `workflow_call`
  interface and adds a single generic `trivy-config` string input (default
  `''`), passed as `trivy-config: ${{ inputs.trivy-config }}` to the
  `aquasecurity/trivy-action` step in both the `trivy-image` and `trivy-fs`
  jobs. Consumers that want scan tuning (skip-dirs, skip-files, etc.) now
  supply their own `trivy.yaml` and point `trivy-config` at it instead of a
  named input in the shared workflow.
- Signal.Bot (the only consumer relying on the removed `skip-dirs` default)
  gets a `trivy.yaml` (`scan.skip-dirs: [docs]`) and sets `trivy-config: trivy.yaml`
  in its own `security.yml`.
- ha-njord gets:
  - `requirements.txt`, the production-only dependency export (`uv export --no-hashes`
    — currently `grpcio`, `protobuf`, `typing-extensions`) that Trivy scans
    instead of `uv.lock`.
  - `trivy.yaml` (`scan.skip-files: [uv.lock]`) and `security.yml` updated to
    `trivy-config: trivy.yaml`.
  - A `make requirements` target to regenerate `requirements.txt`.
  - A `requirements-sync` CI job that fails if `requirements.txt` drifts from
    `uv.lock`.
- The 10 other consumers of the shared workflow (all `scan-type: image`) and
  the 2 remaining `scan-type: fs` consumers without a skip need (Flickr.Net,
  WebSocket.Rx) require no changes — `trivy-config` defaults to `''` and
  `trivy-action` behaves exactly as it does today.
- Supersedes the uncommitted, not-yet-merged `skip-files` input work already
  sitting in the `github-workflows` and `ha-njord` working trees (that
  approach is replaced by `trivy-config`, not layered on top of it).

## Non-goals

- Not re-enabling or reconfiguring Dependabot — the user already disabled
  Dependabot alerts for ha-njord via the GitHub UI; this change is Trivy-only.
- Not changing scan severity, scanners, or `ignore-unfixed` behavior — those
  stay hardcoded in the shared workflow (Trivy's Viper precedence means
  explicit action inputs always win over `trivy.yaml` for the same key, so
  moving them into `trivy.yaml` would have no effect anyway).
- Not migrating Flickr.Net or WebSocket.Rx — they don't rely on the removed
  defaults and need no `trivy.yaml`.
- Not touching the 10 `scan-type: image` consumers' workflow files — the new
  `trivy-config` input is additive and defaults to a no-op for them.
- No gRPC endpoints are involved — this is CI/supply-chain tooling only, not
  an ha-njord runtime/integration change.

## Capabilities

### New Capabilities

- `dependency-scan-config`: observable contract for how ha-njord's CI scopes
  its Trivy filesystem scan to the shipped dependency footprint (not HA
  entity behavior — a CI/supply-chain contract, scoped to this repo's own
  `security.yml`/`trivy.yaml`/`requirements.txt`).

### Modified Capabilities

None — no observable HA entity or integration behavior changes. The
`github-workflows` shared-workflow interface change and the Signal.Bot
migration are cross-repo infrastructure tasks without their own OpenSpec
setup; they are tracked in this change's `design.md`/`tasks.md`, not as a
`specs/<name>/spec.md` delta (OpenSpec specs track per-repo observable
behavior, and those two repos have no spec tree to delta against).

## Impact

- **Repos touched**: `github-workflows` (shared `security.yml`), `Signal.Bot`
  (`trivy.yaml` + `security.yml`), `ha-njord` (`requirements.txt`,
  `trivy.yaml`, `security.yml`, `Makefile`, `ci.yml`).
- **CI behavior**: ha-njord's and Signal.Bot's security scans start passing
  cleanly (scoped to what each repo actually ships); the other 12 shared-workflow
  consumers see no behavior change.
- **Dependencies**: none added; `uv export` (already bundled with `uv`) is the
  only new tool invocation, used in CI and via `make requirements`.
- **Risk**: the shared workflow's public `workflow_call` interface changes
  (two inputs removed). Since only Signal.Bot and ha-njord pass those inputs
  today, the blast radius is exactly those two repos, both covered by this
  change's tasks.
