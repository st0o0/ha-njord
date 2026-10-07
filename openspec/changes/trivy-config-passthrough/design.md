## Context

`st0o0/github-workflows/.github/workflows/security.yml` is a reusable
`workflow_call` workflow with two jobs: `trivy-image` (Docker image scan) and
`trivy-fs` (filesystem/dependency scan), both running `aquasecurity/trivy-action@v0.36.0`
and uploading SARIF to GitHub Code Scanning. 14 repos consume it today:

| scan-type | repos |
|---|---|
| `image` (default) | FunkArr, FunkCrawlArr, OpenTraverse, bifrost, eir, forseti, mjolnir, njord, ran, shutterfall, var |
| `fs` | Flickr.Net, WebSocket.Rx, Signal.Bot, ha-njord |

Only `trivy-fs` reads `skip-dirs` (input, default `'docs'`) and the
not-yet-merged `skip-files` (added for ha-njord's `uv.lock` problem but never
committed). Checking each `fs` consumer's repo tree:

- Flickr.Net: no `docs/` directory — never needed the default.
- WebSocket.Rx: `docs/logo/` only, no lockfile — never needed the default.
- Signal.Bot: `docs/package.json` (VitePress site with its own npm lockfile)
  — actively relies on the `skip-dirs: 'docs'` default today.
- ha-njord: needs to skip `uv.lock` (the trigger for this change).

So exactly one existing consumer (Signal.Bot) depends on the input being
removed; the other 12 are unaffected either way.

## Goals / Non-Goals

**Goals:**
- Give every current and future consumer of the shared `security.yml` a way
  to tune Trivy's fs/image scan (skip files, skip dirs, and anything else
  Trivy's config file supports) without editing the shared workflow again.
- Fix ha-njord's scan so it reflects what actually ships
  (`grpcio`/`protobuf`/`typing-extensions`), not the `homeassistant` test
  dependency's full closure.
- Keep the migration blast radius to exactly the repos that need it
  (Signal.Bot, ha-njord); zero changes for the other 12 consumers.

**Non-Goals:**
- Making `severity`, `scanners`, or `ignore-unfixed` configurable per-repo —
  out of scope for this change, and moot anyway (see Decisions: Viper
  precedence).
- A generic "every repo gets a trivy.yaml" rollout — only repos that actually
  need scan tuning get one.
- Changing how Dependabot is configured — already handled via the GitHub UI
  by the user, outside this change.

## Decisions

### Replace `skip-dirs`/`skip-files` with a single `trivy-config` passthrough

**Decision**: Remove the `skip-dirs` and `skip-files` inputs from
`security.yml`'s `workflow_call.inputs`. Add one input, `trivy-config`
(string, default `''`), passed as `trivy-config: ${{ inputs.trivy-config }}`
to the `aquasecurity/trivy-action` step in both `trivy-image` and `trivy-fs`
jobs. Consumers that need scan tuning check in their own `trivy.yaml` and
point `trivy-config` at it.

**Why**: Every previous tuning need (skip-dirs, now skip-files) required a
new named input in the shared workflow — a round-trip through a repo other
than the one that actually needs the behavior. `trivy-config` is a generic
passthrough: once added, no future tuning need (another skip pattern, a
repo-specific allowlist) ever requires touching `github-workflows` again.

**Alternatives considered**:
- *Keep `skip-dirs`, just add `skip-files`* (the original, already-drafted
  approach): rejected — it fixes today's problem but repeats the same
  pattern next time a new knob is needed. Already in the working tree as
  uncommitted changes; this change replaces that approach rather than
  layering `trivy-config` on top of it.
- *No shared-workflow change at all; ha-njord calls `trivy-action` directly*:
  rejected — breaks the project's consistent pattern of centralizing scan
  logic in `github-workflows`, and ha-njord would be the only repo
  maintaining its own copy of the Trivy step.
