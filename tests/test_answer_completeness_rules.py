"""Downstream tests for shipped answer-completeness and response-delta behavior.

Direct prompt-bundle ownership stays in ``tests/test_prompt_context.py``. This
module exercises how shipped contracts drive answer-pressure derivation, social
escalation eligibility, and final-emission gate behavior.
"""
from __future__ import annotations

import importlib

import pytest

from game.defaults import default_session, default_world
from game.final_emission_gate import (
    _apply_answer_completeness_layer,
    apply_final_emission_gate,
    apply_spoken_state_refinement_cash_out,
    validate_answer_completeness,
)
from game.narration_visibility import validate_player_facing_referential_clarity
from game.social import determine_social_escalation_outcome
from tests.test_social_escalation import _session_with_pressure

_prompt_contracts = importlib.import_module("game.prompt_context")
# Consume shipped contracts through a local module handle so this suite reads as
# a downstream consumer of prompt-derived policy, not as a prompt-owner home.
ANSWER_COMPLETENESS_PARTIAL_REASONS = _prompt_contracts.ANSWER_COMPLETENESS_PARTIAL_REASONS
_answer_pressure_followup_details = _prompt_contracts._answer_pressure_followup_details
build_answer_completeness_contract = _prompt_contracts.build_answer_completeness_contract
build_response_delta_contract = _prompt_contracts.build_response_delta_contract
question_detected_from_player_text = _prompt_contracts.question_detected_from_player_text

pytestmark = pytest.mark.unit


# feature: emission, social, fallback
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


def test_answer_completeness_question_detector_flags_direct_questions():
    assert question_detected_from_player_text("Where did they go?") is True
    assert question_detected_from_player_text("I head toward the gate.") is False


def test_answer_completeness_contract_tracks_player_direct_question_trace():
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


def test_answer_completeness_contract_prefers_npc_voice_for_active_target_questions():
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


def test_answer_completeness_contract_disables_action_only_turns():
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


def _recent_log_vague_npc_answer() -> list[dict]:
    return [
        {
            "player_input": "What do you know about the seal?",
            "gm_snippet": (
                "The runner shrugs. Hard to say—there are rumors, but nothing you can hang a warrant on."
            ),
        }
    ]


