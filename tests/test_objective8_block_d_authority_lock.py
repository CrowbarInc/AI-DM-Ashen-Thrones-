"""Objective #8 Block D — authority flow, canonical precedence, anti-reconstruction, combat isolation.

Locks: runtime seam → ``noncombat_resolution`` → ``build_ctir`` → CTIR ``noncombat`` slice →
``normalize_resolution`` overlays → prompt/narrative consumers prefer CTIR-backed semantics.
"""

from __future__ import annotations

import pytest

from game.api import _resolve_engine_noncombat_seam
from game.ctir import build_ctir, normalize_resolution
from game.narrative_planning import build_narrative_plan
from game.noncombat_resolution import NONCOMBAT_FRAMEWORK_VERSION, classify_noncombat_kind, normalize_noncombat_resolution
from game.prompt_context import _ctir_to_prompt_semantics, derive_narration_obligations
from game.scene_actions import normalize_scene_action

pytestmark = [pytest.mark.unit]


def _explore_kw():
    return {"list_scene_ids": lambda: [], "load_scene_fn": lambda _sid: {"scene": {"id": _sid}}}


@pytest.mark.integration
def test_e2e_seam_observe_to_ctir_to_prompt_semantics_and_narrative_plan() -> None:
    """Structured action → runtime seam → resolution w/ contract → CTIR → downstream preference."""
    scene = {"scene": {"id": "e2e_s", "location": "Courtyard", "visible_facts": [], "discoverable_clues": [], "hidden_facts": []}}
    action = normalize_scene_action(
        {"id": "e2e_o", "label": "Observe", "type": "observe", "prompt": "Scan the courtyard."}
    )
    resolution = _resolve_engine_noncombat_seam(
        scene,
        {},
        {},
        action,
        raw_player_text="Scan the courtyard.",
        character=None,
        turn_counter=1,
        exploration_kwargs=_explore_kw(),
        explicit_route=None,
    )
    assert isinstance(resolution.get("noncombat_resolution"), dict)
    nc = resolution["noncombat_resolution"]
    assert nc.get("kind") == "perception"
    assert nc.get("outcome_type") == "closed"

    c = build_ctir(
        turn_id=901,
        scene_id="e2e_s",
        player_input="Scan the courtyard.",
        builder_source="tests.objective8.e2e",
        resolution=resolution,
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    assert c["noncombat"].get("kind") == "perception"
    assert c["noncombat"].get("framework_version") == NONCOMBAT_FRAMEWORK_VERSION
    assert c["resolution"].get("outcome_type") == "closed"

    sem = _ctir_to_prompt_semantics(c)
    assert sem["noncombat"].get("kind") == "perception"
    assert sem["resolution"].get("outcome_type") == "closed"

    plan = build_narrative_plan(ctir=c, public_scene_slice={"scene_id": "e2e_s", "scene_name": "Courtyard"})
    kinds = {item.get("kind") for item in plan.get("required_new_information", [])}
    assert "outcome_type" in kinds
    ot_rows = [x for x in plan["required_new_information"] if x.get("kind") == "outcome_type"]
    assert ot_rows and ot_rows[0].get("value") == "closed"


def test_normalize_resolution_contract_requires_check_over_raw() -> None:
    raw = {
        "kind": "observe",
        "requires_check": True,
        "check_request": {"requires_check": True, "reason": "raw_legacy", "skill_id": "perception"},
        "noncombat_resolution": {
            "framework_version": NONCOMBAT_FRAMEWORK_VERSION,
            "kind": "perception",
            "subkind": "observe",
            "authority_domain": "scene_state",
            "deterministic_resolved": True,
            "requires_check": False,
            "outcome_type": "closed",
            "success_state": "neutral",
        },
    }
    out = normalize_resolution(raw)
    assert out["requires_check"] is False
    assert "check_request" not in out


def test_normalize_resolution_contract_check_request_over_raw() -> None:
    contract_cr = {"requires_check": True, "reason": "contract_wins", "skill_id": "diplomacy"}
    raw = {
        "kind": "persuade",
        "requires_check": True,
        "check_request": {"requires_check": True, "reason": "raw_legacy"},
        "noncombat_resolution": {
            "framework_version": NONCOMBAT_FRAMEWORK_VERSION,
            "kind": "social_probe",
            "subkind": "persuade",
            "authority_domain": "interaction_state",
            "deterministic_resolved": False,
            "requires_check": True,
            "check_request": contract_cr,
            "outcome_type": "pending_check",
            "success_state": "unknown",
        },
    }
    out = normalize_resolution(raw)
    assert out["check_request"]["reason"] == "contract_wins"
    assert out["outcome_type"] == "pending_check"


def test_normalize_resolution_contract_outcome_and_success_over_raw_social_shape() -> None:
    raw = {
        "kind": "question",
        "success": True,
        "outcome_type": "closed",
        "success_state": "success",
        "social": {"npc_reply_expected": True, "reply_kind": "answer"},
        "noncombat_resolution": {
            "framework_version": NONCOMBAT_FRAMEWORK_VERSION,
            "kind": "social_probe",
            "subkind": "question",
            "authority_domain": "interaction_state",
            "deterministic_resolved": True,
            "requires_check": False,
            "outcome_type": "ambiguous",
            "success_state": "neutral",
            "ambiguous_reason_codes": ["synthetic_contract_signal"],
        },
    }
    out = normalize_resolution(raw)
    assert out["outcome_type"] == "ambiguous"
    assert out["success_state"] == "neutral"
    assert "social" not in out


def test_prompt_semantics_prefers_noncombat_narration_constraints_over_legacy_social() -> None:
    """Passthrough merge: obligation-facing ``resolution.social`` reflects contract narration_constraints."""
    ncr = {
        "framework_version": NONCOMBAT_FRAMEWORK_VERSION,
        "kind": "social_probe",
        "subkind": "question",
        "authority_domain": "interaction_state",
        "deterministic_resolved": True,
        "requires_check": False,
        "outcome_type": "closed",
        "success_state": "neutral",
        "narration_constraints": {"npc_reply_expected": True, "reply_kind": "answer"},
    }
    c = build_ctir(
        turn_id=902,
        scene_id="hall",
        player_input="Why?",
        builder_source="tests.objective8.sem",
        resolution={
            "kind": "question",
            "social": {"npc_reply_expected": False, "reply_kind": "reaction"},
            "noncombat_resolution": ncr,
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    sem = _ctir_to_prompt_semantics(c)
    soc = sem["resolution"].get("social") or {}
    assert soc.get("npc_reply_expected") is True
    assert soc.get("reply_kind") == "answer"

    session_view = {
        "turn_counter": 3,
        "visited_scene_count": 2,
        "active_interaction_target_id": "npc_a",
        "active_interaction_kind": "question",
        "interaction_mode": "social",
    }
    obl = derive_narration_obligations(
        session_view=session_view,
        resolution=sem["resolution"],
        intent={"labels": ["social_probe"]},
        recent_log_for_prompt=[],
        scene_runtime={},
    )
    assert obl.get("active_npc_reply_expected") is True
    assert obl.get("active_npc_reply_kind") == "answer"


def test_narrative_planning_prefers_noncombat_narration_constraints_over_raw_social() -> None:
    ncr = {
        "framework_version": NONCOMBAT_FRAMEWORK_VERSION,
        "kind": "social_probe",
        "subkind": "question",
        "authority_domain": "interaction_state",
        "deterministic_resolved": True,
        "requires_check": False,
        "outcome_type": "closed",
        "success_state": "neutral",
        "narration_constraints": {"npc_reply_expected": True, "reply_kind": "answer"},
    }
    c = build_ctir(
        turn_id=903,
        scene_id="z",
        player_input="?",
        builder_source="tests.objective8.plan",
        resolution={
            "kind": "question",
            "social": {"npc_reply_expected": False, "reply_kind": "reaction"},
            "noncombat_resolution": ncr,
        },
        interaction={"active_target_id": "npc_z", "interaction_mode": "social", "interaction_kind": "question"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    plan = build_narrative_plan(ctir=c, public_scene_slice={"scene_id": "z", "scene_name": "Hall"})
    codes = plan["active_pressures"].get("scene_tension_codes") or []
    assert any("social.reply_kind:answer" in str(x) for x in codes)
    assert not any("social.reply_kind:reaction" in str(x) for x in codes)


def test_narrative_planning_check_pressure_follows_contract_not_raw_when_normalized() -> None:
    """After ``build_ctir``, ``resolution`` is contract-overlaid — no phantom check from superseded raw."""
    cls = classify_noncombat_kind({"type": "observe", "id": "x"})
    ncr = normalize_noncombat_resolution(
        {"kind": "observe", "success": None, "requires_check": False},
        cls,
        route="exploration",
        source_engine="test",
    )
    c = build_ctir(
        turn_id=904,
        scene_id="z",
        player_input="look",
        builder_source="tests.objective8.check",
        resolution={
            "kind": "observe",
            "requires_check": True,
            "check_request": {"requires_check": True, "reason": "stale_raw"},
            "noncombat_resolution": ncr,
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    assert c["resolution"].get("requires_check") is False
    plan = build_narrative_plan(ctir=c, public_scene_slice={"scene_id": "z", "scene_name": "Yard"})
    assert plan["active_pressures"].get("interaction_pressure") != "check_pending"


def test_no_reconstruction_when_noncombat_resolution_absent() -> None:
    """Raw exploration/social keys must not populate CTIR ``noncombat`` without a contract."""
    resolution = {
        "kind": "observe",
        "success": True,
        "requires_check": False,
        "social": {"npc_reply_expected": True, "reply_kind": "answer"},
        "discovered_clues": ["lead_alpha"],
        "metadata": {"exploration_probe": True},
    }
    c = build_ctir(
        turn_id=905,
        scene_id="nr",
        player_input="look around",
        builder_source="tests.objective8.no_nc",
        resolution=resolution,
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    assert c["noncombat"] == {}
    assert isinstance(c["resolution"].get("social"), dict)
    assert c["resolution"].get("kind") == "observe"


def test_combat_shaped_resolution_without_contract_has_empty_noncombat() -> None:
    """Combat-only resolutions skip ``noncombat_resolution`` — CTIR must not invent a probe slice."""
    c = build_ctir(
        turn_id=906,
        scene_id="battle",
        player_input="I swing.",
        builder_source="tests.objective8.combat",
        resolution={
            "kind": "attack",
            "action_id": "atk1",
            "label": "Longsword",
            "success": True,
            "skill_check": {"roll": 18, "total": 24, "dc": 15, "success": True},
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    assert c["noncombat"] == {}
    assert c["resolution"].get("kind") == "attack"


def test_initiative_like_resolution_without_contract_has_empty_noncombat() -> None:
    c = build_ctir(
        turn_id=907,
        scene_id="battle",
        player_input="Roll for it.",
        builder_source="tests.objective8.init",
        resolution={
            "kind": "initiative",
            "action_id": "initiative",
            "label": "Roll initiative",
            "success": None,
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    assert c["noncombat"] == {}
