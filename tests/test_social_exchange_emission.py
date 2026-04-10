from __future__ import annotations

import game.final_emission_gate as feg

from game.defaults import default_session, default_world
from game.gm import apply_deterministic_retry_fallback, sanitize_player_facing_text
from game.final_emission_gate import (
    apply_final_emission_gate,
    enforce_emitted_speaker_with_contract,
    inspect_answer_completeness_failure,
    validate_answer_completeness,
)
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.output_sanitizer import (
    _already_has_terminal_punctuation,
    _cohere_sentences,
    _contains_template_fragment,
    final_validation_pass,
    sanitize_player_facing_output,
)
from game.social_exchange_emission import (
    _apply_interruption_repeat_guard,
    apply_strict_social_ownership_enforcement,
    apply_strict_social_sentence_ownership_filter,
    build_final_strict_social_response,
    coerce_resolution_for_strict_social_emission,
    effective_strict_social_resolution_for_emission,
    hard_reject_social_exchange_text,
    is_route_illegal_global_or_sanitizer_fallback_text,
    normalize_social_exchange_candidate,
    reconcile_strict_social_resolution_speaker,
    should_apply_strict_social_exchange_emission,
    strict_social_emission_will_apply,
    strict_social_ownership_terminal_fallback,
    synthetic_social_exchange_resolution_for_emission,
)
from game.response_policy_contracts import build_social_response_structure_contract
from game.storage import get_scene_runtime


import pytest

pytestmark = pytest.mark.unit

def _strict_social_resolution() -> dict:
    return {
        "kind": "question",
        "prompt": "Where did they go?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "The runner",
        },
    }


def _interruptible_runner_resolution() -> dict:
    return {
        "kind": "social_probe",
        "prompt": "What happened to the missing patrol?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
        },
    }


def test_template_heuristics_ignore_quoted_the_next_name():
    beat = 'the tattered man murmurs. "Walk with me if you want the next name."'
    assert _contains_template_fragment(beat) is False


def test_cohere_dialogue_terminal_avoids_lonely_period_sentence_in_validation():
    processed = [
        "Rain beads on the checkpoint while nobody moves first.",
        (
            "Guards notices you lingering and comes over at once. "
            '"If you\'re waiting on trouble, it already passed the checkpoint," he says. '
            '"Take the east-road report or get clear."'
        ),
    ]
    rebuilt = " ".join(_cohere_sentences(processed)).strip()
    assert rebuilt.endswith('"')
    assert _already_has_terminal_punctuation(processed[1])
    validated = final_validation_pass(rebuilt, {})
    assert "from here, no certain answer" not in validated.lower()


def test_passive_pressure_merged_text_survives_sanitize_and_gate():
    gpt = "The square stays hushed except for the scrape of boots on wet stone."
    beat = (
        "the tattered man leaves by the shuttered well and cuts through the crowd and stops at your shoulder. "
        '"You\'re asking the wrong questions out loud," they murmur. "Walk with me if you want the next name."'
    )
    merged = gpt + "\n\n" + beat
    san = sanitize_player_facing_output(merged, {})
    low = san.lower()
    assert "tattered man" in low
    assert "the truth is still buried" not in low
    out = apply_final_emission_gate(
        {"player_facing_text": san, "tags": []},
        resolution=None,
        session={},
        scene_id="scene_investigate",
    )
    assert "for a breath, the scene holds" not in out["player_facing_text"].lower()


def test_hard_reject_flags_scene_hold_on_strict_social():
    res = _strict_social_resolution()
    reasons = hard_reject_social_exchange_text(
        "For a breath, the scene holds while voices shift around you.",
        resolution=res,
        session={},
    )
    assert reasons


def test_strict_social_vocative_runner_with_empty_world_npc_list():
    """Vocative address to the runner must activate strict social even when world.npcs is empty on disk."""
    session = default_session()
    world = {"npcs": []}
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Runner, who attacked them?"
    resolution = {"kind": "question", "prompt": "Runner, who attacked them?"}
    _eff, social_route, _reason = effective_strict_social_resolution_for_emission(
        resolution, session, world, sid
    )
    assert social_route is True
    assert strict_social_emission_will_apply(resolution, session, world, sid) is True


def test_coerce_synthetic_when_resolution_none_and_active_social_question():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What should I do next?"
    eff, on, reason = coerce_resolution_for_strict_social_emission(None, session, world, sid)
    assert on is True
    assert reason == "synthetic_active_interlocutor_question"


def test_guard_coerces_strict_social_when_synthetic_emission_inactive():
    """Synthetic strict-social resolution fails (e.g. engagement), but npc_directed_guard still coerces."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Where did they go?"
    resolution = {"kind": "question", "prompt": "Where did they go?"}
    assert synthetic_social_exchange_resolution_for_emission(session, world, sid, prompt_text="Where did they go?") is None
    eff, on, _reason = coerce_resolution_for_strict_social_emission(resolution, session, world, sid)
    assert on is False
    eff2, on2, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert on2 is True
    assert isinstance(eff2, dict)


def test_deterministic_retry_fallback_never_injects_uncertainty_templates_on_guard_coerced_strict_social():
    """apply_deterministic_retry_fallback must match final gate strict-social routing (incl. guard)."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Where did they go?"
    resolution = {"kind": "question", "prompt": "Where did they go?"}
    gm = {"player_facing_text": "The reply is vague.", "tags": []}
    failure = {"failure_class": "unresolved_question", "reasons": ["test"]}
    out = apply_deterministic_retry_fallback(
        gm,
        failure=failure,
        player_text="Where did they go?",
        scene_envelope={"scene": {"id": sid}},
        session=session,
        world=world,
        resolution=resolution,
    )
    txt = out["player_facing_text"].lower()
    assert "nothing in the scene points" not in txt
    assert "answer has not formed yet" not in txt
    assert "pin down who they meet" not in txt
    assert "you can narrow it to" not in txt
    assert "for a breath" not in txt
    assert "scene holds" not in txt
    assert "the answer has not formed yet" not in txt
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "social_exchange_retry_fallback" in tags