def test_strict_social_answer_pressure_sets_answer_contract_and_trace():
    log = _recent_log_vague_npc_answer()
    c = build_answer_completeness_contract(
        player_input="Stop dodging. Be specific about the seal.",
        narration_obligations=_obligations_social_answer(),
        resolution=None,
        session_view={"active_interaction_target_id": "tavern_runner"},
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    assert c["answer_required"] is True
    assert c["trace"]["trigger_source"] == "answer_pressure_followup"
    assert c["trace"]["answer_pressure_followup_detected"] is True
    assert c["trace"]["strict_social_answer_seek_override"] is True


def test_strict_social_response_delta_contract_not_suppressed_when_answer_pressure():
    log = _recent_log_vague_npc_answer()
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "tavern_runner"}
    ac = build_answer_completeness_contract(
        player_input="Stop dodging. Be specific about the seal.",
        narration_obligations=obligations,
        resolution=None,
        session_view=session_view,
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    rd = build_response_delta_contract(
        player_input="Stop dodging. Be specific about the seal.",
        recent_log_compact=log,
        narration_obligations=obligations,
        resolution=None,
        answer_completeness=ac,
        session_view=session_view,
    )
    assert rd["enabled"] is True
    assert rd["trace"]["strict_social_answer_seek_override"] is True
    assert "social_lock" not in rd["trace"]["suppressed_because"]


def test_strict_social_non_answer_seeking_turn_still_suppresses_response_delta():
    log = _recent_log_vague_npc_answer()
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "tavern_runner"}
    ac = build_answer_completeness_contract(
        player_input="I nod and study the gate timbers while the crowd shuffles.",
        narration_obligations=obligations,
        resolution=None,
        session_view=session_view,
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    rd = build_response_delta_contract(
        player_input="I nod and study the gate timbers while the crowd shuffles.",
        recent_log_compact=log,
        narration_obligations=obligations,
        resolution=None,
        answer_completeness=ac,
        session_view=session_view,
    )
    assert rd["enabled"] is False
    assert "social_lock" in rd["trace"]["suppressed_because"]


def test_answer_pressure_contradiction_challenge_why_tensions():
    """Inability/challenge + embedded why + lexical anchor to prior GM (Block 1 families)."""
    log = [
        {
            "player_input": "What's happening at the gate?",
            "gm_snippet": (
                "The guard keeps his tone flat. Tensions are up—more patrols, shorter tempers—but "
                "he won't spell out causes with this crowd listening."
            ),
        }
    ]
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "gate_guard"}
    line = "You can't tell me why tensions are rising?"
    ac = build_answer_completeness_contract(
        player_input=line,
        narration_obligations=obligations,
        resolution=None,
        session_view=session_view,
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    assert ac["answer_required"] is True
    assert ac["trace"]["answer_pressure_followup_detected"] is True
    assert ac["trace"]["contradiction_followup_detected"] is True
    assert ac["trace"]["answer_pressure_family"] == "contradiction_or_refusal_challenge"
    rd = build_response_delta_contract(
        player_input=line,
        recent_log_compact=log,
        narration_obligations=obligations,
        resolution=None,
        answer_completeness=ac,
        session_view=session_view,
    )
    assert rd["enabled"] is True
    assert rd["trace"]["strict_social_answer_seek_override"] is True


def test_answer_pressure_short_why_after_guarded_prior():
    log = [
        {
            "player_input": "Who moved the wagons?",
            "gm_snippet": (
                'The clerk murmurs, "I can\'t point to a name—not without starting a fight in the yard."'
            ),
        }
    ]
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "clerk_npc"}
    ac = build_answer_completeness_contract(
        player_input="Why?",
        narration_obligations=obligations,
        resolution=None,
        session_view=session_view,
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    assert ac["trace"]["short_followup_anchor_detected"] is True
    assert ac["trace"]["answer_pressure_followup_detected"] is True


def test_bare_what_without_continuity_anchor_not_answer_pressure():
    log = [
        {
            "player_input": "Describe the granary layout.",
            "gm_snippet": (
                "Stone bins on the east, threshing floor west, hoist chain over the center—"
                "workers move in two shifts."
            ),
        }
    ]
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "foreman"}
    ac = build_answer_completeness_contract(
        player_input="What?",
        narration_obligations=obligations,
        resolution=None,
        session_view=session_view,
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    assert ac["trace"]["answer_pressure_followup_detected"] is not True


def test_clarification_of_recent_reference_eyes_on_you_whose_eyes():
    log = [
        {
            "player_input": "What should I worry about?",
            "gm_snippet": (
                "The runner doesn't smile. Too many eyes are on you in this yard—walk like you belong."
            ),
        }
    ]
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "yard_runner"}
    line = "Whose eyes?"
    ac = build_answer_completeness_contract(
        player_input=line,
        narration_obligations=obligations,
        resolution=None,
        session_view=session_view,
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    assert ac["trace"]["recent_reference_clarification_detected"] is True
    assert ac["trace"]["answer_pressure_family"] == "clarification_of_recent_reference"
    assert ac["trace"]["clarification_prompt_shape"] == "whose_eyes"
    assert "path:clarification_of_recent_reference" in ac["trace"]["answer_pressure_reasons"]
    rd = build_response_delta_contract(
        player_input=line,
        recent_log_compact=log,
        narration_obligations=obligations,
        resolution=None,
        answer_completeness=ac,
        session_view=session_view,
    )
    assert rd["enabled"] is True
    assert rd["trace"]["strict_social_answer_seek_override"] is True


def test_clarification_of_recent_reference_they_watching_who_bare():
    log = [
        {
            "player_input": "Are we safe here?",
            "gm_snippet": 'The clerk murmurs, "Not really—they\'re watching the side door."',
        }
    ]
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "clerk_npc"}
    line = "Who?"
    ac = build_answer_completeness_contract(
        player_input=line,
        narration_obligations=obligations,
        resolution=None,
        session_view=session_view,
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    assert ac["trace"]["recent_reference_clarification_detected"] is True
    assert ac["trace"]["answer_pressure_family"] == "clarification_of_recent_reference"
    assert ac["trace"]["clarification_prompt_shape"] == "who_bare"
    rd = build_response_delta_contract(
        player_input=line,
        recent_log_compact=log,
        narration_obligations=obligations,
        resolution=None,
        answer_completeness=ac,
        session_view=session_view,
    )
    assert rd["enabled"] is True


def test_clarification_recent_reference_isolated_who_without_prior_referent():
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "gate_guard"}
    ap = _answer_pressure_followup_details(
        player_input="Who?",
        recent_log_compact=[],
        narration_obligations=obligations,
        session_view=session_view,
        answer_completeness=None,
    )
    assert ap.get("recent_reference_clarification_detected") is not True
    assert ap.get("answer_pressure_family") != "clarification_of_recent_reference"


