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
    validate_action_outcome_plan_contract,
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


def test_plan_debug_nmc_ship_trace_is_compact_and_aligned_with_contract() -> None:
    c = _minimal_ctir(
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_guard", "interaction_mode": "social"},
    )
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    tr = (plan.get("debug") or {}).get("nmc_ship_trace")
    assert isinstance(tr, dict)
    assert tr.get("mode") == "dialogue"
    assert tr.get("enabled") is True
    assert tr.get("contract_ok") is True
    assert isinstance(tr.get("ob_keys_head"), list)
    assert isinstance(tr.get("fm_head"), list)
    nmc = plan["narrative_mode_contract"]
    assert tr["mode"] == nmc["mode"]


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


def test_action_outcome_structure_present_and_deterministic_for_combat() -> None:
    """Identical CTIR inputs must yield identical prose-free action_outcome plan output."""
    c = _minimal_ctir(
        resolution={
            "kind": "attack",
            "action_id": "atk_sword",
            "success_state": "success",
            "combat": {
                "combat_phase": "attack",
                "actor_id": "pc_hero",
                "target_id": "enemy_orc",
                "hit": True,
                "damage_dealt": 5,
                "healing_applied": 0,
                "conditions_applied": [],
                "conditions_removed": [],
                "combat_ended": False,
                "winner": None,
                "rolls": {"attack_roll": 14, "attack_total": 19, "target_ac": 15},
            },
        },
    )
    p1 = build_narrative_plan(ctir=c)
    p2 = build_narrative_plan(ctir=c)
    assert p1["narrative_mode"] == "action_outcome"
    assert json.dumps(p1["action_outcome"], sort_keys=True) == json.dumps(p2["action_outcome"], sort_keys=True)
    ao = p1["action_outcome"]
    assert ao["present"] is True
    assert ao["source_kind"] == "combat"
    assert ao["result"]["action_id"] == "atk_sword"
    assert ao["effects"]["damage_dealt"] == 5
    assert validate_narrative_plan(p1, strict=True) is None


def test_validation_rejects_action_outcome_with_proseish_fields() -> None:
    c = _minimal_ctir(resolution={"kind": "attack", "combat": {"damage_dealt": 1, "rolls": {"attack_roll": 10}}})
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    ao = dict(bad["action_outcome"])
    ao["result"] = dict(ao["result"])
    ao["result"]["hint"] = "Narrate the outcome."  # banned key under plan tree
    bad["action_outcome"] = ao
    err = validate_narrative_plan(bad, strict=True)
    assert err and ("banned_key_path" in err or "action_outcome_" in err)


def test_validate_action_outcome_plan_contract_passes_for_valid_combat_plan() -> None:
    c = _minimal_ctir(resolution={"kind": "attack", "combat": {"damage_dealt": 1, "rolls": {"attack_roll": 10}}})
    plan = build_narrative_plan(ctir=c)
    ok, reasons = validate_action_outcome_plan_contract(plan, response_type_required="action_outcome")
    assert ok is True
    assert reasons == []


def test_validate_action_outcome_plan_contract_skips_when_narrative_mode_not_action_outcome() -> None:
    c = _minimal_ctir(resolution={"kind": "question", "social": {"npc_reply_expected": True}})
    plan = build_narrative_plan(ctir=c, **_DIALOGUE_CONTRACT_INPUTS)
    bad = dict(plan)
    bad.pop("action_outcome", None)
    ok, reasons = validate_action_outcome_plan_contract(bad, response_type_required="action_outcome")
    assert ok is True
    assert reasons == []


def test_validate_action_outcome_plan_contract_fails_when_action_outcome_missing() -> None:
    c = _minimal_ctir(resolution={"kind": "attack", "combat": {"damage_dealt": 1, "rolls": {"attack_roll": 10}}})
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    bad.pop("action_outcome", None)
    ok, reasons = validate_action_outcome_plan_contract(bad, response_type_required="action_outcome")
    assert ok is False
    assert any("missing_action_outcome" in r for r in reasons)