def test_final_emission_gate_answer_contract_prefers_response_policy_surface_and_repairs_scene_prose():
    resolution = {
        "kind": "adjudication_query",
        "prompt": "Is Sleight of Hand needed?",
        "requires_check": True,
        "check_request": {
            "requires_check": True,
            "player_prompt": "Roll Sleight of Hand to determine whether the move goes unnoticed.",
        },
        "metadata": {
            "response_type_contract": {
                "required_response_type": "dialogue",
                "allow_escalation": True,
            }
        },
    }
    session = {
        "last_action_debug": {
            "player_input": "Is Sleight of Hand needed?",
            "response_type_contract": {
                "required_response_type": "action_outcome",
                "allow_escalation": True,
            },
        }
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Rain beads on the square while voices drift around you.",
            "tags": [],
            "response_policy": {
                "response_type_contract": {
                    "required_response_type": "answer",
                    "allow_escalation": False,
                }
            },
        },
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert out["player_facing_text"] == "Roll Sleight of Hand to determine whether the move goes unnoticed."
    assert meta.get("response_type_required") == "answer"
    assert meta.get("response_type_contract_source") == "response_policy"
    assert meta.get("response_type_candidate_ok") is True
    assert meta.get("response_type_repair_used") is True
    assert meta.get("response_type_repair_kind") == "answer_minimal_repair"


_SAMPLE_ANSWER_COMPLETENESS_CONTRACT = {
    "enabled": True,
    "answer_required": True,
    "answer_must_come_first": True,
    "player_direct_question": True,
    "expected_voice": "narrator",
    "expected_answer_shape": "direct",
    "allowed_partial_reasons": ["uncertainty", "lack_of_knowledge", "gated_information"],
    "forbid_deflection": True,
    "forbid_generic_nonanswer": True,
    "require_concrete_payload": True,
    "concrete_payload_any_of": ["place", "direction"],
    "trace": {},
}


def test_validate_answer_completeness_flags_question_before_substance():
    contract = dict(_SAMPLE_ANSWER_COMPLETENESS_CONTRACT)
    res = validate_answer_completeness(
        "Do you know who took the ledger? The east road is watched.",
        contract,
        resolution=None,
    )
    assert res["checked"] is True
    assert res["question_first_violation"] is True
    assert res["passed"] is False
    fail = inspect_answer_completeness_failure(res)
    assert fail["failed"] is True
    assert "opening_question_before_answer" in fail["failure_reasons"]


def test_final_emission_gate_answer_completeness_repairs_frontloaded_direct_answer():
    contract = dict(_SAMPLE_ANSWER_COMPLETENESS_CONTRACT)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Rain beads on the square. The east road runs past the old gate.",
            "tags": [],
            "response_policy": {"answer_completeness": contract},
        },
        resolution={"kind": "question", "prompt": "Which way did they go?"},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("answer_completeness_repaired") is True
    assert meta.get("answer_completeness_repair_mode") == "frontload_direct_answer"
    low = out["player_facing_text"].lower()
    assert low.startswith("the east road")
    assert "rain beads" in low


def test_final_emission_gate_action_outcome_contract_repairs_exposition_only_candidate():
    resolution = {
        "kind": "investigate",
        "prompt": "I investigate the desk.",
        "success": False,
        "state_changes": {"already_searched": True},
        "metadata": {
            "response_type_contract": {
                "required_response_type": "action_outcome",
                "allow_escalation": False,
            }
        },
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Mist hangs over the room while the scene stays still.",
            "tags": [],
        },
        resolution=resolution,
        session={"last_action_debug": {"player_input": "I investigate the desk."}},
        scene_id="frontier_gate",
        world={},
    )
    low = out["player_facing_text"].lower()
    meta = out.get("_final_emission_meta") or {}
    assert "you investigate the desk" in low
    assert "nothing new" in low
    assert meta.get("response_type_required") == "action_outcome"
    assert meta.get("response_type_candidate_ok") is True
    assert meta.get("response_type_repair_used") is True
    assert meta.get("response_type_repair_kind") == "action_outcome_minimal_repair"


def test_final_emission_gate_non_hostile_contract_blocks_sudden_aggression():
    resolution = {
        "kind": "adjudication_query",
        "prompt": "Is Sleight of Hand needed?",
        "requires_check": True,
        "check_request": {
            "requires_check": True,
            "player_prompt": "Roll Sleight of Hand to determine whether the move goes unnoticed.",
        },
        "metadata": {
            "response_type_contract": {
                "required_response_type": "answer",
                "allow_escalation": False,
            }
        },
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "He draws steel and lunges at you.",
            "tags": [],
        },
        resolution=resolution,
        session={"last_action_debug": {"player_input": "Is Sleight of Hand needed?"}},
        scene_id="frontier_gate",
        world={},
    )
    low = out["player_facing_text"].lower()
    meta = out.get("_final_emission_meta") or {}
    assert "draws steel" not in low
    assert "lunges" not in low
    assert "sleight of hand" in low
    assert meta.get("non_hostile_escalation_blocked") is True
    assert meta.get("response_type_candidate_ok") is True


