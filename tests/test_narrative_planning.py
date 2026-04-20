"""Unit tests for deterministic narrative planning (no GPT, no integration seams)."""

from __future__ import annotations

import json

import pytest

from game.ctir import build_ctir
from game.narrative_mode_contract import NARRATIVE_MODES
from game.narrative_planning import (
    NARRATIVE_PLAN_VERSION,
    build_narrative_plan,
    narrative_plan_matches_ctir_derivation,
    narrative_plan_version,
    normalize_narrative_plan,
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
        builder_source="tests.narrative_planning",
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


def test_version_constant() -> None:
    assert narrative_plan_version() == NARRATIVE_PLAN_VERSION == 1


def test_build_rejects_non_ctir() -> None:
    with pytest.raises(ValueError, match="looks_like_ctir"):
        build_narrative_plan(ctir={"version": 0})


def test_deterministic_json_stable() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True, "reply_kind": "answer"}},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    p1 = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    p2 = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)


def test_dialogue_mode_and_weights() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_guard", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    assert plan["narrative_mode"] == "dialogue"
    assert plan["narrative_mode_contract"]["mode"] == "dialogue"
    assert validate_narrative_plan(plan) is None
    ra = plan["role_allocation"]
    assert sum(ra[k] for k in ("dialogue", "exposition", "outcome_forward", "transition")) == 100
    assert ra["dialogue"] >= ra["transition"]


def test_plan_carries_validated_mode_contract() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_guard", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    assert plan["narrative_mode"] in NARRATIVE_MODES
    assert plan["narrative_mode_contract"]["mode"] == plan["narrative_mode"]


def test_validate_rejects_legacy_narrative_mode_values() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    legacy = dict(plan)
    legacy["narrative_mode"] = "consequence"
    assert validate_narrative_plan(legacy, strict=True) == "bad_narrative_mode"


def test_validate_rejects_narrative_mode_contract_mismatch() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    bad["narrative_mode"] = "dialogue"
    assert validate_narrative_plan(bad, strict=True) == "narrative_mode_contract_mode_mismatch"


def test_validate_rejects_malformed_narrative_mode_contract() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    nmc = dict(bad["narrative_mode_contract"])
    fm = list(nmc.get("forbidden_moves") or [])
    if "no_generic_fallback" in fm:
        fm.remove("no_generic_fallback")
    nmc["forbidden_moves"] = fm
    bad["narrative_mode_contract"] = nmc
    err = validate_narrative_plan(bad, strict=True)
    assert err and err.startswith("narrative_mode_contract_invalid:")


def test_transition_mode() -> None:
    c = _minimal_ctir(
        resolution={
            "kind": "scene_transition",
            "target_scene_id": "inn",
            "state_changes": {"scene_transition_occurred": True},
        },
    )
    plan = build_narrative_plan(ctir=c)
    assert plan["narrative_mode"] == "transition"
    assert plan["role_allocation"]["transition"] >= 50


def test_allowable_entity_references_option_a_full_visible_roster_not_focal_subset() -> None:
    """OPTION A: with a non-empty published slice, every visible id is listed; CTIR does not shrink the set."""
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_bob", "interaction_mode": "social"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [{"id": "npc_bob", "name": "Bob"}],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    published = [
        {"entity_id": "npc_alice", "display_name": "Alice"},
        {"entity_id": "npc_bob", "display_name": "Bob"},
    ]
    plan = build_narrative_plan(ctir=c, published_entities=published)
    ids = [r["entity_id"] for r in plan["allowable_entity_references"]]
    assert ids == ["npc_alice", "npc_bob"]
    assert plan["scene_anchors"].get("active_interlocutor") == "npc_bob"


def test_allowable_entity_references_omitted_published_is_ctir_only() -> None:
    """Without published_entities, the field lists CTIR-addressed entities only (no visibility slice at builder)."""
    c = _minimal_ctir(
        interaction={"active_target_id": "npc_x"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [{"id": "npc_y", "name": "Y"}],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    plan = build_narrative_plan(ctir=c)
    ids = sorted(r["entity_id"] for r in plan["allowable_entity_references"])
    assert ids == ["npc_x", "npc_y"]


def test_allowable_entity_references_stable_ordering_across_input_row_order() -> None:
    """Deterministic sort: same published rows in different list order yield identical allowable_entity_references."""
    c = _minimal_ctir()
    pub_a = [{"entity_id": "zebra"}, {"entity_id": "alpha"}, {"entity_id": "mule"}]
    pub_b = list(reversed(pub_a))
    p1 = build_narrative_plan(ctir=c, published_entities=pub_a)
    p2 = build_narrative_plan(ctir=c, published_entities=pub_b)
    assert p1["allowable_entity_references"] == p2["allowable_entity_references"]
    assert [r["entity_id"] for r in p1["allowable_entity_references"]] == ["alpha", "mule", "zebra"]


def test_allowable_entities_intersect_published() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_hidden", "interaction_mode": "social"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [{"id": "npc_hidden", "name": "X"}, {"id": "npc_public", "name": "Y"}],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    plan = build_narrative_plan(
        ctir=c,
        published_entities=[{"entity_id": "npc_public", "display_name": "Public"}],
    )
    ids = {r["entity_id"] for r in plan["allowable_entity_references"]}
    assert "npc_public" in ids
    assert "npc_hidden" not in ids


def test_empty_published_list_blocks_all() -> None:
    c = _minimal_ctir(
        interaction={"active_target_id": "npc_guard"},
    )
    plan = build_narrative_plan(ctir=c, published_entities=[])
    assert plan["allowable_entity_references"] == []


def test_normalize_idempotent_sorting() -> None:
    c = _minimal_ctir(
        resolution={"kind": "observe", "clue_id": "c1"},
        interaction={"active_target_id": "z", "responder_target": {"id": "a", "name": "A"}},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [{"id": "m", "name": "M"}, {"id": "a", "name": "A2"}],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    plan = build_narrative_plan(ctir=c)
    n1 = normalize_narrative_plan(plan)
    n2 = normalize_narrative_plan(n1)
    assert json.dumps(n1, sort_keys=True) == json.dumps(n2, sort_keys=True)


def test_validate_rejects_banned_nested_key() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    plan["resolution_meta"] = {"ok": 1, "prompt": "leak"}
    err = validate_narrative_plan(plan, strict=True)
    assert err and "banned" in err


def test_validate_rejects_unknown_required_new_information_kind() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    plan["required_new_information"] = list(plan["required_new_information"]) + [
        {"kind": "invented_semantic_category", "value": "x"},
    ]
    err = validate_narrative_plan(plan, strict=True)
    assert err and "unknown_kind" in err


def test_narrative_plan_matches_ctir_derivation_detects_tampering() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    assert narrative_plan_matches_ctir_derivation(plan, ctir=c, **_DIALOGUE_CONTRACT_INPUTS) is True
    tampered = dict(plan)
    tampered["scene_anchors"] = {**(tampered.get("scene_anchors") or {}), "scene_id": "tampered_scene"}
    assert narrative_plan_matches_ctir_derivation(tampered, ctir=c, **_DIALOGUE_CONTRACT_INPUTS) is False


def test_recent_compressed_events_bounded() -> None:
    c = _minimal_ctir()
    many = [{"turn": i, "code": f"c{i}"} for i in range(30)]
    plan = build_narrative_plan(ctir=c, recent_compressed_events=many)
    assert len(plan["recent_compressed_events"]) <= 12
