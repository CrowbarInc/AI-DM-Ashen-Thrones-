"""Objective N3 — abstract ``narrative_roles`` composition (deterministic + validation)."""

from __future__ import annotations

import json

import pytest

from game.ctir import build_ctir
from game.narrative_planning import (
    NARRATIVE_ROLE_FAMILY_KEYS,
    build_narrative_plan,
    derive_narrative_roles_composition,
    narrative_plan_matches_ctir_derivation,
    narrative_roles_emphasis_band_map,
    validate_narrative_plan,
)

pytestmark = pytest.mark.unit

_DIALOGUE_CONTRACT_INPUTS = {
    "narration_obligations": {"active_npc_reply_expected": True, "active_npc_reply_kind": "answer"},
}


def _minimal_ctir(**kwargs: object) -> dict:
    base = dict(
        turn_id=1,
        scene_id="test_scene",
        player_input="action",
        builder_source="tests.narrative_roles",
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    base.update(kwargs)
    return build_ctir(**base)


def test_narrative_roles_emphasis_band_map_matches_plan_block() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    bands = narrative_roles_emphasis_band_map(plan.get("narrative_roles"))
    assert list(bands) == list(NARRATIVE_ROLE_FAMILY_KEYS)
    for rk in NARRATIVE_ROLE_FAMILY_KEYS:
        assert rk in bands
        assert bands[rk] in {"minimal", "low", "moderate", "elevated", "high"}


def test_build_plan_includes_narrative_roles_and_role_allocation() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    assert "role_allocation" in plan
    assert sum(plan["role_allocation"][k] for k in ("dialogue", "exposition", "outcome_forward", "transition")) == 100
    nr = plan.get("narrative_roles")
    assert isinstance(nr, dict)
    assert set(nr.keys()) == set(NARRATIVE_ROLE_FAMILY_KEYS)
    for rk in nr:
        assert isinstance(nr[rk], dict)
        assert nr[rk].get("emphasis_band") in {"minimal", "low", "moderate", "elevated", "high"}
        assert isinstance(nr[rk].get("signals"), list)


def test_narrative_roles_derivation_deterministic_json_stable() -> None:
    c = _minimal_ctir(
        resolution={"kind": "consequence", "consequences": ["portcullis slams shut behind you"]},
        interaction={"interaction_mode": "activity"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [{"id": "npc_w", "name": "W"}],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    p1 = build_narrative_plan(ctir=c)
    p2 = build_narrative_plan(ctir=c)
    assert json.dumps(p1["narrative_roles"], sort_keys=True) == json.dumps(p2["narrative_roles"], sort_keys=True)


def test_consequence_atoms_prose_not_copied_into_narrative_roles() -> None:
    """N3 roles carry flags/tags only—no consequence sentence text."""
    prose = "portcullis slams shut behind you with extra words"
    c = _minimal_ctir(
        resolution={"kind": "consequence", "consequences": [prose]},
        interaction={"interaction_mode": "activity"},
    )
    plan = build_narrative_plan(ctir=c)
    blob = json.dumps(plan["narrative_roles"], sort_keys=True)
    assert "portcullis" not in blob.lower()
    assert plan["narrative_roles"]["consequence"].get("has_consequence_information") is True


def test_validate_rejects_unknown_narrative_roles_top_key() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    nr = dict(bad["narrative_roles"])
    nr["extra_role"] = {}
    del nr["hook"]
    bad["narrative_roles"] = nr
    err = validate_narrative_plan(bad, strict=True)
    assert err and "narrative_roles_bad_keys" in err


def test_validate_rejects_unsorted_signals() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    la = dict(bad["narrative_roles"]["location_anchor"])
    la["signals"] = ["has_scene_label", "has_scene_id"]  # valid tokens, lexicographically wrong order
    nr = dict(bad["narrative_roles"])
    nr["location_anchor"] = la
    bad["narrative_roles"] = nr
    err = validate_narrative_plan(bad, strict=True)
    assert err and "signals_not_sorted" in err


def test_validate_rejects_outcome_forward_tier_mismatch() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    cons = dict(bad["narrative_roles"]["consequence"])
    cons["outcome_forward_tier"] = "max"
    nr = dict(bad["narrative_roles"])
    nr["consequence"] = cons
    bad["narrative_roles"] = nr
    err = validate_narrative_plan(bad, strict=True)
    assert err == "narrative_roles_outcome_forward_tier_mismatch_role_allocation"


def test_derive_narrative_roles_composition_matches_build_plan_roles() -> None:
    c = _minimal_ctir(
        resolution={"kind": "scene_transition", "target_scene_id": "inn", "state_changes": {"scene_transition_occurred": True}},
    )
    plan = build_narrative_plan(
        ctir=c,
        public_scene_slice={"scene_id": "inn", "scene_name": "The Inn", "location_tokens": ["hearth", "bar"]},
    )
    nr2, _codes = derive_narrative_roles_composition(
        scene_anchors=plan["scene_anchors"],
        active_pressures=plan["active_pressures"],
        required_new_information=plan["required_new_information"],
        narrative_mode=plan["narrative_mode"],
        narrative_mode_contract=plan["narrative_mode_contract"],
        allowable_entity_references=plan["allowable_entity_references"],
        role_allocation=plan["role_allocation"],
    )
    assert nr2 == plan["narrative_roles"]


def test_validate_strict_rejects_banned_key_anywhere_in_plan_tree() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    bad["scene_anchors"] = {**(bad.get("scene_anchors") or {}), "instructions": "do a thing"}
    err = validate_narrative_plan(bad, strict=True)
    assert err and "banned_key_path" in err


def test_narrative_plan_matches_ctir_derivation_includes_narrative_roles() -> None:
    c = _minimal_ctir(resolution={"kind": "observe"}, interaction={"interaction_mode": "activity"})
    plan = build_narrative_plan(ctir=c)
    assert narrative_plan_matches_ctir_derivation(plan, ctir=c) is True
    tampered = dict(plan)
    tr = dict(tampered["narrative_roles"])
    loc = dict(tr["location_anchor"])
    loc["location_token_n"] = 99
    tr["location_anchor"] = loc
    tampered["narrative_roles"] = tr
    assert narrative_plan_matches_ctir_derivation(tampered, ctir=c) is False