def test_validate_action_outcome_plan_contract_fails_on_extra_prose_key_in_action_outcome() -> None:
    c = _minimal_ctir(resolution={"kind": "attack", "combat": {"damage_dealt": 1, "rolls": {"attack_roll": 10}}})
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    ao = dict(bad["action_outcome"])
    ao["hint"] = "forbidden"
    bad["action_outcome"] = ao
    ok, reasons = validate_action_outcome_plan_contract(bad, response_type_required="action_outcome")
    assert ok is False
    assert any("action_outcome_bad_keys" in r or "narrative_plan_invalid" in r for r in reasons)


def test_action_outcome_mode_fails_without_present_structure() -> None:
    c = _minimal_ctir(resolution={"kind": "attack", "combat": {"damage_dealt": 1, "rolls": {"attack_roll": 10}}})
    plan = build_narrative_plan(ctir=c)
    bad = dict(plan)
    bad["action_outcome"] = {"present": False}
    err = validate_narrative_plan(bad, strict=True)
    assert err is not None


def test_action_outcome_skill_check_source_and_determinism() -> None:
    c = _minimal_ctir(
        resolution={
            "kind": "investigate",
            "action_id": "search_crate",
            "success_state": "success",
            "interactable_id": "crate_a",
            "skill_check": {
                "skill": "perception",
                "dc": 12,
                "difficulty": 12,
                "modifier": 1,
                "roll": 18,
                "total": 19,
                "success": True,
            },
        },
    )
    p1 = build_narrative_plan(ctir=c)
    p2 = build_narrative_plan(ctir=c)
    assert p1["narrative_mode"] == "action_outcome"
    assert json.dumps(p1["action_outcome"], sort_keys=True) == json.dumps(p2["action_outcome"], sort_keys=True)
    ao = p1["action_outcome"]
    assert ao["source_kind"] == "skill_check"
    assert ao["result"]["roll_summary"].get("total") == 19
    assert ao["result"]["target_id"] == "crate_a"
    assert validate_narrative_plan(p1, strict=True) is None


def test_action_outcome_environment_source_from_noncombat_slice() -> None:
    nc = {
        "framework_version": "2026.04.noncombat.v1",
        "kind": "investigation",
        "subkind": "interact",
        "authority_domain": "scene_state",
        "deterministic_resolved": True,
        "requires_check": False,
        "outcome_type": "closed",
        "success_state": "success",
        "discovered_entities": [{"entity_kind": "interactable", "entity_id": "lever_2"}],
        "blocked_reason_codes": [],
        "ambiguous_reason_codes": [],
        "unsupported_reason_codes": [],
    }
    c = _minimal_ctir(
        resolution={
            "kind": "interact",
            "action_id": "pull_lever",
            "success_state": "success",
            "outcome_type": "closed",
            "noncombat_resolution": nc,
        },
    )
    p1 = build_narrative_plan(ctir=c)
    p2 = build_narrative_plan(ctir=c)
    assert p1["narrative_mode"] == "action_outcome"
    assert json.dumps(p1["action_outcome"], sort_keys=True) == json.dumps(p2["action_outcome"], sort_keys=True)
    ao = p1["action_outcome"]
    assert ao["source_kind"] == "environment"
    assert ao["result"]["target_id"] == "lever_2"
    assert ao["result"]["roll_summary"].get("outcome_type") == "closed"
    assert validate_narrative_plan(p1, strict=True) is None


def test_validate_rejects_unknown_required_new_information_kind() -> None:
    c = _minimal_ctir()
    plan = build_narrative_plan(ctir=c)
    plan["required_new_information"] = list(plan["required_new_information"]) + [
        {"kind": "invented_semantic_category", "value": "x"},
    ]
    err = validate_narrative_plan(plan, strict=True)
    assert err and "unknown_kind" in err