def test_final_emission_gate_non_hostile_answer_contract_stays_non_escalatory_with_active_interlocutor():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"] = {"active_scene_id": sid, "active_entities": ["tavern_runner"]}
    session["last_action_debug"] = {"player_input": "Is Sleight of Hand needed?"}
    resolution = {
        "kind": "adjudication_query",
        "prompt": "Is Sleight of Hand needed?",
        "requires_check": True,
        "check_request": {
            "requires_check": True,
            "player_prompt": "Roll Sleight of Hand to determine whether the move goes unnoticed.",
        },
        "metadata": {
            "response_type_contract": {
                "required_response_type": "answer",
                "allow_escalation": False,
            }
        },
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The tavern runner draws steel and lunges at you.",
            "tags": [],
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out["player_facing_text"].lower()
    meta = out.get("_final_emission_meta") or {}
    assert "draws steel" not in low
    assert "lunges" not in low
    assert "sleight of hand" in low
    assert "the move goes unnoticed" in low
    assert "tavern runner" not in low
    assert meta.get("response_type_required") == "answer"
    assert meta.get("response_type_candidate_ok") is True
    assert meta.get("response_type_repair_used") is True
    assert meta.get("non_hostile_escalation_blocked") is True


def test_final_emission_gate_dialogue_contract_can_repair_from_debug_surface():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    session["last_action_debug"] = {
        "player_input": "Who attacked them?",
        "response_type_contract": {
            "required_response_type": "dialogue",
            "allow_escalation": False,
        },
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Rain beads on stone nearby.",
            "tags": [],
        },
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out["player_facing_text"].lower()
    meta = out.get("_final_emission_meta") or {}
    assert "rain beads on stone" not in low
    assert "tavern runner" in low
    assert ('"' in out["player_facing_text"]) or ("starts to answer" in low)
    assert meta.get("response_type_required") == "dialogue"
    assert meta.get("response_type_contract_source") == "debug"
    assert meta.get("response_type_candidate_ok") is True
    assert meta.get("response_type_repair_used") is True
    assert meta.get("response_type_repair_kind") == "dialogue_minimal_repair"


def test_strict_social_pipeline_forbids_scene_hold_and_ambiguity_emitter_phrases():
    """Strict-social must never surface final-emission scene-hold or GM uncertainty-template lines."""
    forbidden = (
        "for a breath",
        "the scene holds",
        "voices shift around you",
        "nothing in the scene points",
        "for a breath, the scene stays still",
        "confirms a culprit",
        "nothing around the faces",
    )
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who ordered the patrol?"
    resolution = {"kind": "question", "prompt": "Who ordered the patrol?"}

    gate_out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "Nothing in the scene points to a clear answer yet. "
                "Nothing around the faces lingering over the missing patrol notice confirms a culprit yet. "
                "For a breath, the scene holds while voices shift around you."
            ),
            "tags": [],
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = gate_out["player_facing_text"].lower()
    for frag in forbidden:
        assert frag not in low, frag

    gm_retry = apply_deterministic_retry_fallback(
        {"player_facing_text": "vague", "tags": []},
        failure={"failure_class": "unresolved_question", "reasons": ["t"]},
        player_text="Who ordered the patrol?",
        scene_envelope={"scene": {"id": sid}},
        session=session,
        world=world,
        resolution=resolution,
    )
    low = gm_retry["player_facing_text"].lower()
    for frag in forbidden:
        assert frag not in low, frag

    scene = {"scene": {"id": sid, "visible_facts": [], "location": "gate"}}
    spoil = sanitize_player_facing_text(
        "noble house secret leak noble house",
        scene,
        "Who ordered the patrol?",
        discovered_clues=[],
        session=session,
        world=world,
        resolution=resolution,
    )
    assert spoil["did_sanitize"] is True
    low = spoil["text"].lower()
    for frag in forbidden:
        assert frag not in low, frag


def test_spoiler_guard_on_strict_social_never_replaces_with_uncertainty_renderer():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Where did they go?"
    resolution = {"kind": "question", "prompt": "Where did they go?"}
    scene = {"scene": {"id": sid, "visible_facts": [], "location": "gate"}}
    res = sanitize_player_facing_text(
        "noble house secret leak noble house",
        scene,
        "Where did they go?",
        discovered_clues=[],
        session=session,
        world=world,
        resolution=resolution,
    )
    assert res["did_sanitize"] is True
    low = res["text"].lower()
    assert "nothing in the scene points" not in low
    assert "answer has not formed yet" not in low
    assert "pin down who they meet" not in low


