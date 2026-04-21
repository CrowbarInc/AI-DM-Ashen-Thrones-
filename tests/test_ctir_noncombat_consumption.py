"""CTIR consumes runtime ``noncombat_resolution`` (Objective #8 Block C)."""

from __future__ import annotations

import pytest

from game import ctir
from game.ctir_runtime import build_runtime_ctir_for_narration
from game.noncombat_resolution import (
    NONCOMBAT_FRAMEWORK_VERSION,
    attach_noncombat_contract,
    classify_noncombat_kind,
    normalize_noncombat_resolution,
    resolve_noncombat_action,
)
from game.prompt_context import _ctir_to_prompt_semantics
from game.scene_actions import normalize_scene_action

pytestmark = pytest.mark.unit


def _normalized_observe_action() -> dict:
    return normalize_scene_action(
        {"id": "o1", "label": "Observe", "type": "observe", "prompt": "Look around."}
    )


def _normalized_investigate_action() -> dict:
    return normalize_scene_action(
        {"id": "i1", "label": "Investigate", "type": "investigate", "prompt": "Search the desk."}
    )


def test_ctir_noncombat_from_resolve_perception() -> None:
    scene = {"scene": {"id": "s1", "location": "Yard", "visible_facts": [], "discoverable_clues": [], "hidden_facts": []}}
    res = resolve_noncombat_action(scene, {}, {}, _normalized_observe_action(), raw_player_text="Look around.")
    c = ctir.build_ctir(
        turn_id=1,
        scene_id="s1",
        player_input="Look around.",
        builder_source="tests.nc.perception",
        resolution=res,
    )
    nc = c["noncombat"]
    assert nc.get("kind") == "perception"
    assert nc.get("subkind") == "observe"
    assert nc.get("framework_version") == NONCOMBAT_FRAMEWORK_VERSION
    assert nc.get("outcome_type") == "closed"
    assert c["resolution"].get("outcome_type") == "closed"
    assert "social" not in c["resolution"]


def test_ctir_noncombat_from_resolve_investigation() -> None:
    scene = {"scene": {"id": "s2", "location": "Hall", "visible_facts": [], "discoverable_clues": [], "hidden_facts": []}}
    res = resolve_noncombat_action(scene, {}, {}, _normalized_investigate_action(), raw_player_text="Search the desk.")
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s2",
        player_input="Search the desk.",
        builder_source="tests.nc.investigation",
        resolution=res,
    )
    assert c["noncombat"].get("kind") == "investigation"
    assert c["noncombat"].get("subkind") == "investigate"


def test_ctir_noncombat_social_probe_contract() -> None:
    scene = {"scene": {"id": "s3", "location": "Gate", "visible_facts": [], "discoverable_clues": [], "hidden_facts": []}}
    session = {
        "active_interaction_target_id": "npc_guard",
        "interaction_context": {"interaction_mode": "social", "active_interaction_kind": "question"},
    }
    # ``normalize_scene_action`` maps declarative ``question`` into ``custom``; use engine-shaped action.
    action = {"id": "q1", "label": "Ask", "type": "question", "prompt": "Who is in charge?"}
    res = resolve_noncombat_action(
        scene,
        session,
        {},
        action,
        raw_player_text="Who is in charge?",
        explicit_route="social",
    )
    c = ctir.build_ctir(
        turn_id=3,
        scene_id="s3",
        player_input="Who is in charge?",
        builder_source="tests.nc.social",
        resolution=res,
    )
    ncb = c["noncombat"]
    assert ncb.get("kind") == "social_probe"
    assert ncb.get("subkind") == "question"
    narr = ncb.get("narration_constraints") or {}
    assert isinstance(narr, dict)


def test_ctir_preserves_pending_check_from_contract() -> None:
    raw = {
        "kind": "observe",
        "requires_check": True,
        "check_request": {"requires_check": True, "reason": "engine_pending_check"},
    }
    cls = classify_noncombat_kind({"type": "observe", "id": "p1"})
    ncr = normalize_noncombat_resolution(raw, cls, route="exploration", source_engine="test")
    assert ncr["outcome_type"] == "pending_check"
    c = ctir.build_ctir(
        turn_id=4,
        scene_id="z",
        player_input="peer",
        builder_source="tests.nc.pending",
        resolution={**raw, "noncombat_resolution": ncr},
    )
    assert c["noncombat"]["outcome_type"] == "pending_check"
    assert c["noncombat"]["requires_check"] is True
    assert isinstance(c["noncombat"].get("check_request"), dict)
    assert c["resolution"]["requires_check"] is True
    assert c["resolution"]["outcome_type"] == "pending_check"