def test_clarification_recent_reference_generic_roles_insufficient_without_watch_cue():
    log = [
        {
            "player_input": "Who runs this post?",
            "gm_snippet": "The captain nods once. The guard shifts his weight but says nothing.",
        }
    ]
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "gate_captain"}
    ap = _answer_pressure_followup_details(
        player_input="Who?",
        recent_log_compact=log,
        narration_obligations=obligations,
        session_view=session_view,
        answer_completeness=None,
    )
    assert ap.get("recent_reference_clarification_detected") is not True


def test_answer_completeness_contract_uses_grounded_partial_reason_buckets():
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


def test_spoken_state_refinement_cash_out_appends_refinement_on_answer_pressure(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "lead_registry": {
            "lid_milestone": {
                "id": "lid_milestone",
                "title": "Investigate the old milestone",
                "summary": "",
            }
        }
    }
    resolution = {
        "kind": "question",
        "prompt": "Where was the patrol last seen?",
        "clue_id": "lid_milestone",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_milestone",
                "enforced_lead_source": "extracted_social",
            }
        },
    }
    gm = {
        "player_facing_text": "I can't name names.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out = apply_spoken_state_refinement_cash_out(
        gm,
        resolution=resolution,
        session=session,
        world={},
        scene_id="frontier_gate",
    )
    assert "milestone" in out["player_facing_text"].lower()
    assert out.get("_spoken_refinement_cash_out", {}).get("applied") is True


def test_spoken_state_refinement_cash_out_skips_when_already_spoken(monkeypatch):
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "clue_knowledge": {"lid_milestone": {"text": "near the old milestone"}},
        "lead_registry": {
            "lid_milestone": {"id": "lid_milestone", "title": "Investigate the old milestone"}
        },
    }
    resolution = {
        "kind": "question",
        "prompt": "Where?",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_milestone",
                "enforced_lead_source": "extracted_social",
            }
        },
    }
    text = 'They were last seen near the old milestone; I can say that much.'
    gm = {"player_facing_text": text, "tags": [], "response_policy": {"answer_completeness": ac}}
    out = apply_spoken_state_refinement_cash_out(
        gm,
        resolution=resolution,
        session=session,
        world={},
        scene_id="frontier_gate",
    )
    assert out["player_facing_text"] == text
    assert "_spoken_refinement_cash_out" not in out


def test_spoken_state_refinement_cash_out_default_source_minimum_actionable_lead(monkeypatch):
    """When ``enforced_lead_source`` is absent, debug uses ``minimum_actionable_lead`` bucket."""
    monkeypatch.setattr(
        "game.final_emission_gate.strict_social_emission_will_apply",
        lambda *a, **k: True,
    )
    ac = {
        "enabled": True,
        "answer_required": True,
        "trace": {"strict_social_answer_seek_override": True},
    }
    session = {
        "lead_registry": {
            "lid_default_src": {
                "id": "lid_default_src",
                "title": "Trace the eastern cistern line",
                "summary": "",
            }
        }
    }
    resolution = {
        "kind": "question",
        "prompt": "Anything on the eastern cistern line?",
        "clue_id": "lid_default_src",
        "metadata": {
            "minimum_actionable_lead": {
                "minimum_actionable_lead_enforced": True,
                "enforced_lead_id": "lid_default_src",
            }
        },
    }
    gm = {
        "player_facing_text": "Can't say.",
        "tags": [],
        "response_policy": {"answer_completeness": ac},
    }
    out = apply_spoken_state_refinement_cash_out(
        gm,
        resolution=resolution,
        session=session,
        world={},
        scene_id="frontier_gate",
    )
    assert "spoken_state_refinement_cash_out:minimum_actionable_lead" in (out.get("debug_notes") or "")
    cash = out.get("_spoken_refinement_cash_out") or {}
    assert cash.get("source") == "minimum_actionable_lead"
    assert "cistern" in str(cash.get("refinement_preview") or "").lower()


def _ap_details(player: str, compact: list, *, active_id: str = "tavern_runner") -> dict:
    return _answer_pressure_followup_details(
        player_input=player,
        recent_log_compact=compact,
        narration_obligations={},
        session_view={"active_interaction_target_id": active_id},
    )


