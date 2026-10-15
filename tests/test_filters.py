"""Tests that the request-filter ``TypedDict``\\s carry the keys their endpoint accepts.

These pin the *splits* — where one endpoint honours a filter key and a sibling
accepts-then-silently-ignores it. Request schemas are open (no ``additionalProperties:
false``), so the API never rejects the extra key; the type is the only thing standing
between a caller and a query that quietly matched on the wrong criteria.
"""

from __future__ import annotations

from blitz_api.types import (
    CompanyFilter,
    JobCompanyFilter,
    KeywordFilter,
    PeopleCompanyFilter,
    PeopleEducationFilter,
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


def test_is_recent_hire_is_not_a_filter_key() -> None:
    # ``is_recent_hire`` is a top-level body field on every route that takes it. The API
    # rejects unknown fields at any depth with a 422, so a ``people.is_recent_hire`` key would
    # turn a typo-free call into an error: it must not be typeable on the people object.
    for filter_type in (PeopleFilter, TamPeopleFilter, PeopleEducationFilter):
        assert "is_recent_hire" not in filter_type.__annotations__, filter_type.__name__


def test_mx_filter_is_on_every_company_filter_that_takes_it() -> None:
    # company.mx is declared on search.companies, search.people and company.tam_by_people
    # (the three CompanyFilter users) -- not on the job-side company filter.
    assert "mx" in CompanyFilter.__annotations__
    assert "mx" in PeopleCompanyFilter.__annotations__  # inherited, not restated
    assert "mx" not in JobCompanyFilter.__annotations__


def test_people_education_filter_extends_the_keyword_filter() -> None:
    # Extends rather than restates, so include/exclude can't drift from KeywordFilter.
    assert set(KeywordFilter.__annotations__) <= set(PeopleEducationFilter.__annotations__)
    assert {"start_year", "end_year"} <= set(PeopleEducationFilter.__annotations__)
    assert PeopleEducationFilter.__required_keys__ == frozenset()


def test_a_reused_keyword_filter_variable_is_still_accepted_as_education() -> None:
    # Regression for a *static* check: ``mypy`` / ``pyright`` fail this file if it stops
    # type-checking. ``people.education`` was a ``KeywordFilter`` before it gained year ranges,
    # and a ``KeywordFilter`` *variable* is not assignable to the wider ``PeopleEducationFilter``
    # alone -- ``TypedDict`` assignability is structural and its extra optional keys could carry
    # any type -- so the field must keep accepting the old type too. (The reverse direction,
    # a declared child where the parent is expected, is the one the ``Tam*`` docstrings measure.)
    education: KeywordFilter = {"include": ["Stanford"]}
    people: PeopleFilter = {"education": education}
    tam: TamPeopleFilter = {"education": education}
    assert people["education"] is education
    assert tam["education"] is education

    # ...and the new type still works as a declared variable and as a dict literal.
    dated: PeopleEducationFilter = {"include": ["Stanford"], "end_year": {"min": 2015}}
    people_dated: PeopleFilter = {"education": dated}
    assert people_dated["education"] is dated
    literal: PeopleFilter = {"education": {"include": ["MIT"], "start_year": {"max": 2020}}}
    literal_education = literal.get("education")
    assert literal_education is not None
    assert literal_education.get("include") == ["MIT"]
