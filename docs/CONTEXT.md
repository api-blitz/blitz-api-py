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
- **Rate limit**: 10 req/s **per endpoint** on all plans (each endpoint has its own
  budget); plans created before 2026-09-30 run at 50 req/s. Per-key value in
  `key-info.max_requests_per_seconds` and, live, in `fair_usage.rate_limit`. The SDK's
  client-side default stays at **5 rps** — half the cap, per the vendor's own SDK docs.
- **OpenAPI**: 3.1.0. `https://api.blitz-api.ai/openapi` reports `info.version` `1.0.0`;
  the docs-site mirror (`docs.blitz-api.ai/api-reference/v2.openapi.json`) says `2.0.0`.
  They are two different documents — the live endpoint is the one `gen_enums.py --fetch`
  reads and the one to audit against. All endpoints are `/v2/...`.
- **Status conventions**: 401 invalid/missing key · 402 insufficient records ·
  404 key not found · 422 invalid request body (e.g. a filter list over 50 entries, or
  `null` on a required field) · 429 rate limited (official client waits 60 s then
  retries) · 5xx server error.

### Endpoint → method → response model (all 21)

| HTTP | Path | SDK method | Response model |
| --- | --- | --- | --- |
| GET | `/v2/account/key-info` | `account.key_info()` | `KeyInfo` |
| POST | `/v2/search/waterfall-icp-keyword` | `search.waterfall_icp()` | `WaterfallIcpResponse` |
| POST | `/v2/search/employee-finder` | `search.employee_finder()` | `PageNumberPage[Person]` |
| POST | `/v2/search/people` | `search.people()` | `CursorPage[Person]` |
| POST | `/v2/search/companies` | `search.companies()` | `CursorPage[Company]` |
| POST | `/v2/jobs/search` | `jobs.search()` | `CursorPage[Job]` |
| POST | `/v2/jobs/company` | `jobs.company()` | `CursorPage[Job]` |
| POST | `/v2/company/tam-by-jobs` | `company.tam_by_jobs()` | `CursorPage[TamByJobsMatch]` |
| POST | `/v2/company/tam-by-people` | `company.tam_by_people()` | `CursorPage[TamByPeopleMatch]` |
| POST | `/v2/enrichment/person` | `enrichment.person()` | `PersonEnrichmentResponse` |
| POST | `/v2/enrichment/email` | `enrichment.email()` | `EmailEnrichmentResponse` |
| POST | `/v2/enrichment/phone` | `enrichment.phone()` | `PhoneEnrichmentResponse` |
| POST | `/v2/enrichment/email-to-person` | `enrichment.email_to_person()` | `EmailToPersonResponse` |
| POST | `/v2/enrichment/phone-to-person` | `enrichment.phone_to_person()` | `PhoneToPersonResponse` |
| POST | `/v2/enrichment/company` | `enrichment.company()` | `CompanyEnrichmentResponse` |
| POST | `/v2/enrichment/domain-to-linkedin` | `enrichment.domain_to_linkedin()` | `DomainToLinkedinResponse` |
| POST | `/v2/enrichment/linkedin-to-domain` | `enrichment.linkedin_to_domain()` | `LinkedinToDomainResponse` |
| POST | `/v2/enrichment/company-distribution-by-country` | `enrichment.company_distribution_by_country()` | `CompanyDistributionByCountryResponse` |
| POST | `/v2/enrichment/company-distribution-by-department` | `enrichment.company_distribution_by_department()` | `CompanyDistributionByDepartmentResponse` |
| POST | `/v2/utils/current-date` | `utils.current_date()` | `CurrentDateResponse` |
| GET | `/changelog/` | `changelog.list()` | `list[ChangelogEntry]` |

### How to re-derive the API surface (IMPORTANT)

The API spec/docs are public. To inspect or refresh:

- Fetch the OpenAPI spec from `https://api.blitz-api.ai/openapi` and use `jq`
  against it, e.g. `jq '.paths["/v2/search/people"].post.requestBody...'`.
- The `.md` mirror of any docs page is at `https://docs.blitz-api.ai/<path>.md`,
  and the index is at `https://docs.blitz-api.ai/llms.txt`.

---

## 3. THE crux: why response models are hand-written

This is the single most important fact about this codebase:

- **Request bodies in the spec are richly typed** — nested objects, `required`,
  defaults, and large `enum`s (e.g. the ~535-value `industry`). These are modeled
  precisely (`TypedDict` filters + generated enums).
- **Response bodies were example-only** when the models were written — every response
  schema was `{"type": "object", "example": {...}}` with **no `properties`**. An
  off-the-shelf OpenAPI generator (openapi-python-client, datamodel-code-generator)
  would have emitted `dict[str, Any]` for every response → unacceptable for mandate #1.

