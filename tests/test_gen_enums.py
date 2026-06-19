"""Unit tests for the spec-walk + dedup logic in ``scripts/gen_enums.py``.

These exercise the pure functions only (no network, no disk). The generated
``src/blitz_api/types/enums.py`` is byte-identical to before, so the existing enum
tests stay unchanged; the live byte-identity is verified separately via
``gen_enums.py --check`` (and the release-time sync gate).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

INDUSTRY = ["Software Development", "Banking"]
COMPANY_TYPE = ["Public Company", "Nonprofit"]
EMPLOYEE_RANGE = ["1-10", "11-50"]
CONTINENT = ["Africa", "Asia"]
SALES_REGION = ["NORAM", "EMEA"]
JOB_FUNCTION = ["Engineering", "Finance & Accounting"]
JOB_LEVEL = ["C-Team", "Director"]
FUNDING_TYPE = ["Series A", "Seed"]

DEFAULTS: dict[str, list[str]] = {
    "industry": INDUSTRY,
    "type": COMPANY_TYPE,
    "employee_range": EMPLOYEE_RANGE,
    "continent": CONTINENT,
    "sales_region": SALES_REGION,
    "job_function": JOB_FUNCTION,
    "job_level": JOB_LEVEL,
    "last_funding_type": FUNDING_TYPE,
}


def _load_gen_enums() -> ModuleType:
    script = Path(__file__).resolve().parent.parent / "scripts" / "gen_enums.py"
    spec = importlib.util.spec_from_file_location("gen_enums", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _filter_prop(values: list[str]) -> dict[str, object]:
    """``{ include: {items.enum}, exclude: {items.enum} }`` — the industry/type shape."""
    return {
        "type": "object",
        "properties": {
            "include": {"type": "array", "items": {"type": "string", "enum": values}},
            "exclude": {"type": "array", "items": {"type": "string", "enum": values}},
        },
    }


def _array_enum_prop(values: list[str]) -> dict[str, object]:
    """``{ type: "array", items: {type:"string", enum} }`` — the plain list shape."""
    return {"type": "array", "items": {"type": "string", "enum": values}}


def _obj_schema(properties: dict[str, object]) -> dict[str, object]:
    return {"type": "object", "properties": properties}


def _endpoint(schema: dict[str, object]) -> dict[str, object]:
    """A POST endpoint repeating the schema across two content-types (like the real spec)."""
    return {
        "post": {
            "requestBody": {
                "content": {
                    "application/json": {"schema": schema},
                    "multipart/form-data": {"schema": copy.deepcopy(schema)},
                },
            },
        },
    }


def _company_block(v: dict[str, list[str]]) -> dict[str, object]:
    return _obj_schema(
        {
            "company": _obj_schema(
                {
                    "industry": _filter_prop(v["industry"]),
                    "type": _filter_prop(v["type"]),
                    "employee_range": _array_enum_prop(v["employee_range"]),
                    "last_funding_type": _filter_prop(v["last_funding_type"]),
                    "hq": _obj_schema(
                        {
                            "continent": _array_enum_prop(v["continent"]),
                            "sales_region": _array_enum_prop(v["sales_region"]),
                        }
                    ),
                }
            ),
        }
    )


def _full_spec(overrides: dict[str, list[str]] | None = None) -> dict[str, object]:
    """A complete spec mirroring the real one: all 8 enums, each repeated across two
    content-types (json + multipart) and, for industry/type/last_funding_type, include +
    exclude, plus continent/sales_region under both companies.hq and employee-finder. Every
    occurrence is identical, so it round-trips cleanly.
    """
    v = {**DEFAULTS, **(overrides or {})}
    return {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "paths": {
            "/v2/search/companies": _endpoint(_company_block(v)),
            "/v2/search/employee-finder": _endpoint(
                _obj_schema(
                    {
                        "continent": _array_enum_prop(v["continent"]),
                        "sales_region": _array_enum_prop(v["sales_region"]),
                        "job_function": _array_enum_prop(v["job_function"]),
                        "job_level": _array_enum_prop(v["job_level"]),
                    }
                )
            ),
        },
    }


def test_maps_all_eight_owning_properties_in_canonical_order() -> None:
    g = _load_gen_enums()
    enums = g.extract_enums(_full_spec())
    assert list(enums) == [
        "Industry",
        "CompanyType",
        "EmployeeRange",
        "Continent",
        "SalesRegion",
        "JobFunction",
        "JobLevel",
        "FundingType",
    ]
    assert enums == {
        "Industry": INDUSTRY,
        "CompanyType": COMPANY_TYPE,
        "EmployeeRange": EMPLOYEE_RANGE,
        "Continent": CONTINENT,
        "SalesRegion": SALES_REGION,
        "JobFunction": JOB_FUNCTION,
        "JobLevel": JOB_LEVEL,
        "FundingType": FUNDING_TYPE,
    }


def test_collapses_identical_duplicate_occurrences() -> None:
    # _full_spec repeats each enum 4x (content-types x include/exclude or endpoints);
    # the result must not be doubled.
    g = _load_gen_enums()
    enums = g.extract_enums(_full_spec())
    assert enums["Continent"] == CONTINENT
    assert enums["Industry"] == INDUSTRY


def test_raises_when_two_occurrences_diverge() -> None:
    g = _load_gen_enums()
    spec = {
        "paths": {
            "/a": _endpoint(_obj_schema({"industry": _filter_prop(["Software Development"])})),
            "/b": _endpoint(_obj_schema({"industry": _filter_prop(["Banking"])})),
        },
    }
    with pytest.raises(ValueError, match=r"(?s)Industry.*divergent"):
        g.extract_enums(spec)


def test_raises_when_a_mapped_enum_is_absent() -> None:
    g = _load_gen_enums()
    spec = {
        "paths": {
            "/v2/search/companies": _endpoint(_company_block(DEFAULTS)),
            # employee-finder is present but job_level is omitted
            "/v2/search/employee-finder": _endpoint(
                _obj_schema({"job_function": _array_enum_prop(JOB_FUNCTION)})
            ),
        },
    }
    with pytest.raises(ValueError, match=r"JobLevel"):
        g.extract_enums(spec)


def test_drops_exact_duplicate_values_but_keeps_near_duplicates() -> None:
    g = _load_gen_enums()
    enums = g.extract_enums(_full_spec({"continent": ["Africa", "Africa", "Africa/North"]}))
    assert enums["Continent"] == ["Africa", "Africa/North"]


def test_warns_about_and_ignores_an_unmapped_property(
    capsys: pytest.CaptureFixture[str],
) -> None:
    g = _load_gen_enums()
    spec = {
        "paths": {
            "/v2/search/companies": _endpoint(_company_block(DEFAULTS)),
            "/v2/search/employee-finder": _endpoint(
                _obj_schema(
                    {
                        "continent": _array_enum_prop(CONTINENT),
                        "sales_region": _array_enum_prop(SALES_REGION),
                        "job_function": _array_enum_prop(JOB_FUNCTION),
                        "job_level": _array_enum_prop(JOB_LEVEL),
                        "seniority": _array_enum_prop(["Junior", "Senior"]),
                    }
                )
            ),
        },
    }
    enums = g.extract_enums(spec)
    assert "Seniority" not in enums
    assert len(enums) == 8
    assert "seniority" in capsys.readouterr().err


def test_records_provenance_and_live_spec_version() -> None:
    g = _load_gen_enums()
    artifact = g.build_artifact(_full_spec())
    assert artifact["_source_url"] == "https://api.blitz-api.ai/openapi"
    assert artifact["spec_version"] == "1.0.0"
    assert re.search(r"do not hand-edit", artifact["_comment"], re.IGNORECASE)


def test_build_artifact_falls_back_to_unknown_version() -> None:
    g = _load_gen_enums()
    spec = _full_spec()
    del spec["info"]
    assert g.build_artifact(spec)["spec_version"] == "unknown"


def test_round_trips_the_double_escaped_value_byte_for_byte() -> None:
    g = _load_gen_enums()
    # Two literal backslashes + apostrophe, exactly as stored upstream.
    value = "Women\\\\'s Handbag Manufacturing"
    artifact = g.build_artifact(_full_spec({"industry": [value]}))
    assert artifact["enums"]["Industry"][0] == value
    reparsed = json.loads(g.serialize_artifact(artifact))
    assert reparsed["enums"]["Industry"][0] == value


def test_serializes_compact_value_lists_with_trailing_newline() -> None:
    g = _load_gen_enums()
    out = g.serialize_artifact(g.build_artifact(_full_spec()))
    assert out.endswith("}\n")
    # Arrays are emitted on one line (no spaces after commas).
    assert '"Continent": ["Africa","Asia"]' in out