def test_final_emission_with_coercion_never_emits_global_scene_hold_for_strict_turn():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who ordered the patrol?"
    out = apply_final_emission_gate(
        {"player_facing_text": "For a breath, the scene holds while voices shift around you.", "tags": []},
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out["player_facing_text"].lower()
    assert "for a breath" not in low
    assert "scene holds" not in low
    assert '"' in out["player_facing_text"] or "shouting breaks out" in low


def test_final_emission_rejects_checkpoint_guidance_blob_under_coercion():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What should I do next?"
    blob = (
        "The answer has not formed yet; one visible lead still stands open at the checkpoint. "
        "I'd suggest you press the runner on names before the shift change."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": blob, "tags": []},
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out["player_facing_text"].lower()
    assert "the answer has not formed yet" not in low
    assert "i'd suggest you" not in low
    assert "checkpoint" not in low
    assert '"' in out["player_facing_text"] or "shouting breaks out" in low


def test_social_probe_false_npc_reply_expected_strict_when_runtime_question_matches_active_npc():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What did you hear about the gate?"
    resolution = {
        "kind": "social_probe",
        "prompt": "",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_reply_expected": False,
        },
    }
    assert should_apply_strict_social_exchange_emission(
        resolution,
        session,
        scene_runtime_prompt=rt["last_player_action_text"],
    )


def test_apply_strict_social_keeps_bounded_ignorance_strips_narrator_tail():
    res = _strict_social_resolution()
    raw = 'No one here can swear to it. Nothing in the scene points to a clear answer yet.'
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    assert "nothing in the scene" not in out.lower()
    assert "no one here" in out.lower() or "swear" in out.lower()


def test_apply_strict_social_rejects_detached_omniscient_analysis():
    res = _strict_social_resolution()
    raw = "The plan behind attacking a patrol is likely to disrupt local order."
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    assert out == strict_social_ownership_terminal_fallback(res)
    assert "likely to disrupt" not in out.lower()
    reasons = hard_reject_social_exchange_text(raw, resolution=res, session={})
    assert "detached_omniscient_analysis" in reasons


def test_apply_strict_social_allows_speculation_with_speaker_frame():
    res = _strict_social_resolution()
    raw = 'The runner grimaces. "If I had to guess, they wanted supplies or fear."'
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    assert "if i had to guess" in out.lower()
    assert '"' in out


def test_apply_strict_social_never_emits_scene_hold_sentence():
    res = _strict_social_resolution()
    raw = "For a breath, the scene holds while voices shift around you."
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    assert out == strict_social_ownership_terminal_fallback(res)
    assert "for a breath" not in out.lower() and "scene holds" not in out.lower()


def test_gate_replaces_when_all_sentences_non_social_strict_social():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who ordered the patrol?"
    out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "Nothing in the scene points to a clear answer yet. "
                "The plan behind attacking a patrol is likely to disrupt local order."
            ),
            "tags": [],
        },
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out["player_facing_text"].lower()
    assert "nothing in the scene" not in low
    assert "likely to disrupt" not in low
    assert "for a breath" not in low
    assert '"' in out["player_facing_text"] or "shouting breaks out" in low


