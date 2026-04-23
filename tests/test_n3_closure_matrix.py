"""N3 closure: composable fixture matrix + cross-scenario invariants."""

from __future__ import annotations

import json

import pytest

from game.narrative_plan_upstream import apply_upstream_narrative_role_reemphasis
from game.narrative_planning import NARRATIVE_PLAN_VERSION, normalize_narrative_plan, validate_narrative_plan
from tests.helpers.n3_closure_matrix import N3_CLOSURE_SCENARIOS, build_plan_for_n3_scenario

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("row", N3_CLOSURE_SCENARIOS, ids=lambda r: r["name"])
def test_n3_matrix_plan_builds_validates_and_roles_bounded(row: dict) -> None:
    plan = build_plan_for_n3_scenario(row)
    assert plan.get("version") == NARRATIVE_PLAN_VERSION
    assert validate_narrative_plan(plan, strict=True) is None
    nr = plan["narrative_roles"]
    for rk, sub in nr.items():
        assert len(sub.get("signals") or []) <= 12
        if rk == "hook":
            assert len(sub.get("information_kind_tags") or []) <= 8


@pytest.mark.parametrize("row", N3_CLOSURE_SCENARIOS, ids=lambda r: r["name"])
def test_n3_matrix_deterministic_roles_json(row: dict) -> None:
    a = json.dumps(build_plan_for_n3_scenario(row)["narrative_roles"], sort_keys=True)
    b = json.dumps(build_plan_for_n3_scenario(row)["narrative_roles"], sort_keys=True)
    assert a == b


def test_normalize_narrative_plan_idempotent_on_valid_plan() -> None:
    plan = build_plan_for_n3_scenario(N3_CLOSURE_SCENARIOS[0])
    n1 = normalize_narrative_plan(plan)
    n2 = normalize_narrative_plan(n1)
    assert n1 == n2
    assert validate_narrative_plan(n1, strict=False) is None


def test_normalize_narrative_plan_dedupes_duplicate_role_signals() -> None:
    plan = build_plan_for_n3_scenario(N3_CLOSURE_SCENARIOS[0])
    p2 = json.loads(json.dumps(plan))
    la = dict(p2["narrative_roles"]["location_anchor"])
    la["signals"] = ["has_scene_id", "has_scene_id", "has_scene_label"]
    nr = dict(p2["narrative_roles"])
    nr["location_anchor"] = la
    p2["narrative_roles"] = nr
    assert validate_narrative_plan(p2, strict=False) is None
    fixed = normalize_narrative_plan(p2)
    sigs = fixed["narrative_roles"]["location_anchor"]["signals"]
    assert sigs == sorted(set(sigs))
    assert len(sigs) <= len(["has_scene_id", "has_scene_id", "has_scene_label"])


def test_upstream_apply_is_idempotent_per_plan_object() -> None:
    row = next(x for x in N3_CLOSURE_SCENARIOS if x["name"] == "grounding_location_forward")
    plan = build_plan_for_n3_scenario(row)
    p = json.loads(json.dumps(plan))
    la = dict(p["narrative_roles"]["location_anchor"])
    la["emphasis_band"] = "minimal"
    p["narrative_roles"] = {**dict(p["narrative_roles"]), "location_anchor": la}
    assert validate_narrative_plan(p, strict=False) is None
    bands_before = {k: dict(p["narrative_roles"][k])["emphasis_band"] for k in p["narrative_roles"]}
    _, t1 = apply_upstream_narrative_role_reemphasis(p)
    assert t1.get("applied") is True
    bands_mid = {k: dict(p["narrative_roles"][k])["emphasis_band"] for k in p["narrative_roles"]}
    _, t2 = apply_upstream_narrative_role_reemphasis(p)
    assert t2.get("skip_reason") == "upstream_repair_idempotent_already_applied"
    bands_after = {k: dict(p["narrative_roles"][k])["emphasis_band"] for k in p["narrative_roles"]}
    assert bands_mid == bands_after
    assert bands_mid != bands_before


def test_collapse_observability_hint_on_high_contrast_scenario() -> None:
    from game import prompt_context as pc

    row = next(x for x in N3_CLOSURE_SCENARIOS if x["name"] == "collapse_risk_high_contrast_natural")
    plan = build_plan_for_n3_scenario(row)
    skim = pc._narrative_roles_prompt_debug_skim(plan, plan_validation_error=None)
    hint = (skim.get("collapse_observability") or {}).get("anchor_hint")
    assert hint in ("high_band_vs_sparse_peers", "low_signal_coverage", "none")


def test_upstream_no_repair_when_no_weak_roles() -> None:
    plan = build_plan_for_n3_scenario(next(x for x in N3_CLOSURE_SCENARIOS if x["name"] == "sparse_but_valid"))
    p = json.loads(json.dumps(plan))
    for k in list(p["narrative_roles"].keys()):
        sub = dict(p["narrative_roles"][k])
        sub["emphasis_band"] = "moderate"
        p["narrative_roles"][k] = sub
    assert validate_narrative_plan(p, strict=False) is None
    _, trace = apply_upstream_narrative_role_reemphasis(p)
    assert trace.get("applied") is False
    assert trace.get("skip_reason") == "no_weak_roles"
