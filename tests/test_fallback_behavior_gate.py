"""Downstream gate application coverage for shipped fallback-behavior contracts.

Direct ``game.final_emission_repairs`` helper semantics live in
``tests/test_final_emission_repairs.py``. This file keeps gate ordering, application,
and emitted-metadata behavior focused on downstream orchestration.
"""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg
import game.final_emission_repairs as fer
from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.storage import get_scene_runtime


pytestmark = pytest.mark.unit
_FORBIDDEN_META_BITS = (
    "unclear",
    "not settled",
    "move plays out",
    "move resolves",
    "unresolved",
    "insufficient",
    "information",
    "system",
)


def _fallback_contract(**overrides: object) -> dict:
    contract = {
        "enabled": True,
        "uncertainty_active": True,
        "uncertainty_sources": ["unknown_identity"],
        "uncertainty_mode": "scene_ambiguity",
        "allowed_behaviors": {
            "ask_clarifying_question": True,
            "hedge_appropriately": True,
            "provide_partial_information": True,
        },
        "disallowed_behaviors": {
            "invented_certainty": True,
            "fabricated_authority": True,
            "meta_system_explanations": True,
        },
        "diegetic_only": True,
        "max_clarifying_questions": 1,
        "prefer_partial_over_question": True,
        "require_partial_to_state_known_edge": True,
        "require_partial_to_state_unknown_edge": True,
        "require_partial_to_offer_next_lead": True,
        "allowed_hedge_forms": [
            "I can't swear to it, but",
            "From what I saw,",
            "As far as rumor goes,",
            "Looks like",
            "Hard to tell, but",
        ],
        "forbidden_hedge_forms": [
            "I lack enough information to answer confidently.",
            "The system cannot confirm that.",
            "Canon proves it.",
            "As an AI, I don't know.",
            "There is insufficient context available.",
        ],
        "allowed_authority_bases": [
            "direct_observation",
            "established_report",
            "rumor_marked_as_rumor",
            "visible_evidence",
        ],
        "forbidden_authority_bases": [
            "unsupported_named_culprit",
            "unsupported_exact_location",
            "unsupported_motive_as_fact",
            "unsupported_procedural_certainty",
            "system_or_canon_claims",
        ],
        "debug": {},
    }
    contract.update(overrides)
    return contract


def _response_type_contract(required: str = "answer") -> dict:
    return {
        "required_response_type": required,
        "action_must_preserve_agency": required == "action_outcome",
    }


def _answer_contract(**overrides: object) -> dict:
    contract = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": False,
        "player_direct_question": True,
        "expected_voice": "narrator",
        "expected_answer_shape": "bounded_partial",
        "allowed_partial_reasons": ["uncertainty", "lack_of_knowledge", "gated_information"],
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["place", "name", "next_lead"],
        "trace": {},
    }
    contract.update(overrides)
    return contract


def _strict_social_bundle() -> tuple[dict, dict, str, dict]:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": sid,
            "topics": [{"id": "lanes", "text": "East lanes.", "clue_id": "east_lanes"}],
        }
    ]
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    set_social_target(session, "runner")
    rebuild_active_scene_entities(session, world, sid)
    interaction_context = dict(session.get("interaction_context") or {})
    interaction_context["engagement_level"] = "engaged"
    session["interaction_context"] = interaction_context
    runtime = get_scene_runtime(session, sid)
    runtime["last_player_action_text"] = "No. Exactly who?"
    resolution = {
        "kind": "question",
        "prompt": "No. Exactly who?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Tavern Runner",
        },
    }
    return session, world, sid, resolution


def _assert_no_meta_bits(text: str) -> None:
    low = text.lower()
    for bit in _FORBIDDEN_META_BITS:
        assert bit not in low


def test_gate_repairs_meta_fallback_voice_into_bounded_partial() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
            "tags": [],
            "response_policy": {"fallback_behavior": _fallback_contract()},
        },
        resolution={"kind": "adjudication_query", "prompt": "Who did it?"},
        session=None,
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    meta = out.get("_final_emission_meta") or {}
    emission_debug = ((out.get("metadata") or {}).get("emission_debug") or {}).get("fallback_behavior") or {}

    assert "enough information" not in low
    assert "ward clerk" in low
    assert "hearsay" in low or "unclear" in low or "no name" in low
    assert meta.get("fallback_behavior_repaired") is True
    assert meta.get("fallback_behavior_meta_voice_stripped") is True
    assert meta.get("fallback_behavior_partial_used") is True
    assert "strip_meta_voice" in str(meta.get("fallback_behavior_repair_mode") or "")
    assert meta.get("fallback_behavior_failed") is False
    assert emission_debug.get("validation", {}).get("checked") is True
    assert emission_debug.get("validation", {}).get("passed") is True
    assert emission_debug.get("repair_mode") == meta.get("fallback_behavior_repair_mode")