def test_what_should_i_do_next_strict_social_never_scene_placeholder_only():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What should I do next?"
    out = apply_final_emission_gate(
        {"player_facing_text": "For a breath, the scene holds while voices shift around you.", "tags": []},
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out["player_facing_text"].lower()
    assert "for a breath" not in low
    assert "scene holds" not in low
    assert '"' in out["player_facing_text"] or "don't know" in low or "shouting" in low


def test_normalize_collapses_mixed_npc_answer_and_scene_uncertainty():
    res = _strict_social_resolution()
    raw = (
        'The runner says, "Old Millstone—south road." '
        "Nothing in the scene points to a clear answer yet."
    )
    out = normalize_social_exchange_candidate(raw, resolution=res)
    assert "nothing in the scene" not in out.lower()
    assert "old millstone" in out.lower()
    assert '"' in out


def test_normalize_strips_appended_ambient_after_social_answer():
    res = _strict_social_resolution()
    raw = (
        'The runner says "The mill." '
        "Rain beads on the checkpoint while nobody moves first."
    )
    out = normalize_social_exchange_candidate(raw, resolution=res)
    assert "rain beads" not in out.lower()
    assert "the mill" in out.lower()


def test_normalize_drops_clue_description_fragments_after_social_line():
    res = _strict_social_resolution()
    raw = (
        'The runner says "Try the east lane." '
        "Scuffed mud, broken chalk, and damp paper scraps mark where the crowd surged."
    )
    out = normalize_social_exchange_candidate(raw, resolution=res)
    assert "scuffed mud" not in out.lower()
    assert "east lane" in out.lower()


def test_normalize_interruption_emits_single_breakoff_only():
    res = _strict_social_resolution()
    raw = (
        "The runner starts to answer, then glances past you as shouting breaks out in the crowd. "
        "From here, no clear answer presents itself."
    )
    out = normalize_social_exchange_candidate(raw, resolution=res)
    assert "from here, no clear answer" not in out.lower()
    assert "shouting" in out.lower() or "breaks out" in out.lower()


def test_first_interruption_still_allowed_for_strict_social_exchange():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _interruptible_runner_resolution()
    candidate = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."

    out, meta = build_final_strict_social_response(
        candidate,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )

    low = out.lower()
    assert "runner" in low
    assert "shouting" in low or "breaks out" in low
    assert meta.get("forced_interruption_progression") is False
    assert meta.get("interruption_repeat_count") == 1


def test_repeated_interruption_reuse_forces_socially_grounded_progression():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _interruptible_runner_resolution()
    candidate = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."

    out1, meta1 = build_final_strict_social_response(
        candidate,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    out2, meta2 = build_final_strict_social_response(
        candidate,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )

    assert meta1.get("forced_interruption_progression") is False
    low2 = out2.lower()
    assert meta2.get("forced_interruption_progression") is True
    assert meta2.get("interruption_repeat_count") >= 2
    assert "runner" in low2 or '"' in out2
    assert "starts to answer" not in low2
    assert "shouting breaks out" not in low2
    assert (
        "ward clerk" in low2
        or "main gate" in low2
        or "old crossroads" in low2
        or "old millstone" in low2
    )
    assert out2 != out1


def test_paraphrased_interruption_repeat_still_counts_and_forces_progression():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _interruptible_runner_resolution()
    first = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."
    second = "Tavern Runner opens their mouth, then breaks off as a shout cuts across the square."

    out1, meta1 = build_final_strict_social_response(
        first,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    out2, meta2 = build_final_strict_social_response(
        second,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )

    assert meta1.get("forced_interruption_progression") is False
    low2 = out2.lower()
    assert meta2.get("forced_interruption_progression") is True
    assert meta2.get("interruption_repeat_count") >= 2
    assert "runner" in low2 or '"' in out2
    assert "breaks off" not in low2
    assert "shout cuts across the square" not in low2
    assert (
        "ward clerk" in low2
        or "main gate" in low2
        or "old crossroads" in low2
        or "old millstone" in low2
    )
    assert out2 != out1


def test_noise_pulls_attention_away_counts_as_same_interruption_signature():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _interruptible_runner_resolution()
    first = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."
    second = "Tavern Runner begins to respond before noise from the crowd pulls their attention away."

    out1, meta1 = build_final_strict_social_response(
        first,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    out2, meta2 = build_final_strict_social_response(
        second,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )

    assert meta1.get("forced_interruption_progression") is False
    low2 = out2.lower()
    assert meta2.get("forced_interruption_progression") is True
    assert meta2.get("interruption_repeat_count") >= 2
    assert "begins to respond" not in low2
    assert "noise from the crowd pulls their attention away" not in low2
    assert (
        "ward clerk" in low2
        or "main gate" in low2
        or "old crossroads" in low2
        or "old millstone" in low2
    )


def test_interruption_repeat_tracker_resets_on_scene_change():
    session = default_session()
    world = default_world()
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, "frontier_gate")
    resolution = _interruptible_runner_resolution()
    candidate = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."

    _out1, meta1 = build_final_strict_social_response(
        candidate,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id="frontier_gate",
        world=world,
    )
    out2, meta2 = build_final_strict_social_response(
        candidate,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id="eastern_square",
        world=world,
    )

    low2 = out2.lower()
    assert meta1.get("interruption_repeat_count") == 1
    assert meta2.get("forced_interruption_progression") is False
    assert meta2.get("interruption_repeat_count") == 1
    assert "starts to answer" in low2
    assert "shouting" in low2 or "breaks out" in low2


def test_genuinely_new_interruption_signature_is_treated_fresh():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _interruptible_runner_resolution()
    first = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."
    same = "Tavern Runner opens their mouth, then breaks off as a shout cuts across the square."
    new_beat = "Tavern Runner starts to answer, then glances toward the main gate as an alarm rises and two guards shove through the lane."

    _out1, meta1 = build_final_strict_social_response(
        first,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    out2, meta2 = build_final_strict_social_response(
        same,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    out3, meta3 = build_final_strict_social_response(
        new_beat,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )

    assert meta1.get("forced_interruption_progression") is False
    assert meta2.get("forced_interruption_progression") is True
    low3 = out3.lower()
    assert meta3.get("forced_interruption_progression") is False
    assert meta3.get("interruption_repeat_count") == 1
    assert "starts to answer" in low3 or "opens their mouth" in low3
    assert "old millstone" not in low3


def test_existing_progression_output_for_cause_followup_survives_repeat_guard():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _interruptible_runner_resolution()
    interruption = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."
    progressed = (
        'Tavern Runner jerks their chin toward the main gate. '
        '"Fish carts collided there, and two watchmen are hauling a fishmonger clear."'
    )

    _apply_interruption_repeat_guard(
        interruption,
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        tags=[],
        source_text=interruption,
    )
    out, meta = _apply_interruption_repeat_guard(
        progressed,
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        tags=[],
        source_text=interruption,
    )

    low = out.lower()
    assert meta.get("forced_interruption_progression") is True
    assert meta.get("forced_interruption_progression_kind") == "existing_progression_output"
    assert "starts to answer" not in low
    assert "main gate" in low or "watchmen" in low or "fishmonger" in low


def test_existing_progression_output_for_reaction_followup_survives_repeat_guard():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _interruptible_runner_resolution()
    interruption = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."
    progressed = (
        'Tavern Runner grimaces at the shout and leans close. '
        '"That rattled me. Give me a breath and I will tell you where the patrol was last seen."'
    )

    _apply_interruption_repeat_guard(
        interruption,
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        tags=[],
        source_text=interruption,
    )
    out, meta = _apply_interruption_repeat_guard(
        progressed,
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        tags=[],
        source_text=interruption,
    )

    low = out.lower()
    assert meta.get("forced_interruption_progression") is True
    assert meta.get("forced_interruption_progression_kind") == "existing_progression_output"
    assert "starts to answer" not in low
    assert "flinches" in low or "leans close" in low or "doorway clears" in low


def test_existing_progression_output_for_partial_answer_survives_repeat_guard():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = _interruptible_runner_resolution()
    interruption = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."
    progressed = 'Tavern Runner says, "Short version: they were last seen near the old millstone. I did not see who led them."'

    _apply_interruption_repeat_guard(
        interruption,
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        tags=[],
        source_text=interruption,
    )
    out, meta = _apply_interruption_repeat_guard(
        progressed,
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
        tags=[],
        source_text=interruption,
    )

    low = out.lower()
    assert meta.get("forced_interruption_progression") is True
    assert meta.get("forced_interruption_progression_kind") == "existing_progression_output"
    assert "starts to answer" not in low
    assert "short version" in low or "old millstone" in low


def test_interruption_repeat_tracker_resets_on_target_change():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    first = _interruptible_runner_resolution()
    second = {
        "kind": "question",
        "prompt": "Guard Captain, what happened at the gate?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
            "npc_name": "Guard Captain",
            "npc_reply_expected": True,
        },
    }
    candidate = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."

    _out1, meta1 = build_final_strict_social_response(
        candidate,
        resolution=first,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    out2, meta2 = build_final_strict_social_response(
        "Guard Captain starts to answer, then glances toward the doorway as shouting breaks out in the crowd.",
        resolution=second,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )

    low2 = out2.lower()
    assert meta1.get("interruption_repeat_count") == 1
    assert meta2.get("forced_interruption_progression") is False
    assert meta2.get("interruption_repeat_count") == 1
    assert "guard captain" in low2


def test_normalize_ambiguous_follow_up_question_stays_speaker_owned():
    res = _strict_social_resolution()
    raw = (
        'The runner says, "What do you mean?" They look at you narrowly. '
        "You can trace the rumor in the mud, but not the name."
    )
    out = normalize_social_exchange_candidate(raw, resolution=res)
    assert "you can trace" not in out.lower()
    assert "what do you mean" in out.lower()
    assert "look at you" in out.lower()


def test_normalize_contradictory_ignorance_and_answer_returns_terminal_fallback():
    res = _strict_social_resolution()
    raw = (
        'The guard says "East road." They mutter, "I don\'t know."'
    )
    out = normalize_social_exchange_candidate(raw, resolution=res)
    assert out == strict_social_ownership_terminal_fallback(res)


def test_build_final_strict_social_response_rewrites_scene_ambiguity_into_speaker_voice():
    """Strict-social cleanup is owned by build_final_strict_social_response, not sanitize_player_facing_output."""
    res = {
        "kind": "question",
        "prompt": "What should I do next?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Runner",
        },
    }
    raw = "Nothing in the scene points to a clear answer yet. You should pick a next step."
    out, _ = build_final_strict_social_response(
        raw,
        resolution=res,
        tags=[],
        session={},
        scene_id="",
    )
    low = out.lower()
    assert "nothing in the scene points" not in low
    assert "you should" not in low
    assert '"' in out or "shouting" in low or "breaks out" in low
    assert "runner" in low or "don't know" in low or "frowns" in low or "hesitates" in low or "shouting" in low


def test_strict_social_emission_meta_documents_final_emitted_source():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who ordered the patrol?"
    out = apply_final_emission_gate(
        {"player_facing_text": 'The runner says "I don\'t know."', "tags": []},
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("strict_social_active") is True
    assert meta.get("final_emitted_source") in (
        "generated_candidate",
        "normalized_social_candidate",
        "retry_output",
        "resolved_grounded_social_answer",
    )
    assert meta.get("candidate_validation_passed") is True


def test_strict_social_gate_merges_social_response_structure_metadata(monkeypatch):
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Where is the east gate?"
    rtc = {"required_response_type": "dialogue", "action_must_preserve_agency": False}
    srs = build_social_response_structure_contract(rtc)
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

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return (
            'Runner says "East gate lies two hundred feet south along the market road."',
            dict(stub_details),
        )

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "stub",
            "tags": [],
            "response_policy": {"response_type_contract": rtc, "social_response_structure": srs},
        },
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("strict_social_active") is True
    for key in (
        "social_response_structure_checked",
        "social_response_structure_applicable",
        "social_response_structure_passed",
        "social_response_structure_repair_applied",
        "social_response_structure_skip_reason",
    ):
        assert key in meta
    assert meta.get("social_response_structure_applicable") is True
    assert meta.get("social_response_structure_passed") is True


def test_strict_social_replacement_never_uses_global_scene_fallback_in_meta():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who ordered the patrol?"
    out = apply_final_emission_gate(
        {
            "player_facing_text": "For a breath, the scene holds while voices shift around you.",
            "tags": [],
        },
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("final_emitted_source") != "global_scene_fallback"
    assert meta.get("final_emitted_source") in (
        "deterministic_social_fallback",
        "minimal_social_emergency_fallback",
        "normalized_social_candidate",
    )
    low = out["player_facing_text"].lower()
    assert "for a breath" not in low


def test_strict_social_visibility_replacement_prefers_social_owned_fallback_over_visible_intro():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who ordered the patrol?"
    scene = {
        "scene": {
            "id": sid,
            "location": "checkpoint",
            "visible_facts": ["A tavern runner lingers under an awning near the checkpoint."],
        }
    }
    out = apply_final_emission_gate(
        {"player_facing_text": 'He says, "I don\'t know."', "tags": []},
        resolution=None,
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )
    low = out["player_facing_text"].lower()
    assert "stands nearby" not in low
    assert "stands in checkpoint" not in low
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("strict_social_active") is True
    assert meta.get("final_emitted_source") in (
        "deterministic_social_fallback",
        "minimal_social_emergency_fallback",
        "normalized_social_candidate",
    )
    assert meta.get("final_emitted_source") != "explicit_visible_entity_scene_intro"


def test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere():
    session = default_session()
    sid = "scene_investigate"
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_passive"] = True
    rt["passive_action_streak"] = 1
    rt["recent_contextual_leads"] = [
        {
            "key": "tattered-man-by-the-shuttered-well",
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
            "named": False,
            "positioned": True,
            "mentions": 2,
            "last_turn": 1,
        }
    ]
    out = apply_final_emission_gate(
        {"player_facing_text": "The square stays hushed except for the scrape of boots on wet stone.", "tags": []},
        resolution=None,
        session=session,
        scene_id=sid,
        scene={"scene": {"id": sid, "location": "square", "visible_facts": []}},
        world=default_world(),
    )
    low = out["player_facing_text"].lower()
    assert "the tattered man" in low
    assert "cuts through the crowd" in low or "comes straight to you" in low
    assert "for a breath, the scene holds" not in low
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("final_emitted_source") == "passive_scene_pressure_fallback"


def test_clue_advice_sludge_intercepted_for_strict_npc_question():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who was behind it?"
    sludge = (
        "Shadow Tavern Runner and pin down who they meet next. "
        "The answer has not formed yet; one visible lead still stands open at the checkpoint."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": sludge, "tags": []},
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out["player_facing_text"].lower()
    assert "shadow tavern runner" not in low
    assert "pin down who they meet" not in low
    assert "the answer has not formed yet" not in low
    assert is_route_illegal_global_or_sanitizer_fallback_text(out["player_facing_text"]) is False


def test_generic_guard_direct_question_never_degrades_to_global_scene_hold():
    """Generic 'one of the guards' address: still block global scene hold when scene has an NPC."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    session["scene_state"]["active_entities"] = ["guard_captain"]
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = (
        "Galinor approaches one of the guards. 'What happened to the missing patrol?'"
    )
    out = apply_final_emission_gate(
        {"player_facing_text": "For a breath, the scene holds while voices shift around you.", "tags": []},
        resolution=None,
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out["player_facing_text"].lower()
    assert "for a breath" not in low
    assert "scene holds" not in low
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("strict_social_active") is True
    assert meta.get("final_emitted_source") != "global_scene_fallback"


def test_ownership_pass_strips_leading_narrator_keeps_npc_line():
    res = _strict_social_resolution()
    raw = (
        "Nothing in the scene points to a clear answer yet. "
        'The runner shrugs. "Could be east—hard to say."'
    )
    out = apply_strict_social_ownership_enforcement(raw, resolution=res)
    assert "nothing in the scene" not in out.lower()
    assert "east" in out.lower() and '"' in out


def test_ownership_pass_removes_scene_hold_line_entirely():
    res = _strict_social_resolution()
    raw = 'For a breath, the scene holds. The runner says, "Patrol went north."'
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    assert "for a breath" not in out.lower() and "scene holds" not in out.lower()
    assert "north" in out.lower()


def test_ownership_pass_mixed_blob_keeps_only_social_sentences():
    res = _strict_social_resolution()
    raw = (
        "Nothing in the scene points to a clear answer yet. "
        'He says, "I heard it was the mill." '
        "It might be worth pressing the clerk for names."
    )
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    low = out.lower()
    assert "nothing in the scene" not in low
    assert "it might be worth" not in low
    assert "mill" in low


def test_ownership_pass_empty_input_is_terminal_fallback():
    res = _strict_social_resolution()
    assert apply_strict_social_sentence_ownership_filter("", resolution=res) == strict_social_ownership_terminal_fallback(
        res
    )


def test_ownership_pass_aliases_match():
    res = _strict_social_resolution()
    raw = "The plan behind attacking a patrol is likely to disrupt local order."
    a = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    b = apply_strict_social_ownership_enforcement(raw, resolution=res)
    assert a == b == strict_social_ownership_terminal_fallback(res)


def test_strict_social_keeps_two_sentences_when_both_npc_owned_direct_answer():
    """Two dialogue beats should not collapse to one sentence when both are social."""
    res = _strict_social_resolution()
    raw = (
        'The runner mutters, "No witnesses named." '
        'They add, "Word is, it was messy near the east bend."'
    )
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    parts = [p.strip() for p in out.replace("“", '"').replace("”", '"').split('"') if p.strip()]
    assert out.count('"') >= 2
    assert "east" in out.lower() and "witnesses" in out.lower()


def test_strict_social_ignorance_plus_compatible_detail_keeps_both_sentences():
    res = _strict_social_resolution()
    raw = (
        'The runner shakes their head. "I don\'t know who ordered it." '
        'They lean in. "I did hear extra watches posted by dusk."'
    )
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    low = out.lower()
    assert "don\'t know who" in low or "don't know who" in low
    assert "watches" in low or "dusk" in low


def test_deterministic_social_fallback_variety_uses_speaker_label():
    from game.social_exchange_emission import deterministic_social_fallback_line

    res = {
        "kind": "question",
        "prompt": "Who attacked them?",
        "social": {"social_intent_class": "social_exchange", "npc_id": "runner", "npc_name": "The runner"},
    }
    lines = []
    for i in range(12):
        line, _ = deterministic_social_fallback_line(
            resolution=res,
            uncertainty_source="npc_ignorance",
            pressure_active=False,
            interruption_active=False,
            seed=f"test{i}",
        )
        lines.append(line.lower())
    assert len(set(lines)) >= 3
    assert all("runner" in ln for ln in lines)


def test_scene_narration_leakage_still_removed_from_strict_social_blob():
    res = _strict_social_resolution()
    raw = (
        "For a breath, the scene holds while voices shift around you. "
        'The runner says, "Patrol never came back."'
    )
    out = apply_strict_social_sentence_ownership_filter(raw, resolution=res)
    low = out.lower()
    assert "for a breath" not in low and "scene holds" not in low
    assert "patrol" in low or "came" in low


def test_strict_social_reconcile_binds_fallback_to_active_not_first_roster():
    """Stale engine npc_id must not make deterministic fallback speak as roster[0] when active is another NPC."""
    from game.social_exchange_emission import deterministic_social_fallback_line

    session = default_session()
    world = dict(default_world())
    sid = "frontier_gate"
    world["npcs"] = [
        {"id": "guard_captain", "name": "Guard Captain", "location": sid},
        {"id": "rian", "name": "Rian", "location": sid},
    ]
    set_social_target(session, "rian")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "engaged"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What did you hear about the patrol?"
    resolution = {
        "kind": "question",
        "prompt": "What did you hear about the patrol?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
            "npc_name": "Guard Captain",
            "npc_reply_expected": True,
        },
    }
    eff, on, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert on is True
    assert eff["social"]["npc_id"] == "rian"
    assert eff["social"]["npc_name"] == "Rian"
    line, _ = deterministic_social_fallback_line(
        resolution=eff,
        uncertainty_source="npc_ignorance",
        pressure_active=False,
        interruption_active=False,
        seed="bind-test",
    )
    assert "Rian" in line
    assert "Guard Captain" not in line


def test_social_exchange_whispers_answer_passes_question_contract():
    from game.gm import question_resolution_rule_check

    res = {
        "kind": "question",
        "prompt": "Who ordered the patrol?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "The runner",
            "npc_reply_expected": True,
        },
    }
    reply = 'The runner lowers their voice. "I\'ve heard whispers, but no one will swear to it."'
    chk = question_resolution_rule_check(player_text=res["prompt"], gm_reply_text=reply, resolution=res)
    assert chk["ok"] is True


def test_strict_social_detect_retry_allows_trust_phrase_in_quoted_dialogue():
    from game.gm import detect_retry_failures

    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    resolution = {
        "kind": "question",
        "prompt": "What do you think of newcomers?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
        },
    }
    gm = {"player_facing_text": 'Tavern Runner mutters. "Trust is hard to come by out here."'}
    failures = detect_retry_failures(
        player_text="What do you think of newcomers?",
        gm_reply=gm,
        scene_envelope={"scene": {"id": sid}},
        session=session,
        world=world,
        resolution=resolution,
    )
    classes = [str(f.get("failure_class") or "") for f in failures]
    assert "forbidden_generic_phrase" not in classes


def test_wait_turn_keeps_strict_social_binding_without_scene_uncertainty_blob():
    """Passive wait during an active social exchange should still coerce strict-social (merged prompt)."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "engaged"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "I wait, watching the gate."
    resolution = {"kind": "observe", "prompt": "I wait, watching the gate."}
    eff, on, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert on is True
    assert isinstance(eff, dict)
    assert eff.get("social", {}).get("npc_id") == "tavern_runner"
    out, _ = build_final_strict_social_response(
        "From here, no certain answer presents itself about the gate.",
        resolution=eff,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out.lower()
    assert "from here, no certain answer" not in low
    assert "nothing in the scene points" not in low


def test_reconcile_strict_social_stores_speaker_selection_contract_in_emission_debug():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "engaged"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What happened to the patrol?"
    resolution = {
        "kind": "social_probe",
        "prompt": "What happened to the patrol?",
        "metadata": {"normalized_action": {"target_id": "tavern_runner", "targetEntityId": "tavern_runner"}},
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
        },
    }
    out = reconcile_strict_social_resolution_speaker(resolution, session, world, sid)
    em = out.get("metadata", {}).get("emission_debug", {})
    contract = em.get("speaker_selection_contract")
    assert isinstance(contract, dict)
    assert contract.get("debug", {}).get("contract_missing") is not True
    assert isinstance(contract.get("allowed_speaker_ids"), list)


def test_enforce_speaker_contract_reads_stored_contract_without_calling_build_speaker_selection_contract(
    monkeypatch,
):
    """Downstream enforcement must consume emission_debug.speaker_selection_contract (no re-resolution)."""
    from game import interaction_context as ic_mod

    calls: list[int] = []
    _orig_build = ic_mod.build_speaker_selection_contract

    def spy_build(*args, **kwargs):
        calls.append(1)
        return _orig_build(*args, **kwargs)

    monkeypatch.setattr(ic_mod, "build_speaker_selection_contract", spy_build)

    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Test?"
    resolution = {
        "kind": "question",
        "prompt": "Test?",
        "metadata": {"normalized_action": {"target_id": "tavern_runner"}},
        "social": {"social_intent_class": "social_exchange", "npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
    }
    eff = reconcile_strict_social_resolution_speaker(resolution, session, world, sid)
    assert len(calls) == 1

    gm_out = {"metadata": dict(eff.get("metadata") or {}), "trace": {}}
    calls.clear()
    enforce_emitted_speaker_with_contract(
        'Tavern Runner says, "Fine."',
        gm_output=gm_out,
        resolution=eff,
        eff_resolution=eff,
        world=world,
        scene_id=sid,
    )
    assert len(calls) == 0
