"""Asynchronous quickstart for the Blitz API SDK.

Run with a real key:  BLITZ_API_KEY=sk_... python examples/async_quickstart.py
"""

from __future__ import annotations

import asyncio

from blitz_api import AsyncBlitzAPI


async def main() -> None:
    async with AsyncBlitzAPI() as client:
        # Resolve a company LinkedIn URL to a full, typed company profile.
        result = await client.enrichment.company(
            company_linkedin_url="https://www.linkedin.com/company/openai",
        )
        if result.found and result.company is not None:
            company = result.company
            print(
                f"{company.name} — {company.industry} — {company.employees_on_linkedin} employees"
            )
            if company.hq is not None:
                print(f"HQ: {company.hq.city}, {company.hq.country_code}")


if __name__ == "__main__":
    asyncio.run(main())
