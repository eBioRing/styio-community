# styio-community

`styio-community` is the coordination and community-operations home for the
Styio ecosystem. It owns decision records, cross-repository workflow state, and
adapter-facing requests between upstream and downstream repositories.

The first implementation target is a minimal decision framework:

- a generic state machine for coordination records
- repository adapters for `styio` and `styio-view`
- a small web UI for human approval and execution opinions
- a local HTTP API that can later sit behind a private cloud service

The first two adapter directions are:

- `styio` syntax change -> community approval -> `styio-view` adaptation
- `styio-view` IDE capability gap -> community approval -> `styio` follow-up

## Run Locally

```sh
./scripts/run-dev.sh
```

Then open:

```text
http://127.0.0.1:8765
```

## Test

```sh
python3 -m unittest discover -s tests
```

## Stitch Theme

The Stitch prompt lives in
[docs/design/STITCH-THEME-BRIEF.md](docs/design/STITCH-THEME-BRIEF.md).

```sh
cd tools/stitch
npm install
STITCH_API_KEY=... npm run theme
```

Generated Stitch artifacts are written under `.stitch/`, which is ignored by
git. Do not commit API keys or generated credentials.

## Workflow Boundary

GitHub issues and pull requests are projection surfaces, not the source of
truth. The source of truth is the coordination record managed by this
repository. Repository adapters decide how that record is translated for each
downstream repo.

See [docs/workflows/DECISION-FRAMEWORK.md](docs/workflows/DECISION-FRAMEWORK.md).
