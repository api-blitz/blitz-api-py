"""Tests that the request-filter ``TypedDict``\\s carry the keys their endpoint accepts.

These pin the *splits* — where one endpoint honours a filter key and a sibling
accepts-then-silently-ignores it. Request schemas are open (no ``additionalProperties:
false``), so the API never rejects the extra key; the type is the only thing standing
between a caller and a query that quietly matched on the wrong criteria.
"""

from __future__ import annotations

from blitz_api.types import (
    CompanyFilter,
    PeopleCompanyFilter,
    PeopleFilter,
    TamPeopleFilter,
)


def test_company_filter_has_no_linkedin_url() -> None:
    # The live spec declares ``linkedin_url`` on the ``company`` object of
    # /v2/search/people and /v2/company/tam-by-people, but NOT /v2/search/companies.
    assert "linkedin_url" not in CompanyFilter.__annotations__


def test_people_company_filter_adds_linkedin_url() -> None:
    assert "linkedin_url" in PeopleCompanyFilter.__annotations__
    # ...and inherits the full shared firmographic set rather than restating it, so the
    # two can never drift.
    assert set(CompanyFilter.__annotations__) <= set(PeopleCompanyFilter.__annotations__)


def test_people_filter_has_no_linkedin_url() -> None:
    # /v2/search/people stopped honouring people.linkedin_url on 2026-09-11; it survives
    # only on company.tam_by_people.
    assert "linkedin_url" not in PeopleFilter.__annotations__
    assert "linkedin_url" in TamPeopleFilter.__annotations__
    assert set(PeopleFilter.__annotations__) <= set(TamPeopleFilter.__annotations__)


def test_every_filter_key_is_optional() -> None:
    # All four are ``total=False``: omitting a filter must always be legal.
    for filter_type in (CompanyFilter, PeopleCompanyFilter, PeopleFilter, TamPeopleFilter):
        assert filter_type.__required_keys__ == frozenset(), filter_type.__name__