Therefore **response models are hand-derived** and stay that way. As of the 2026-09-02
refresh the live spec **does** publish real response `properties` (per-field types,
`required`, nullability), so it is now a usable *audit* source: flatten it and diff it
against the models to catch renames and additions (see the "Audit the response models"
playbook in §10). It is still not the *generator* input — the hand-written models carry
the superset/`Optional` design (§5), the shared-model reuse, and the docstrings that a
generator would flatten away. The accepted trade-off is unchanged: when the API changes a
response shape, a human updates the model (the `extra="allow"` base means new fields don't
break anything in the meantime — see §5).

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
    _models.py       BlitzModel (base for all responses, extra="allow", see §5) +
                     BlitzResponse (adds the fair_usage envelope; base for top-level
                     responses and BasePage) + FairUsage / FairUsageRateLimit +
                     BlitzList (Annotated list type that coerces null->[], see §5).
    shared.py        Person, Experience, Education, Certification, Location, HQ,
                     Company.
    enums.py         GENERATED. Industry (535) + CompanyType/EmployeeRange/Continent/
                     SalesRegion/JobFunction/JobLevel/LastFundingType. Never hand-edit (see §7).
    filters.py       Request TypedDicts (CompanyFilter, PeopleFilter, CascadeTier,
                     TamJobFilter, TamPeopleFilter, ...)
                     and *Value type aliases (e.g. IndustryValue = Industry | str).
    account.py       KeyInfo, ActivePlan
    search.py        WaterfallIcpResponse, WaterfallIcpMatch (the paginated search results
                     return the page classes below, not per-endpoint models)
    enrichment.py    8 enrichment response models + EmailMatch + the two company-distribution
                     responses (CompanyDistributionByCountryResponse / *ByDepartment*) + per-item models
    company.py       TamByJobsMatch / TamByPeopleMatch (both TAM builders are paginated,
                     so they return the page class below, not a per-endpoint model)
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
timeout)` → `to_jsonable(body)` *and* `to_jsonable(params)` (enum→value, strip None, at
every depth — resources never filter their own arguments) → await a rate-limit slot
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
- **The `fair_usage` envelope lives on a `BlitzResponse` base, not on `BlitzModel`.**
  Every `/v2` response carries a `fair_usage` block (records used/remaining, reset time,
  rate-limit headroom, request id) — but only at the *top level*. Nested entities
  (`Person`, `Company`, `Location`, ...) don't have it, so putting the field on
  `BlitzModel` would have lied about every nested model. `BlitzResponse(BlitzModel)` adds
  `fair_usage: FairUsage | None` and is the base for the top-level response models and for
  `BasePage`, so pages expose it too — each page carries the block of the request that
  fetched *it*, which is what makes it usable for metering a long auto-paged run.
  `Optional` because the public `/changelog/` endpoint isn't metered (and old recorded
  payloads predate the rollout). `FairUsage.rate_limit` is `Optional` for the same honest
  reason: the API omits it on `account.key-info`, which is not rate limited. The block is
  also attached to `402` bodies, so `APIStatusError.fair_usage` parses it there
  (`_parse_fair_usage` never raises — a malformed block yields `None` rather than masking
  the API's own error).
- **`null` list fields are coerced to `[]` by a type, not a validator.** The spec types a
  person's `education`/`skills`/`certifications` and a company's `specialties` as
  `array | null`, and `GET /changelog/` really does send `null` rather than `[]` for an
  empty `affected_endpoints`/`links` (the spec types those two as plain arrays, so the
  coercion there is observed behaviour, not schema). A bare `list[T] = []` field **rejects** `null`
  (`ValidationError`). The fix is `_models.BlitzList[T]` —
  `Annotated[list[T], BeforeValidator(...)]` — used as the field's annotation, so the
  coercion travels with the type. Chosen over a `field_validator("a", "b", …)` on each
  model because that form names its fields as **strings**: adding a nullable list field
  means remembering to also extend a string tuple somewhere else in the class, and nothing
  catches you when you don't. `BlitzList` makes the field self-declaring and that class of
  mistake unrepresentable. `Person.experiences` uses it too even though the spec currently
  marks it non-nullable — uniform across the four person lists beats tracking which single
  one upstream has not yet loosened. **The rule is exhaustive**: every field the spec types
  `array | null` is a `BlitzList`, so a caller never needs a `None` guard on a list. Audited
  against the live spec on 2026-09-22 — the remaining plain `list[T] = []` fields
  (`allowed_apis`, `active_plans`, `all_emails`, `other`, both `distribution`s, the waterfall
  `results`) are all non-nullable upstream. If you add a nullable list, use `BlitzList`.
- **The `Tam*Filter` request types extend their base, they don't restate it.**
  `TamJobFilter(JobFilter)` and `TamPeopleFilter(PeopleFilter)` add only the keys the TAM
  endpoints have on top of the shared criteria. This replaced a flat copy-paste convention
  whose stated rationale — "so the shared `JobFilter` never gains `min_per_company`" — was
  simply wrong: inheriting *never* mutates the parent. Measured both forms against mypy and
  pyright, and they are **identical** on every case that matters: a dict literal carrying
  `min_per_company` is rejected by `search.people` either way; a *declared*
  `TamPeopleFilter` variable is accepted by `search.people` either way (TypedDict
  assignability is structural, so the flat copy never bought that protection); resolved
  key sets and required/optional splits match exactly. The copy therefore bought nothing
  and cost a guaranteed drift point between two types the API documents as taking *the
  same input*. If you re-flatten these, you are re-introducing that drift for no
  type-safety gain — the one honest cost of inheritance is that an IDE hover on the child
  shows only the added keys.
- **Superset models with nullable fields, not per-endpoint duplicates.** The API
  returns slightly different shapes for the "same" object across endpoints. We model
  one `Person`/`Company`/`Experience`/etc. with the union of fields, all `Optional`.
  Example: `Location` carries `continent`/`postal_code`/`street_address` on a person but
  not on an `Experience.job_location`. Absence is honestly `None`. (Two older examples
  cited here were wrong and have been dropped: `Experience.company_name` is returned by
  every person-returning endpoint, not just `search.people`, and `HQ.postcode`/`street`
  are returned by nothing — see §7.)
- **Pagination uses auto-paging page objects** (see §11 decision log). Cursor-based
  endpoints (`people`/`companies`, `jobs.*`, both TAM builders) return `CursorPage[T]`; the
  page-based `employee_finder` returns `PageNumberPage[Person]` (`Async*` twins for the
  async client).
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
  fetch it from the public OpenAPI endpoint (§2).
- **Client-side rate limiter is a per-process sliding window, applied per endpoint.** At
  most `rps` requests may begin in any rolling 1-second window (`_rate_limit.py`), matching
  the Blitz docs' per-rolling-second wording and the official reference client. A token
  bucket was rejected: its initial capacity lets a fresh client fire `rps` requests *and*
  refill within the first second, briefly doubling the rate — the exact pattern the docs say
  triggers 429 on bulk runs. Default 5 rps — deliberately **half** the API's current
  10 rps/endpoint cap, which is what the vendor's own SDK docs prescribe, and which leaves
  throughput on the table for anyone who raises it to their key's
  `max_requests_per_seconds`. `rate_limit_rps=None` disables it.
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
  immediately, no retry** (retrying wastes records/time). Transport errors are split by
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
    ├── InsufficientRecordsError  # 402
    ├── NotFoundError             # 404
    ├── RateLimitError            # 429 (only after retries exhausted)
    └── ServerError               # 5xx (only after retries exhausted)
```
Unmapped non-2xx → generic `APIStatusError` (or `ServerError` for any 5xx).
The `InsufficientCreditsError` alias of the `402` class (deprecated in 2.3) was **removed
in 4.0.0**; `tests/test_exceptions.py` pins its absence so it is not reintroduced.

