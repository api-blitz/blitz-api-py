# CLAUDE.md — agent guide for blitz-api-py

Typed Python SDK for the **Blitz API** (https://blitz-api.ai), a B2B data/search/
enrichment REST API. Two mandates drive everything: **(1) maximally typed** to
prevent user errors, **(2) automated releases on `main`** to PyPI.

**Read [`docs/CONTEXT.md`](docs/CONTEXT.md) first** — it's the extensive source of
truth (API surface, architecture, every design decision + rationale, data quirks,
and step-by-step playbooks). This file is just the quick rules.

## Golden rules

- **Never hand-edit `src/blitz_api/types/enums.py` _or_ `openapi/enum-source.json`** —
  both are generated. Run `uv run python scripts/gen_enums.py --fetch` to pull the live
  OpenAPI spec (`https://api.blitz-api.ai/openapi`), de-dup, and rewrite both; commit both.
  Only `--fetch` hits the network; the offline drift guard `gen_enums.py --check` re-renders
  from the committed cache. CI fails if `enums.py` is stale, and the release job blocks a
  publish whose enums drifted from the live spec.
- **Never hand-edit the sync client/resources** — `src/blitz_api/_client_sync.py` and
  everything under `src/blitz_api/resources/_sync/` are generated from the async source
  (`_client_async.py`, `resources/_async/`) by `uv run python scripts/gen_sync.py`. Edit
  the async file, regenerate, commit both. CI fails if stale (`gen_sync.py --check`).
- **Responses are hand-written models, not generated.** The Blitz OpenAPI spec types
  requests richly but its response schemas are *example-only* (no properties), so a
  generator can't produce typed responses. Derive response models from examples.
- **All response models subclass `BlitzModel`** (`extra="allow"`) so unknown/new API
  fields never break deserialization. Reuse the shared models in `types/shared.py`
  (one superset model with `Optional` fields, not per-endpoint duplicates).
- **Every change must keep all checks green** before you call it done:
  `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pyright && uv run pytest`,
  plus the drift guards `uv run python scripts/gen_enums.py --check` and
  `uv run python scripts/gen_sync.py --check`. mypy and pyright are both **strict**.
- **Conventional Commits are mandatory** (`feat:`/`fix:`/`feat!:`) — release-please
  derives the version and changelog from them, and PR titles are linted.
- **Add endpoints to the async source only** (`resources/_async/<group>.py`), then run
  `gen_sync.py`; the sync class is generated. Add sync+async tests. See the "Add a new
  endpoint" playbook in `docs/CONTEXT.md` §10.
- Don't commit build artifacts (`dist/`) or the venv; `uv.lock` IS committed.

## Where things live

- Clients: `src/blitz_api/_client.py` re-exports `BlitzAPI` (generated, `_client_sync.py`)
  and `AsyncBlitzAPI` (source, `_client_async.py`).
- Shared request pipeline / retry / errors: `src/blitz_api/_base_client.py`.
- Resources (one module per tag): `resources/_async/` (source) + `resources/_sync/`
  (generated). Sleep/timeout type aliases live in `_compat.py`.
- Types: `src/blitz_api/types/` (`shared.py`, `<group>.py` responses, `filters.py`
  request TypedDicts, `enums.py` generated).
- Pagination: `search.*` return auto-paging page objects (`CursorPage[T]`,
  `PageNumberPage[T]`, `Async*` twins; exported from `blitz_api`). Iteration is written in
  `_pagination_async.py` (gen_sync'd → `_pagination_sync.py`); shared state in
  `_pagination_base.py`. Edit the async source, never the sync.
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
