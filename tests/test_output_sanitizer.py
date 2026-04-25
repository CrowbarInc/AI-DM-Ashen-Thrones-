"""Canonical owner for post-GM emit hygiene: ``sanitize_player_facing_output``, final validation
/coherence passes, leaked-payload stripping, and procedural / scaffold phrase rewrites on
**player-facing** text.

Prompt construction, ``build_messages``, guards, and ``build_retry_prompt_for_failure`` belong in
``tests/test_prompt_and_guard.py``. Integration suites prove the stack runs; detailed substring
families stay here.
"""
from __future__ import annotations

import game.output_sanitizer as output_sanitizer_module
import game.social_exchange_emission as social_exchange_emission_module
from game.defaults import default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.output_sanitizer import (
    SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE,
    extract_player_text_from_serialized_payload,
    final_validation_pass,
    final_coherence_pass,
    rewrite_analytical_sentence,
    sanitize_player_facing_output,
)


def _legacy_rewrite_ctx(extra: dict | None = None) -> dict:
    base = {"sanitizer_boundary_mode": SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE}
    if extra:
        return {**base, **extra}
    return dict(base)


import pytest

pytestmark = pytest.mark.unit

def test_strip_only_mode_drops_scaffold_without_diegetic_template_substitution():
    text = "I need a more concrete action or target to resolve that procedurally."
    ctx: dict = {
        "sanitizer_boundary_mode": "strip_only",
        "upstream_prepared_emission": {"prepared_sanitizer_empty_fallback_text": "UPSTREAM_EMPTY_STOCK."},
    }
    out = sanitize_player_facing_output(text, ctx)
    assert out == "UPSTREAM_EMPTY_STOCK."
    events = [e.get("event") for e in (ctx.get("sanitizer_debug") or []) if isinstance(e, dict)]
    assert "strip_only_dropped_rewrite_candidate" in events


def test_strip_only_preserves_clean_atmospheric_narration():
    text = "Rain needles across the checkpoint as lanternlight wavers on wet stone."
    ctx = {"sanitizer_boundary_mode": "strip_only", "upstream_prepared_emission": {}}
    assert sanitize_player_facing_output(text, ctx) == text


def test_sanitizer_rewrites_procedural_engine_text():
    text = "I need a more concrete action or target to resolve that procedurally."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "resolve that procedurally" not in low
    assert "more concrete action" not in low
    assert "state exactly what you do" not in low
    assert "scene offers no clear answer yet" not in low
    assert (
        "no answer presents itself from here" in low
        or "truth stays locked until someone pushes a concrete move" in low
        or "answer has not formed yet" in low
    )


