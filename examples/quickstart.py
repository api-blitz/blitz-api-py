"""Synchronous quickstart for the Blitz API SDK.

Run with a real key:  BLITZ_API_KEY=sk_... python examples/quickstart.py
"""

from __future__ import annotations

from blitz_api import BlitzAPI
from blitz_api.types import Industry, JobLevel


def main() -> None:
    # api_key defaults to the BLITZ_API_KEY environment variable.
    with BlitzAPI() as client:
        # Health-check the key before a batch job.
        info = client.account.key_info()
        print(f"valid={info.valid} records={info.records_remaining}")
        print(f"rate limit: {info.max_requests_per_seconds} req/s")

        # Enrich a LinkedIn profile to a verified work email.
        email = client.enrichment.email(
            person_linkedin_url="https://www.linkedin.com/in/example-person",
        )
        if email.found:
            print(f"email: {email.email}")

        # Every /v2 response carries a fair_usage block: what this call cost, what's
        # left on the plan, and the request id to quote to support.
        if email.fair_usage is not None:
            print(
                f"used {email.fair_usage.records_used} record(s); "
                f"{email.fair_usage.records_remaining} left "
                f"(request {email.fair_usage.request_id})"
            )

        # Search people across companies with typed, autocompleted filters.
        people = client.search.people(
            company={"industry": {"include": [Industry.SOFTWARE_DEVELOPMENT]}},
            people={"job_level": [JobLevel.VP], "job_title": {"include": ["Engineering"]}},
            max_results=10,
        )
        print(f"found {people.total_results} people; showing {people.results_length}")
        for person in people.results:
            current = next((e for e in person.experiences if e.job_is_current), None)
            company = current.company_name if current else None
            print(f"- {person.full_name} | {person.headline} | {company}")


if __name__ == "__main__":
    main()