---

## 7. Data-model specifics & known quirks

- **`Industry` has 535 unique values** including upstream data-quality oddities:
  near-duplicates (`"Airlines and Aviation"` vs `"Airlines/Aviation"`, `"Hospitals"`
  vs `"Hospitals and Health Care"`) and one double-escaped value,
  `"Women\\'s Handbag Manufacturing"` (two literal backslashes + apostrophe). These
  are pulled straight from the live spec and kept **byte-for-byte** — they round-trip
  through the `--fetch` → `enum-source.json` (`json.dumps`) → `enums.py` (`repr`) pipeline
  unchanged — so requests match the API. Do not "fix" them.
- **`Industry.UNKNOWN` (`"Unknown"`) is a bucket, not an industry.** Added upstream
  2026-09-16 and appended at the *end* of the taxonomy (the generator preserves spec
  order, so it is the last member, not alphabetical). It is directional: additive in
  `include`, subtractive in `exclude`. **What it matches depends on the endpoint** (widened
  2026-09-17): companies with no industry on file everywhere, *plus* people with no company
  on `search.people` / `company.tam_by_people`, *plus* postings with no company on
  `jobs.search` / `company.tam_by_jobs`. `search.companies` keeps the narrow meaning.
  Documented on `IndustryFilter`, since the semantics live with the filter rather than the
  enum.
- **Generated enum member names** are an upper-snake slug of the value
  (`"IT Services and IT Consulting"` → `IT_SERVICES_AND_IT_CONSULTING`); collisions
  get a numeric suffix. The `.value` is always the exact API string.
- **`waterfall_icp` response shape came from the docs**, not the spec (its OpenAPI
  example is `null`). Shape: `{results: [{icp, ranking, person}]}`.
- **`Company.linkedin_id` is an int**; `Person`/`Experience` linkedin ids are strings.
- **`Location`** is reused for `Person.location` (has `continent`, `postal_code` and
  `street_address`) and `Experience.job_location` (none of the three); every field is
  optional so one model serves both.
- **Every response schema in the spec is closed** — all 236 response object schemas carry
  `additionalProperties: false`, and most list every key as `required`. So the spec's key
  set for a response object is *exhaustive*: an SDK field absent from it is not "maybe
  undocumented", it provably cannot be returned. That makes a full model audit mechanical;
  see the §10 playbook.
- **`HQ.postcode` and `HQ.street` are unverified and are probably not real.** They predate
  the spec publishing real response properties. Every `hq` object in the live spec —
  `search.companies`, `enrichment.company`, `tam_by_jobs`, `tam_by_people` — has exactly
  `city`/`state`/`country_code`/`country_name`/`region`/`continent`, closed and all
  required; the strings `postcode` and `street` occur **zero** times in the live spec, zero
  times in the docs-site mirror (whose `enrichment.company` example shows the six-key `hq`),
  and zero times in the published docs. They are kept for now only because they shipped in a
  released version, unlike the three phantom `Company` fields caught in the same audit,
  which were removed before release. **Open question for the API owner**: confirm they are
  gone and remove both in the next major, following the `field_of_study` precedent.