def test_sanitizer_strips_internal_role_prefixes():
    text = (
        "Planner: Move to branch A.\n"
        "Router: choose dialogue route.\n"
        "Validator: based on established state, uncertain."
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "planner:" not in low
    assert "router:" not in low
    assert "validator:" not in low


def test_sanitizer_cleans_malformed_concatenation_splice():
    text = "there's no solid evidence... you might start leaves by speaking to the runner."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "start leaves by speaking" not in low
    assert "start by speaking" not in low
    assert "state exactly what you do" not in low


def test_sanitizer_blocks_router_planner_validator_scaffold_terms():
    text = "internal validator state says router planner instructions are unresolved."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "validator state" not in low
    assert "router" not in low
    assert "planner" not in low


def test_sanitizer_preserves_valid_atmospheric_narration():
    text = "Rain needles across the checkpoint as lanternlight wavers on wet stone."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    assert out == text


def test_sanitizer_rewrites_fragmented_scaffold_start_with():
    text = "Start with man in tattered clothes appears to be waiting by the gate."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "start with" not in low
    assert "man in tattered clothes" in low
    assert "lingers nearby" in low


def test_sanitizer_removes_instructional_prompt_sentence():
    text = "The moment hangs unresolved; state exactly what you do."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "state exactly what you do" not in low
    assert "moment hangs unresolved" not in low


def test_sanitizer_rewrites_unresolved_answer_without_old_fallback_phrase():
    text = "Cannot determine roll requirements yet; state the specific action and target first."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "cannot determine roll requirements yet" not in low
    assert "state the specific action and target first" not in low
    assert "scene offers no clear answer yet" not in low
    assert (
        "no answer presents itself from here" in low
        or "truth stays locked until someone pushes a concrete move" in low
        or "answer has not formed yet" in low
    )


def test_sanitizer_uses_procedural_insufficiency_fallback_for_adjudication_context():
    # Canonical post-emission procedural phrasing lives here; prompt/guard owns source classification upstream.
    text = "Cannot determine roll requirements yet; state the specific action and target first."
    out = sanitize_player_facing_output(
        text,
        _legacy_rewrite_ctx(
            {
                "resolution": {
                    "kind": "adjudication_query",
                    "requires_check": True,
                    "adjudication": {"answer_type": "needs_concrete_action"},
                }
            }
        ),
    )
    low = out.lower()
    assert "no answer presents itself from here" in low or "answer has not formed yet" in low
    assert "nothing in the scene points to a clear answer yet" not in low


def test_sanitizer_prefers_npc_uncertainty_for_dialogue_like_instructional_text():
    text = 'Guard says, "Resolve that procedurally for now."'
    out = sanitize_player_facing_output(
        text,
        _legacy_rewrite_ctx(
            {"resolution": {"kind": "question", "social": {"social_intent_class": "social_exchange"}}}
        ),
    )
    low = out.lower()
    assert "resolve that procedurally" not in low
    assert "scene offers no clear answer yet" not in low
    assert (
        ('"i do not know that part for certain."' in low)
        or ('"i have heard the talk, but not the names."' in low)
        or ("heard talk, not names" in low)
        or ("do not know enough to name anyone" in low)
        or ("do not know a name" in low)
        or ("word is, it was messy" in low)
        or ("couldn't tell you" in low)
        or ('"no one here can swear to it."' in low)
        or ("no answer presents itself from here" in low)
        or ("truth stays locked until someone pushes a concrete move" in low)
        or ("answer has not formed yet" in low)
        or ('"i don\'t know."' in low)
        or ("that's all i've got" in low)
        or ("can't help you there" in low)
    )


def test_sanitizer_removes_duplicate_and_spliced_fragments():
    text = (
        "A man in tattered clothes lingers nearby, watching the crowd. "
        "A man in tattered clothes lingers nearby, watching the crowd. "
        "Stay with many want it."
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert low.count("a man in tattered clothes lingers nearby, watching the crowd.") == 1
    assert "stay with many want it" not in low


def test_sanitizer_extracts_player_text_from_full_serialized_payload_dump():
    text = (
        '{"player_facing_text":"The bell tolls once in the fog.",'
        '"tags":["tone:grim"],'
        '"scene_update":{"visible_facts_add":["x"]},'
        '"activate_scene_id":null,'
        '"new_scene_draft":null,'
        '"world_updates":{"append_events":[]},'
        '"suggested_action":{"kind":"wait"},'
        '"debug_notes":"trace"}'
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "bell tolls once in the fog" in low
    assert "player_facing_text" not in low
    assert "scene_update" not in low
    assert "debug_notes" not in low
    assert "tags" not in low


def test_sanitizer_extracts_from_malformed_truncated_payload_fragment():
    text = (
        '{"player_facing_text":"A cold draft slips under the gate",'
        '"tags":["leak"],"scene_update":{"visible_facts_add":["'
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "cold draft slips under the gate" in low
    assert "player_facing_text" not in low
    assert "scene_update" not in low
    assert "tags" not in low


def test_sanitizer_keeps_narrative_when_mixed_with_structured_fragment():
    text = (
        'You hear boots on wet cobbles behind you. '
        '"tags":["meta"],"scene_update":{"visible_facts_add":["patrol"]},"debug_notes":"x"'
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "you hear boots on wet cobbles behind you" in low
    assert "scene_update" not in low
    assert "debug_notes" not in low
    assert "tags" not in low


def test_sanitizer_preserves_normal_quoted_dialogue():
    text = '"Who goes there?" the guard asks, leveling his spear.'
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    assert out == text


def test_extractor_returns_none_for_plain_narration():
    text = '"Keep your hood up," she says as rain hits the shutters.'
    assert extract_player_text_from_serialized_payload(text) is None


def test_rewrite_analytical_sentence_notice_board_trace_becomes_diegetic_observation():
    text = "You can trace what happened around the notice board."
    out = rewrite_analytical_sentence(text, {})
    low = out.lower()
    assert "you can" not in low
    assert "notice board" in low
    assert any(token in low for token in ("postings", "torn", "hands"))


def test_rewrite_analytical_sentence_social_uncertainty_prefers_npc_bounded_voice():
    text = "No clear answer has surfaced yet."
    out = rewrite_analytical_sentence(
        text,
        {"resolution": {"kind": "question", "social": {"social_intent_class": "social_exchange"}}},
    )
    low = out.lower()
    assert "no clear answer" not in low
    assert '"' in out
    assert any(
        phrase in low
        for phrase in (
            "i do not know",
            "don't know",
            "i have heard",
            "i've heard",
            "no one here can swear",
        )
    )


def test_sanitizer_rewrites_gauntlet_analytical_phrases_into_diegetic_lines():
    text = (
        "You can trace what happened around the notice board. "
        "You can narrow it to two suspects. "
        "Only fragments of the method are visible. "
        "Another name seems to sit behind the story. "
        "The scene suggests coordination. "
        "It can be inferred that someone planned this. "
        "No clear answer has surfaced."
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    banned_fragments = (
        "you can",
        "you can trace",
        "you can narrow it",
        "only fragments of",
        "another name seems to",
        "the scene suggests",
        "it can be inferred",
        "no clear answer",
    )
    for fragment in banned_fragments:
        assert fragment not in low
    assert any(token in low for token in ("notice board", "boot", "whisper", "rain", "mud", "clues"))


def test_sanitizer_strips_you_might_want_to_investigative_framing():
    text = "You might want to question the crowd before nightfall."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "you might want to" not in low
    assert "you can" not in low


def test_sanitizer_keeps_visual_it_appears_that_sentence():
    text = "It appears that torchlight flickers behind the shutters."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    assert out == text


def test_sanitizer_rewrites_abstract_it_appears_that_sentence():
    text = "It appears that the operation is coordinated."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "it appears that" not in low
    assert "operation is coordinated" not in low


def test_sanitizer_rewrites_you_should_directive():
    text = "You should investigate the notice board."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "you should" not in low
    assert "notice board" in low


def test_sanitizer_rewrites_you_might_want_to_directive():
    text = "You might want to ask the runner."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "you might want to" not in low
    assert "ask the runner" not in low
    assert "runner" in low


def test_sanitizer_rewrites_implicit_imperative_investigate_without_you():
    text = "Investigate the man in tattered clothes."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "investigate" not in low
    assert "you" not in low
    assert "man in tattered clothes" in low


def test_sanitizer_rewrites_advisory_it_is_advisable_language():
    text = "It is advisable to approach him discreetly."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "it is advisable" not in low
    assert "approach him discreetly" not in low
    assert "you" not in low
    assert any(token in low for token in ("margins of the crowd", "edge of the scene", "waiting to be noticed"))


def test_sanitizer_rewrites_implicit_imperative_observe_without_you():
    text = "Observe the tavern runner."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "observe" not in low
    assert "you" not in low
    assert "tavern runner" in low


def test_sanitizer_removes_you_recognize_them_as_identity_phrase():
    text = "You recognize them as the Tavern Runner."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "you recognize them as" not in low
    assert "tavern runner" not in low
    assert "runner shifts under your gaze" in low


def test_final_coherence_pass_collapses_duplicate_sentence():
    text = "The runner shifts under your gaze. The runner shifts under your gaze."
    out = final_coherence_pass(text)
    low = out.lower()
    assert low.count("the runner shifts under your gaze.") == 1


def test_final_coherence_pass_repairs_malformed_join_and_drops_fragment():
    text = "the runner watches the crowd, clearly listening for more than he says  the runner watches the crowd, clearly listening for more than he says. and behind the."
    out = final_coherence_pass(text)
    low = out.lower()
    assert low.count("the runner watches the crowd, clearly listening for more than he says.") == 1
    assert "and behind the" not in low


def test_sanitizer_rewrites_partial_template_fragments_atomically():
    text = "The next name remains within reach, framed by the noise of the scene."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "the next name" not in low
    assert "remains within reach" not in low
    assert "framed by the noise" not in low


def test_final_validation_pass_rejects_merged_fragment_sentence():
    text = "The rumors surrounding the tavern or approach the man in tattered clothes."
    out = final_validation_pass(text, {})
    low = out.lower()
    assert "surrounding the tavern or approach" not in low
    assert "or approach" not in low
    assert "man in tattered clothes lingers nearby, watching the crowd." in low


def test_sanitizer_handles_overlapping_rewrite_artifacts_without_hybrids():
    text = (
        "You might want to ask the runner. "
        "The next name remains within reach, framed by the noise of the scene. "
        "Details that do not quite fit."
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "you might want to" not in low
    assert "the next name" not in low
    assert "remains within reach" not in low
    assert "framed by the noise" not in low
    assert "details that do not quite fit" not in low


def test_sentence_atomic_overlap_rewrite_never_keeps_partial_stumps():
    text = (
        "You might want to ask the runner because no clear answer has surfaced yet and "
        "the next name remains within reach, framed by the noise."
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "you might want to" not in low
    assert "no clear answer" not in low
    assert "the next name" not in low
    assert "remains within reach" not in low
    assert "framed by the noise" not in low
    assert out.endswith((".", "!", "?"))


def test_sentence_atomic_hybrid_sentence_prefers_full_rewrite():
    text = (
        "Rain needles across the checkpoint while planner notes say to resolve that procedurally before you should investigate."
    )
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "rain needles across the checkpoint while planner notes" not in low
    assert "resolve that procedurally" not in low
    assert "you should investigate" not in low
    assert "planner" not in low


def test_sentence_atomic_advisory_removal_preserves_neighbor_sentence():
    text = "Rain beads on the gate stones. You should investigate the notice board."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "rain beads on the gate stones." in low
    assert "you should investigate" not in low
    assert "notice board" in low


def test_sentence_atomic_quoted_dialogue_integrity_after_rewrite():
    text = '"Resolve that procedurally," the guard says. "Keep your hood up," he adds.'
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "resolve that procedurally" not in low
    assert low.count('"') % 2 == 0
    assert '"keep your hood up," he adds.' in low


def test_sentence_atomic_punctuation_cleanup_after_dropped_sentence():
    text = "State exactly what you do. And behind the. Rain beads on stone.."
    out = sanitize_player_facing_output(text, _legacy_rewrite_ctx())
    low = out.lower()
    assert "state exactly what you do" not in low
    assert "and behind the" not in low
    assert ".." not in out
    assert "rain beads on stone." in low


def _strict_social_resolution_for_sanitizer() -> dict:
    return {
        "kind": "question",
        "prompt": "Where did they go?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "The runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
    }


def test_post_gate_strict_clamp_does_not_call_strict_social_ownership_filter(monkeypatch):
    """Strict-social post-gate path must not invoke ownership filter from the sanitizer."""
    calls: list[int] = []
    real = social_exchange_emission_module.apply_strict_social_sentence_ownership_filter

    def spy(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(social_exchange_emission_module, "apply_strict_social_sentence_ownership_filter", spy)
    res = _strict_social_resolution_for_sanitizer()
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    set_social_target(session, "runner")
    text = 'The runner nods once. "South road."'
    sanitize_player_facing_output(
        text,
        {
            "resolution": res,
            "session": session,
            "world": world,
            "scene_id": sid,
            "tags": [],
            "post_final_emission_gate": True,
            "strict_social_terminal_clamp": True,
            "gate_sealed_text": text,
        },
    )
    assert calls == []

    sanitize_player_facing_output(
        text,
        {
            "resolution": res,
            "session": session,
            "world": world,
            "scene_id": sid,
            "tags": [],
        },
    )
    assert calls == []


def test_post_gate_strict_clamp_preserves_valid_social_line():
    """Non-semantic passes should leave already-gate-valid social text stable."""
    res = _strict_social_resolution_for_sanitizer()
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    set_social_target(session, "runner")
    text = 'The runner nods once. "South road."'
    ctx = {
        "resolution": res,
        "session": session,
        "world": world,
        "scene_id": sid,
        "tags": [],
        "post_final_emission_gate": True,
        "strict_social_terminal_clamp": True,
        "gate_sealed_text": text,
    }
    out = sanitize_player_facing_output(text, ctx)
    assert out == text


def test_post_gate_strict_clamp_empty_rebuilt_returns_gate_sealed_text():
    sealed = 'The runner shrugs. "I don\'t know."'
    out = sanitize_player_facing_output(
        "",
        {
            "post_final_emission_gate": True,
            "strict_social_terminal_clamp": True,
            "gate_sealed_text": sealed,
        },
    )
    assert out == sealed