def test_ctir_reason_codes_lists() -> None:
    cls = classify_noncombat_kind({"type": "not_a_real_engine_type", "id": "z"})
    ncr = normalize_noncombat_resolution({}, cls, route="none", source_engine="noncombat_router")
    c = ctir.build_ctir(
        turn_id=5,
        scene_id=None,
        player_input="?",
        builder_source="tests.nc.codes",
        resolution={"kind": "none", "noncombat_resolution": ncr},
    )
    rc = c["noncombat"]["reason_codes"]
    assert "unknown_action_type_for_noncombat" in rc["ambiguous"]
    assert c["noncombat"]["outcome_type"] == "ambiguous"


def test_ctir_unsupported_downtime_contract() -> None:
    raw = {"kind": "downtime", "action_id": "d1"}
    wrapped = attach_noncombat_contract(raw, {"type": "downtime", "id": "d1"})
    c = ctir.build_ctir(
        turn_id=6,
        scene_id="camp",
        player_input="I make camp.",
        builder_source="tests.nc.downtime",
        resolution=wrapped,
    )
    assert c["noncombat"]["kind"] == "downtime"
    assert "downtime_engine_not_wired" in (c["noncombat"].get("reason_codes") or {}).get("unsupported", [])
    assert c["noncombat"]["outcome_type"] == "unsupported"


def test_precedence_noncombat_over_raw_resolution_fields() -> None:
    cls = classify_noncombat_kind({"type": "observe", "id": "o"})
    ncr = normalize_noncombat_resolution(
        {"kind": "observe", "success": True, "requires_check": False},
        cls,
        route="exploration",
        source_engine="test",
    )
    ncr["outcome_type"] = "ambiguous"
    ncr["ambiguous_reason_codes"] = list(ncr.get("ambiguous_reason_codes") or []) + ["synthetic_test_ambiguous"]
    resolution = {
        "kind": "observe",
        "success": True,
        "outcome_type": "closed",
        "noncombat_resolution": ncr,
        "social": {"npc_reply_expected": True, "reply_kind": "answer"},
    }
    c = ctir.build_ctir(
        turn_id=7,
        scene_id="x",
        player_input="look",
        builder_source="tests.nc.precedence",
        resolution=resolution,
    )
    assert c["resolution"]["outcome_type"] == "ambiguous"
    assert "social" not in c["resolution"]
    assert "synthetic_test_ambiguous" in c["noncombat"]["reason_codes"]["ambiguous"]


def test_legacy_transitional_fallback_is_empty_without_contract() -> None:
    c = ctir.build_ctir(
        turn_id=8,
        scene_id="y",
        player_input="act",
        builder_source="tests.nc.legacy",
        resolution={"kind": "observe", "social": {"npc_reply_expected": True}},
    )
    assert c["noncombat"] == {}
    assert isinstance(c["resolution"].get("social"), dict)


def test_runtime_ctir_passes_through_noncombat_resolution() -> None:
    cls = classify_noncombat_kind({"type": "observe", "id": "ro"})
    ncr = normalize_noncombat_resolution(
        {"kind": "observe", "success": None, "requires_check": False},
        cls,
        route="exploration",
        source_engine="game.exploration",
    )
    c = build_runtime_ctir_for_narration(
        turn_id=10,
        scene_id="rs",
        player_input="watch",
        builder_source="tests.nc.runtime",
        resolution={"kind": "observe", "noncombat_resolution": ncr},
        normalized_action={"type": "observe", "labels": ["investigation"]},
        combat=None,
        session={"active_scene_id": "rs", "interaction_context": {}},
    )
    assert c["noncombat"]["kind"] == "perception"
    assert c["noncombat"]["framework_version"] == NONCOMBAT_FRAMEWORK_VERSION


def test_prompt_semantics_merges_narration_constraints_from_noncombat() -> None:
    cls = classify_noncombat_kind({"type": "question", "id": "q"})
    raw = {
        "kind": "question",
        "social": {"target_resolved": True, "npc_id": "npc_a", "npc_reply_expected": True, "reply_kind": "answer"},
    }
    ncr = normalize_noncombat_resolution(raw, cls, route="social", source_engine="game.social")
    c = ctir.build_ctir(
        turn_id=11,
        scene_id="hall",
        player_input="Why?",
        builder_source="tests.nc.sem",
        resolution={**raw, "noncombat_resolution": ncr},
    )
    sem = _ctir_to_prompt_semantics(c)
    soc = sem["resolution"].get("social") or {}
    assert soc.get("npc_reply_expected") is True
    assert soc.get("reply_kind") == "answer"
    assert isinstance(sem.get("noncombat"), dict)
    assert sem["noncombat"].get("kind") == "social_probe"
