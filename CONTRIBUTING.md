# Contributing

## Local setup

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync                 # create the venv and install runtime + dev dependencies
```

## Checks

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run mypy                  # strict type-check (src, tests, scripts, examples)
uv run pyright               # second type-checker
uv run pytest                # tests (sync + async)
```

CI (`.github/workflows/ci.yml`) runs all of the above, plus a test matrix on
Python 3.10–3.14.

## Generated enums

`src/blitz_api/types/enums.py` is **generated** from `openapi/enum-source.json`
(value lists extracted verbatim from the Blitz OpenAPI v2 spec). Never edit it by
hand.

```bash
python scripts/gen_enums.py            # regenerate
python scripts/gen_enums.py --check     # verify it is in sync (CI runs this)
```

To update the taxonomy, edit `openapi/enum-source.json`, regenerate, and commit.

## Generated sync client

The async client and resources are the source of truth; the **sync** client
(`_client_sync.py`) and resources (`resources/_sync/`) are generated from them:

```bash
python scripts/gen_sync.py             # regenerate the sync mirror
python scripts/gen_sync.py --check      # verify it is in sync (CI runs this)
```

Edit the async file (`_client_async.py` or `resources/_async/<group>.py`), regenerate,
and commit both. Never hand-edit the generated `_sync` files.

## Project layout

```
src/blitz_api/
  _client.py        re-exports BlitzAPI + AsyncBlitzAPI
  _client_async.py  AsyncBlitzAPI (hand-written source)
  _client_sync.py   BlitzAPI (generated from _client_async.py)
  _base_client.py   request pipeline, retry/backoff, error mapping
  _rate_limit.py    sync + async sliding-window limiters
  _compat.py        sleep + timeout type aliases (async->sync rename seam)
  _exceptions.py    exception hierarchy
  resources/        _async/ (source) + _sync/ (generated): account/search/enrichment/utils
  types/            response models (Pydantic) + request filters (TypedDict) + enums
```

## Releases (automated)

Releases are driven by [release-please](https://github.com/googleapis/release-please)
and published to PyPI via **Trusted Publishing (OIDC)** — no API token is stored
anywhere.

The flow:

1. Land PRs to `main` using **[Conventional Commits](https://www.conventionalcommits.org/)**
   (`feat:`, `fix:`, `feat!:` / `BREAKING CHANGE:`). PR titles are linted because
   squash-merges use the title as the commit subject.
2. release-please maintains a **"Release PR"** that bumps the version
   (`src/blitz_api/_version.py`), updates `CHANGELOG.md`, and updates the manifest.
3. **Merging the Release PR** tags the release, creates a GitHub Release, and the
   `publish` job builds (`uv build`) and uploads to PyPI via OIDC.

`chore:`/`docs:`/`refactor:` commits do not trigger a release on their own.

### One-time setup (must be done by a maintainer)

These steps cannot be automated from the repo:

1. **PyPI Trusted Publisher** — at <https://pypi.org/manage/account/publishing/>,
   add a publisher (use a *pending* publisher before the first release):
   - PyPI project name: `blitz-api-py`
   - Owner / repository: this repo
   - Workflow filename: `release.yml`
   - Environment name: `pypi`

   All four must match exactly or OIDC auth fails.
2. **GitHub Environment** — create an environment named `pypi`
   (Settings → Environments) and, recommended, restrict it to the `main` branch
   and/or add required reviewers.
3. **Branch protection** — protect `main`, require the CI checks, and require PRs.
4. **Actions permissions** — Settings → Actions → General → enable
   "Allow GitHub Actions to create and approve pull requests" so release-please can
   open its Release PR.

### First release

The manifest starts at `0.1.0`. To cut the initial `0.1.0` release, either tag it
manually once, or add a commit/PR with `Release-As: 0.1.0` in the body so
release-please proposes exactly that version. Subsequent releases are fully
automatic from Conventional Commits.
