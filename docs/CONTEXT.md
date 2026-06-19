# blitz-api-py — Project Context

> Source-of-truth reference for maintaining and extending this repo. Read this
> before making changes so you don't re-derive decisions already made.
> Companion docs: [`README.md`](../README.md) (users), [`CONTRIBUTING.md`](../CONTRIBUTING.md)
> (dev workflow + release setup), [`CLAUDE.md`](../CLAUDE.md) (agent quick rules).

---

## 1. What this repo is

The official **typed Python SDK for the Blitz API** (https://blitz-api.ai), a B2B
data / GTM REST API (people & company search, contact enrichment, utilities).

Two design mandates from the project owner, which everything else serves:

1. **As strongly typed as possible** — prevent user mistakes via static typing
   (IDE autocomplete + mypy/pyright) *and* runtime validation.
2. **Automated releases on `main`** — merging to `main` publishes to PyPI with no
   manual token handling.

Distribution name: **`blitz-api-py`** (PyPI). Import name: **`blitz_api`**.

---

## 2. The Blitz API (what we wrap)

- **Base URL**: `https://api.blitz-api.ai`
- **Auth**: `x-api-key` HTTP header (NOT `Authorization`). Key from
  [app.blitz-api.ai](https://app.blitz-api.ai).
- **Rate limit**: 5 req/s on all plans; per-key value in
  `key-info.max_requests_per_seconds`.
- **OpenAPI**: 3.1.0, version `2.0.0`. All endpoints are `/v2/...`.
- **Status conventions**: 401 invalid/missing key · 402 insufficient credits ·
  404 key not found · 429 rate limited (official client waits 60 s then retries) ·
  5xx server error.

### Endpoint → method → response model (all 15)

| HTTP | Path | SDK method | Response model |
| --- | --- | --- | --- |
| GET | `/v2/account/key-info` | `account.key_info()` | `KeyInfo` |
| POST | `/v2/search/waterfall-icp-keyword` | `search.waterfall_icp()` | `WaterfallIcpResponse` |
| POST | `/v2/search/employee-finder` | `search.employee_finder()` | `PageNumberPage[Person]` |
| POST | `/v2/search/people` | `search.people()` | `CursorPage[Person]` |
| POST | `/v2/search/companies` | `search.companies()` | `CursorPage[Company]` |
| POST | `/v2/enrichment/email` | `enrichment.email()` | `EmailEnrichmentResponse` |
| POST | `/v2/enrichment/phone` | `enrichment.phone()` | `PhoneEnrichmentResponse` |
| POST | `/v2/enrichment/email-to-person` | `enrichment.email_to_person()` | `EmailToPersonResponse` |
| POST | `/v2/enrichment/phone-to-person` | `enrichment.phone_to_person()` | `PhoneToPersonResponse` |
| POST | `/v2/enrichment/company` | `enrichment.company()` | `CompanyEnrichmentResponse` |
| POST | `/v2/enrichment/domain-to-linkedin` | `enrichment.domain_to_linkedin()` | `DomainToLinkedinResponse` |
| POST | `/v2/enrichment/linkedin-to-domain` | `enrichment.linkedin_to_domain()` | `LinkedinToDomainResponse` |
| POST | `/v2/enrichment/company-distribution-by-country` | `enrichment.company_distribution_by_country()` | `CompanyCountryDistributionResponse` |
| POST | `/v2/enrichment/company-distribution-by-department` | `enrichment.company_distribution_by_department()` | `CompanyDepartmentDistributionResponse` |
| POST | `/v2/utils/current-date` | `utils.current_date()` | `CurrentDateResponse` |

### How to re-derive the API surface (IMPORTANT)

The API spec/docs are not committed in full. They come from the **Blitz docs MCP
server** (a Claude connector). To inspect or refresh:

- `mcp__claude_ai_Blitz__search_blitz_api_the_api_engine_for` — conceptual search.
- `mcp__claude_ai_Blitz__query_docs_filesystem_blitz_api_the_api_engine_for` — a
  read-only shell over the docs. The OpenAPI spec lives at
  `/openapi/api-reference/v2.openapi.json`. Use `jq` against it, e.g.
  `jq '.paths["/v2/search/people"].post.requestBody...' v2.openapi.json`.

If the MCP is unavailable, the `.md` mirror of any docs page is at
`https://docs.blitz-api.ai/<path>.md` and the index at
`https://docs.blitz-api.ai/llms.txt`.

---

## 3. THE crux: why response models are hand-written

This is the single most important fact about this codebase:

- **Request bodies in the spec are richly typed** — nested objects, `required`,
  defaults, and large `enum`s (e.g. the ~534-value `industry`). These are modeled
  precisely (`TypedDict` filters + generated enums).
- **Response bodies in the spec are example-only** — every response schema is
  `{"type": "object", "example": {...}}` with **no `properties`**. An off-the-shelf
  OpenAPI generator (openapi-python-client, datamodel-code-generator) would emit
  `dict[str, Any]` for every response → unacceptable for mandate #1.

Therefore **response models are hand-derived** from the example JSON (and the docs'
response-field tables). Do NOT try to auto-generate them — the spec can't drive it.
The trade-off accepted: when the API changes a response shape, a human updates the
model (the `extra="allow"` base means new fields don't break anything in the
meantime — see §5).

---

## 4. Architecture map

```
src/blitz_api/
  __init__.py        Public surface: BlitzAPI, AsyncBlitzAPI, exceptions, __version__,
                     and a few common types. Full types under blitz_api.types.
  _version.py        Single source of version. Line has `# x-release-please-version`
                     so release-please bumps it. hatchling reads it (dynamic version).
  _constants.py      Base URL, env-var name, header name, timeout, retry count,
                     default rate (5 rps), default 429 wait (60s), User-Agent.
  _exceptions.py     Exception hierarchy (see §6).
  _rate_limit.py     RateLimiter + AsyncRateLimiter: sliding-window limiters (<= rps per
                     rolling 1s). Clock & sleep injectable (monotonic=, sleep=) for tests.
  _base_client.py    IO-FREE shared logic: to_jsonable() (enum->value, drop None),
                     _retry_after_seconds() (parse Retry-After: delta or HTTP-date),
                     BaseClient (api-key resolution, _build_url, _build_headers,
                     _should_retry, _should_retry_exception, _backoff_seconds,
                     _retry_delay (clamped to MAX_RETRY_WAIT), _make_status_error,
                     _parse_model (wraps json/pydantic errors -> APIResponseValidationError)).
                     _STATUS_EXCEPTIONS maps code->exception.
  _compat.py         AsyncSleep/SyncSleep + TimeoutParam type aliases. The async ones are
                     token-renamed by gen_sync (the generator can't rewrite Awaitable[...]).
  _client_async.py   AsyncBlitzAPI (async). Owns an httpx client + a per-endpoint rate
                     limiter registry (_limiter_for) and implements _request() (the retry
                     loop). HAND-WRITTEN SOURCE.
  _client_sync.py    BlitzAPI (sync). GENERATED from _client_async.py by gen_sync.py.
  _client.py         Thin re-export of BlitzAPI + AsyncBlitzAPI (stable import path).
  resources/         One module per OpenAPI tag group.
    _async/<g>.py    Async resource classes (AsyncAccountResource, ...). HAND-WRITTEN SOURCE.
    _sync/<g>.py     Sync resource classes (AccountResource, ...). GENERATED by gen_sync.py.
    __init__.py      Re-exports both flavours.
  types/
    _models.py       BlitzModel — base for all responses (extra="allow", see §5).
    shared.py        Person, Experience, Education, Certification, Location, HQ, Company.
    enums.py         GENERATED. Industry (534) + CompanyType/EmployeeRange/Continent/
                     SalesRegion/JobFunction/JobLevel/FundingType. Never hand-edit (see §7).
    filters.py       Request TypedDicts (CompanyFilter, PeopleFilter, CascadeTier, ...)
                     and *Value type aliases (e.g. IndustryValue = Industry | str).
    account.py       KeyInfo, ActivePlan
    search.py        WaterfallIcpResponse, WaterfallIcpMatch (the paginated search results
                     return the page classes below, not per-endpoint models)
    enrichment.py    7 enrichment response models + EmailMatch + the two company-distribution
                     responses (CompanyCountryDistributionResponse / *Department*) + per-item models
    utils.py         CurrentDateResponse
    __init__.py      Re-exports the public type surface (grouped).
  _pagination_base.py   BasePage — shared pagination state/context + _bind (no async).
  _pagination_async.py  AsyncPaginator/AsyncCursorPage/AsyncPageNumberPage. HAND-WRITTEN SOURCE.
  _pagination_sync.py   Paginator/CursorPage/PageNumberPage. GENERATED by gen_sync.py.
  py.typed           PEP 561 marker (ships in the wheel; makes our types visible).

scripts/gen_enums.py        --fetch pulls the live OpenAPI spec → rewrites the
                            openapi/enum-source.json cache + types/enums.py; --check guards drift (offline).
scripts/gen_sync.py         Regenerates the sync client+resources from the async source
                            (token-rename + strip async/await via tokenize-rt). --check guards drift.
openapi/enum-source.json    GENERATED cache of enum value lists (offline codegen source; see §5/§7).
tests/                       pytest + pytest-httpx + pytest-asyncio (see §8).
examples/                    quickstart.py, async_quickstart.py (type-checked docs).
.github/workflows/           ci.yml, release.yml, pr-title.yml (see §9).
release-please-config.json, .release-please-manifest.json   release automation config.
```

### Request flow
`resource.method(...)` builds a body dict → `client._request(method, path, body, cast_to,
timeout)` → `to_jsonable(body)` (enum→value, strip None) → await a rate-limit slot
(sliding window, per-endpoint limiter keyed by path) → httpx dispatch → on success `_parse_model` (wraps bad bodies as
`APIResponseValidationError`); on non-2xx map to an exception; on 429/5xx retry per policy,
on connect/pool transport errors retry, on read/write timeout raise.

---

## 5. Design decisions & rationale (the "why")

Confirmed with the owner up front:

- **Pydantic v2 for responses + TypedDict for requests.** Runtime validation +
  attribute access + autocomplete for outputs; static-only, zero-overhead, dict-literal
  ergonomics for inputs. (Considered & rejected: zero-dependency dataclasses — no
  runtime validation, more boilerplate.)
- **Both sync (`BlitzAPI`) and async (`AsyncBlitzAPI`)** over **httpx**, sharing a
  pure `BaseClient`. (Cheap to build together; costly to retrofit async later.) The
  **async side is the hand-written source of truth; the sync side is generated** from it
  by `scripts/gen_sync.py` (the unasync technique: strip `async`/`await`, token-rename
  `AsyncBlitzAPI`→`BlitzAPI`, etc.). This removes the sync/async duplication while keeping
  both fully, explicitly typed — Python can't make one function both sync and async, and a
  runtime/metaprogramming dedup would have sacrificed mandate #1. A CI drift guard
  (`gen_sync.py --check`) fails the build if the generated files are stale, exactly like
  the enum guard.
- **release-please PR gate** → tag → **PyPI Trusted Publishing (OIDC)**. Avoids
  releasing on every trivial commit and stores no token. (See §9.)
- **Distribution `blitz-api-py`, import `blitz_api`.**

Internal decisions worth preserving:

- **`extra="allow"` on `BlitzModel`** (`types/_models.py`) — forward compatibility.
  New API response fields are preserved (reachable via `model.model_extra`) instead
  of raising. Known fields stay precisely typed. This is what lets hand-written
  models survive API additions without an SDK release.
- **Superset models with nullable fields, not per-endpoint duplicates.** The API
  returns slightly different shapes for the "same" object across endpoints. We model
  one `Person`/`Company`/`Experience`/etc. with the union of fields, all `Optional`.
  Examples: `Experience.company_name` is populated only by `search.people`;
  `HQ.postcode`/`street` only by `enrichment.company`. Absence is honestly `None`.
- **Pagination uses auto-paging page objects** (see §11 decision log). Cursor-based
  endpoints (`people`/`companies`) return `CursorPage[Person|Company]`; the page-based
  `employee_finder` returns `PageNumberPage[Person]` (`Async*` twins for the async client).
  Iterating a page transparently fetches the next one; `.auto_paging_iter(max_items=)`,
  `.iter_pages(max_pages=)`, and `.get_next_page()` give bounded / per-page / manual control.
  `waterfall_icp` is not paginated — it returns `WaterfallIcpResponse` wrapping
  `{icp, ranking, person}` matches. Page classes live in `_pagination_async.py` (→ generated
  `_pagination_sync.py`) with shared state in `_pagination_base.py`.
- **`str`-backed enums that also accept raw strings.** Enums subclass `str` and the
  request filter aliases are `Enum | str` (e.g. `IndustryValue = Industry | str`), so
  a value missing from the generated taxonomy never blocks a caller. `to_jsonable`
  serializes enums to `.value`.
- **Generated `enum-source.json` cache, pulled from the live spec.** `gen_enums.py
  --fetch` walks the live OpenAPI spec (`https://api.blitz-api.ai/openapi`), maps each
  inlined enum to a class by its owning request property (`PROPERTY_TO_CLASS`), collapses
  the 6–12 byte-identical duplicate occurrences, and caches just the de-duplicated value
  lists in `openapi/enum-source.json` (99% of the 130 KB spec is repeated enum arrays, so
  we don't vendor the whole thing). That cache is the **offline** drift-guard source: the
  default render and `--check` read it without the network, so per-PR CI never breaks when
  the spec endpoint is down or changes — refreshes land as deliberate `--fetch` PRs, and a
  release-time gate blocks shipping enums stale vs prod (§9). The generator **throws**
  rather than silently shrink output if a mapped enum goes missing upstream or its
  occurrences diverge, and warns-and-ignores unmapped enums. If you need the full spec,
  pull it from the Blitz MCP (§2).
- **Client-side rate limiter is a per-process sliding window, applied per endpoint.** At
  most `rps` requests may begin in any rolling 1-second window (`_rate_limit.py`), matching
  the Blitz docs ("max 5 per 1000 ms") and the official reference client. A token bucket
  was rejected: its initial capacity lets a fresh client fire `rps` requests *and* refill
  within the first second, briefly doubling the rate — the exact pattern the docs say
  triggers 429 on bulk runs. Default 5 rps; `rate_limit_rps=None` disables it.
  (Auto-detecting the limit from `key-info` on first call was considered but not
  implemented — would add a surprise network call on construction.)
  The client holds **one limiter per endpoint path**, built lazily in
  `AsyncBlitzAPI._limiter_for` and keyed by the request path (`self._rate_limiters: dict`),
  so each endpoint throttles independently — the rate limit on `.email` is separate from
  `.phone`. This mirrors the *server*, whose limit is also per endpoint — 5 RPS on
  `/enrichment/email` and 5 RPS on `/enrichment/phone` run concurrently, and
  `key-info.max_requests_per_seconds` is the per-endpoint budget — so a single client stays
  under the limit on every endpoint without endpoints competing. `blitz-api-js` does the
  same (a token-bucket limiter per endpoint), so the two SDKs stay in parity; only the
  algorithm differs (sliding window vs. token bucket). The remaining overflow case is
  **multiple processes** sharing one endpoint's budget, which leans on the 429 → retry
  backstop.
- **Retry policy:** 429 → wait `Retry-After` (delta-seconds or HTTP-date), else 60 s,
  **clamped to `MAX_RETRY_WAIT_SECONDS` (120 s)** so a pathological header can't sleep the
  client for hours; 5xx → exponential backoff + jitter; **401/402/404 → raise
  immediately, no retry** (retrying wastes credits/time). Transport errors are split by
  whether the request could already have been processed: **connect timeout / connect
  error / pool timeout → retry** (nothing was sent); **read/write timeout → raise
  immediately** (`_should_retry_exception`) — retrying a billable POST that the server
  already processed would double-charge the caller. Up to `max_retries` (default 3).
- **Successful responses are validated inside the error hierarchy.** `_parse_model` wraps
  `response.json()` and `model_validate()`; a 2xx body that isn't JSON (proxy HTML, empty
  body) or doesn't match the model raises `APIResponseValidationError(BlitzError)` instead
  of leaking a raw `json`/`pydantic` error, honouring "catch `BlitzError` for anything".
- **Per-call `timeout=`** is accepted on every resource method (and threaded through
  `_request`), since the docs recommend different timeouts per endpoint (10 s search, 20 s
  validation). Passing both `http_client` and `timeout` raises `ValueError` (a supplied
  client carries its own timeout) rather than silently ignoring one.
- **Enum filter typing is advisory, not enforced.** `IndustryValue = Industry | str`
  collapses to `str` for the type checker (the enums subclass `str`), so the taxonomy is
  an autocomplete aid; a typo'd value is sent as-is, not caught by mypy. Deliberate
  "never blocked" trade-off (see §7).
- **Tooling suppressions (deliberate, localized):**
  - `pyright`: `reportPrivateUsage = false` — resources call the client's internal
    `_request` across modules; this is internal encapsulation, not a public-API
    concern (mypy allows it).
  - `ruff`: `extend-exclude` the generated `types/enums.py` (the generator owns its
    formatting; a CI drift guard verifies it). `RUF012` ignored under `types/*` —
    `= []` defaults are safe on Pydantic models (deep-copied per instance) and keep
    pyright happy (it infers type from the annotation). `RUF022` ignored — `__all__`
    is grouped by category, not alphabetized.
  - mypy uses the `pydantic.mypy` plugin and is `strict`.

---

## 6. Exception hierarchy (`_exceptions.py`)

```
BlitzError
├── APIConnectionError → APITimeoutError      # request never completed
├── APIResponseValidationError                # 2xx body not JSON / not the expected shape; .response, .status_code, .request_id
└── APIStatusError                            # non-2xx; .status_code, .body, .message, .request_id
    ├── AuthenticationError       # 401
    ├── InsufficientCreditsError  # 402
    ├── NotFoundError             # 404
    ├── RateLimitError            # 429 (only after retries exhausted)
    └── ServerError               # 5xx (only after retries exhausted)
```
Unmapped non-2xx → generic `APIStatusError` (or `ServerError` for any 5xx).

---

## 7. Data-model specifics & known quirks

- **`Industry` has 534 unique values** including upstream data-quality oddities:
  near-duplicates (`"Airlines and Aviation"` vs `"Airlines/Aviation"`, `"Hospitals"`
  vs `"Hospitals and Health Care"`) and one double-escaped value,
  `"Women\\'s Handbag Manufacturing"` (two literal backslashes + apostrophe). These
  are pulled straight from the live spec and kept **byte-for-byte** — they round-trip
  through the `--fetch` → `enum-source.json` (`json.dumps`) → `enums.py` (`repr`) pipeline
  unchanged — so requests match the API. Do not "fix" them.
- **Generated enum member names** are an upper-snake slug of the value
  (`"IT Services and IT Consulting"` → `IT_SERVICES_AND_IT_CONSULTING`); collisions
  get a numeric suffix. The `.value` is always the exact API string.
- **`waterfall_icp` response shape came from the docs**, not the spec (its OpenAPI
  example is `null`). Shape: `{results: [{icp, ranking, person}]}`.
- **`Company.linkedin_id` is an int**; `Person`/`Experience` linkedin ids are strings.
- **`Location`** is reused for `Person.location` (has `continent`) and
  `Experience.job_location` (no `continent`); both fields are optional so one model
  serves both.

---

## 8. Tooling & local commands

uv + hatchling. Python floor **3.10** (3.9 is EOL). Runtime deps: `httpx`,
`pydantic` (v2), `typing-extensions`.

```bash
uv sync                              # install runtime + dev deps
uv run ruff check . && uv run ruff format .
uv run mypy                          # strict; includes src, tests, scripts, examples
uv run pyright                       # strict
uv run pytest                        # 132 tests, sync + async
uv run python scripts/gen_enums.py --check   # enum drift guard
uv run python scripts/gen_sync.py --check    # sync-client/resources drift guard
uv build                             # sdist + wheel (wheel includes py.typed)
```

Tests use `pytest-httpx` (mocks httpx transport for ALL clients created in-test),
`pytest-asyncio` (auto mode), and a `FakeClock`/`SleepRecorder` (in `conftest.py`)
so retry/rate-limit tests never actually sleep. Example payloads live in `tests/data.py`.

---

## 9. Release automation

`release-please` (config: `release-please-config.json`, manifest:
`.release-please-manifest.json`; `release-type: python`) maintains a Release PR from
**Conventional Commits**. Merging it bumps `_version.py` (via the
`x-release-please-version` marker in `extra-files`), updates `CHANGELOG.md`, tags, and
creates a GitHub Release. The `publish` job in `release.yml` then runs `uv build` and
`pypa/gh-action-pypi-publish` using **OIDC Trusted Publishing** — no stored token.

- `pyproject.toml` version is **dynamic** (hatch reads `_version.py`); the manifest is
  release-please's source of truth for the current version.
- `pr-title.yml` lints PR titles (squash-merge uses the title as the commit subject).
- **Enum sync gate.** Before building, the `publish` job runs `gen_enums.py --fetch` and
  fails the release if the rendered `enums.py` drifted from the live spec — the only place
  CI touches the network for enums (per-PR `ci.yml` stays offline). It diffs only `enums.py`
  (not the cache's `spec_version`/`_comment` metadata), so a version-only bump never
  spuriously blocks a release.
- **One-time human setup** (PyPI trusted publisher, GitHub `pypi` environment, branch
  protection, Actions PR permission) and the **first-release nuance** are documented
  in [`CONTRIBUTING.md`](../CONTRIBUTING.md). The pipeline cannot publish until that
  setup is done.

---

## 10. Playbooks for common updates

### Refresh enums from the live spec
1. `uv run python scripts/gen_enums.py --fetch` — pulls the live OpenAPI spec, de-dups,
   and rewrites both `openapi/enum-source.json` and `types/enums.py`. Do **not** hand-edit
   either file.
2. Review the diff (a value change is a real taxonomy update; metadata-only churn is fine)
   and commit both files in a `feat:`/`fix:` PR.
3. CI's offline drift guard (`gen_enums.py --check`) fails if `enums.py` is stale; the
   release-time gate (§9) blocks any publish whose enums drifted from prod.

### Add a new endpoint
1. Get its request schema + a response example from the Blitz MCP (§2).
2. **Request types**: add/extend a `TypedDict` in `types/filters.py` if it has nested
   filters; otherwise the method takes plain keyword args.
3. **Response model**: add a `BlitzModel` subclass in the right `types/<group>.py`,
   reusing `shared.py` models where possible (add fields as `Optional`). Export it
   from `types/__init__.py`.
4. **Resource method**: add it to the **async** class only in
   `resources/_async/<group>.py`, calling
   `await self._client._request("POST", path, body=..., cast_to=..., timeout=timeout)` with a
   `timeout: TimeoutParam = None` keyword. Use a module-level path constant and a
   `_drop_none`-style body builder. Then run `uv run python scripts/gen_sync.py` to
   regenerate the sync class and commit both. (Never hand-edit `resources/_sync/`.)
5. **Tests**: add a deserialization test (`tests/test_models.py` + payload in
   `tests/data.py`) and a request/response test (`tests/resources/test_endpoints.py`),
   covering sync and async.
6. Run all checks (§8). Use a `feat:` commit.

### Update a response model when the API adds fields
Add the typed field (Optional) to the model. Until then, `extra="allow"` already keeps
the data reachable via `model.model_extra`, so this is non-breaking and non-urgent.

### Bump dependencies / Python floor
Edit `pyproject.toml` (`dependencies` / `requires-python` / classifiers + the matrix
in `ci.yml`), `uv lock`, run checks. Note mypy is `2.x` and pydantic `2.x`.

### Cut a release
Just land `feat:`/`fix:` PRs to `main`; merge the Release PR release-please opens. For
the very first `0.1.0`, see the first-release note in `CONTRIBUTING.md`.

---

## 11. Known limitations / future work

- No streaming and no built-in response caching. (Per-call `timeout=` IS supported.)
- Rate limiter does not auto-detect the per-key limit from `key-info` (uses 5 rps).
- Client-side rate limiting is per process: it mirrors the server's per-endpoint limit for
  one client, but multiple processes sharing an endpoint's budget can still exceed it and
  rely on the 429 retry path (see §5).
- The full OpenAPI spec is not vendored (only the de-duplicated enum value lists, cached
  from the live spec by `gen_enums.py --fetch`) — see §5.
- Response models are validated only against the spec's *examples*, not a formal
  response schema (the API doesn't publish one). Watch for shape changes; `extra="allow"`
  is the safety net.

---

## 12. Decision log

Append significant decisions here (date — decision — why) so future maintainers see
the history rather than re-litigating it.

- **2026-06-01** — Initial SDK. Pydantic v2 (responses) + TypedDict (requests); sync +
  async; release-please + PyPI OIDC; hand-written response models because the spec's
  responses are example-only; vendored enum-source.json instead of the full spec.
- **2026-06-01** — Post-review hardening (eng review). (A3) Sync client/resources are now
  **generated** from the async source via `scripts/gen_sync.py` (unasync) + a CI drift
  guard, removing the sync/async duplication while staying fully typed. (A2) Rate limiter
  switched from a token bucket to a **sliding window** to match the docs + reference client
  (no first-second 2× burst). (A1) Added `APIResponseValidationError` so malformed 2xx
  bodies stay inside `BlitzError`. (C1) Read/write timeouts are no longer retried (avoids
  double-charging billable POSTs); only connect/pool failures retry. (C2) `Retry-After` is
  parsed (delta or HTTP-date) and clamped to 120 s. (C4) Per-call `timeout=` on every
  method; `http_client`+`timeout` together now raises. Test suite 72 → 94.
- **2026-06-01** — Auto-pagination. The search methods now return auto-paging page objects
  (OpenAI/Stainless pattern — the most popular, best-DX choice): `CursorPage[T]`
  (people/companies) and `PageNumberPage[T]` (employee_finder), with `Async*` twins. Bare
  `for`/`async for` walks every page; `.auto_paging_iter(max_items=)`, `.iter_pages(max_pages=)`,
  and `.get_next_page()` round it out. Iteration lives in the gen_sync'd
  `_pagination_async.py` (→ `_pagination_sync.py`); shared state/context in
  `_pagination_base.py`. The old `PeopleSearchResponse`/`CompanySearchResponse`/
  `EmployeeFinderResponse` models were removed (safe — not yet published). gen_sync gained
  `AsyncIterator→Iterator`, `__aiter__→__iter__`, `_pagination_async→_pagination_sync` and the
  page-class renames. Test suite 94 → 105.
- **2026-06-04** — Enums are now generated from the **live** OpenAPI spec
  (`https://api.blitz-api.ai/openapi`) instead of a hand-maintained file, porting
  `blitz-api-js` PR #7 for cross-SDK parity. `gen_enums.py --fetch` walks the spec, maps each
  inlined enum to a class by its owning request property (`PROPERTY_TO_CLASS`), collapses the
  6–12 byte-identical duplicate occurrences, de-dups exact-repeat values, and rewrites both
  the committed cache `openapi/enum-source.json` (now generated, with `_source_url` +
  `spec_version` from `info.version`) and `types/enums.py`. Verified byte-identical to the
  prior output for all 7 enums (incl. the double-escaped `Women\\'s Handbag Manufacturing`);
  only cache metadata churned (`spec_version` 2.0.0→1.0.0, new `_source_url`). Kept the drift
  guard **offline** (only `--fetch` hits the network): `gen_enums.py --check` re-renders from
  the committed cache, so per-PR CI never depends on the network or breaks on an upstream
  change — refreshes land as deliberate PRs. The generator **throws** (rather than silently
  shrinking output) if a mapped enum is missing upstream or its occurrences diverge, and
  warns-and-ignores unmapped enums. The `publish` job in `release.yml` adds a **release-time
  sync gate**: it runs `--fetch` and fails if the regenerated `enums.py` differs from what's
  committed (diffing only `enums.py`, so a `spec_version`-only bump never spuriously blocks a
  release) — the only CI use of the network. Added `tests/test_gen_enums.py` (pure-function
  unit tests; no network/disk). Test suite 122 → 132.
- **2026-06-17** — Added `utils.company_department_distribution()`
  (`POST /v2/utils/company-department-distribution`). Same request shape
  as `company_employment_distribution` (one `company_linkedin_url`); the response groups
  employees by **department** (Blitz job function) instead of country, with unclassified
  employees bucketed under `"Other"` and `total_employees` summing all buckets. New models
  `DepartmentDistributionItem` / `CompanyDepartmentDistributionResponse` in `types/utils.py`
  (kept `department` as plain `str`, mirroring `EmploymentDistributionItem.country` — response
  models stay forward-compatible, not enum-bound). Added to the async source only and
  regenerated the sync class via `gen_sync.py`. Sync+async endpoint tests and a model-parse
  test added (15th endpoint).
- **2026-06-18** — Synced three endpoints to the live spec (`info.version` 1.0.0). **Find People /
  Company Search:** the shared `CompanyFilter` gained six funding/HQ fields —
  `total_funding` / `last_funding_amount` / `last_funding_year` (`RangeFilter`),
  `last_funding_type` (new `FundingTypeFilter` over the generated **`FundingType`** enum, 23
  values), `lead_investors` (`KeywordFilter`), and `hq.state` (`KeywordFilter`). `FundingType`
  was added by mapping `last_funding_type` → `FundingType` in `gen_enums.py`'s
  `PROPERTY_TO_CLASS` and running `--fetch` (8 enums now; existing seven byte-identical).
  Response models unchanged — funding is request-only, absent from the people/company examples.
  **Distribution endpoints (breaking):** the API moved both off the `Utilities` tag to
  `Company Enrichment` and renamed them, so they were relocated `client.utils.*` →
  `client.enrichment.*` and renamed `company_employment_distribution` →
  `company_distribution_by_country` (`POST /v2/enrichment/company-distribution-by-country`) and
  `company_department_distribution` → `company_distribution_by_department`
  (`POST /v2/enrichment/company-distribution-by-department`); the old `/v2/utils/company-*`
  paths are gone from the spec. Response models moved `types/utils.py` → `types/enrichment.py`
  and the country pair was renamed for parity (`EmploymentDistributionItem` →
  `CountryDistributionItem`, `CompanyEmploymentDistributionResponse` →
  `CompanyCountryDistributionResponse`; department pair unchanged). Country buckets are ISO
  3166-1 alpha-2 codes plus a literal `"unknown"` bucket. No deprecated shims (pre-1.0; the
  user opted into the break). Still 15 endpoints. Cross-check `blitz-api-js` for parity.
