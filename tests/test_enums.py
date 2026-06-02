"""Tests for the generated enums, including a codegen drift guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from blitz_api.types import (
    CompanyType,
    Continent,
    EmployeeRange,
    Industry,
    JobFunction,
    JobLevel,
    SalesRegion,
)


def test_industry_is_a_str_enum() -> None:
    assert issubclass(Industry, str)
    assert Industry.SOFTWARE_DEVELOPMENT.value == "Software Development"
    # A str-enum member is usable anywhere a plain string is expected.
    assert isinstance(Industry.SOFTWARE_DEVELOPMENT, str)
    assert str(Industry.SOFTWARE_DEVELOPMENT.value) in {Industry.SOFTWARE_DEVELOPMENT.value}


def test_industry_has_full_taxonomy() -> None:
    assert len(list(Industry)) == 534


def test_small_enums_have_expected_values() -> None:
    assert {m.value for m in JobLevel} == {"C-Team", "Director", "Manager", "Other", "Staff", "VP"}
    assert {m.value for m in SalesRegion} == {"NORAM", "LATAM", "EMEA", "APAC"}
    assert {m.value for m in Continent} >= {"Africa", "Asia", "Europe", "North America"}
    assert {m.value for m in EmployeeRange} >= {"1-10", "10001+"}
    assert "Public Company" in {m.value for m in CompanyType}
    assert "Engineering" in {m.value for m in JobFunction}


def _load_gen_enums() -> ModuleType:
    script = Path(__file__).resolve().parent.parent / "scripts" / "gen_enums.py"
    spec = importlib.util.spec_from_file_location("gen_enums", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_enums_file_is_in_sync() -> None:
    """The committed enums.py must match what gen_enums.py would produce now."""
    module = _load_gen_enums()
    assert module.render() == module.TARGET.read_text(encoding="utf-8"), (
        "enums.py is stale — run `python scripts/gen_enums.py` and commit."
    )


def test_slug_normalizes_punctuation() -> None:
    g = _load_gen_enums()
    assert g.slug("IT Services and IT Consulting") == "IT_SERVICES_AND_IT_CONSULTING"
    assert g.slug("Airlines/Aviation") == "AIRLINES_AVIATION"


def test_slug_prefixes_leading_digit_with_underscore() -> None:
    g = _load_gen_enums()
    assert g.slug("1-10") == "_1_10"
    assert g.slug("10001+") == "_10001"


def test_slug_falls_back_to_unknown_when_empty() -> None:
    g = _load_gen_enums()
    assert g.slug("---") == "UNKNOWN"
    assert g.slug("") == "UNKNOWN"


def test_member_names_disambiguates_collisions() -> None:
    g = _load_gen_enums()
    pairs = g.member_names(["Airlines/Aviation", "Airlines Aviation", "Airlines-Aviation"])
    names = [name for name, _ in pairs]
    assert names == ["AIRLINES_AVIATION", "AIRLINES_AVIATION_2", "AIRLINES_AVIATION_3"]
    # The exact API value is always preserved, even when the slug collides.
    assert [value for _, value in pairs] == [
        "Airlines/Aviation",
        "Airlines Aviation",
        "Airlines-Aviation",
    ]


def test_member_names_disambiguation_avoids_existing_slug() -> None:
    # A disambiguated `X_2` must not collide with a real value that already slugs to
    # `X_2`; otherwise the generated Enum would have duplicate members and fail to
    # import. The names must all be unique identifiers.
    g = _load_gen_enums()
    pairs = g.member_names(["X", "X", "X_2"])
    names = [name for name, _ in pairs]
    assert names == ["X", "X_2", "X_2_2"]
    assert len(set(names)) == len(names)
    assert all(name.isidentifier() for name in names)


def test_member_names_preserves_backslash_apostrophe_value() -> None:
    g = _load_gen_enums()
    weird = "Women\\'s Handbag Manufacturing"  # backslash + apostrophe data quirk
    pairs = g.member_names([weird])
    name, value = pairs[0]
    assert value == weird  # byte-for-byte, so the request matches the API
    assert name.isidentifier()
