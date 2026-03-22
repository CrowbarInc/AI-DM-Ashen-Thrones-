from __future__ import annotations

from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.output_sanitizer import (
    _already_has_terminal_punctuation,
    _cohere_sentences,
    _contains_template_fragment,
    final_validation_pass,
    sanitize_player_facing_output,
)
from game.social_exchange_emission import (
    apply_strict_social_ownership_enforcement,
    apply_strict_social_sentence_ownership_filter,
    coerce_resolution_for_strict_social_emission,
    hard_reject_social_exchange_text,
    is_route_illegal_global_or_sanitizer_fallback_text,
    normalize_social_exchange_candidate,
    should_apply_strict_social_exchange_emission,
    strict_social_ownership_terminal_fallback,
)
from game.storage import get_scene_runtime


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
    assert isinstance(eff, dict)
    assert eff["social"]["npc_id"] == "tavern_runner"
    assert eff["social"]["social_intent_class"] == "social_exchange"


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


def test_active_social_sanitize_rewrites_scene_ambiguity_into_speaker_voice():
    res = {
        "kind": "question",
        "prompt": "What should I do next?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Runner",
        },
    }
    ctx = {"resolution": res, "session": {}}
    raw = "Nothing in the scene points to a clear answer yet. You should pick a next step."
    out = sanitize_player_facing_output(raw, ctx)
    low = out.lower()
    assert "nothing in the scene points" not in low
    assert "you should" not in low
    assert '"' in out
    assert "runner" in low or "don't know" in low or "frowns" in low or "hesitates" in low


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
    assert meta.get("final_emitted_source") in ("generated_candidate", "normalized_social_candidate", "retry_output")
    assert meta.get("candidate_validation_passed") is True


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
    assert meta.get("final_emitted_source") in ("deterministic_social_fallback", "minimal_social_emergency_fallback")
    low = out["player_facing_text"].lower()
    assert "for a breath" not in low


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