- *Ship a default `trivy.yaml` inside `github-workflows` itself*: rejected —
  the reusable workflow only checks out the *consumer's* repo
  (`actions/checkout@v7` runs in the consumer's context), so a file living in
  `github-workflows` isn't present on disk unless separately fetched, adding
  complexity for no benefit over a per-consumer file.

### Leave `severity`/`scanners`/`ignore-unfixed` hardcoded

**Decision**: Do not move `severity: CRITICAL,HIGH`, `scanners: vuln,secret[,misconfig]`,
or `ignore-unfixed: true` into `trivy.yaml`-controllable territory.

**Why**: Trivy resolves configuration via Viper's precedence order — CLI
flag/action input > environment variable > config file > default. Since
`security.yml` already passes these three as explicit `with:` values (which
`trivy-action` turns into CLI flags), anything a consumer's `trivy.yaml` sets
for the same keys would be silently overridden. Only keys the shared workflow
does *not* already pass explicitly (`skip-files`, `skip-dirs` after removal)
are actually governed by `trivy-config`. Documenting this now avoids a future
consumer wasting time setting `severity` in their `trivy.yaml` and wondering
why it has no effect.

### ha-njord scans `requirements.txt`, not `uv.lock`

**Decision**: Export the production-only dependency closure to a committed
`requirements.txt` via `uv export --no-hashes -o requirements.txt` (no
`--extra`/`--all-extras`, so the `dev` extra is excluded by default). Point
`trivy.yaml`'s `scan.skip-files` at `uv.lock` so Trivy scans
`requirements.txt` instead. Add a `make requirements` target to regenerate it
and a CI job (`requirements-sync`) that fails if it drifts from `uv.lock`.

**Why**: `uv export` without extras already produces exactly the shipped
footprint (verified locally: `grpcio==1.84.0`, `protobuf==6.33.6`,
`typing-extensions==4.16.0`, matching `custom_components/njord/manifest.json`'s
`requirements`). This gives Trivy a real, meaningful target instead of either
scanning nothing (if `uv.lock` were just skipped outright with no
replacement) or scanning everything (today's 100+-finding noise).

**Alternatives considered**:
- *Just skip `uv.lock` with no replacement file*: rejected — loses all
  vulnerability visibility into the 3 packages that actually ship.
- *Point `scan-ref` at a subdirectory without `uv.lock`*: rejected —
  `scan-ref` isn't currently parameterized in the shared workflow, and
  `custom_components/njord/manifest.json` isn't a format Trivy understands
  natively; `requirements.txt` is a format it parses out of the box.
- *Maintain `requirements.txt` by hand*: rejected — the `requirements-sync`
  CI check makes drift a hard CI failure instead of a trust exercise.

## Risks / Trade-offs

- **[Risk]** Removing `skip-dirs`/`skip-files` from `security.yml`'s public
  interface is a breaking change to a `workflow_call` contract.
  → **Mitigation**: only Signal.Bot and ha-njord pass those inputs today
  (verified by grepping every consumer's `security.yml`); both are migrated
  in this change's tasks in the same PR wave as the shared-workflow change.
- **[Risk]** `requirements.txt` could silently drift from `uv.lock` if someone
  edits `pyproject.toml` without running `make requirements`.
  → **Mitigation**: `requirements-sync` CI job diffs a fresh `uv export`
  against the committed file and fails the PR if they differ.
- **[Risk]** A future consumer might expect `trivy.yaml` to control
  `severity`/`scanners`/`ignore-unfixed` and be confused when it doesn't.
  → **Mitigation**: documented explicitly in this design and in a code
  comment on the `trivy-config` input description in `security.yml`.

## Migration Plan

1. Land the `github-workflows` change (remove `skip-dirs`/`skip-files`, add
   `trivy-config`) — safe on its own for the 12 unaffected consumers since
   the new input defaults to a no-op.
2. In the same wave, update Signal.Bot (`trivy.yaml` + `security.yml`) and
   ha-njord (`requirements.txt`, `trivy.yaml`, `security.yml`, `Makefile`,
   `ci.yml`) so no consumer is left calling a removed input.
3. No rollback complexity beyond reverting the commits — the shared workflow
   change and the two consumer migrations are independent, small diffs.

## Open Questions

None — scope, mechanism, and affected repos are all confirmed against the
actual repo trees.