- **`Person.profile_picture_url` is always `null`** since 2026-09-15. The API kept the key
  so clients don't break, so the field stays on the model (typed, documented) rather than
  being removed — removing it would turn a silent `None` into an `AttributeError` for no gain.
- **`Education` has no `field_of_study`.** The API folded it into `degree` on 2026-09-15
  (`"Bachelor of Science, Industrial Engineering"`). Removed outright, no alias — the
  spec-faithful precedent; `extra="allow"` keeps any stray value reachable.
- **`Person.headline` is derived**, not the profile's free-text headline: the API builds it
  from the first position as `"<job title> | @<employer>"`.
- **Search filter lists are capped at 50 entries** server-side (422 past that), and
  `waterfall_icp`'s `cascade` at 10 tiers. A `RangeFilter` whose `min` exceeds its `max`
  is also a 422 as of 2026-09-16 (`max: 0` still means unbounded). Documented in
  `filters.py`, not enforced — the SDK doesn't pre-validate list lengths or range
  ordering (same posture as the advisory enum typing).

---

## 8. Tooling & local commands

uv + hatchling. Python floor **3.10** (3.9 is EOL). Runtime deps: `httpx`,
`pydantic` (v2), `typing-extensions`.

```bash
uv sync                              # install runtime + dev deps
uv run ruff check . && uv run ruff format .
uv run mypy                          # strict; includes src, tests, scripts, examples
uv run pyright                       # strict
uv run pytest                        # 186 tests, sync + async
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

### Audit the response models against the live spec
The spec now publishes real response `properties`, so a refresh is a diff, not a re-read:

1. `curl -s https://api.blitz-api.ai/openapi -o /tmp/spec.json`.
2. Walk `paths[*][method].responses["200"].content["application/json"].schema` and flatten
   it to `path.field: type` lines (a ~40-line `jq`/Python script), then compare against the
   models in `types/`. Renames and new fields fall straight out of the diff.
3. `GET https://api.blitz-api.ai/changelog/` is the narrative companion — it names the
   breaking renames and dates them, which the schema diff alone can't tell you.
4. Apply changes to the models, add fixtures in `tests/data.py`, and run §8.

### Add a new endpoint
1. Get its request schema + a response example from the public docs / OpenAPI spec (§2).
2. **Request types**: add/extend a `TypedDict` in `types/filters.py` if it has nested
   filters; otherwise the method takes plain keyword args.
3. **Response model**: add a `BlitzModel` subclass in the right `types/<group>.py`,
   reusing `shared.py` models where possible (add fields as `Optional`). Export it
   from `types/__init__.py`.
