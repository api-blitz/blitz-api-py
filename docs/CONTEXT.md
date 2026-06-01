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

### Endpoint → method → response model (all 14)

| HTTP | Path | SDK method | Response model |
| --- | --- | --- | --- |
| GET | `/v2/account/key-info` | `account.key_info()` | `KeyInfo` |
| POST | `/v2/search/waterfall-icp-keyword` | `search.waterfall_icp()` | `WaterfallIcpResponse` |
| POST | `/v2/search/employee-finder` | `search.employee_finder()` | `EmployeeFinderResponse` |
| POST | `/v2/search/people` | `search.people()` | `PeopleSearchResponse` |
| POST | `/v2/search/companies` | `search.companies()` | `CompanySearchResponse` |
| POST | `/v2/enrichment/email` | `enrichment.email()` | `EmailEnrichmentResponse` |
| POST | `/v2/enrichment/phone` | `enrichment.phone()` | `PhoneEnrichmentResponse` |
| POST | `/v2/enrichment/email-to-person` | `enrichment.email_to_person()` | `EmailToPersonResponse` |
| POST | `/v2/enrichment/phone-to-person` | `enrichment.phone_to_person()` | `PhoneToPersonResponse` |
| POST | `/v2/enrichment/company` | `enrichment.company()` | `CompanyEnrichmentResponse` |
| POST | `/v2/enrichment/domain-to-linkedin` | `enrichment.domain_to_linkedin()` | `DomainToLinkedinResponse` |
| POST | `/v2/enrichment/linkedin-to-domain` | `enrichment.linkedin_to_domain()` | `LinkedinToDomainResponse` |
| POST | `/v2/utils/current-date` | `utils.current_date()` | `CurrentDateResponse` |
| POST | `/v2/utils/company-employment-distribution` | `utils.company_employment_distribution()` | `CompanyEmploymentDistributionResponse` |

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
  _rate_limit.py     RateLimiter + AsyncRateLimiter: token buckets. Clock & sleep are
                     injectable (monotonic=, sleep=) so tests use a fake clock.
  _base_client.py    IO-FREE shared logic: to_jsonable() (enum->value, drop None),
                     BaseClient (api-key resolution, _build_url, _build_headers,
                     _should_retry, _backoff_seconds, _retry_delay, _make_status_error,
                     _parse_model). _STATUS_EXCEPTIONS maps code->exception.
  _client.py         BlitzAPI (sync) + AsyncBlitzAPI (async). Each owns an httpx
                     client + a rate limiter and implements _request() (the retry
                     loop). Resources attached as @cached_property. Context managers.
  resources/         One module per OpenAPI tag group; each has a sync + async class.
    account.py       AccountResource / AsyncAccountResource
    search.py        SearchResource / AsyncSearchResource (+ shared body builders)
    enrichment.py    EnrichmentResource / AsyncEnrichmentResource
    utils.py         UtilsResource / AsyncUtilsResource
  types/
    _models.py       BlitzModel — base for all responses (extra="allow", see §5).
    shared.py        Person, Experience, Education, Certification, Location, HQ, Company.
    enums.py         GENERATED. Industry (534) + CompanyType/EmployeeRange/Continent/
                     SalesRegion/JobFunction/JobLevel. Never hand-edit (see §7).
    filters.py       Request TypedDicts (CompanyFilter, PeopleFilter, CascadeTier, ...)
                     and *Value type aliases (e.g. IndustryValue = Industry | str).
    account.py       KeyInfo, ActivePlan
    search.py        PeopleSearchResponse, CompanySearchResponse, EmployeeFinderResponse,
                     WaterfallIcpResponse, WaterfallIcpMatch
    enrichment.py    7 enrichment response models + EmailMatch
    utils.py         CurrentDateResponse, CompanyEmploymentDistributionResponse, item
    __init__.py      Re-exports the public type surface (grouped).
  py.typed           PEP 561 marker (ships in the wheel; makes our types visible).

