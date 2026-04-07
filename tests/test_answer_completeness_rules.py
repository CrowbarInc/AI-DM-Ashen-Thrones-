"""Focused tests for answer-completeness contract derivation and gate behavior.

Complements tests/test_social_exchange_emission.py without duplicating question-first,
front-load repair, or inspect_* meta cases already covered there.
"""
from __future__ import annotations

import pytest

from game.defaults import default_session, default_world
from game.final_emission_gate import (
    _apply_answer_completeness_layer,
    apply_final_emission_gate,
    validate_answer_completeness,
)
from game.narration_visibility import validate_player_facing_referential_clarity
from game.prompt_context import (
    ANSWER_COMPLETENESS_PARTIAL_REASONS,
    build_answer_completeness_contract,
    question_detected_from_player_text,
)

pytestmark = pytest.mark.unit


def _obligations_explore_no_npc() -> dict:
    return {
        "suppress_non_social_emitters": False,
        "should_answer_active_npc": False,
        "active_npc_reply_expected": False,
        "active_npc_reply_kind": None,
    }


def _obligations_social_answer(active_reply_expected: bool = True) -> dict:
    return {
        "suppress_non_social_emitters": True,
        "should_answer_active_npc": True,
        "active_npc_reply_expected": active_reply_expected,
        "active_npc_reply_kind": "answer",
    }


def test_question_detected_from_player_text_direct_question():
    assert question_detected_from_player_text("Where did they go?") is True
    assert question_detected_from_player_text("I head toward the gate.") is False


def test_build_answer_contract_player_question_sets_trace_and_player_direct_question():
    c = build_answer_completeness_contract(
        player_input="Who took the ledger?",
        narration_obligations=_obligations_explore_no_npc(),
        resolution=None,
        session_view={},
        uncertainty_hint=None,
    )
    assert c["player_direct_question"] is True
    assert c["answer_required"] is True
    tr = c["trace"]
    assert tr["trigger_source"] == "player_direct_question"
    assert tr["question_detected_from_player_text"] is True
    assert tr["active_target_id"] is None
    assert tr["active_npc_reply_kind"] is None
    assert "partial_answer_permitted" in tr


def test_build_answer_contract_active_target_and_question_expects_npc_voice():
    c = build_answer_completeness_contract(
        player_input="Runner, which way?",
        narration_obligations=_obligations_social_answer(),
        resolution=None,
        session_view={"active_interaction_target_id": "tavern_runner"},
        uncertainty_hint=None,
    )
    assert c["expected_voice"] == "npc"
    assert c["trace"]["active_target_id"] == "tavern_runner"
    assert c["trace"]["active_npc_reply_kind"] == "answer"


def test_build_answer_contract_action_turn_answer_not_required():
    c = build_answer_completeness_contract(
        player_input="I drag the crate aside and search the straw.",
        narration_obligations=_obligations_explore_no_npc(),
        resolution=None,
        session_view={},
        uncertainty_hint=None,
    )
    assert c["answer_required"] is False
    assert c["enabled"] is False
    assert c["expected_voice"] == "either"


def test_build_answer_allowed_partial_reasons_only_grounded_buckets():
    direct = build_answer_completeness_contract(
        player_input="What happened?",
        narration_obligations=_obligations_explore_no_npc(),
        resolution=None,
        session_view={},
        uncertainty_hint=None,
    )
    assert direct["allowed_partial_reasons"] == list(ANSWER_COMPLETENESS_PARTIAL_REASONS)

    refusal = build_answer_completeness_contract(
        player_input="Tell me the name.",
        narration_obligations={
            **_obligations_social_answer(),
            "active_npc_reply_kind": "refusal",
        },
        resolution=None,
        session_view={"active_interaction_target_id": "tavern_runner"},
        uncertainty_hint=None,
    )
    assert refusal["allowed_partial_reasons"] == []
    allowed_set = set(direct["allowed_partial_reasons"])
    assert allowed_set.issubset(set(ANSWER_COMPLETENESS_PARTIAL_REASONS))


def test_gate_skips_answer_completeness_when_contract_disabled(action_turn_contract):
    """Descriptive / action-only narration must not be front-loaded by answer completeness."""
    raw = "Rain beads on the checkpoint timbers while the line holds still."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"answer_completeness": action_turn_contract}},
        resolution={"kind": "investigate", "prompt": "I study the crowd."},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert out["player_facing_text"] == raw
    assert meta.get("answer_completeness_checked") is False
    assert meta.get("answer_completeness_repaired") is False


@pytest.fixture
def action_turn_contract():
    return build_answer_completeness_contract(
        player_input="I study the crowd.",
        narration_obligations=_obligations_explore_no_npc(),
        resolution={"kind": "investigate", "prompt": "I study the crowd."},
        session_view={},
        uncertainty_hint=None,
    )


def test_gate_neutral_narration_not_mutated_when_no_player_question_contract():
    raw = "Torchlight frays in the drizzle; hoofbeats fade toward the east road."
    contract = build_answer_completeness_contract(
        player_input="",
        narration_obligations=_obligations_explore_no_npc(),
        resolution=None,
        session_view={},
        uncertainty_hint=None,
    )
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"answer_completeness": contract}},
        resolution=None,
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    assert out["player_facing_text"] == raw
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_completeness_repaired") is not True