4. **Resource method**: add it to the **async** class only in
   `resources/_async/<group>.py`, calling
   `await self._client._request("POST", path, body=..., cast_to=..., timeout=timeout)` with a
   `timeout: TimeoutParam = None` keyword. Use a module-level path constant and build the
   body as a plain dict literal — do **not** filter `None` yourself, `_request` already runs
   `to_jsonable` over the body and the params. Then run `uv run python scripts/gen_sync.py` to
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
- Rate limiter does not auto-detect the per-key limit from `key-info` (defaults to 5 rps,
  half the API's 10 rps/endpoint cap; legacy keys are allowed 50).
- Client-side rate limiting is per process: it mirrors the server's per-endpoint limit for
  one client, but multiple processes sharing an endpoint's budget can still exceed it and
  rely on the 429 retry path (see §5).
- The full OpenAPI spec is not vendored (only the de-duplicated enum value lists, cached
  from the live spec by `gen_enums.py --fetch`) — see §5.
- Response models are hand-written, not generated. The spec now *does* publish response
  `properties`, so it is a usable audit source (see the §10 playbook) — but nothing enforces
  the two stay in sync per-PR. Watch for shape changes; `extra="allow"` is the safety net.

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
- **2026-06-19** — Renamed three public type identifiers added in 1.0.0 to be spec-faithful
  ([#17](https://github.com/api-blitz/blitz-api-py/issues/17)), a **breaking** change (`feat!`,
  major bump): the `last_funding_type` enum `FundingType` → **`LastFundingType`** (every other
  generated enum PascalCases its full field key — `job_level → JobLevel`; this was the only one
  dropping a prefix), and the two distribution responses `CompanyCountryDistributionResponse`
  / `CompanyDepartmentDistributionResponse` → **`CompanyDistributionBy{Country,Department}Response`**
  (matching the method/path word order, e.g. `company_distribution_by_country()`). The per-item
  models were renamed alongside for path consistency (`CountryDistributionItem` /
  `DepartmentDistributionItem` → `CompanyDistributionBy{Country,Department}Item`), and the
  filter aliases followed (`FundingTypeFilter`/`FundingTypeValue` → `LastFundingType*`). The
  **wire surface is unchanged** — method names, request/response keys (`last_funding_type`,
  `distribution`, …), and enum values are byte-identical; only the PascalCase identifiers moved.
  Enum regenerated via `gen_enums.py --fetch` (cache key + class, values byte-identical); sync
  resource regenerated via `gen_sync.py`. Note: at the time of this change `blitz-api-js@main`
  had *not yet* implemented funding filters or the distribution endpoints (its enums ended at
  `JobLevel`, `enrichment.ts` at `LinkedinToDomainResponse`), so issue #17's "JS already uses
  these names" was aspirational — these are the names JS should adopt when it catches up.
- **2026-07-23** — Added the Job Search endpoints (now 17). **(1)** New `client.jobs` namespace
  (its own OpenAPI tag → its own `resources/_async/jobs.py`, sync twin generated) with
  `jobs.search()` → `POST /v2/jobs/search` and `jobs.company()` → `POST /v2/jobs/company`. Both
  return `CursorPage[Job]` through the existing paginator, inheriting the null-cursor stop and
  the non-advancing-cursor guard; server-side cap is 5,000 jobs/query, 50/page. `jobs.company()`
  requires `company_linkedin_url` (keyword-only, no default) — the API 422s without it. New `Job`
  model in `types/jobs.py` reuses the shared `Location`. **(2)** Three enums added to
  `PROPERTY_TO_CLASS`: `seniority`→`Seniority`, `employment_type`→`EmploymentType`,
  `work_arrangement`→`WorkArrangement`. `company.size` maps onto the **existing** `EmployeeRange`
  class (byte-identical buckets); two properties sharing one class name collapse to a single
  output key (regeneration is a pure append). If upstream forks them, the divergence check
  raises and names both spec paths. `job.field` is left unmapped — free-form upstream, never an
  enum. **(3)** **Breaking**: `PeopleLocationFilter.city` went from `list[str]` to `KeywordFilter`
  (`{include, exclude}`), matching the live spec. No README sample or test exercised it, so
  nothing else failed — hence the explicit call-out. **(4)** `JobCompanyFilter` cannot reuse
  `CompanyFilter`: its `hq.country_code` is an include/exclude object (not `list[str]`), it has no
  `continent`/`sales_region`, and `size` is include-only. `is_agency` is a plain `bool`, not
  `bool | None`: it is a nested key in the `total=False` `JobCompanyFilter`, so the spec's
  tri-state "both" is expressed by omitting it (and a nested `None` would anyway be stripped by
  the recursive `to_jsonable`; `jobs.py`'s `_drop_none` only filters the top-level kwargs —
  *that helper was deleted as redundant on 2026-09-22, see below*).
  `blitz-api-js` carries the identical jobs surface — cross-check it for parity when changing jobs.
- **2026-07-23** — Closed parity gaps found by auditing against the live spec (source of
  truth) field-by-field; applied identically in `blitz-api-js`.
  **(1)** `KeyInfo`'s balance field (now `records_remaining`) and `max_requests_per_seconds` widened to
  `float | Literal["unlimited"]` — the API returns the literal `"unlimited"` on unlimited plans,
  which a number-only model **rejected** (`ValidationError`). Both use `float` to match the spec's
  `number` (an `int` would reject a fractional rate JS accepts). **(2)** `Education.school` →
  **`school_name`** + added `field_of_study`: the server always emits `school_name`, so the old typed
  `school` field never populated (value survived only via `model_extra`). Shared model → every
  Person-returning endpoint benefits. **(3)** `DomainToLinkedinResponse` gained `company_name` +
  `other[]` (new `DomainToLinkedinMatch`). **(4)** Request-side: `PeopleFilter.linkedin_url` and a
  `profile_min_connections` kwarg on `waterfall_icp` (both in the spec, previously unexpressible).
  **(5)** `CascadeTier.location`/`include_headline_search` → `NotRequired` (spec requires only
  `include_title`); `current_date`'s `region` made optional (spec default). `current_date` sends an
  empty body when `region` omitted. Async edits regenerated to sync via `gen_sync.py`.
  `CompanyFilter.linkedin_url` is a documented superset field (applies on `search.people` only).
- **2026-08-13** — Added `company.tam_by_jobs()` (`POST /v2/company/tam-by-jobs`, new
  `client.company` namespace, cursor-paginated → `CursorPage[TamByJobsMatch]`; the streamed item
  is a `{company, matched_jobs}` match reusing the shared `Company`, and the envelope carries **no**
  `total_results`; `min_per_company` lives on a standalone `TamJobFilter` TypedDict so the shared
  `JobFilter` stays clean — *`TamJobFilter` now extends `JobFilter`; see the second 2026-09-15
  entry below* — and `company` reuses `JobCompanyFilter`) and the public `changelog.list()`
  (`GET /changelog/`, new `client.changelog` namespace; not paginated; returns a plain
  `list[ChangelogEntry]`, `type` a loose `str`). Two transport changes: **(1)** the SDK's first GET
  query params — a trailing `params` kwarg on `_request` / `build_url` (rate limiter still keyed on
  the base path). **(2)** the changelog response is a top-level JSON array, so it is modelled as a
  pydantic `RootModel[list[ChangelogEntry]]` (`ChangelogResponse`) and unwrapped to `.root`; this
  widened `_base_client`'s `ResponseT` bound from `BlitzModel` to `BaseModel`. Fixed the enum
  generator to skip the `responses` subtree — the live spec's changelog response `type` enum
  otherwise mapped onto `CompanyType` (`PROPERTY_TO_CLASS["type"]`) and broke `--fetch`. Mirrored
  1:1 in `blitz-api-js`.
- **2026-09-02** — Pulled the live spec's 2026-08-31 / 09-01 changes (verified against
  `GET /changelog/`). **(1)** `KeyInfo`'s balance field renamed to **`records_remaining`** — a hard
  rename, no alias, matching the API's own breaking rename and the repo's spec-faithful
  precedent (v2.0.0). **(2)** Added the `fair_usage` envelope on every response via a new
  `BlitzResponse` base (see §5), including on the page classes and on `APIStatusError`
  (`402` carries it). The API's usage-header rename to `x-records-*` in the same API release
  needed no change: the SDK never read those headers. Enums re-fetched — no taxonomy drift.
  Mirror all of this in `blitz-api-js`, which is still on the pre-rename surface.
- **2026-09-02** — Finished the vocabulary half of the rename above: the SDK's data model
  already spoke in records while its prose still used the API's retired billing noun. Verified
  against the live spec, which is now uniformly records-worded (`Cost: 1 record per result`,
  `Cost: 0 records`, "Records left on the plan after this request", "When the record balance
  resets"). **(1)** The `402` exception class is now **`InsufficientRecordsError`**, with the old
  name kept as a **deprecated alias** — so this ships as a *minor*, not the major the field
  rename above took. The alias is a genuine runtime alias behind a `TYPE_CHECKING` split
  (`_exceptions.py`, bottom): the client raises `InsufficientRecordsError`, so declaring the old
  name a *subclass* would stop `except` on it from catching — the one mistake that would defeat
  the whole exercise. `tests/test_exceptions.py` pins the identity for that reason. The
  `TYPE_CHECKING` branch carries PEP 702 `@deprecated` (via `typing_extensions`, already a dep)
  for the migration signal; **note the cost**: pyright defaults `reportDeprecated` to `error`
  under `strict`, so pyright-strict users see a hard error on the old name where they saw
  nothing before, and our own three deliberate references need
  `# pyright: ignore[reportDeprecated]`. mypy is silent unless you pass
  `--enable-error-code=deprecated` — a useful audit (`uv run mypy --enable-error-code=deprecated`
  should flag only those three). Removal scheduled for **3.0.0** — *done in 4.0.0, see the 2026-09-16 entry below; 3.0.0 shipped without it.* **(2)** All billing prose
  realigned to the spec's wording (`bills 1 record per result returned`, `costs no records`,
  `record balance`) across the async resources, `_pagination_async.py`, the README, and this
  file; sync twins regenerated via `gen_sync.py`. The README stays on the current surface only —
  the deprecation lives in the class docstring, here, and the changelog. **(3)** The retired noun
  therefore survives at exactly three deliberate places: the alias definition and its re-export,
  the compat test, and `Industry.CREDIT_INTERMEDIATION` (`"Credit Intermediation"`) — a LinkedIn
  taxonomy value from the spec, not billing terminology, in a generated file. Not yet mirrored in
  `blitz-api-js`, which still exports only the old `402` class name.
- **2026-09-15** — Synced the live spec + `GET /changelog/` (2026-09-11 and 2026-09-15
  releases). **Two new endpoints (19 → 21).** `enrichment.person()`
  (`POST /v2/enrichment/person`) takes a `person_linkedin_url` and returns the whole career
  — new `PersonEnrichmentResponse`, reusing the shared `Person`. `company.tam_by_people()`
  (`POST /v2/company/tam-by-people`) is the headcount twin of `tam_by_jobs`: same
  `CompanyFilter` firmographics plus a persona, returning the distinct employing companies
  cursor-paginated as `CursorPage[TamByPeopleMatch]` (`{company, matched_people}`, and like
  TAM-by-jobs **no** `total_results`). Its people criteria live in a standalone
  `TamPeopleFilter` (the flat-`TypedDict` convention, mirroring `TamJobFilter`) because they
  are *not* `PeopleFilter`: this endpoint has `min_per_company` **and** still honours
  `linkedin_url`. — *Reversed the same day: `TamPeopleFilter` now extends `PeopleFilter`; see
  the second 2026-09-15 entry below.* **Breaking response changes.** (1) `Education.field_of_study` **removed** —
  the API folded it into `degree`; hard removal, no alias, matching the v2.0.0
  `remaining_credits` precedent (and `extra="allow"` keeps any stray value reachable).
  (2) `PeopleFilter.linkedin_url` **removed** — `/v2/search/people` stopped honouring it on
  2026-09-11 and now *silently ignores* it, which is worse than a 422: you get results for
  your other criteria and never notice. Dropping the key makes the type checker say so, and
  the docstring points at `tam_by_people` as the endpoint that still accepts it.
  **Additive response fields**: `Location.postal_code`/`street_address`,
  `Experience.job_contract_type`/`job_work_arrangement`. — *This entry also added
  `Company.slogan`/`revenue`/`employee_growth` and an `EmployeeGrowth` model; none of the
  three exist in the API. Reverted 2026-09-22, see the entry below.*
  `Person.profile_picture_url` is kept
  though the API now always sends `null` — the key is still in the spec, and removing it
  would turn a silent `None` into an `AttributeError` for nothing. **Robustness:**
  `changelog.py`'s private `null → []` validator was promoted to
  `_models.null_list_to_empty` and applied to `Person.experiences/education/skills/
  certifications` — a bare `list[T] = []` field *rejected* `null`, so this was a latent
  `ValidationError` on a sparse profile. No SDK change needed for the rest of the release: the 50-entry filter-list
  cap and the 10-tier cascade cap are documented in `filters.py` but not pre-validated
  (advisory, like the enum typing); `null`-means-omitted on request bodies is already how
  `to_jsonable` behaves; and unlimited `records_remaining` landed in 3.0.0. Enums
  re-fetched — no taxonomy drift (spec `info.version` still 1.0.0). Mirror all of this in
  `blitz-api-js`.
- **2026-09-15** — Code-quality pass over the sync above; behaviour unchanged, 184 tests
  still green. **(1)** The `null → []` coercion moved from a `field_validator("a", "b", …)`
  on each model to `_models.BlitzList[T]`, an `Annotated[list[T], BeforeValidator(...)]`
  used as the field annotation. The validator form names its fields as strings, so adding a
  nullable list field silently skips the coercion unless you also edit a tuple elsewhere in
  the class; the type form cannot be got wrong. Removed the two `_empty_*` class attributes
  from `shared.py` and the one in `changelog.py`. **(2)** `TamJobFilter` / `TamPeopleFilter`
  now extend `JobFilter` / `PeopleFilter` instead of restating every field. The old
  flat-`TypedDict` convention's rationale was incorrect (inheriting cannot add a key to the
  parent), and both forms were measured identical under mypy *and* pyright — same resolved
  keys, same required/optional split, same accept/reject on every call-site shape. The copy
  bought nothing and guaranteed eventual drift between types the API documents as taking the
  same input. Net: 13 duplicated field declarations deleted. See §5 for the full measurement.