def test_answer_required_ctir_turn_produces_answer_exposition_plan_enabled() -> None:
    nc = {
        "framework_version": "2026.04.noncombat.v1",
        "kind": "question",
        "subkind": "query",
        "authority_domain": "world",
        "deterministic_resolved": True,
        "requires_check": False,
        "outcome_type": "open",
        "success_state": "success",
        "surfaced_facts": ["The frontier gate is watched by two patrols."],
        "blocked_reason_codes": [],
        "ambiguous_reason_codes": [],
        "unsupported_reason_codes": [],
    }
    c = _minimal_ctir(
        player_input="Who is watching the gate?",
        resolution={"kind": "question", "noncombat_resolution": nc},
    )
    response_policy = {
        "answer_completeness": {
            "enabled": True,
            "answer_required": True,
            "answer_must_come_first": True,
            "expected_voice": "narrator",
            "allowed_partial_reasons": [],
            "forbid_deflection": True,
            "forbid_generic_nonanswer": True,
            "trace": {"trigger_source": "player_direct_question"},
        }
    }
    plan = build_narrative_plan(ctir=c, response_policy=response_policy)
    aep = plan.get("answer_exposition_plan") or {}
    assert aep.get("enabled") is True
    assert aep.get("answer_required") is True
    assert aep.get("answer_intent") == "direct_answer"
    assert isinstance(aep.get("facts"), list)
    assert len(aep.get("facts") or []) >= 1
    assert validate_narrative_plan(plan, strict=True) is None


def test_lore_exposition_query_produces_facts_and_delivery_structure() -> None:
    nc = {
        "framework_version": "2026.04.noncombat.v1",
        "kind": "lore",
        "subkind": "exposition",
        "authority_domain": "world",
        "deterministic_resolved": True,
        "requires_check": False,
        "outcome_type": "open",
        "success_state": "success",
        "surfaced_facts": ["The Ashen Thrones are sworn to silence in public courts."],
        "blocked_reason_codes": [],
        "ambiguous_reason_codes": [],
        "unsupported_reason_codes": [],
    }
    c = _minimal_ctir(
        player_input="Tell me about the Ashen Thrones.",
        resolution={"kind": "question", "noncombat_resolution": nc},
    )
    response_policy = {
        "answer_completeness": {
            "enabled": True,
            "answer_required": True,
            "answer_must_come_first": False,
            "expected_voice": "narrator",
            "allowed_partial_reasons": ["npc_ignorance"],
            "trace": {"trigger_source": "lore_exposition_query"},
        }
    }
    plan = build_narrative_plan(ctir=c, response_policy=response_policy)
    aep = plan["answer_exposition_plan"]
    assert aep["enabled"] is True
    assert aep["answer_intent"] == "lore_exposition"
    assert aep["voice"]["delivery_mode"] in {"diegetic_exposition", "plain_answer"}
    assert isinstance(aep["delivery"]["forbidden_moves"], list)
    assert any("ctir_noncombat_fact_" in f.get("id", "") for f in (aep.get("facts") or []))
    assert validate_narrative_plan(plan, strict=True) is None


def test_non_answer_narration_does_not_require_answer_exposition_plan() -> None:
    c = _minimal_ctir(
        player_input="I head toward the gate.",
        resolution={"kind": "move"},
    )
    plan = build_narrative_plan(ctir=c)
    aep = plan.get("answer_exposition_plan") or {}
    assert aep.get("enabled") is False
    assert aep.get("answer_required") is False
    assert aep.get("answer_intent") == "none"
    assert validate_narrative_plan(plan, strict=True) is None


def test_malformed_answer_exposition_plan_fails_validation_when_mode_exposition_answer() -> None:
    c = _minimal_ctir(
        player_input="Where is the barracks?",
        resolution={"kind": "question"},
    )
    response_policy = {
        "answer_completeness": {
            "enabled": True,
            "answer_required": True,
            "answer_must_come_first": True,
            "expected_voice": "narrator",
            "allowed_partial_reasons": [],
            "trace": {"trigger_source": "player_direct_question"},
        }
    }
    plan = build_narrative_plan(ctir=c, response_policy=response_policy)
    assert plan["narrative_mode"] == "exposition_answer"
    bad = dict(plan)
    bad["answer_exposition_plan"] = {"enabled": True}  # missing required keys/shape
    err = validate_narrative_plan(bad, strict=True)
    assert err and err.startswith("answer_exposition_plan_invalid:")


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