def test_frontload_repair_keeps_referential_clarity_explicit_npc_in_opening():
    """Substantive sentence with explicit entity should lead after repair."""
    contract = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": True,
        "player_direct_question": True,
        "expected_voice": "npc",
        "expected_answer_shape": "direct",
        "allowed_partial_reasons": list(ANSWER_COMPLETENESS_PARTIAL_REASONS),
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["place", "direction", "name"],
        "trace": {},
    }
    # adjudication_query avoids strict-social replacement so answer-completeness repair is testable in isolation.
    resolution = {
        "kind": "adjudication_query",
        "prompt": "Which way did they go?",
    }
    raw = (
        "The square holds its breath for a moment. "
        'The runner jerks a thumb toward the treeline. "East road, past the old mill."'
    )
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"answer_completeness": contract}},
        resolution=resolution,
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_completeness_repaired") is True
    low = out["player_facing_text"].lower()
    east_at = low.find("east")
    breath_at = low.find("holds its breath")
    assert east_at != -1 and (breath_at == -1 or east_at < breath_at)
    assert meta.get("answer_completeness_expected_voice") == "npc"
    session = default_session()
    world = default_world()
    scene = {"scene": {"id": "frontier_gate", "location": "gate", "visible_facts": []}}
    ref = validate_player_facing_referential_clarity(
        out["player_facing_text"], session=session, scene=scene, world=world
    )
    assert ref.get("ok") is not False


def test_mixed_player_turn_question_plus_action_still_frontloads_answer():
    contract = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": True,
        "player_direct_question": True,
        "expected_voice": "narrator",
        "expected_answer_shape": "direct",
        "allowed_partial_reasons": list(ANSWER_COMPLETENESS_PARTIAL_REASONS),
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["place", "direction"],
        "trace": {},
    }
    # Avoid place tokens (e.g. pier) in the opening sentence so it cannot pass as a fake "direct" answer.
    raw = (
        "Fog thickens over the water. "
        "The runners used the east lane toward the warehouse district."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"answer_completeness": contract}},
        resolution={
            "kind": "adjudication_query",
            "prompt": "Where did they run? I scan the docks for witnesses.",
        },
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    low = out["player_facing_text"].lower()
    run_at = low.find("the runners used")
    fog_at = low.find("fog thickens")
    assert run_at != -1 and fog_at != -1 and run_at < fog_at
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_completeness_repaired") is True


def test_authoritative_refusal_stays_substantive_after_repair():
    contract = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": True,
        "player_direct_question": True,
        "expected_voice": "npc",
        "expected_answer_shape": "refusal_with_reason",
        "allowed_partial_reasons": [],
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["condition", "next_lead"],
        "trace": {},
    }
    resolution = {
        "kind": "adjudication_query",
        "prompt": "Who signed the arrest warrant?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "clerk",
            "npc_name": "Clerk",
            "gated_information": True,
            "information_gate": "captain's orders",
        },
    }
    raw = (
        "The clerk studies your face for a beat. "
        '"I can\'t say here - the captain has not released that thread. '
        'Check with the ward sergeant at the barracks door."'
    )
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"answer_completeness": contract}},
        resolution=resolution,
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    opening = out["player_facing_text"].split(". ")[0]
    assert "?" not in opening[:40]
    low = out["player_facing_text"].lower()
    assert ("won't" in low or "can't" in low or "not" in low) and ("captain" in low or "sergeant" in low or "barracks" in low)


def test_transcript_style_dodge_opening_repaired_with_meta_flags():
    contract = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": True,
        "player_direct_question": True,
        "expected_voice": "narrator",
        "expected_answer_shape": "direct",
        "allowed_partial_reasons": list(ANSWER_COMPLETENESS_PARTIAL_REASONS),
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["direction", "place"],
        "trace": {},
    }
    candidate = (
        "Why do you ask that now? The east road past the old gate is watched - but say why you care."
    )
    assert validate_answer_completeness(candidate, contract, resolution=None).get("passed") is False

    out = apply_final_emission_gate(
        {"player_facing_text": candidate, "tags": [], "response_policy": {"answer_completeness": contract}},
        resolution={"kind": "question", "prompt": "Which route is watched?"},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_completeness_checked") is True
    assert meta.get("answer_completeness_repaired") is True
    first = out["player_facing_text"].split(". ")[0].lower()
    assert "east" in first or "road" in first or "gate" in first
    assert not first.strip().startswith("why do you ask")


def test_strict_social_path_preserves_npc_voice_after_answer_completeness_repair():
    """Strict-social post-process layer: frontload repair keeps NPC dialogue first (expected_voice npc)."""
    contract = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": True,
        "player_direct_question": True,
        "expected_voice": "npc",
        "expected_answer_shape": "direct",
        "allowed_partial_reasons": list(ANSWER_COMPLETENESS_PARTIAL_REASONS),
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["direction", "place"],
        "trace": {},
    }
    gm = {"response_policy": {"answer_completeness": contract}}
    text = 'Mist hangs over the wet stones. Tavern runner says, "East road past the fold."'
    resolution = {
        "kind": "question",
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
    }
    repaired, meta, extra = _apply_answer_completeness_layer(
        text,
        gm_output=gm,
        resolution=resolution,
        strict_social_details={
            "used_internal_fallback": False,
            "final_emitted_source": "normalized_social_candidate",
        },
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=True,
    )
    assert not extra
    assert meta.get("answer_completeness_repaired") is True
    assert meta.get("answer_completeness_expected_voice") == "npc"
    low = repaired.lower()
    assert low.startswith("tavern runner says") or '"' in repaired
    assert "east" in low