- **2026-09-16** — Re-pulled the live spec: two upstream changes, both request-side.
  **(1)** `Industry` gained a 535th value, **`Unknown`**, appended at the end of the
  taxonomy — a bucket matching companies with no industry on file, additive in `include`
  and subtractive in `exclude`. *Widened on 2026-09-17 to also match records with no company
  at all, per endpoint; see the 2026-09-22 entry below.* Regenerated via `gen_enums.py
  --fetch` (one added member,
  one cache line; every other value byte-identical). The semantics are documented on
  `IndustryFilter`, not on the enum, because they are a property of how the filter reads
  the value. It closes a real gap: before it, reaching those companies meant listing every
  *other* industry in `exclude`, which the 50-entry cap made impossible. **(2)** A
  `RangeFilter` with `min` above `max` now returns `422` naming the field (previously
  accepted — no results, or a `500` on `company.revenue`); `max: 0` still means no upper
  bound. Documented on `RangeFilter`; deliberately **not** pre-validated, consistent with
  the 50-entry cap and the advisory enum typing. Also noted: the spec's
  `phone-to-person` request *example* changed (`+1234567890` → `+123456789`) — example
  only, no schema or SDK impact. No response-shape changes; all three audits still clean.
- **2026-09-16** — Removed the deprecated **`InsufficientCreditsError`** alias, closing out
  the schedule set when it was deprecated on 2026-09-02. It was marked for removal in
  3.0.0 but survived that release, so it went in the next major instead of drifting
  further. Gone from `_exceptions.py` (the whole `TYPE_CHECKING`/`else` split, and with it
  the last use of `typing_extensions.deprecated` and the three
  `# pyright: ignore[reportDeprecated]` suppressions), from the `blitz_api` re-export and
  `__all__`, and from the compat test — which is **replaced, not deleted**, by
  `test_insufficient_credits_alias_is_gone`, asserting the name is absent from both the
  module and `__all__` so it cannot be reintroduced by accident. `uv run mypy
  --enable-error-code=deprecated` is now clean, where it previously flagged the three
  deliberate references. The `402` class is `InsufficientRecordsError`, as it has been
  since 2.3. Verified against `GET /changelog/` in the same pass: still 28 entries, nothing
  newer than the two 2026-09-16 changes already applied, so the SDK is current with the API.
  — *Superseded on 2026-09-22: the changelog now has 30 entries; see the entry below.*
