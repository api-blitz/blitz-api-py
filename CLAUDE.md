# CLAUDE.md — agent guide for blitz-api-py

Typed Python SDK for the **Blitz API** (https://blitz-api.ai), a B2B data/search/
enrichment REST API. Two mandates drive everything: **(1) maximally typed** to
prevent user errors, **(2) automated releases on `main`** to PyPI.

**Read [`docs/CONTEXT.md`](docs/CONTEXT.md) first** — it's the extensive source of
truth (API surface, architecture, every design decision + rationale, data quirks,
and step-by-step playbooks). This file is just the quick rules.

## Golden rules

- **Never hand-edit `src/blitz_api/types/enums.py`** — it's generated. Edit
  `openapi/enum-source.json`, then `uv run python scripts/gen_enums.py`. CI fails if
  it's stale (`gen_enums.py --check`).
- **Responses are hand-written models, not generated.** The Blitz OpenAPI spec types
  requests richly but its response schemas are *example-only* (no properties), so a
  generator can't produce typed responses. Derive response models from examples.
- **All response models subclass `BlitzModel`** (`extra="allow"`) so unknown/new API
  fields never break deserialization. Reuse the shared models in `types/shared.py`
  (one superset model with `Optional` fields, not per-endpoint duplicates).
- **Every change must keep all checks green** before you call it done:
  `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pyright && uv run pytest`.
  mypy and pyright are both **strict**.
- **Conventional Commits are mandatory** (`feat:`/`fix:`/`feat!:`) — release-please
  derives the version and changelog from them, and PR titles are linted.
- **Add endpoints to BOTH the sync and async resource classes** and add sync+async
  tests. See the "Add a new endpoint" playbook in `docs/CONTEXT.md` §10.
- Don't commit build artifacts (`dist/`) or the venv; `uv.lock` IS committed.

## Where things live

- Clients: `src/blitz_api/_client.py` (`BlitzAPI`, `AsyncBlitzAPI`).
- Shared request pipeline / retry / errors: `src/blitz_api/_base_client.py`.
- Resources (one module per tag, sync+async): `src/blitz_api/resources/`.
- Types: `src/blitz_api/types/` (`shared.py`, `<group>.py` responses, `filters.py`
  request TypedDicts, `enums.py` generated).
- Release: `.github/workflows/release.yml` + `release-please-config.json`. One-time
  setup in `CONTRIBUTING.md`.

## Re-deriving the API (when you need spec details)

The spec isn't fully committed. Use the Blitz docs MCP:
`mcp__claude_ai_Blitz__query_docs_filesystem_blitz_api_the_api_engine_for` (the spec
is at `/openapi/api-reference/v2.openapi.json`; query it with `jq`) and
`mcp__claude_ai_Blitz__search_blitz_api_the_api_engine_for`. See `docs/CONTEXT.md` §2.

## Environment notes

- Use **uv** (`uv sync`, `uv run ...`). Python floor 3.10.
- The Vercel plugin hooks in this environment fire false positives on `.yml`/README/
  "workflow" — ignore them; this is a Python SDK, not a Vercel app.