scripts/gen_enums.py        Regenerates types/enums.py from openapi/enum-source.json.
openapi/enum-source.json    Vendored enum value lists (the codegen source; see §5/§7).
tests/                       pytest + pytest-httpx + pytest-asyncio (see §8).
examples/                    quickstart.py, async_quickstart.py (type-checked docs).
.github/workflows/           ci.yml, release.yml, pr-title.yml (see §9).
release-please-config.json, .release-please-manifest.json   release automation config.
```

### Request flow
`resource.method(...)` builds a body dict → `client._request(method, path, body, cast_to)`
→ `to_jsonable(body)` (enum→value, strip None) → acquire rate-limit token → httpx
dispatch → on success `cast_to.model_validate(json)`; on non-2xx map to an exception;
on 429/5xx/network retry per policy.

---

## 5. Design decisions & rationale (the "why")

Confirmed with the owner up front:

- **Pydantic v2 for responses + TypedDict for requests.** Runtime validation +
  attribute access + autocomplete for outputs; static-only, zero-overhead, dict-literal
  ergonomics for inputs. (Considered & rejected: zero-dependency dataclasses — no
  runtime validation, more boilerplate.)
- **Both sync (`BlitzAPI`) and async (`AsyncBlitzAPI`)** over **httpx**, sharing a
  pure `BaseClient`. (Cheap to build together; costly to retrofit async later.)
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
- **Per-endpoint response *envelopes* stay distinct** because pagination differs:
  `people`/`companies` are cursor-based (`cursor`); `employee_finder` is page-based
  (`page`, `total_pages`); `waterfall_icp` wraps each `person` in
  `{icp, ranking, person}`.
- **`str`-backed enums that also accept raw strings.** Enums subclass `str` and the
  request filter aliases are `Enum | str` (e.g. `IndustryValue = Industry | str`), so
  a value missing from the vendored taxonomy never blocks a caller. `to_jsonable`
  serializes enums to `.value`.
- **Vendored `enum-source.json`, not the full OpenAPI spec.** The full 130 KB spec is
  not publicly downloadable and 99% of its size is repeated enum arrays. We vendor
  just the enum value lists (the only part codegen needs); they are the drift-guard
  source. If you need the full spec, pull it from the Blitz MCP (§2).
- **Client-side rate limiter is per-process.** It throttles one client instance to
  stay under 5 rps proactively; the 429-retry path is the cross-process backstop.
  Default 5 rps; `rate_limit_rps=None` disables it. (Auto-detecting the limit from
  `key-info` on first call was considered but not implemented — would add a surprise
  network call on construction.)
- **Retry policy:** 429 → wait `Retry-After` or 60 s; 5xx / timeout / connection
  error → exponential backoff + jitter; **401/402/404 → raise immediately, no retry**
  (retrying wastes credits/time). Up to `max_retries` (default 3).
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
  are kept **byte-for-byte** as the spec defines them so requests match the API. Do
  not "fix" them.
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
uv run pytest                        # 72 tests, sync + async
uv run python scripts/gen_enums.py --check   # enum drift guard
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
- **One-time human setup** (PyPI trusted publisher, GitHub `pypi` environment, branch
  protection, Actions PR permission) and the **first-release nuance** are documented
  in [`CONTRIBUTING.md`](../CONTRIBUTING.md). The pipeline cannot publish until that
  setup is done.

---

## 10. Playbooks for common updates

### Add or change an enum value
1. Edit `openapi/enum-source.json` (keep values byte-identical to the API).
2. `uv run python scripts/gen_enums.py` (regenerates `types/enums.py`).
3. Commit both files. CI's drift guard fails if `enums.py` is stale.

### Add a new endpoint
1. Get its request schema + a response example from the Blitz MCP (§2).
2. **Request types**: add/extend a `TypedDict` in `types/filters.py` if it has nested
   filters; otherwise the method takes plain keyword args.
3. **Response model**: add a `BlitzModel` subclass in the right `types/<group>.py`,
   reusing `shared.py` models where possible (add fields as `Optional`). Export it
   from `types/__init__.py`.
4. **Resource method**: add it to BOTH the sync and async class in
   `resources/<group>.py`, calling `self._client._request("POST", path, body=..., cast_to=...)`.
   Use a module-level path constant and a `_drop_none`-style body builder.
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

- No pagination helpers/auto-iterators yet (callers pass `cursor` / `page` manually).
- No streaming, no built-in response caching, no per-call timeout override.
- Rate limiter does not auto-detect the per-key limit from `key-info` (uses 5 rps).
- The full OpenAPI spec is not vendored (only enum value lists) — see §5.
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