- **2026-09-22** — Code-quality pass over the whole 2026-09-11 → 2026-09-16 sync, plus two
  upstream entries that landed after it. Behaviour-preserving except where noted; 186 tests
  green, both type checkers and both drift guards clean.
  **(1) Deleted the `_drop_none` layer.** `_base_client.to_jsonable` already resolves enums
  and strips `None` *recursively*, and `_request` runs it on every body — so the per-resource
  `_drop_none` helpers in `search.py` / `jobs.py` / `company.py` (and `search.py`'s
  `_employee_finder_body`, which existed only to forward nine kwargs into one) were no-ops.
  Resources now build plain dict literals. The one real case was `changelog.py`, whose
  `_drop_none` filtered *query params* — those bypass `to_jsonable`, and httpx renders
  `days=None` as `days=`. Fixed at the canonical layer instead: `_request` now runs
  `to_jsonable` over `params` too, so the rule is uniform ("the client strips `None`;
  resources never filter") and the last copy could go. Net **−72 lines** across async + sync.
  Pinned by `test_changelog_list_drops_only_the_unset_query_param` — the mixed
  set/unset case, which the pre-existing both-unset test could not catch.
  **(2) `Company.specialties` → `BlitzList[str]`.** The spec types it `array | null`, so it
  was the one nullable list still spelled `list[str] | None = None`. **Minor breaking
  change** for anyone branching on `specialties is None`: it is now `[]`. Audited every
  array field in the live spec — this was the only mismatch, so the `BlitzList` rule is
  now exhaustive (recorded in §5 and on the alias itself).
  **(3) `Unknown` widened upstream (changelog 2026-09-17).** It now also matches records with
  *no company attached* — people on `search.people` / `tam_by_people`, job postings on
  `jobs.search` / `tam_by_jobs`; `search.companies` keeps the narrow meaning. Confirmed in the
  live spec's own per-endpoint filter descriptions. `IndustryFilter`'s docstring stated only
  the narrow `search.companies` meaning while being shared by `CompanyFilter` *and*
  `JobCompanyFilter`, i.e. all five endpoints — it now splits the three cases out.
  **(4) `experiences[]` on `search.people`: upstream contradicts itself — do not "fix" this
  without checking.** The changelog entry of **2026-09-21** says `/v2/search/people` now
  returns *only the position that matched*, reverting the 2026-09-15 "whole career" change.
  But the docs still say the whole career, in four places including the generated
  `api-reference/people-search/find-people` page, and the spec description says nothing either
  way. Rather than encode a fact two upstream sources disagree on, the SDK now asserts
  neither: `Person.experiences` documents the conflict and points at `job_is_current`, and the
  README comment and model test were reworded to stop claiming a count. `enrichment.person`'s
  "whole career" wording is **untouched** — that endpoint is uncontested. **Open question for
  the API owner; resolve and then state it plainly.**
  **(5) Smaller fixes.** `TamJobFilter`/`TamPeopleFilter` docstrings claimed inheritance makes
  `jobs.search` / `search.people` "keep rejecting" the extra keys — true for dict literals
  only, as §5's own measurement already records; the clause now says so. The
  `field_of_study` test asserted `not hasattr(...)`, which under `extra="allow"` passes merely
  because the fixture omits the key (and would fail the day the API sent a stray one); it now
  asserts `"field_of_study" not in Education.model_fields`. `tests/data.py` grew 17 hand-copied
  page envelopes, so cursor/page-number envelopes now come from `data.cursor_page()` /
  `data.number_page()` — which turns "this endpoint reports no `total_results`" from a silent
  omission plus a prose comment into a visible argument.
  **(6) Removed `Company.slogan`/`revenue`/`employee_growth` and the `EmployeeGrowth`
  model — the API has no such fields.** They were added by the 2026-09-15 sync entry above.
  Re-audited against all four upstream sources: the live spec types the company object with
  exactly fourteen keys on *both* `/v2/search/companies` and `/v2/enrichment/company`
  (`linkedin_url, linkedin_id, name, about, specialties, industry, type, size,
  employees_on_linkedin, followers, founded_year, hq, domain, website`); `slogan` and
  `employee_growth` occur zero times in the live spec, in the docs-site mirror, in the
  published docs, and across all 30 `GET /changelog/` entries; `revenue` occurs only
  request-side, as the `RangeFilter` on `CompanyFilter` that was already modelled. Left in
  place they would have read `None`/`[]` on every response forever, and `EmployeeGrowth` —
  re-exported from `blitz_api.types` — could only have come off in another major. The tests
  did not catch it because `tests/data.py`'s own `_COMPANY` fixture supplied the three keys.
  **Lesson: a hand-written response field must be traceable to the live spec, not to a
  plausible-looking fixture** — the §10 playbook's audit step is what would have caught this.
  **(7) Full mechanical audit of every model against the live spec.** Prompted by (6):
  walked all 21 paths, comparing each request-filter `TypedDict` and each response model
  against its schema recursively, treating the superset convention correctly (a key is a
  defect only if it appears at *no* site for that type). **60 of 61 types match the spec
  exactly** — same key sets, nothing missing, nothing invented. The single exception is
  `HQ`, whose `postcode`/`street` appear nowhere in the spec (§7). Worth knowing for next
  time: every response object schema is `additionalProperties: false`, so this audit is
  decisive rather than suggestive, and it is cheap to re-run — the throwaway script just
  walks `properties` against `model_fields` / `get_type_hints`.
  Mirror **(1)**, **(2)**, **(3)**, **(5)** and **(6)** in `blitz-api-js` — and re-run
  **(7)** there: check whether the JS `Company` picked up the same three phantom fields and
  whether its `HQ` carries `postcode`/`street`.
