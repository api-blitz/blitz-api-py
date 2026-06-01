"""Tests for the generated enums, including a codegen drift guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path

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


def test_generated_enums_file_is_in_sync() -> None:
    """The committed enums.py must match what gen_enums.py would produce now."""
    script = Path(__file__).resolve().parent.parent / "scripts" / "gen_enums.py"
    spec = importlib.util.spec_from_file_location("gen_enums", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.render() == module.TARGET.read_text(encoding="utf-8"), (
        "enums.py is stale — run `python scripts/gen_enums.py` and commit."
    )
