# Dependency Usage Boundary

**Purpose:** Record dependency authorization and usage boundaries for
`styio-community`.

**Last updated:** 2026-04-26

## Direct Dependency

`tools/stitch/package.json` declares one direct dependency:

| Dependency | Version | License Evidence | Commercial Authorization | Usage Boundary |
| --- | --- | --- | --- | --- |
| `@google/stitch-sdk` | `0.1.0` | `tools/stitch/package-lock.json` records `Apache-2.0` license metadata for the resolved package. | No paid commercial authorization, private marketplace approval, trial-only grant, or gated access is allowed for repository delivery. | May be used only by local Stitch design helper scripts under `tools/stitch`; generated output belongs under `.stitch/` and remains untracked. |

## Transitive Dependency Boundary

Transitive npm packages recorded in `tools/stitch/package-lock.json` are allowed
only when they resolve from the public npm registry and carry source-visible
open-source license metadata in the lockfile. If a future lockfile update adds
a package that requires commercial authorization, private approval, trial-only
use, or any non-open-source distribution boundary, that update must fail audit
until the package is removed or replaced.

## Operational Rules

- Dependency manifests are `tools/stitch/package.json` and
  `tools/stitch/package-lock.json`.
- `node_modules/` is a dependency cache and must not be committed.
- `.stitch/` is generated design output and must not be committed unless a
  future audit rule explicitly promotes a specific artifact.
- API keys, tokens, credentials, local state, and generated secret material must
  remain outside GitHub and outside distributed source archives.
