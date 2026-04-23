"""Objective N3 upstream role re-emphasis (bounded shaping; trusted plans only)."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from game import ctir
from game import prompt_context as pc
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_plan_bundle import attach_narration_plan_bundle, get_attached_narration_plan_bundle
from game.narrative_plan_upstream import apply_upstream_narrative_role_reemphasis
from game.narrative_planning import build_narrative_plan, validate_narrative_plan
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests
from tests.test_narrative_roles import _DIALOGUE_CONTRACT_INPUTS, _minimal_ctir


pytestmark = pytest.mark.unit


def _assert_upstream_module_has_no_final_emission_import() -> None:
    spec = importlib.util.find_spec("game.narrative_plan_upstream")
    assert spec is not None and spec.origin
    text = Path(spec.origin).read_text(encoding="utf-8")
    assert "final_emission_repairs" not in text


def test_no_final_emission_repairs_dependency_in_upstream_module() -> None:
    _assert_upstream_module_has_no_final_emission_import()


def test_location_anchor_reemphasis_when_grounding_present_but_band_minimal() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    p = copy.deepcopy(plan)
    la = dict(p["narrative_roles"]["location_anchor"])
    assert la.get("scene_id_present") or la.get("location_token_n", 0) > 0 or la.get("scene_label_present")
    la["emphasis_band"] = "minimal"
    nr = dict(p["narrative_roles"])
    nr["location_anchor"] = la
    p["narrative_roles"] = nr
    assert validate_narrative_plan(p, strict=False) is None
    out, trace = apply_upstream_narrative_role_reemphasis(p)
    assert out is p
    assert trace.get("applied") is True
    assert "location_anchor" in (trace.get("reinforced_families") or [])
    assert p["narrative_roles"]["location_anchor"]["emphasis_band"] == "low"


def test_actor_anchor_reemphasis_when_interlocutor_present() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    p = copy.deepcopy(plan)
    aa = dict(p["narrative_roles"]["actor_anchor"])
    assert aa.get("interlocutor_present") is True
    aa["emphasis_band"] = "low"
    nr = dict(p["narrative_roles"])
    nr["actor_anchor"] = aa
    p["narrative_roles"] = nr
    assert validate_narrative_plan(p, strict=False) is None
    _, trace = apply_upstream_narrative_role_reemphasis(p)
    assert trace.get("applied") is True
    assert "actor_anchor" in (trace.get("reinforced_families") or [])
    assert p["narrative_roles"]["actor_anchor"]["emphasis_band"] == "moderate"


def test_pressure_reemphasis_when_pending_leads_signal() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(
        ctir=c,
        session_interaction={"pending_lead_ids": ["lead_a", "lead_b"]},
        **_DIALOGUE_CONTRACT_INPUTS,
    )
    p = copy.deepcopy(plan)
    pr = dict(p["narrative_roles"]["pressure"])
    assert int(pr.get("pending_lead_n") or 0) > 0
    pr["emphasis_band"] = "minimal"
    nr = dict(p["narrative_roles"])
    nr["pressure"] = pr
    p["narrative_roles"] = nr
    assert validate_narrative_plan(p, strict=False) is None
    _, trace = apply_upstream_narrative_role_reemphasis(p)
    assert trace.get("applied") is True
    assert "pressure" in (trace.get("reinforced_families") or [])
    assert p["narrative_roles"]["pressure"]["emphasis_band"] == "low"


def test_hook_reemphasis_when_required_information_nonempty() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "clue_id": "clue_9"},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    p = copy.deepcopy(plan)
    hk = dict(p["narrative_roles"]["hook"])
    assert int(hk.get("required_new_information_n") or 0) > 0
    hk["emphasis_band"] = "low"
    nr = dict(p["narrative_roles"])
    nr["hook"] = hk
    p["narrative_roles"] = nr
    assert validate_narrative_plan(p, strict=False) is None
    _, trace = apply_upstream_narrative_role_reemphasis(p)
    assert trace.get("applied") is True
    assert "hook" in (trace.get("reinforced_families") or [])
    assert p["narrative_roles"]["hook"]["emphasis_band"] == "moderate"


def test_consequence_reemphasis_when_consequence_information_flag() -> None:
    c = _minimal_ctir(
        resolution={"kind": "consequence", "consequences": ["a"]},
        interaction={"interaction_mode": "activity"},
    )
    plan = build_narrative_plan(ctir=c)
    p = copy.deepcopy(plan)
    cn = dict(p["narrative_roles"]["consequence"])
    assert cn.get("has_consequence_information") is True
    cn["emphasis_band"] = "minimal"
    nr = dict(p["narrative_roles"])
    nr["consequence"] = cn
    p["narrative_roles"] = nr
    assert validate_narrative_plan(p, strict=False) is None
    _, trace = apply_upstream_narrative_role_reemphasis(p)
    assert trace.get("applied") is True
    assert "consequence" in (trace.get("reinforced_families") or [])
    assert p["narrative_roles"]["consequence"]["emphasis_band"] == "low"


def test_no_repair_when_plan_not_trustworthy() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    bad = copy.deepcopy(plan)
    bad.pop("narrative_roles", None)
    assert validate_narrative_plan(bad, strict=False) is not None
    before = json.dumps(bad, sort_keys=True)
    _, trace = apply_upstream_narrative_role_reemphasis(bad)
    assert trace.get("skip_reason") == "plan_not_trustworthy"
    assert trace.get("applied") is False
    assert json.dumps(bad, sort_keys=True) == before
    assert "n3_upstream_role_reemphasis" not in json.dumps(bad)


def test_no_repair_when_no_weak_roles() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    p = copy.deepcopy(plan)
    nr_new: dict[str, object] = {}
    for k, sub in (p.get("narrative_roles") or {}).items():
        if isinstance(sub, dict):
            d = dict(sub)
            d["emphasis_band"] = "moderate"
            nr_new[str(k)] = d
    p["narrative_roles"] = nr_new
    assert validate_narrative_plan(p, strict=False) is None
    _, trace = apply_upstream_narrative_role_reemphasis(p)
    assert trace.get("applied") is False
    assert trace.get("skip_reason") == "no_weak_roles"
    dbg = p.get("debug") or {}
    ur = dbg.get("n3_upstream_role_reemphasis")
    assert isinstance(ur, dict)
    assert ur.get("skip_reason") == "no_weak_roles"


def test_repair_preserves_hook_counters_and_kind_tags() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "clue_id": "c1"},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    p = copy.deepcopy(plan)
    hk = dict(p["narrative_roles"]["hook"])
    hk["emphasis_band"] = "minimal"
    p["narrative_roles"] = {**dict(p["narrative_roles"]), "hook": hk}
    assert validate_narrative_plan(p, strict=False) is None
    hook_before = copy.deepcopy(p["narrative_roles"]["hook"])
    apply_upstream_narrative_role_reemphasis(p)
    hk_after = p["narrative_roles"]["hook"]
    for fld in (
        "required_new_information_n",
        "distinct_information_kind_n",
        "information_kind_tags",
        "prompt_obligation_key_n",
        "narrative_mode_contract_enabled",
    ):
        assert hk_after.get(fld) == hook_before.get(fld)


def test_repair_does_not_touch_role_allocation_or_ctir_fields() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "clue_id": "c1"},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    ra_before = copy.deepcopy(plan["role_allocation"])
    p = copy.deepcopy(plan)
    hk = dict(p["narrative_roles"]["hook"])
    hk["emphasis_band"] = "minimal"
    p["narrative_roles"] = {**dict(p["narrative_roles"]), "hook": hk}
    assert validate_narrative_plan(p, strict=False) is None
    apply_upstream_narrative_role_reemphasis(p)
    assert p["role_allocation"] == ra_before
    assert p.get("version") == plan.get("version")


def test_prompt_debug_skim_includes_upstream_role_reemphasis() -> None:
    session = {
        "active_scene_id": "s1",
        "turn_counter": 3,
        "visited_scene_ids": ["s0", "s1"],
        "interaction_context": {
            "active_interaction_target_id": None,
            "active_interaction_kind": None,
            "interaction_mode": "none",
        },
    }
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s1",
        player_input="What do you hear?",
        builder_source="tests.test_narrative_upstream_role_reemphasis",
        intent={"raw_text": "What do you hear?", "labels": ["general"], "mode": "social"},
        resolution={
            "kind": "question",
            "label": "ask",
            "action_id": "ctir-q",
            "clue_id": "clue_x",
            "authoritative_outputs": {},
            "metadata": {},
        },
        interaction={"active_target_id": "npc_x", "interaction_mode": "social", "interaction_kind": "question"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    kw = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": session,
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "What do you hear?",
        "resolution": {"kind": "travel", "label": "move", "action_id": "raw-walk"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"]},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
        "include_non_public_prompt_keys": True,
    }
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
        bundle = get_attached_narration_plan_bundle(session)
        assert isinstance(bundle, dict)
        plan = bundle.get("narrative_plan")
        assert isinstance(plan, dict)
        hk = dict(plan["narrative_roles"]["hook"])
        hk["emphasis_band"] = "minimal"
        plan2 = copy.deepcopy(plan)
        plan2["narrative_roles"] = {**dict(plan2["narrative_roles"]), "hook": hk}
        assert validate_narrative_plan(plan2, strict=False) is None
        apply_upstream_narrative_role_reemphasis(plan2)
        bundle2 = dict(bundle)
        bundle2["narrative_plan"] = plan2
        attach_narration_plan_bundle(session, bundle2)
        ctx = pc.build_narration_context(**kw)
    finally:
        detach_ctir(session)
    skim = (ctx.get("prompt_debug") or {}).get("narrative_plan", {}).get("narrative_roles_skim") or {}
    ur = skim.get("upstream_role_reemphasis")
    assert isinstance(ur, dict)
    assert ur.get("applied") is True
    assert ur.get("reinforced_families")
    instr = "\n".join(ctx.get("instructions") or [])
    assert "N3 bundle upstream" in instr
