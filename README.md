# blitz-api-py

The typed Python SDK for the [Blitz API](https://blitz-api.ai) — B2B data, search,
and enrichment.

- **Fully typed** — Pydantic v2 response models with attribute access and IDE
  autocomplete, `TypedDict` request filters, and a shipped `py.typed` marker so
  mypy/pyright see the types in your own code.
- **Sync & async** — `BlitzAPI` and `AsyncBlitzAPI` over `httpx`.
- **Resilient** — built-in client-side rate limiting, retries with backoff on
  `429`/`5xx`, and a typed exception hierarchy.
- **Forward-compatible** — new fields the API adds never break deserialization.

> Create and manage API keys at [app.blitz-api.ai](https://app.blitz-api.ai).

## Installation

```bash
pip install blitz-api-py
# or: uv add blitz-api-py
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
| `client.enrichment` | `email()`, `phone()`, `email_to_person()`, `phone_to_person()`, `company()`, `domain_to_linkedin()`, `linkedin_to_domain()` |
| `client.utils` | `current_date()`, `company_employment_distribution()` |

Every method returns a typed Pydantic model (see `blitz_api.types`). Enum-backed
filter fields (e.g. `Industry`, `JobLevel`, `Continent`) accept either an enum
member or a raw string.

## Pagination

The search methods return an **auto-paginating page**: iterate it and the SDK fetches
each subsequent page for you. `search.people`/`search.companies` are cursor-based;
`search.employee_finder` is page-based — both behave identically here.

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
in any rolling second — so a single client instance stays under the API's limit (5 req/s
by default; check your key's limit via
`client.account.key_info().max_requests_per_seconds`). Across multiple processes you may
still hit `429` — the retry path handles that.

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

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, the test/type/lint
commands, the enum code generator, and the automated release process.

## License

[MIT](LICENSE)