def test_correction_reask_followup_after_redirect_clue_line():
    prior_gm = (
        'The runner taps two fingers on the bar. "Word is the seal-house is holding a quiet drop '
        'tonight—might be worth a glance if you like trouble."'
    )
    compact = [{"player_input": "Why is that?", "gm_snippet": prior_gm}]
    line = "What? I asked you why people here wouldn't be friendly to newcomers."
    ap = _ap_details(line, compact)
    assert ap["correction_reask_followup_detected"] is True
    assert ap["answer_pressure_followup_detected"] is True
    assert ap["answer_pressure_family"] == "correction_reask_followup"
    assert ap["answer_pressure_anchor_kind"] == "explicit_question_reassertion"
    assert "path:correction_reask_followup" in ap["answer_pressure_reasons"]


def test_correction_reask_no_i_asked_why_after_mismatch():
    prior_gm = (
        "She shrugs. If you want gossip, the east stall had a strange crate moved after dark—"
        "that's all I noticed."
    )
    compact = [{"player_input": "What makes you say that?", "gm_snippet": prior_gm}]
    ap = _ap_details("No, I asked why.", compact)
    assert ap["correction_reask_followup_detected"] is True
    assert ap["answer_pressure_family"] == "correction_reask_followup"


def test_correction_reask_did_not_answer_my_question():
    prior_gm = (
        "He grins. There's a dice game in the back if you're bored—buy-in's steep tonight."
    )
    compact = [{"player_input": "Should I worry about the road north?", "gm_snippet": prior_gm}]
    ap = _ap_details("That didn't answer my question.", compact)
    assert ap["correction_reask_followup_detected"] is True
    assert ap["answer_pressure_followup_detected"] is True


def test_correction_reask_not_fired_for_bare_what_without_prior_exchange():
    ap = _ap_details("What?", [])
    assert ap["correction_reask_followup_detected"] is False
    ap2 = _ap_details(
        "What?",
        [{"player_input": "Hello.", "gm_snippet": "Evening—what'll it be?"}],
    )
    assert ap2["correction_reask_followup_detected"] is False


def test_correction_reask_social_escalation_explicit_reassertion_not_first_attempt():
    prior_gm = (
        'Runner leans in. "If you want something juicy, ask about the cellar key—they say it moved hands."'
    )
    compact = [{"player_input": "Why wouldn't people be friendly to strangers?", "gm_snippet": prior_gm}]
    line = "What? I asked you why people here wouldn't be friendly to newcomers."
    ap = _ap_details(line, compact)
    session = _session_with_pressure("scene_tavern", "tavern_gossip", "tavern_runner", 1)
    out = determine_social_escalation_outcome(
        session=session,
        scene_id="scene_tavern",
        npc_id="tavern_runner",
        topic_key="tavern_gossip",
        reply_kind="answer",
        progress_signals={"npc_knowledge_exhausted": False},
        player_text=line,
        answer_pressure_details=ap,
    )
    assert out["valid_followup_detected"] is True
    assert out["prior_same_dimension_answer_exists"] is True
    assert out["escalation_reason"] == "explicit_question_reassertion"
    assert out["escalation_reason"] != "first_attempt_same_topic"


def test_correction_reask_contracts_strict_social_answer_pressure_eligible():
    log = [
        {
            "player_input": "Runner, anything interesting tonight?",
            "gm_snippet": "The runner shrugs. Travelers talk about the old well—some say coins still glint down there.",
        },
        {
            "player_input": "Why is that?",
            "gm_snippet": (
                'He taps the bar. "If you want a real thread, watch who visits the seal-house after dark."'
            ),
        },
    ]
    correction = "What? I asked you why people here wouldn't be friendly to newcomers."
    obligations = _obligations_social_answer()
    session_view = {"active_interaction_target_id": "tavern_runner"}
    resolution = {
        "kind": "question",
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
    }
    ac = build_answer_completeness_contract(
        player_input=correction,
        narration_obligations=obligations,
        resolution=resolution,
        session_view=session_view,
        uncertainty_hint=None,
        recent_log_compact=log,
    )
    rd = build_response_delta_contract(
        player_input=correction,
        recent_log_compact=log,
        narration_obligations=obligations,
        resolution=resolution,
        answer_completeness=ac,
        session_view=session_view,
    )
    assert ac["trace"]["correction_reask_followup_detected"] is True
    assert ac["trace"]["strict_social_answer_seek_override"] is True
    assert ac["answer_required"] is True
    assert rd["enabled"] is True
    assert rd["trigger_source"] == "strict_social_answer_pressure"
    assert rd["trace"]["correction_reask_followup_detected"] is True
