# blitz-api-py

[![PyPI version](https://img.shields.io/pypi/v/blitz-api-py.svg)](https://pypi.org/project/blitz-api-py/)
[![types: py.typed](https://img.shields.io/badge/types-py.typed-blue.svg)](https://pypi.org/project/blitz-api-py/)
[![CI](https://github.com/api-blitz/blitz-api-py/actions/workflows/ci.yml/badge.svg)](https://github.com/api-blitz/blitz-api-py/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/pypi/l/blitz-api-py.svg)](./LICENSE)

The typed Python SDK for the [Blitz API](https://blitz-api.ai) — B2B data, search,
and enrichment.

- **Fully typed** — Pydantic v2 response models with attribute access and IDE
  autocomplete, `TypedDict` request filters, and a shipped `py.typed` marker so
  mypy/pyright see the types in your own code.
- **Sync & async** — `BlitzAPI` and `AsyncBlitzAPI` over `httpx`.
- **Resilient** — built-in client-side rate limiting, retries with backoff on
  `429`/`5xx`, and a typed exception hierarchy.
- **Forward-compatible** — new fields the API adds never break deserialization.
- **1:1 with the API** — request filters and response fields are snake_case,
  matching [docs.blitz-api.ai](https://docs.blitz-api.ai).

> Create and manage API keys at [app.blitz-api.ai](https://app.blitz-api.ai).

> **Billing.** Blitz bills **per result**. A bare `for person in client.search.people(...)`
> loop streams every match up to the server-side limit (people: 50k results), which can be
> a lot of credits. Bound spend with **`max_items`** (a client-side total cap on
> `.collect()` / `.auto_paging_iter()`, never sent on the wire) — details in
> [Pagination](#pagination).

## Contents

- [Installation](#installation)
- [Quickstart](#quickstart)
- [Example: find, enrich, collect](#example-find-enrich-collect)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Pagination](#pagination)
- [Configuration](#configuration)
- [Error handling](#error-handling)
- [Forward compatibility](#forward-compatibility)
- [Development](#development)

## Installation

```bash
pip install blitz-api-py
# or: poetry add blitz-api-py   /   uv add blitz-api-py
```

Requires Python 3.10+.

## Quickstart

```python
from blitz_api import BlitzAPI
from blitz_api.types import Industry, JobLevel

# api_key defaults to the BLITZ_API_KEY environment variable.
with BlitzAPI() as client:
    # Health-check the key before a batch job.
    info = client.account.key_info()
    print(info.valid, info.remaining_credits, info.max_requests_per_seconds)

    # LinkedIn profile URL -> verified work email.
    email = client.enrichment.email(
        person_linkedin_url="https://www.linkedin.com/in/example-person",
    )
    if email.found:
        print(email.email)

    # Search people with typed, autocompleted filters.
    people = client.search.people(
        company={"industry": {"include": [Industry.SOFTWARE_DEVELOPMENT]}},
        people={"job_level": [JobLevel.VP]},
        max_results=10,
    )
    for person in people.results:
        print(person.full_name, person.headline)
```

### Async

```python
import asyncio
from blitz_api import AsyncBlitzAPI

async def main() -> None:
    async with AsyncBlitzAPI() as client:
        result = await client.enrichment.company(
            company_linkedin_url="https://www.linkedin.com/company/openai",
        )
        print(result.company.name if result.company else None)

asyncio.run(main())
```

## Example: find, enrich, collect

A complete flow — find people, enrich each one's verified work email, collect the
contacts. `max_items` caps the total fetched so the run can't surprise you with credits.

```python
from blitz_api import BlitzAPI
from blitz_api.types import Industry, JobLevel

client = BlitzAPI()  # reads BLITZ_API_KEY

# 1. Find up to 25 VPs at software companies (typed filters, 1:1 with the API).
leads = client.search.people(
    company={"industry": {"include": [Industry.SOFTWARE_DEVELOPMENT]}},
    people={"job_level": [JobLevel.VP]},
    max_results=25,
).collect(max_items=25)  # client-side total cap — bounds credit spend

# 2. Enrich each lead's verified work email from their LinkedIn profile URL.
contacts: list[dict[str, str | None]] = []
for person in leads:
    if not person.linkedin_url:
        continue
    result = client.enrichment.email(person_linkedin_url=person.linkedin_url)
    if result.found:
        contacts.append({"name": person.full_name, "email": result.email})

print(f"Collected {len(contacts)} contacts")
```

What comes back is typed and snake_case. A `Person` from the search above (fields are a
**superset** — only what the profile has is populated, and unknown fields the API adds
later are preserved):

```python
Person(
    full_name="Jordan Lee",
    headline="VP of Engineering at Acme",
    linkedin_url="https://www.linkedin.com/in/example-person",
    location=Location(city="San Francisco", state_code="CA", country_code="US", continent="North America"),
    experiences=[Experience(job_title="VP of Engineering", company_name="Acme", job_is_current=True)],
    # first_name, last_name, skills, education, certifications, … also present
)
```

And `enrichment.email(...)` returns:

```python
EmailEnrichmentResponse(
    found=True,
    email="jordan@acme.com",
    all_emails=[EmailMatch(email="jordan@acme.com", email_domain="acme.com")],
)
```

## Authentication

Pass the key explicitly or via the `BLITZ_API_KEY` environment variable:

```python
client = BlitzAPI(api_key="sk_...")          # explicit
client = BlitzAPI()                           # reads BLITZ_API_KEY
```

The key is sent in the `x-api-key` header. Never expose it in client-side code —
always call the API from your backend.

## Endpoints

All methods are grouped into four namespaces:

| Namespace | Methods |
| --- | --- |
| `client.account` | `key_info()` |
| `client.search` | `people()`, `companies()`, `employee_finder()`, `waterfall_icp()` |
| `client.enrichment` | `email()`, `phone()`, `email_to_person()`, `phone_to_person()`, `company()`, `domain_to_linkedin()`, `linkedin_to_domain()`, `company_distribution_by_country()`, `company_distribution_by_department()` |
| `client.utils` | `current_date()` |

Every method returns a typed Pydantic model (see `blitz_api.types`). Enum-backed
filter fields (e.g. `Industry`, `JobLevel`, `Continent`) accept either an enum
member or a raw string.

## Pagination

The search methods return an **auto-paginating page**: iterate it and the SDK fetches
each subsequent page for you. `search.people`/`search.companies` are cursor-based;
`search.employee_finder` is page-based — both behave identically here.

> **`max_results` is the page size, not a total.** It's results per page, and the API
> **bills 1 credit per result returned**. A bare `for person in client.search.people(...)`
> loop streams *every* match up to the server-side limit (people: 50k results / 1k pages;
> employee finder: 10k), which can be a lot of credits. Bound it with **`max_items`** on
> `.collect()` / `.auto_paging_iter()` (a client-side total cap — never sent on the wire),
> `break` out of the loop, or drive pages manually.

```python
# Iterate every matching person across all pages — no cursor handling needed.
for person in client.search.people(people={"job_level": ["VP"]}):
    print(person.full_name)

# Async works the same way.
async for person in await async_client.search.people(people={"job_level": ["VP"]}):
    ...

# Bound how much you pull.
for person in client.search.people(...).auto_paging_iter(max_items=200):
    ...

# Per-page control: inspect totals / cursors as you go.
for page in client.search.companies(company={...}).iter_pages(max_pages=5):
    print(page.total_results, len(page.results), page.cursor)

# Or page manually.
page = client.search.people(people={...}, max_results=50)
print(page.results, page.cursor)
nxt = page.get_next_page()        # None once exhausted
```

The page types (`CursorPage`, `PageNumberPage`, and their `Async*` variants) are
exported from `blitz_api`.

## Configuration

```python
client = BlitzAPI(
    api_key=None,                 # falls back to BLITZ_API_KEY
    base_url="https://api.blitz-api.ai",
    timeout=30.0,                 # seconds, or an httpx.Timeout
    max_retries=3,                # retries on 429 / 5xx / network errors
    rate_limit_rps=5.0,           # client-side throttle; None to disable
)
```

The client-side rate limiter is a sliding window — at most `rate_limit_rps` requests
in any rolling second — applied **per endpoint**: each endpoint (e.g. `.email` vs
`.phone`) is throttled independently, mirroring the API's own limit, which is also per
endpoint (5 req/s by default; check yours via
`client.account.key_info().max_requests_per_seconds`). A single client instance therefore
stays under the limit on every endpoint, so a burst on one never blocks another. Across
multiple processes — which share an endpoint's budget — you may still hit `429`; the retry
path handles that.

Every method also accepts a per-call `timeout` (seconds or an `httpx.Timeout`) when one
endpoint needs longer than the client default:

```python
client.search.people(people={"job_level": ["VP"]}, timeout=10.0)
```

## Error handling

```python
from blitz_api import (
    BlitzError, AuthenticationError, InsufficientCreditsError,
    NotFoundError, RateLimitError, APIStatusError, APIConnectionError,
    APITimeoutError, APIResponseValidationError,
)

try:
    client.enrichment.email(person_linkedin_url="...")
except InsufficientCreditsError:
    ...                            # 402 — out of credits
except AuthenticationError:
    ...                            # 401 — bad key
except APIStatusError as err:
    print(err.status_code, err.message, err.body)
except APIResponseValidationError:
    ...                            # 2xx whose body wasn't valid / didn't match the model
except BlitzError:
    ...                            # base class for everything this SDK raises
```

`429` and `5xx` are retried automatically (with backoff) up to `max_retries`;
`401`/`402`/`404` raise immediately. Connect timeouts and connection errors are retried,
but a **read timeout is not** — the server may already have processed (and billed) the
request, so it surfaces as `APITimeoutError` rather than risking a double charge.

## Forward compatibility

Response models subclass a base configured with `extra="allow"`, so a field the API adds
before this SDK models it is still present on the parsed object (via attribute access or
`.model_extra`). Known fields stay precisely typed.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, the test/type/lint
commands, the enum code generator, and the automated release process.

## License

[MIT](LICENSE)
