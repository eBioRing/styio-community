# Security Boundaries

**Purpose:** Define public-source and private-material boundaries for
`styio-community`.

**Last updated:** 2026-04-26

`styio-community` currently exposes a local HTTP API and static web UI. The
repository may publish standard server-side implementation code, but production
credentials, deployment private material, and generated secret bundles must not
enter GitHub.

## Boundary Rules

- Authentication, authorization, and identity implementation is not currently
  enabled for the local server. Any future hosted auth implementation must use
  documented standard protocols and must be reviewed before deployment.
- Privacy, PII, and personal data must not be committed in decision records,
  forum records, examples, fixtures, or logs.
- Password storage is not a repository responsibility. Production passwords
  must not be stored in JSON files, forum records, source code, examples, or
  tests.
- Secret, token, key, credential, Stitch API key, and deployment credential
  material must remain private and must not be committed.
- Production private material is offline or not committed to GitHub. `.env`
  files, private keys, generated credential bundles, and hosted server secrets
  must stay outside tracked source.
- Permission matrix and route authorization behavior for decision, forum,
  approval, rejection, dispatch, reaction, and demo routes must be explicit
  before hosted deployment.
- Deployment security config must cover TLS, CORS, CSRF, cookie, debug
  exposure, and hosted server deployment boundaries before cloud publication.
- SBOM, CVE, and dependency vulnerability scan evidence is required for
  `@google/stitch-sdk` and future npm or Python dependencies before release
  gates pass.
- DAST black-box penetration security regression must cover hosted or
  externally reachable community server surfaces before public deployment.
- Runtime secret manager or KMS key rotation owns production tokens, Stitch
  keys, deployment credentials, and hosted server secrets.
- Rate limit, anti replay nonce, replay protection, and idempotency boundaries
  must be documented for externally reachable POST routes before hosted
  deployment.
- Log redaction and audit log rules must prevent request tokens, PII, API keys,
  credentials, and decision-private data from being written to logs.
- SSRF egress allowlist, URL allowlist, and outbound request boundaries must be
  documented before adapters perform network calls.
- Command execution must use subprocess allowlist boundaries and reject shell
  injection surfaces in scripts and future server helpers.

## Current Public Source Boundary

The current implementation is local development tooling:

- `community/server.py` serves local HTTP routes and static files.
- `community/storage.py` and `community/forum.py` store local JSON state under
  ignored paths by default.
- `tools/stitch/` invokes a design helper dependency only from a developer
  machine. Generated artifacts are ignored.
- `.github/workflows/ci-gate.yml` runs repository-local unit tests.
- `.github/workflows/styio-audit.yml` runs the external Styio audit policy from
  `eBioRing/styio-audit@stable`.