def test_gate_skips_fallback_behavior_when_uncertainty_inactive() -> None:
    raw = "Rain tracks down the gatehouse stone."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "response_policy": {"fallback_behavior": _fallback_contract(uncertainty_active=False)},
        },
        resolution={"kind": "observe", "prompt": "I look at the gatehouse."},
        session=None,
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    meta = out.get("_final_emission_meta") or {}
    emission_debug = ((out.get("metadata") or {}).get("emission_debug") or {}).get("fallback_behavior") or {}
    assert out.get("player_facing_text") == raw
    assert meta.get("fallback_behavior_checked") is False
    assert meta.get("fallback_behavior_skip_reason") == "uncertainty_inactive"
    assert meta.get("fallback_behavior_repaired") is False
    assert meta.get("fallback_behavior_uncertainty_active") is False
    assert emission_debug.get("validation", {}).get("checked") is False
    assert emission_debug.get("validation", {}).get("passed") is True
    assert emission_debug.get("skip_reason") == "uncertainty_inactive"


def test_gate_runs_fallback_behavior_after_interaction_continuity_non_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    orig_ic = feg._apply_interaction_continuity_emission_step
    orig_fb = feg._apply_fallback_behavior_layer

    def wrap_ic(*args, **kwargs):
        order.append("interaction_continuity")
        return orig_ic(*args, **kwargs)

    def wrap_fb(*args, **kwargs):
        order.append("fallback_behavior")
        return orig_fb(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_interaction_continuity_emission_step", wrap_ic)
    monkeypatch.setattr(feg, "_apply_fallback_behavior_layer", wrap_fb)

    apply_final_emission_gate(
        {
            "player_facing_text": "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
            "tags": [],
            "response_policy": {"fallback_behavior": _fallback_contract()},
        },
        resolution={"kind": "adjudication_query", "prompt": "No. Exactly who?"},
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    assert order.index("interaction_continuity") < order.index("fallback_behavior")


def test_gate_runs_fallback_behavior_after_strict_social_continuity(monkeypatch: pytest.MonkeyPatch) -> None:
    session, world, sid, resolution = _strict_social_bundle()
    order: list[str] = []
    orig_ic = feg._apply_interaction_continuity_emission_step
    orig_fb = feg._apply_fallback_behavior_layer

    def wrap_ic(*args, **kwargs):
        order.append("interaction_continuity")
        return orig_ic(*args, **kwargs)

    def wrap_fb(*args, **kwargs):
        order.append("fallback_behavior")
        return orig_fb(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_interaction_continuity_emission_step", wrap_ic)
    monkeypatch.setattr(feg, "_apply_fallback_behavior_layer", wrap_fb)

    stub_details = {
        "used_internal_fallback": False,
        "final_emitted_source": "test_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }

    def fake_build(candidate_text: str, *, resolution: dict, tags: list[str], session: dict, scene_id: str, world: dict):
        _ = candidate_text, resolution, tags, session, scene_id, world
        return (
            "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
            dict(stub_details),
        )

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {
            "player_facing_text": "No names yet.",
            "tags": [],
            "response_policy": {
                "fallback_behavior": _fallback_contract(),
                "response_type_contract": _response_type_contract("dialogue"),
            },
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    meta = out.get("_final_emission_meta") or {}
    assert order.index("interaction_continuity") < order.index("fallback_behavior")
    assert "enough information" not in str(out.get("player_facing_text") or "").lower()
    assert meta.get("fallback_behavior_repaired") is True
    assert meta.get("final_emitted_source") == meta.get("fallback_behavior_repair_mode")


@pytest.mark.parametrize(
    ("source", "prompt", "raw", "forbidden"),
    [
        pytest.param(
            "unknown_identity",
            "No. Exactly who?",
            "The culprit was Captain Verrick at the gate. Check the ward clerk at the east gate office.",
            "culprit was",
            marks=pytest.mark.xfail(reason="current identity repair still preserves unsupported named culprit text"),
        ),
        (
            "unknown_location",
            "Which dock exactly?",
            "They are under Dock Seven by the customs gate. Check the harbor watch by the customs arch.",
            "dock seven",
        ),
        (
            "unknown_quantity",
            "How many were there?",
            "There were exactly 5 guards at the gate. Ask the watch captain for the tally sheet.",
            "exactly 5",
        ),
        (
            "unknown_feasibility",
            "Can I safely bribe the guard?",
            "It is safe to bribe the guard at the gate. Check the patrol map at the watchhouse.",
            "it is safe",
        ),
    ],
)
def test_gate_repairs_adversarial_uncertainty_followups_without_fabricating_certainty(
    source: str,
    prompt: str,
    raw: str,
    forbidden: str,
) -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "response_policy": {
                "response_type_contract": _response_type_contract("answer"),
                "fallback_behavior": _fallback_contract(uncertainty_sources=[source]),
            },
        },
        resolution={"kind": "adjudication_query", "prompt": prompt},
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    meta = out.get("_final_emission_meta") or {}

    assert forbidden not in low
    _assert_no_meta_bits(text)
    assert text.strip()
    assert meta.get("fallback_behavior_repaired") is True


def test_gate_rewrites_runner_copper_meta_leak_into_diegetic_partial() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The reason is still unclear.",
            "tags": [],
            "response_policy": {
                "fallback_behavior": _fallback_contract(
                    uncertainty_sources=["unknown_motive"],
                    require_partial_to_state_known_edge=False,
                    require_partial_to_offer_next_lead=False,
                )
            },
        },
        resolution={
            "kind": "question",
            "prompt": "I offer the tavern runner a copper for the story.",
            "social": {
                "npc_id": "runner",
                "npc_name": "The Tavern Runner",
                "social_intent_class": "social_exchange",
            },
        },
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    assert (
        "eyes the copper" in low
        or "does not answer at once" in low
        or "guarded look" in low
        or "starts to answer" in low
    )
    _assert_no_meta_bits(text)


def test_gate_rewrites_open_call_move_plays_out_meta_leak_into_diegetic_partial() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "That is not settled until the move plays out.",
            "tags": [],
            "response_policy": {
                "fallback_behavior": _fallback_contract(
                    uncertainty_sources=["unknown_feasibility"],
                    require_partial_to_state_known_edge=False,
                    require_partial_to_offer_next_lead=False,
                )
            },
        },
        resolution={
            "kind": "question",
            "prompt": "Anyone willing to talk if I toss a copper into the crowd?",
            "social": {
                "social_intent_class": "open_call",
            },
        },
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    meta = out.get("_final_emission_meta") or {}

    assert ("no one answers at once" in low or "glance over" in low or "heads turn toward the copper" in low)
    _assert_no_meta_bits(text)
    assert meta.get("fallback_behavior_repaired") is True


def test_gate_smooths_repaired_repeated_subject_social_line(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_ensure_known_unknown_shape(*args, **kwargs):
        _ = args, kwargs
        return (
            "Tavern Runner nods once. Tavern Runner does not answer at once.",
            {"fallback_behavior_unknown_edge_added": True},
        )

    monkeypatch.setattr(fer, "_ensure_known_unknown_shape", fake_ensure_known_unknown_shape)

    out = apply_final_emission_gate(
        {
            "player_facing_text": "The reason is still unclear.",
            "tags": [],
            "response_policy": {
                "fallback_behavior": _fallback_contract(
                    uncertainty_sources=["unknown_feasibility"],
                    require_partial_to_state_known_edge=False,
                    require_partial_to_offer_next_lead=False,
                )
            },
        },
        resolution={
            "kind": "question",
            "prompt": "I press the tavern runner for a straight answer.",
            "social": {
                "npc_id": "runner",
                "npc_name": "Tavern Runner",
                "social_intent_class": "social_exchange",
            },
        },
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    meta = out.get("_final_emission_meta") or {}

    assert "system" not in low
    assert "unclear" not in low
    assert "tavern runner nods once. tavern runner" not in low
    assert "does not answer at once" in low
    assert meta.get("fallback_behavior_repaired") is True
    assert meta.get("fallback_behavior_failed") is False
