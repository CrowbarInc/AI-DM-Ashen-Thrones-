from __future__ import annotations

from game.output_sanitizer import (
    extract_player_text_from_serialized_payload,
    final_validation_pass,
    final_coherence_pass,
    rewrite_analytical_sentence,
    sanitize_player_facing_output,
)


def test_sanitizer_rewrites_procedural_engine_text():
    text = "I need a more concrete action or target to resolve that procedurally."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "resolve that procedurally" not in low
    assert "more concrete action" not in low
    assert "state exactly what you do" not in low
    assert "scene offers no clear answer yet" not in low
    assert (
        "nothing in the scene points to a clear answer yet" in low
        or "from here, no certain answer presents itself" in low
        or "the truth is still buried beneath rumor and rain" in low
    )


def test_sanitizer_strips_internal_role_prefixes():
    text = (
        "Planner: Move to branch A.\n"
        "Router: choose dialogue route.\n"
        "Validator: based on established state, uncertain."
    )
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "planner:" not in low
    assert "router:" not in low
    assert "validator:" not in low


def test_sanitizer_cleans_malformed_concatenation_splice():
    text = "there's no solid evidence... you might start leaves by speaking to the runner."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "start leaves by speaking" not in low
    assert "start by speaking" not in low
    assert "state exactly what you do" not in low


def test_sanitizer_blocks_router_planner_validator_scaffold_terms():
    text = "internal validator state says router planner instructions are unresolved."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "validator state" not in low
    assert "router" not in low
    assert "planner" not in low


def test_sanitizer_preserves_valid_atmospheric_narration():
    text = "Rain needles across the checkpoint as lanternlight wavers on wet stone."
    out = sanitize_player_facing_output(text, {})
    assert out == text


def test_sanitizer_rewrites_fragmented_scaffold_start_with():
    text = "Start with man in tattered clothes appears to be waiting by the gate."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "start with" not in low
    assert "man in tattered clothes" in low
    assert "lingers nearby" in low


def test_sanitizer_removes_instructional_prompt_sentence():
    text = "The moment hangs unresolved; state exactly what you do."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "state exactly what you do" not in low
    assert "moment hangs unresolved" not in low


def test_sanitizer_rewrites_unresolved_answer_without_old_fallback_phrase():
    text = "Cannot determine roll requirements yet; state the specific action and target first."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "cannot determine roll requirements yet" not in low
    assert "state the specific action and target first" not in low
    assert "scene offers no clear answer yet" not in low
    assert (
        "nothing in the scene points to a clear answer yet" in low
        or "from here, no certain answer presents itself" in low
        or "the truth is still buried beneath rumor and rain" in low
    )


def test_sanitizer_prefers_npc_uncertainty_for_dialogue_like_instructional_text():
    text = 'Guard says, "Resolve that procedurally for now."'
    out = sanitize_player_facing_output(
        text,
        {"resolution": {"kind": "question", "social": {"social_intent_class": "social_exchange"}}},
    )
    low = out.lower()
    assert "resolve that procedurally" not in low
    assert "scene offers no clear answer yet" not in low
    assert ('"i do not know that part for certain."' in low) or ('"i have heard the talk, but not the names."' in low) or (
        '"no one here can swear to it."' in low
    )


def test_sanitizer_removes_duplicate_and_spliced_fragments():
    text = (
        "A man in tattered clothes lingers nearby, watching the crowd. "
        "A man in tattered clothes lingers nearby, watching the crowd. "
        "Stay with many want it."
    )
    out = sanitize_player_facing_output(text, {})
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
    out = sanitize_player_facing_output(text, {})
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
    out = sanitize_player_facing_output(text, {})
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
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "you hear boots on wet cobbles behind you" in low
    assert "scene_update" not in low
    assert "debug_notes" not in low
    assert "tags" not in low


def test_sanitizer_preserves_normal_quoted_dialogue():
    text = '"Who goes there?" the guard asks, leveling his spear.'
    out = sanitize_player_facing_output(text, {})
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
    assert any(phrase in low for phrase in ("i do not know", "i have heard", "no one here can swear"))


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
    out = sanitize_player_facing_output(text, {})
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
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "you might want to" not in low
    assert "you can" not in low


def test_sanitizer_keeps_visual_it_appears_that_sentence():
    text = "It appears that torchlight flickers behind the shutters."
    out = sanitize_player_facing_output(text, {})
    assert out == text


def test_sanitizer_rewrites_abstract_it_appears_that_sentence():
    text = "It appears that the operation is coordinated."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "it appears that" not in low
    assert "operation is coordinated" not in low


def test_sanitizer_rewrites_you_should_directive():
    text = "You should investigate the notice board."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "you should" not in low
    assert "notice board" in low


def test_sanitizer_rewrites_you_might_want_to_directive():
    text = "You might want to ask the runner."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "you might want to" not in low
    assert "ask the runner" not in low
    assert "runner" in low


def test_sanitizer_rewrites_implicit_imperative_investigate_without_you():
    text = "Investigate the man in tattered clothes."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "investigate" not in low
    assert "you" not in low
    assert "man in tattered clothes" in low


def test_sanitizer_rewrites_advisory_it_is_advisable_language():
    text = "It is advisable to approach him discreetly."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "it is advisable" not in low
    assert "approach him discreetly" not in low
    assert "you" not in low
    assert any(token in low for token in ("margins of the crowd", "edge of the scene", "waiting to be noticed"))


def test_sanitizer_rewrites_implicit_imperative_observe_without_you():
    text = "Observe the tavern runner."
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "observe" not in low
    assert "you" not in low
    assert "tavern runner" in low


def test_sanitizer_removes_you_recognize_them_as_identity_phrase():
    text = "You recognize them as the Tavern Runner."
    out = sanitize_player_facing_output(text, {})
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
    out = sanitize_player_facing_output(text, {})
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
    out = sanitize_player_facing_output(text, {})
    low = out.lower()
    assert "you might want to" not in low
    assert "the next name" not in low
    assert "remains within reach" not in low
    assert "framed by the noise" not in low
    assert "details that do not quite fit" not in low
