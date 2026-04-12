"""Canonical owner for pre-generation contracts: ``build_messages``, system/instruction hooks,
guards (``guard_gm_output``, NPC contracts, uncertainty/retry classification, policy enforcement
before final emit), and **retry prompt text** from ``build_retry_prompt_for_failure``.

Post-GM player-string hygiene (``sanitize_player_facing_output`` and related phrase families) is
owned by ``tests/test_output_sanitizer.py``. Transcript / gauntlet suites should keep **E2E
smoke** for those boundaries unless exact wording is itself the regression target.
"""
import json
import re

import pytest

pytestmark = [pytest.mark.brittle, pytest.mark.integration]

FRONTIER_GATE_SCENE = {
    "scene": {
        "id": "frontier_gate",
        "location": "Cinderwatch Gate District",
        "summary": "Rain spatters soot-dark stone as caravans and refugees choke the eastern gate. Guards watch the crowd with brittle discipline.",
        "mode": "exploration",
        "visible_facts": [
            "Refugees crowd the muddy approach road.",
            "A notice board lists new taxes, curfews, and a missing patrol.",
            "A tavern runner loudly offers rumor and hot stew for coin.",
        ],
        "discoverable_clues": [
            "A well-dressed onlooker near the gate seems more interested in newcomers than in the refugees.",
            "A rough-looking bystander keeps watching anyone with unusual gear or arcane signs.",
        ],
        "hidden_facts": [
            "An agent of a noble house is watching new arrivals.",
            "A smuggler contact in the crowd is looking for magical talent.",
        ],
        "exits": [],
        "enemies": [],
    }
}


def _dummy_state():
    campaign = {"title": "T", "character_role": "R"}
    world = {
        "event_log": [],
        "npcs": [
            {
                "id": "guard_captain",
                "name": "Captain Veyra",
                "scene_id": "frontier_gate",
            }
        ],
    }
    session = {
        "active_scene_id": "frontier_gate",
        "interaction_context": {
            "active_interaction_target_id": "guard_captain",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
            "conversation_privacy": "lowered_voice",
            "player_position_context": "seated_with_target",
        },
    }
    character = {"name": "Galinor", "hp": {"current": 8, "max": 8}, "ac": {"normal": 12, "touch": 12, "flat_footed": 10}}
    combat = {"in_combat": False}
    recent_log = []
    return campaign, world, session, character, combat, recent_log


def _assert_text_contains_all(text: str, *substrings: str) -> None:
    """Structural prose check: avoid pinning full canonical sentences from scene fixtures."""
    low = (text or "").lower()
    for s in substrings:
        assert s.lower() in low, (s, text)


def _assert_uncertainty_render_helper_contract(text: str, *, forbidden_terms: tuple[str, ...] = ()) -> None:
    """Pre-sanitizer contract for :func:`render_uncertainty_response` (classification + template shape).

    Validator/meta tone is asserted via :func:`game.gm.detect_validator_voice` (policy registry).
    Phrase-level legality for emitted LLM prose after the full pipeline lives in
    ``tests/test_output_sanitizer.py``.
    """
    from game.gm import detect_validator_voice

    vh = detect_validator_voice(text)
    assert vh == [], vh
    low = (text or "").lower()
    # Narrow stock-template bans not covered by detect_validator_voice (e.g. bare "i can't answer"
    # without "that", legacy uncertainty line shapes).
    for phrase in (
        "i can't answer",
        "i cannot answer",
        "training data",
        "tools",
        "best lead:",
        "no one here can",
        "no one here will",
        "the exact place is still blurred",
        "the means are still obscured",
        "the effect is plain enough",
    ):
        assert phrase not in low, (phrase, text)
    for term in forbidden_terms:
        assert term not in low


def _assert_local_anchor(text: str) -> None:
    low = text.lower()
    assert any(
        phrase in low
        for phrase in (
            "cinderwatch gate district",
            "notice board",
            "missing patrol",
            "tavern runner",
            "refugee",
            "checkpoint",
            "main gate",
            "muddy approach",
        )
    )


def _assert_actionable_lead(text: str) -> None:
    low = text.lower()
    assert any(
        phrase in low
        for phrase in (
            "ask ",
            "press ",
            "follow ",
            "take the route",
            "buy ",
            "pull names",
            "start at ",
            "lean on ",
            "watch ",
            "count ",
            "find out ",
            "inspect ",
            "test ",
            "use ",
            "track ",
            "chase ",
            "lock down ",
        )
    )


def test_prompt_structure_separates_hidden_facts():
    from game.gm import build_messages
    from game.storage import get_scene_runtime

    campaign, world, session, character, combat, recent_log = _dummy_state()
    # Use session without active_scene_id so build_messages uses the passed scene (tests need specific content)
    session_no_active = {
        "scene_runtime": {},
        "interaction_context": dict(session.get("interaction_context") or {}),
    }
    scene_rt = get_scene_runtime(session_no_active, "frontier_gate")
    msgs = build_messages(
        campaign,
        world,
        session_no_active,
        character,
        FRONTIER_GATE_SCENE,
        combat,
        recent_log,
        "Look around.",
        None,
        scene_runtime=scene_rt,
    )
    assert msgs[0]["role"] == "system"
    assert "hidden_facts" in msgs[0]["content"]
    assert "Spoiler safeguard" in msgs[0]["content"]

    payload = json.loads(msgs[1]["content"])
    scene_payload = payload["scene"]
    assert "public" in scene_payload
    assert "gm_only" in scene_payload
    assert scene_payload["public"]["visible_facts"] == FRONTIER_GATE_SCENE["scene"]["visible_facts"]
    # Not justified by "Look around." => discoverable clues must not be in the main discoverable list.
    assert scene_payload["discoverable_clues"] == []
    assert scene_payload["gm_only"]["hidden_facts"] == FRONTIER_GATE_SCENE["scene"]["hidden_facts"]
    # Locked discoverables should still be available GM-side, but explicitly labeled as locked.
    assert scene_payload["gm_only"]["discoverable_clues_locked"] == FRONTIER_GATE_SCENE["scene"]["discoverable_clues"]
    assert payload["session"]["active_interaction_target_id"] == "guard_captain"
    assert payload["session"]["active_interaction_target_name"] == "Captain Veyra"
    assert payload["session"]["active_interaction_kind"] == "social"
    assert payload["session"]["interaction_mode"] == "social"
    assert payload["session"]["engagement_level"] == "engaged"
    assert payload["session"]["conversation_privacy"] == "lowered_voice"
    assert payload["session"]["player_position_context"] == "seated_with_target"
    assert payload["interaction_continuity"]["active_interaction_target_id"] == "guard_captain"
    assert payload["interaction_continuity"]["active_interaction_target_name"] == "Captain Veyra"
    assert payload["interaction_continuity"]["active_interaction_kind"] == "social"
    assert payload["interaction_continuity"]["interaction_mode"] == "social"
    assert payload["interaction_continuity"]["engagement_level"] == "engaged"
    assert payload["interaction_continuity"]["conversation_privacy"] == "lowered_voice"
    assert payload["interaction_continuity"]["player_position_context"] == "seated_with_target"
    obligations = payload["narration_obligations"]
    assert obligations["should_answer_active_npc"] is True
    assert obligations["avoid_input_echo"] is True


def test_prompt_includes_speaker_lock_and_privacy_guidance():
    from game.gm import build_messages
    from game.storage import get_scene_runtime

    campaign, world, session, character, combat, recent_log = _dummy_state()
    scene_rt = get_scene_runtime({"scene_runtime": {}}, "frontier_gate")
    msgs = build_messages(
        campaign,
        world,
        session,
        character,
        FRONTIER_GATE_SCENE,
        combat,
        recent_log,
        "I speak quietly with the guard captain.",
        None,
        scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    instructions = " ".join(payload.get("instructions", [])).lower()
    assert "always answer the player. prefer partial truth over refusal. never output meta explanations." in instructions
    assert "default conversational counterpart" in instructions
    assert "non-addressed npcs should not casually interject" in instructions
    assert "private exchange" in instructions
    assert "authoritative engine state" in instructions
    assert "narration_obligations.should_answer_active_npc" in instructions
    assert "do not restate or paraphrase the player's input" in instructions


def test_allow_discoverable_clues_heuristic():
    from game.gm import allow_discoverable_clues, classify_player_intent

    # Classification labels.
    i1 = classify_player_intent("I search the wagon carefully.")
    assert "investigation" in i1["labels"]
    assert i1["allow_discoverable_clues"] is True

    i2 = classify_player_intent("I question the guard about the caravans.")
    assert "social_probe" in i2["labels"]
    assert i2["allow_discoverable_clues"] is True

    i3 = classify_player_intent("I walk north to the market.")
    assert "travel" in i3["labels"] or "general" in i3["labels"]
    # Travel alone should not auto-allow clues.
    assert i3["allow_discoverable_clues"] is False

    # Backward-compatible wrapper still behaves.
    assert allow_discoverable_clues("Look around.") is False
    assert allow_discoverable_clues("What do I notice immediately?") is False
    assert allow_discoverable_clues("I investigate the area carefully.") is True
    assert allow_discoverable_clues("I question locals about anything unusual.") is True


def test_guard_blocks_hidden_fact_phrasing():
    from game.gm import guard_gm_output

    gm = {
        "player_facing_text": "You spot an agent of a noble house and also a smuggler contact looking for magical talent.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = guard_gm_output(gm, FRONTIER_GATE_SCENE, "Look around.", [])
    assert out["player_facing_text"] != gm["player_facing_text"]
    assert "spoiler_guard" in out.get("tags", [])
    assert "spoiler_guard" in out.get("debug_notes", "")


@pytest.mark.parametrize(
    ("player_text", "expected_category"),
    [
        ("Who is behind this?", "unknown_identity"),
        ("Where did they take it?", "unknown_location"),
        ("Why would they risk this?", "unknown_motive"),
        ("How did they get through?", "unknown_method"),
        ("How many were there?", "unknown_quantity"),
        ("Can I get through the gate tonight?", "unknown_feasibility"),
    ],
)
def test_typed_uncertainty_categories_render_bounded_answers(player_text, expected_category):
    from game.gm import classify_uncertainty, render_uncertainty_response

    _, world, session, _, _, _ = _dummy_state()
    uncertainty = classify_uncertainty(
        player_text,
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
    )
    text = render_uncertainty_response(uncertainty)

    assert uncertainty["category"] == expected_category
    assert uncertainty["known_edge"]
    assert uncertainty["unknown_edge"]
    assert uncertainty["next_lead"]
    _assert_uncertainty_render_helper_contract(
        text,
        forbidden_terms=("noble house", "smuggler", "magical talent"),
    )
    assert uncertainty["speaker"]["name"] == "Captain Veyra"
    assert uncertainty["speaker"]["role"] == "npc"
    _assert_local_anchor(text)
    _assert_actionable_lead(text)


def test_npc_dialogue_uncertainty_is_speaker_anchored():
    from game.gm import classify_uncertainty, render_uncertainty_response

    _, world, session, _, _, _ = _dummy_state()
    uncertainty = classify_uncertainty(
        "Where did they take the patrol report?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution={
            "kind": "question",
            "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "reply_kind": "answer"},
        },
    )
    text = render_uncertainty_response(uncertainty)

    assert uncertainty["speaker"]["role"] == "npc"
    assert uncertainty["speaker"]["name"] == "Captain Veyra"
    assert "captain veyra" in text.lower()
    assert '"' in text
    _assert_local_anchor(text)


def test_narrator_uncertainty_outside_direct_dialogue_is_scene_anchored():
    from game.gm import classify_uncertainty, render_uncertainty_response

    _, world, _session, _, _, _ = _dummy_state()
    uncertainty = classify_uncertainty(
        "Where did they take the patrol report?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session={"active_scene_id": "frontier_gate"},
        world=world,
        resolution=None,
        speaker_identity={"role": "narrator"},
    )
    text = render_uncertainty_response(uncertainty)

    assert uncertainty["speaker"]["role"] == "narrator"
    assert "captain veyra" not in text.lower()
    assert '"' not in text
    _assert_local_anchor(text)


def test_uncertainty_source_modes_render_distinct_voice_and_shape():
    from game.gm import classify_uncertainty, render_uncertainty_response

    _, world, session, _, _, _ = _dummy_state()

    npc_uncertainty = classify_uncertainty(
        "Who is behind this?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution={
            "kind": "question",
            "social": {"social_intent_class": "social_exchange", "npc_id": "guard_captain", "npc_name": "Captain Veyra"},
        },
    )
    npc_text = render_uncertainty_response(npc_uncertainty)
    assert npc_uncertainty["source"] == "npc_ignorance"
    assert "captain veyra" in npc_text.lower()
    assert '"' in npc_text

    scene_uncertainty = classify_uncertainty(
        "Who is behind this?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session={"active_scene_id": "frontier_gate"},
        world=world,
        resolution=None,
        speaker_identity={"role": "narrator"},
    )
    scene_text = render_uncertainty_response(scene_uncertainty)
    assert scene_uncertainty["source"] == "scene_ambiguity"
    assert '"' not in scene_text
    assert "captain veyra" not in scene_text.lower()

    procedural_uncertainty = classify_uncertainty(
        "How far away is he?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution={
            "kind": "adjudication_query",
            "requires_check": True,
            "check_request": {"requires_check": True, "skill": "perception", "reason": "line of sight"},
            "adjudication": {"answer_type": "needs_concrete_action"},
        },
    )
    procedural_text = render_uncertainty_response(procedural_uncertainty)
    assert procedural_uncertainty["source"] == "procedural_insufficiency"
    assert procedural_uncertainty["category"] == "unknown_quantity"
    assert len(procedural_text.strip()) > 12
    assert procedural_text.strip()[-1] in ".!?"


def test_social_exchange_uncertainty_stays_npc_grounded_on_repeated_questions():
    from game.gm import classify_uncertainty, render_uncertainty_response

    _, world, session, _, _, _ = _dummy_state()
    resolution = {
        "kind": "question",
        "social": {"social_intent_class": "social_exchange", "npc_id": "guard_captain", "npc_name": "Captain Veyra"},
    }
    for prompt in ("Who hit them?", "Who ordered it?", "Who is behind this?"):
        uncertainty = classify_uncertainty(
            prompt,
            scene_envelope=FRONTIER_GATE_SCENE,
            session=session,
            world=world,
            resolution=resolution,
        )
        text = render_uncertainty_response(uncertainty)
        low = text.lower()
        assert uncertainty["source"] == "npc_ignorance"
        assert "captain veyra" in low
        assert '"' in text


def test_uncertainty_questions_in_same_scene_render_different_contextual_answers():
    from game.gm import classify_uncertainty, render_uncertainty_response

    _, world, session, _, _, _ = _dummy_state()
    questions = [
        "Who is behind this?",
        "Where did they take it?",
        "Why would they risk this?",
    ]
    rendered = []
    for question in questions:
        uncertainty = classify_uncertainty(
            question,
            scene_envelope=FRONTIER_GATE_SCENE,
            session=session,
            world=world,
            resolution={"kind": "question", "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra"}},
        )
        text = render_uncertainty_response(uncertainty)
        rendered.append(text)
        _assert_uncertainty_render_helper_contract(text)
        _assert_local_anchor(text)
        _assert_actionable_lead(text)

    assert len(set(rendered)) == len(rendered)


def test_contextual_lead_rotates_away_from_repeated_board_when_other_live_leads_exist():
    from game.gm import choose_contextual_lead

    selected = choose_contextual_lead(
        {
            "category": "unknown_location",
            "scene_snapshot": {
                "location": "Cinderwatch Gate District",
                "visible_facts": [
                    "A tattered watcher near the tavern entrance keeps one eye on the gate.",
                    "Nearby guards react sharply to every mention of the missing patrol.",
                    "A notice board lists new taxes, curfews, and a missing patrol.",
                ],
                "other_npc_names": [],
                "pending_leads": [],
                "has_notice_board": True,
                "has_missing_patrol": True,
                "has_refugees": True,
                "has_tax_or_curfew": True,
                "exit_label": "",
            },
            "turn_context": {"player_text": "Where should I start?"},
        },
        recent_leads=[
            {
                "key": "notice_board",
                "kind": "notice_board",
                "subject": "the notice board",
                "position": "",
                "named": False,
                "positioned": False,
            }
        ],
        current_speaker={"role": "narrator", "name": ""},
        player_prompt="Where should I start?",
    )

    assert selected["key"] != "notice_board"
    assert "notice board" not in selected["lead_text"].lower()
    assert any(term in selected["lead_text"].lower() for term in ("tattered watcher", "guards", "missing patrol"))


def test_contextual_lead_preserves_recent_named_follow_up():
    from game.gm import choose_contextual_lead

    selected = choose_contextual_lead(
        {
            "category": "unknown_location",
            "scene_snapshot": {
                "location": "Cinderwatch Gate District",
                "visible_facts": [
                    "A notice board lists new taxes, curfews, and a missing patrol.",
                    "Nearby guards watch the crowd.",
                ],
                "other_npc_names": ["Captain Veyra"],
                "pending_leads": [],
                "has_notice_board": True,
                "has_missing_patrol": True,
                "has_refugees": True,
                "has_tax_or_curfew": True,
                "exit_label": "",
            },
            "turn_context": {"player_text": "Where do I find that person?"},
        },
        recent_leads=[
            {
                "key": "lady-misia-near-the-tavern-entrance",
                "kind": "recent_named_figure",
                "subject": "Lady Misia",
                "position": "near the tavern entrance",
                "named": True,
                "positioned": True,
            }
        ],
        current_speaker={"role": "npc", "name": "Captain Veyra"},
        player_prompt="Where do I find that person?",
    )

    assert selected["subject"] == "Lady Misia"
    assert "lady misia" in selected["lead_text"].lower()
    assert "tavern entrance" in selected["lead_text"].lower()


def test_contextual_lead_prefers_engaged_npc_over_notice_board():
    from game.gm import choose_contextual_lead

    selected = choose_contextual_lead(
        {
            "category": "unknown_identity",
            "scene_snapshot": {
                "location": "Cinderwatch Gate District",
                "visible_facts": [
                    "A notice board lists new taxes, curfews, and a missing patrol.",
                ],
                "other_npc_names": ["Lady Misia"],
                "pending_leads": [],
                "has_notice_board": True,
                "has_missing_patrol": True,
                "has_refugees": False,
                "has_tax_or_curfew": True,
                "exit_label": "",
            },
            "turn_context": {"player_text": "Who should I press first?"},
        },
        recent_leads=[],
        current_speaker={"role": "npc", "name": "Captain Veyra"},
        player_prompt="Who should I press first?",
    )

    assert selected["subject"] == "Captain Veyra"
    assert selected["lead_text"].startswith("Press Captain Veyra")


def test_remember_recent_contextual_leads_extracts_named_and_positioned_live_leads():
    from game.gm import remember_recent_contextual_leads

    session = {"scene_runtime": {}, "turn_counter": 3}
    remembered = remember_recent_contextual_leads(
        session,
        "frontier_gate",
        "Lady Misia waits near the tavern entrance while nearby guards watch the missing patrol notice.",
    )

    assert any(entry["subject"] == "Lady Misia" and entry["position"] == "near the tavern entrance" for entry in remembered)
    assert any("missing patrol" in entry["subject"].lower() or "guards" in entry["subject"].lower() for entry in remembered)


def test_known_fact_guard_resolves_recent_named_follow_up_before_uncertainty():
    from game.gm import build_messages, classify_uncertainty, render_uncertainty_response, resolve_known_fact_before_uncertainty
    from game.storage import get_scene_runtime

    campaign, world, session, character, combat, recent_log = _dummy_state()
    session_no_active = {
        "scene_runtime": {
            "frontier_gate": {
                "recent_contextual_leads": [
                    {
                        "key": "lady-misia-near-the-tavern-entrance",
                        "kind": "recent_named_figure",
                        "subject": "Lady Misia",
                        "position": "near the tavern entrance",
                        "named": True,
                        "positioned": True,
                    }
                ]
            }
        },
        "interaction_context": dict(session.get("interaction_context") or {}),
    }
    resolution = {
        "kind": "question",
        "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "reply_kind": "answer"},
    }

    known = resolve_known_fact_before_uncertainty(
        "Where do I find that person?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session_no_active,
        world=world,
        resolution=resolution,
    )
    assert known is not None
    _assert_text_contains_all(known["text"], "lady", "misia", "tavern")
    assert known["source"] == "recent_dialogue_continuity"

    uncertainty = classify_uncertainty(
        "Where do I find that person?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session_no_active,
        world=world,
        resolution=resolution,
    )
    assert uncertainty["category"] == ""
    rendered = render_uncertainty_response(uncertainty)
    _assert_text_contains_all(rendered, "lady", "misia", "tavern")
    assert rendered.strip() == known["text"].strip()

    scene_rt = get_scene_runtime(session_no_active, "frontier_gate")
    msgs = build_messages(
        campaign,
        world,
        session_no_active,
        character,
        FRONTIER_GATE_SCENE,
        combat,
        recent_log,
        "Where do I find that person?",
        resolution,
        scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    assert payload["uncertainty_hint"] is None
    kah = (payload.get("known_answer_hint") or {}).get("text") or ""
    _assert_text_contains_all(kah, "lady", "misia", "tavern")
    assert kah.strip() == known["text"].strip()


def test_known_fact_guard_resolves_explicit_location_clue_before_uncertainty():
    from game.gm import classify_uncertainty, render_uncertainty_response, resolve_known_fact_before_uncertainty

    _, world, session, _, _, _ = _dummy_state()
    known = resolve_known_fact_before_uncertainty(
        "Where are the refugees?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
    )
    assert known is not None
    _assert_text_contains_all(known["text"], "refugees", "muddy", "road")
    assert known["source"] == "observable_scene_fact"

    uncertainty = classify_uncertainty(
        "Where are the refugees?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
    )
    assert uncertainty["category"] == ""
    rendered = render_uncertainty_response(uncertainty)
    _assert_text_contains_all(rendered, "refugees", "muddy", "road")
    assert rendered.strip() == known["text"].strip()


def test_known_fact_guard_resolves_observable_scene_fact_before_uncertainty():
    from game.gm import classify_uncertainty, render_uncertainty_response, resolve_known_fact_before_uncertainty

    _, world, session, _, _, _ = _dummy_state()
    known = resolve_known_fact_before_uncertainty(
        "What is on the notice board?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
    )
    assert known is not None
    _assert_text_contains_all(known["text"], "notice", "board", "patrol")
    assert known["source"] == "observable_scene_fact"

    uncertainty = classify_uncertainty(
        "What is on the notice board?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
    )
    assert uncertainty["category"] == ""
    rendered = render_uncertainty_response(uncertainty)
    _assert_text_contains_all(rendered, "notice", "board", "patrol")
    assert rendered.strip() == known["text"].strip()


def test_guard_blocks_discoverable_clue_when_not_justified():
    from game.gm import guard_gm_output

    clue = FRONTIER_GATE_SCENE["scene"]["discoverable_clues"][0]
    gm = {
        "player_facing_text": f"You immediately notice: {clue}",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = guard_gm_output(gm, FRONTIER_GATE_SCENE, "What do I notice immediately?", [])
    assert out["player_facing_text"] != gm["player_facing_text"]


def test_guard_allows_discoverable_clue_when_justified():
    from game.gm import guard_gm_output

    clue = FRONTIER_GATE_SCENE["scene"]["discoverable_clues"][0]
    gm = {
        "player_facing_text": f"As you investigate carefully, you notice: {clue}",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = guard_gm_output(gm, FRONTIER_GATE_SCENE, "I investigate the area carefully.", [])
    assert out["player_facing_text"] == gm["player_facing_text"]


def test_npc_response_contract_enforces_specificity_on_direct_question():
    from game.gm import enforce_npc_response_contract

    campaign, world, session, character, combat, recent_log = _dummy_state()
    _ = campaign, character, combat, recent_log
    gm = {
        "player_facing_text": "These are dangerous times. Be careful who you trust.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    resolution = {
        "kind": "question",
        "social": {
            "npc_id": "guard_captain",
            "npc_name": "Captain Veyra",
            "npc_reply_expected": True,
            "reply_kind": "answer",
        },
    }
    out = enforce_npc_response_contract(
        gm,
        player_text="Where can I find the missing patrol report?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=resolution,
    )
    assert "npc_response_contract" in out.get("tags", [])
    assert "Next step:" in out.get("player_facing_text", "")


def test_npc_response_contract_does_not_apply_without_question():
    from game.gm import enforce_npc_response_contract

    campaign, world, session, character, combat, recent_log = _dummy_state()
    _ = campaign, character, combat, recent_log
    gm = {
        "player_facing_text": "The captain watches you for a long moment, saying nothing.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = enforce_npc_response_contract(
        gm,
        player_text="I wait.",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution={"kind": "social_probe", "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra"}},
    )
    assert out["player_facing_text"] == gm["player_facing_text"]
    assert "npc_response_contract" not in out.get("tags", [])


# --- Resolved exploration context tests ---


def test_build_messages_includes_resolved_exploration_context():
    """build_messages adds resolved_exploration_action, resolution_kind, scene_transition_already_occurred when resolution is exploration."""
    from game.gm import build_messages
    from game.storage import get_scene_runtime

    campaign, world, session, character, combat, recent_log = _dummy_state()
    scene_rt = get_scene_runtime({"scene_runtime": {}}, "frontier_gate")
    resolution = {
        "kind": "observe",
        "action_id": "observe-area",
        "label": "Observe the area",
        "prompt": "I look around.",
        "resolved_transition": False,
        "target_scene_id": None,
        "hint": "Player is focusing on observing.",
    }
    msgs = build_messages(
        campaign, world, session, character, FRONTIER_GATE_SCENE,
        combat, recent_log, "I look around.", resolution, scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    assert "resolved_exploration_action" in payload
    assert payload["resolved_exploration_action"]["id"] == "observe-area"
    assert payload["resolved_exploration_action"]["type"] == "observe"
    assert payload["resolution_kind"] == "observe"
    assert payload["scene_transition_already_occurred"] is False
    assert "resolution_summary" in payload


def test_build_messages_exploration_with_transition_includes_originating_scene():
    """When scene transition occurred, payload includes originating_scene_id and scene_transition_already_occurred."""
    from game.gm import build_messages
    from game.storage import get_scene_runtime

    campaign, world, session, character, combat, recent_log = _dummy_state()
    # Simulate post-transition: session now has active_scene_id = destination (build_messages loads from session)
    session["active_scene_id"] = "market_quarter"
    scene_rt = get_scene_runtime({"scene_runtime": {}}, "market_quarter")
    resolution = {
        "kind": "scene_transition",
        "action_id": "go-market",
        "label": "Go: Market",
        "prompt": "I go to the market.",
        "resolved_transition": True,
        "target_scene_id": "market_quarter",
        "originating_scene_id": "frontier_gate",
        "hint": "Player has moved to scene market_quarter.",
    }
    market_scene = {
        "scene": {
            "id": "market_quarter",
            "location": "Cinderwatch Market",
            "summary": "Canvases snap in the wind.",
            "mode": "exploration",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    msgs = build_messages(
        campaign, world, session, character, market_scene,
        combat, recent_log, "I go to the market.", resolution, scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    assert payload["resolved_exploration_action"]["target_scene_id"] == "market_quarter"
    assert payload["scene_transition_already_occurred"] is True
    assert payload["originating_scene_id"] == "frontier_gate"
    assert "market_quarter" in payload["resolution_summary"]


def test_build_messages_exploration_instructions_no_restate():
    """Exploration instructions explicitly mention not restating the previous scene after resolved transition."""
    from game.gm import build_messages
    from game.storage import get_scene_runtime

    campaign, world, session, character, combat, recent_log = _dummy_state()
    scene_rt = get_scene_runtime({"scene_runtime": {}}, "frontier_gate")
    resolution = {
        "kind": "investigate",
        "action_id": "inv",
        "label": "Investigate",
        "prompt": "I investigate the wagon.",
        "resolved_transition": False,
    }
    msgs = build_messages(
        campaign, world, session, character, FRONTIER_GATE_SCENE,
        combat, recent_log, "I investigate.", resolution, scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    instructions = " ".join(payload.get("instructions", [])).lower()
    assert "do not restate the previous scene" in instructions
    assert "resolved_exploration_action" in instructions or "resolved" in instructions
    assert "never repeat the same observation" in instructions


def test_system_prompt_mentions_resolved_exploration():
    """SYSTEM_PROMPT explicitly mentions resolved exploration and not restating previous scene."""
    from game.gm import SYSTEM_PROMPT

    assert "resolved_exploration_action" in SYSTEM_PROMPT or "resolved" in SYSTEM_PROMPT
    assert "do not restate" in SYSTEM_PROMPT
    assert "scene_transition_already_occurred" in SYSTEM_PROMPT
    assert "third person" in SYSTEM_PROMPT.lower()
    assert "quoted in-character speech" in SYSTEM_PROMPT.lower()
    assert "do not restate or paraphrase the player's input" in SYSTEM_PROMPT.lower()
    assert "question resolution rule" in SYSTEM_PROMPT.lower()
    assert "direct answer (first sentence)" in SYSTEM_PROMPT.lower()


def test_question_resolution_rule_enforcement_prepends_uncertain_answer_when_needed():
    from game.gm import enforce_question_resolution_rule

    _, world, session, _, _, _ = _dummy_state()
    gm = {
        "player_facing_text": "Rain slicks the cobbles as the crowd surges around you.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = enforce_question_resolution_rule(
        gm,
        player_text="Where is the missing patrol report?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
    )
    low = out["player_facing_text"].lower()
    assert "captain veyra" in low
    _assert_local_anchor(out["player_facing_text"])
    assert "question_resolution_rule" in out.get("tags", [])
    assert "uncertainty:unknown_location" in out.get("tags", [])
    _assert_actionable_lead(out["player_facing_text"])


@pytest.mark.parametrize(
    "reply_text",
    [
        'Tavern Runner says, "Two cloaked riders hit them near the east road."',
        'The runner shakes his head. "I don\'t know who hit them."',
        "No names have surfaced yet, the runner says.",
        'The runner\'s face tightens. "Ask me that again and I\'m done talking."',
    ],
)
def test_social_exchange_question_first_sentence_contract_accepts_explicit_shapes(reply_text):
    from game.gm import question_resolution_rule_check

    check = question_resolution_rule_check(
        player_text="Who hit them?",
        gm_reply_text=reply_text,
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "runner",
                "npc_name": "Tavern Runner",
            },
        },
    )
    assert check["applies"] is True
    assert check["ok"] is True
    assert check["reasons"] == []


def test_social_exchange_contract_accepts_beat_then_substantive_indirect_answer():
    """Short NPC beat + follow-on counts as explicit; grounding tokens match npc_id slug."""
    from game.gm import question_resolution_rule_check

    check = question_resolution_rule_check(
        player_text="What happened to the missing patrol?",
        gm_reply_text=(
            "The runner frowns. They never came back from the east bend—just rumors after that."
        ),
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "tavern_runner",
                "npc_name": "The runner",
            },
        },
    )
    assert check["applies"] is True
    assert check["ok"] is True
    assert check["reasons"] == []


def test_social_exchange_contract_accepts_leading_dialogue_without_name_prefix():
    from game.gm import question_resolution_rule_check

    check = question_resolution_rule_check(
        player_text="Any idea who attacked them?",
        gm_reply_text='"Couldn\'t tell you—only rumors from the road."',
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "runner",
                "npc_name": "Tavern Runner",
            },
        },
    )
    assert check["applies"] is True
    assert check["ok"] is True


def test_opening_echo_skips_when_reply_leads_with_dialogue():
    from game.gm import opening_sentence_echoes_player_input

    player = "What happened to the missing patrol?"
    reply = '"Patrol never made the rendezvous," the runner mutters. "I heard riders, not names."'
    assert opening_sentence_echoes_player_input(reply, player) is False


def test_social_exchange_question_first_sentence_contract_rejects_atmospheric_opener():
    from game.gm import question_resolution_rule_check

    check = question_resolution_rule_check(
        player_text="Who hit them?",
        gm_reply_text=(
            "The truth is still buried beneath rumor and rain. "
            "The runner glances away and avoids your eyes."
        ),
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "runner",
                "npc_name": "Tavern Runner",
            },
        },
    )
    assert check["applies"] is True
    assert check["ok"] is False
    assert "question_rule:social_exchange_first_sentence_not_speaker_grounded" in check["reasons"]
    assert "question_rule:social_exchange_first_sentence_not_substantive_answer" in check["reasons"]


def test_detect_retry_failures_flags_social_exchange_first_sentence_contract():
    from game.gm import detect_retry_failures

    _, world, session, _, _, _ = _dummy_state()
    failures = detect_retry_failures(
        player_text="Who hit them?",
        gm_reply={
            "player_facing_text": "Around you, small details sharpen into clues as the gate crowd churns.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        },
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "guard_captain",
                "npc_name": "Captain Veyra",
            },
        },
    )
    unresolved = next((f for f in failures if f.get("failure_class") == "unresolved_question"), None)
    assert unresolved is not None
    reasons = unresolved.get("reasons") or []
    assert "question_rule:social_exchange_first_sentence_not_speaker_grounded" in reasons
    assert "question_rule:social_exchange_first_sentence_not_substantive_answer" in reasons


def test_retry_prompt_warns_against_known_gate_failure_shapes():
    """Anti-railroading strings in retry guidance (canonical owner: messages-to-model, not transcript harness)."""
    from game.gm import build_retry_prompt_for_failure

    p = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=None,
    ).lower()
    assert "meta-story gravity" in p or "the story wants" in p
    assert "forced conclusions" in p or "obvious you must" in p
    assert "you head straight" not in p
    assert "so you go there" not in p


def test_retry_prompt_multi_lead_and_urgency_language():
    """Retry instructions stay agency-safe under multiple leads and time pressure (same owner as gate-failure shapes)."""
    from game.gm import build_retry_prompt_for_failure

    gm = {
        "anti_railroading_contract": {
            "enabled": True,
            "forbid_player_decision_override": True,
            "forbid_forced_direction": True,
            "forbid_exclusive_path_claims_without_basis": True,
            "forbid_lead_to_plot_gravity_upgrade": True,
            "allow_directional_language_from_resolved_transition": False,
            "allow_exclusivity_from_authoritative_resolution": False,
            "allow_commitment_language_when_player_explicitly_committed": False,
            "surfaced_lead_ids": ["lead_patrol", "lead_river", "lead_gate"],
            "surfaced_lead_labels": [],
        }
    }
    for fc, extra in (
        ("scene_stall", {}),
        (
            "topic_pressure_escalation",
            {"topic_context": {"topic_key": "patrol", "repeat_count": 3, "previous_answer_snippet": "Maybe."}},
        ),
    ):
        failure: dict = {"failure_class": fc, **extra}
        p = build_retry_prompt_for_failure(failure, response_policy=None, gm_output=gm).lower()
        assert "without choosing for the player" in p
        assert "the story wants" in p
        if fc == "topic_pressure_escalation":
            assert "forced pathing" in p
        if fc == "scene_stall":
            assert "multiple leads are in play" in p


def test_retry_prompt_for_social_exchange_first_sentence_failure_requests_substantive_shape():
    from game.gm import build_retry_prompt_for_failure

    prompt = build_retry_prompt_for_failure(
        {
            "failure_class": "unresolved_question",
            "reasons": [
                "question_rule:social_exchange_first_sentence_not_speaker_grounded",
                "question_rule:social_exchange_first_sentence_not_substantive_answer",
            ],
            "uncertainty_category": "unknown_identity",
            "uncertainty_context": {
                "speaker": {"role": "npc", "name": "Captain Veyra"},
                "scene_snapshot": {"location": "Cinderwatch Gate District"},
            },
        }
    )
    low = prompt.lower()
    assert "retry target: unresolved_question." in low
    assert "sentence one must directly answer" in low
    assert "social exchange contract" in low
    assert "speaker-grounded and substantive" in low


def test_social_exchange_natural_warning_passes_question_rule():
    from game.gm import question_resolution_rule_check

    check = question_resolution_rule_check(
        player_text="Anyone I should steer clear of for sure?",
        gm_reply_text=(
            "Tavern Runner doesn't look at you. "
            "Keep clear of House Verevin's bailiffs by the east crossroads—people vanish near that stretch."
        ),
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "tavern_runner",
                "npc_name": "Tavern Runner",
            },
        },
    )
    assert check["applies"] is True
    assert check["ok"] is True
    assert check.get("social_answer_validation_mode") == "substantive_content"
    assert check.get("first_sentence_substantive") is True
    assert check.get("rejected_as_cinematic_nonanswer") is False


def test_social_exchange_natural_directional_passes_question_rule():
    from game.gm import question_resolution_rule_check

    check = question_resolution_rule_check(
        player_text="Where shouldn't I go tonight?",
        gm_reply_text='Tavern Runner says, "Watch out for the mill yard after dark—best not cross Verevin\'s riders there."',
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "tavern_runner",
                "npc_name": "Tavern Runner",
            },
        },
    )
    assert check["applies"] is True
    assert check["ok"] is True


def test_social_exchange_cinematic_interruption_fails_question_rule():
    from game.gm import question_resolution_rule_check

    check = question_resolution_rule_check(
        player_text="Who should I avoid?",
        gm_reply_text=(
            "Tavern Runner starts to answer, then pauses as shouting breaks out by the gate."
        ),
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "tavern_runner",
                "npc_name": "Tavern Runner",
            },
        },
    )
    assert check["applies"] is True
    assert check["ok"] is False
    assert "question_rule:social_exchange_first_sentence_not_substantive_answer" in check["reasons"]
    assert check.get("rejected_as_cinematic_nonanswer") is True


def test_is_valid_social_answer_first_sentence_helper():
    from game.gm import is_valid_social_answer_first_sentence

    assert is_valid_social_answer_first_sentence("Keep clear of House Verevin's men by the crossroads.") is True
    assert is_valid_social_answer_first_sentence("Watch out for riders on the east road.") is True
    assert is_valid_social_answer_first_sentence("Tavern Runner starts to answer, then pauses.") is False
    assert is_valid_social_answer_first_sentence("For a moment the scene holds, unreadable.") is False
    assert is_valid_social_answer_first_sentence("") is False


def test_social_exchange_short_substantive_answer_passes_question_rule():
    from game.gm import question_resolution_rule_check

    check = question_resolution_rule_check(
        player_text="Any names I should know?",
        gm_reply_text='Tavern Runner mutters, "Don\'t trust the night clerk at the Crown."',
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "tavern_runner",
                "npc_name": "Tavern Runner",
            },
        },
    )
    assert check["applies"] is True
    assert check["ok"] is True


def test_validator_voice_detection_matches_forbidden_patterns():
    from game.gm import detect_validator_voice

    text = (
        "I can't answer that right now. "
        "Based on what's established, we can determine only a little. "
        "As an AI, I don't have access to the tools. "
        "By the rules, that would require a roll."
    )
    hits = detect_validator_voice(text)
    assert "validator_voice:cant_answer_that" in hits
    assert "validator_voice:based_on_established" in hits
    assert "validator_voice:we_can_determine" in hits
    assert "validator_voice:as_an_ai" in hits
    assert "validator_voice:tool_access" in hits
    assert "validator_voice:rules_explanation" in hits


def test_validator_voice_enforcement_rewrites_system_tone():
    from game.gm import detect_validator_voice, enforce_no_validator_voice

    _, world, session, _, _, _ = _dummy_state()
    gm = {
        "player_facing_text": (
            "I can't answer that. Based on what's established, we can determine very little."
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = enforce_no_validator_voice(
        gm,
        scene_envelope=FRONTIER_GATE_SCENE,
        player_text="Where is the patrol report?",
    )
    assert out["player_facing_text"].strip() != gm["player_facing_text"].strip()
    assert detect_validator_voice(out["player_facing_text"]) == []
    assert "validator_voice_rewrite" in out.get("tags", [])
    assert "uncertainty:unknown_location" in out.get("tags", [])


def test_validator_voice_enforcement_keeps_clean_diegetic_sentences_when_possible():
    from game.gm import detect_validator_voice, enforce_no_validator_voice

    gm = {
        "player_facing_text": (
            "As an AI, I don't have access to that. "
            "Rain beads on the east gate while refugees keep glancing toward the checkpoint."
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = enforce_no_validator_voice(
        gm,
        scene_envelope=FRONTIER_GATE_SCENE,
        player_text="Describe the gate.",
    )
    low = out["player_facing_text"].lower()
    assert detect_validator_voice(out["player_facing_text"]) == []
    assert "rain beads on the east gate" in low
    assert "validator_voice_rewrite" in out.get("tags", [])


def test_opening_sentence_echo_detection():
    from game.gm import opening_sentence_echoes_player_input, opening_sentence_overlaps_player_quote

    echoed = opening_sentence_echoes_player_input(
        "Galinor steps into the gate and looks around before speaking.",
        "Galinor steps into the gate and looks around.",
    )
    assert echoed is True

    forward_progress = opening_sentence_echoes_player_input(
        "Rain slicks the stone beneath his boots as the crowd presses in.",
        "Galinor steps into the gate and looks around.",
    )
    assert forward_progress is False

    quoted_echo = opening_sentence_overlaps_player_quote(
        '"Footman? I require an audience," Galinor calls out at the gate.',
        'Galinor says, "Footman? I require an audience."',
    )
    assert quoted_echo is True

    quoted_reaction = opening_sentence_overlaps_player_quote(
        "His demand carries through the entry hall with practiced authority.",
        'Galinor says, "Footman? I require an audience."',
    )
    assert quoted_reaction is False


def test_prompt_includes_explicit_spoken_line_no_repeat_instruction():
    from game.gm import build_messages
    from game.storage import get_scene_runtime

    campaign, world, session, character, combat, recent_log = _dummy_state()
    scene_rt = get_scene_runtime({"scene_runtime": {}}, "frontier_gate")
    msgs = build_messages(
        campaign,
        world,
        session,
        character,
        FRONTIER_GATE_SCENE,
        combat,
        recent_log,
        'Galinor says, "Footman? I require an audience."',
        None,
        scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    instructions = " ".join(payload.get("instructions", []))
    assert "Do not repeat the player's spoken line. React to it instead." in instructions


def test_stock_warning_filler_repetition_detection():
    from game.gm import detect_stock_warning_filler_repetition

    clustered = detect_stock_warning_filler_repetition(
        "Be careful who you trust. Keep your wits about you."
    )
    assert bool(clustered) is True

    repeated = detect_stock_warning_filler_repetition(
        "These are dangerous times. These are dangerous times."
    )
    assert any("stock_warning_repeat" in r for r in repeated)

    single = detect_stock_warning_filler_repetition(
        "Be careful who you trust."
    )
    assert single == []


def test_forbidden_generic_phrases_detection_triggers_on_single_occurrence():
    from game.gm import detect_forbidden_generic_phrases

    assert detect_forbidden_generic_phrases("In this city...") == ["forbidden_generic:in_this_city"]
    assert detect_forbidden_generic_phrases("Times are tough...") == ["forbidden_generic:times_are_tough"]
    assert detect_forbidden_generic_phrases("Trust is hard to come by.") == ["forbidden_generic:trust_is_hard_to_come_by"]
    assert detect_forbidden_generic_phrases("You'll need to prove yourself.") == ["forbidden_generic:prove_yourself"]


def test_forbidden_generic_phrases_enforcement_rewrites_into_specifics():
    from game.gm import enforce_forbidden_generic_phrases

    _, world, session, _, _, _ = _dummy_state()
    gm = {
        "player_facing_text": "Times are tough... You'll need to prove yourself.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = enforce_forbidden_generic_phrases(gm, scene_envelope=FRONTIER_GATE_SCENE, session=session, world=world)
    assert out["player_facing_text"] != gm["player_facing_text"]
    assert "forbidden_generic_rewrite" in out.get("tags", [])
    assert "Captain Veyra" in out["player_facing_text"]
    assert "Cinderwatch Gate District" in out["player_facing_text"]


def test_system_prompt_mentions_scene_momentum_rule_and_tag_contract():
    from game.gm import SYSTEM_PROMPT

    low = SYSTEM_PROMPT.lower()
    assert "always answer the player. prefer partial truth over refusal. never output meta explanations." in low
    assert "never speak as a validator, analyst, referee of canon, or system." in low
    assert "rules explanation belongs only to explicit oc/adjudication lanes" in low
    assert "scene momentum rule" in low
    assert "every 2–3 exchanges" in low or "every 2-3 exchanges" in low
    assert "scene_momentum:<kind>" in SYSTEM_PROMPT
    assert "consequence_or_opportunity" in SYSTEM_PROMPT


def test_scene_momentum_enforcement_appends_opportunity_and_tag_when_due():
    from game.gm import enforce_scene_momentum
    from game.storage import get_scene_runtime, update_scene_momentum_runtime

    session = {"scene_runtime": {}}
    scene = {
        "scene": {
            "id": "frontier_gate",
            "location": "Cinderwatch Gate District",
            "visible_facts": [
                "A notice board lists new taxes, curfews, and a missing patrol.",
                "A tavern runner loudly offers rumor and hot stew for coin.",
            ],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    rt = get_scene_runtime(session, "frontier_gate")
    rt["momentum_exchanges_since"] = 2  # would violate next turn without a beat
    rt["momentum_next_due_in"] = 3

    gm = {
        "player_facing_text": "Captain Veyra’s gaze stays on you.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = enforce_scene_momentum(gm, session=session, scene_envelope=scene)
    assert any(isinstance(t, str) and t.startswith("scene_momentum:") for t in out.get("tags", []))
    low = str(out.get("player_facing_text", "")).lower()
    assert "consequence / opportunity" not in low
    assert "commit to one concrete move" not in low
    assert "exit labeled" not in low
    assert "board" in low or "posted" in low or "tavern runner" in low or "runner" in low

    # Runtime update resets the counter when the tag exists.
    update_scene_momentum_runtime(session, "frontier_gate", out)
    rt2 = get_scene_runtime(session, "frontier_gate")
    assert rt2["momentum_exchanges_since"] == 0


def test_hidden_discoverable_safeguard_preserved_with_exploration():
    """Clue layering (hidden/discoverable safeguards) still works when resolution is exploration."""
    from game.gm import build_messages, guard_gm_output
    from game.storage import get_scene_runtime

    campaign, world, session, character, combat, recent_log = _dummy_state()
    # Avoid session.active_scene_id forcing a load from disk; tests need controlled scene content.
    session_no_active = {
        "scene_runtime": {},
        "interaction_context": dict(session.get("interaction_context") or {}),
    }
    scene_rt = get_scene_runtime({"scene_runtime": {}}, "frontier_gate")
    resolution = {
        "kind": "observe",
        "action_id": "observe",
        "label": "Observe",
        "prompt": "Look around.",
        "resolved_transition": False,
    }
    msgs = build_messages(
        campaign, world, session_no_active, character, FRONTIER_GATE_SCENE,
        combat, recent_log, "Look around.", resolution, scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    # "Look around." does not justify discoverable clues => must be empty
    assert payload["scene"]["discoverable_clues"] == []
    assert payload["scene"]["gm_only"]["hidden_facts"] == FRONTIER_GATE_SCENE["scene"]["hidden_facts"]
    # Guard still blocks hidden fact leak
    leaky_gm = {
        "player_facing_text": "An agent of a noble house watches you.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = guard_gm_output(leaky_gm, FRONTIER_GATE_SCENE, "Look around.", [])
    assert out["player_facing_text"] != leaky_gm["player_facing_text"]


def test_rule_priority_prefers_bounded_answer_before_specificity():
    from game.gm import apply_response_policy_enforcement, detect_validator_voice
    from game.prompt_context import build_response_policy

    _, world, session, _, _, _ = _dummy_state()
    gm = {
        "player_facing_text": "Trust is hard to come by.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = apply_response_policy_enforcement(
        gm,
        response_policy=build_response_policy(),
        player_text="Who signed the order?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution={
            "kind": "question",
            "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "npc_reply_expected": True},
        },
        discovered_clues=[],
    )
    low = out["player_facing_text"].lower()
    assert "forbidden_generic_rewrite" in out.get("tags", [])
    assert detect_validator_voice(out["player_facing_text"]) == []
    assert "captain veyra" in low
    _assert_local_anchor(out["player_facing_text"])


def test_rule_priority_answers_without_leaking_hidden_facts():
    from game.gm import apply_response_policy_enforcement, detect_validator_voice
    from game.prompt_context import build_response_policy

    _, world, session, _, _, _ = _dummy_state()
    gm = {
        "player_facing_text": "An agent of a noble house is watching new arrivals for a smuggler contact looking for magical talent.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = apply_response_policy_enforcement(
        gm,
        response_policy=build_response_policy(),
        player_text="Who is really watching the new arrivals?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution={
            "kind": "question",
            "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "npc_reply_expected": True},
        },
        discovered_clues=[],
    )
    low = out["player_facing_text"].lower()
    assert "noble house" not in low
    assert "smuggler" not in low
    assert "magical talent" not in low
    assert "captain veyra" in low
    _assert_local_anchor(out["player_facing_text"])
    assert detect_validator_voice(out["player_facing_text"]) == []


def test_rule_priority_keeps_momentum_when_certainty_is_incomplete():
    from game.gm import apply_response_policy_enforcement, detect_validator_voice
    from game.prompt_context import build_response_policy
    from game.storage import get_scene_runtime

    _, world, session, _, _, _ = _dummy_state()
    scene_rt = get_scene_runtime(session, "frontier_gate")
    scene_rt["momentum_exchanges_since"] = 2
    scene_rt["momentum_next_due_in"] = 3
    gm = {
        "player_facing_text": "I can't answer that.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = apply_response_policy_enforcement(
        gm,
        response_policy=build_response_policy(narration_obligations={"scene_momentum_due": True}),
        player_text="Where did the patrol go?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
        discovered_clues=[],
    )
    low = out["player_facing_text"].lower()
    assert "captain veyra" in low
    _assert_local_anchor(out["player_facing_text"])
    assert detect_validator_voice(out["player_facing_text"]) == []
    assert any(isinstance(tag, str) and tag.startswith("scene_momentum:") for tag in out.get("tags", []))


def test_normalize_topic_clusters_semantic_variants():
    from game.gm import normalize_topic

    scene_ctx = FRONTIER_GATE_SCENE["scene"]
    assert normalize_topic("What happened to the missing patrol?", scene_ctx) == "missing_patrol"
    assert normalize_topic("Did anyone see those shadowy figures?", scene_ctx) == "shadowy_figures"
    assert normalize_topic("Who is behind this attack?", scene_ctx) == "responsible_party"
    assert normalize_topic("What happened at the crossroads last night?", scene_ctx) == "crossroads_incident"


def test_topic_pressure_triggers_escalation_by_third_low_progress_probe():
    from game.gm import _commit_topic_progress, detect_retry_failures, register_topic_probe

    _, world, session, _, _, _ = _dummy_state()
    resolution = {
        "kind": "question",
        "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "npc_reply_expected": True},
    }
    stale_reply = {
        "player_facing_text": (
            "Captain Veyra lowers her voice. Rumor says the crossroads were bad last night, "
            "but no one here can give you names yet and whispers keep circling the same uncertainty."
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    prompts = [
        "What happened at the crossroads?",
        "Who attacked them at the crossroads?",
        "Who is behind the crossroads attack?",
    ]
    seen_pressure_failure = False
    for idx, prompt in enumerate(prompts, start=1):
        session["turn_counter"] = idx
        register_topic_probe(
            session=session,
            scene_envelope=FRONTIER_GATE_SCENE,
            player_text=prompt,
            resolution=resolution,
        )
        failures = detect_retry_failures(
            player_text=prompt,
            gm_reply=stale_reply,
            scene_envelope=FRONTIER_GATE_SCENE,
            session=session,
            world=world,
            resolution=resolution,
        )
        has_pressure = any(f.get("failure_class") == "topic_pressure_escalation" for f in failures if isinstance(f, dict))
        if idx < 3:
            assert has_pressure is False
        else:
            assert has_pressure is True
            seen_pressure_failure = True
        _commit_topic_progress(
            session=session,
            scene_envelope=FRONTIER_GATE_SCENE,
            reply_text=stale_reply["player_facing_text"],
        )
    assert seen_pressure_failure is True


def test_topic_pressure_does_not_escalate_when_each_answer_adds_concrete_info():
    from game.gm import apply_response_policy_enforcement, detect_retry_failures, register_topic_probe
    from game.prompt_context import build_response_policy

    _, world, session, _, _, _ = _dummy_state()
    resolution = {
        "kind": "question",
        "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "npc_reply_expected": True},
    }
    turns = [
        (
            "What happened to the patrol?",
            "Captain Veyra says the missing patrol was last seen near the east road milestone before dusk.",
        ),
        (
            "Who attacked them?",
            "Captain Veyra adds that carter Rellan saw two hooded riders peel off toward the old mill road.",
        ),
        (
            "Who is behind it?",
            "Captain Veyra taps a torn dispatch seal marked Ash Cartel and tells you to question Rellan at the mill yard now.",
        ),
    ]
    for idx, (prompt, reply_text) in enumerate(turns, start=1):
        session["turn_counter"] = idx
        register_topic_probe(
            session=session,
            scene_envelope=FRONTIER_GATE_SCENE,
            player_text=prompt,
            resolution=resolution,
        )
        gm = {
            "player_facing_text": reply_text,
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        }
        failures = detect_retry_failures(
            player_text=prompt,
            gm_reply=gm,
            scene_envelope=FRONTIER_GATE_SCENE,
            session=session,
            world=world,
            resolution=resolution,
        )
        assert not any(f.get("failure_class") == "topic_pressure_escalation" for f in failures if isinstance(f, dict))
        apply_response_policy_enforcement(
            gm,
            response_policy=build_response_policy(),
            player_text=prompt,
            scene_envelope=FRONTIER_GATE_SCENE,
            session=session,
            world=world,
            resolution=resolution,
            discovered_clues=[],
        )


def test_topic_pressure_requires_same_target_not_just_same_topic():
    from game.gm import _commit_topic_progress, detect_retry_failures, register_topic_probe

    _, world, session, _, _, _ = _dummy_state()
    stale_reply = {
        "player_facing_text": (
            "Captain Veyra keeps repeating the same rumor: nobody can name who struck the patrol, "
            "and every witness repeats the same uncertainty."
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    turns = [
        (
            1,
            "Who ordered the crossroads hit?",
            {"kind": "question", "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "social_intent_class": "social_exchange"}},
        ),
        (
            2,
            "Who ordered it then?",
            {"kind": "question", "social": {"npc_id": "runner", "npc_name": "Tavern Runner", "social_intent_class": "social_exchange"}},
        ),
        (
            3,
            "Fine, who is behind it?",
            {"kind": "question", "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "social_intent_class": "social_exchange"}},
        ),
    ]

    for idx, prompt, resolution in turns:
        session["turn_counter"] = idx
        register_topic_probe(
            session=session,
            scene_envelope=FRONTIER_GATE_SCENE,
            player_text=prompt,
            resolution=resolution,
        )
        failures = detect_retry_failures(
            player_text=prompt,
            gm_reply=stale_reply,
            scene_envelope=FRONTIER_GATE_SCENE,
            session=session,
            world=world,
            resolution=resolution,
        )
        assert not any(f.get("failure_class") == "topic_pressure_escalation" for f in failures if isinstance(f, dict))
        _commit_topic_progress(
            session=session,
            scene_envelope=FRONTIER_GATE_SCENE,
            reply_text=stale_reply["player_facing_text"],
        )


def test_topic_pressure_does_not_escalate_across_clearly_different_topics():
    from game.gm import _commit_topic_progress, detect_retry_failures, register_topic_probe

    _, world, session, _, _, _ = _dummy_state()
    resolution = {
        "kind": "question",
        "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "social_intent_class": "social_exchange"},
    }
    stale_reply = {
        "player_facing_text": (
            "Captain Veyra keeps her answer thin: the board is noisy, details are incomplete, "
            "and rumors are still too muddy to lock down."
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    prompts = [
        "What happened to the missing patrol?",
        "Did anyone see those shadowy figures?",
        "What happened at the crossroads last night?",
    ]
    for idx, prompt in enumerate(prompts, start=1):
        session["turn_counter"] = idx
        register_topic_probe(
            session=session,
            scene_envelope=FRONTIER_GATE_SCENE,
            player_text=prompt,
            resolution=resolution,
        )
        failures = detect_retry_failures(
            player_text=prompt,
            gm_reply=stale_reply,
            scene_envelope=FRONTIER_GATE_SCENE,
            session=session,
            world=world,
            resolution=resolution,
        )
        assert not any(f.get("failure_class") == "topic_pressure_escalation" for f in failures if isinstance(f, dict))
        _commit_topic_progress(
            session=session,
            scene_envelope=FRONTIER_GATE_SCENE,
            reply_text=stale_reply["player_facing_text"],
        )


def test_topic_pressure_escalation_skipped_for_strict_social_exchange(monkeypatch):
    """Strict-social turns bypass topic_pressure_escalation so the final emission gate sees the raw candidate."""
    from game.gm import apply_response_policy_enforcement, register_topic_probe
    from game.prompt_context import build_response_policy

    _, world, session, _, _, _ = _dummy_state()
    monkeypatch.setattr("game.gm.enforce_question_resolution_rule", lambda gm, **_kwargs: gm)
    resolution = {
        "kind": "question",
        "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "social_intent_class": "social_exchange"},
    }
    stale_gm = {
        "player_facing_text": (
            "Captain Veyra lowers her voice. Rumor says the crossroads were bad last night, "
            "but no one here can give you names yet and whispers keep circling the same uncertainty."
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    prompts = [
        "Who is behind the crossroads attack?",
        "Who is really behind it?",
        "Who ordered it?",
        "Who funds them?",
    ]
    for idx, prompt in enumerate(prompts, start=1):
        session["turn_counter"] = idx
        register_topic_probe(
            session=session,
            scene_envelope=FRONTIER_GATE_SCENE,
            player_text=prompt,
            resolution=resolution,
        )
        out = apply_response_policy_enforcement(
            dict(stale_gm),
            response_policy=build_response_policy(),
            player_text=prompt,
            scene_envelope=FRONTIER_GATE_SCENE,
            session=session,
            world=world,
            resolution=resolution,
            discovered_clues=[],
        )
        text = str(out.get("player_facing_text") or "")
        low = text.lower()
        tags = out.get("tags") or []
        assert "topic_pressure_escalation" not in tags
        assert "crossroads" in low and "rumor" in low
        assert "captain veyra" in low


def test_apply_response_policy_enforcement_strict_social_bypasses_upstream_narrative_mutators():
    """Strict social: no uncertainty prepend, momentum/pressure, next-step patches, spoiler/validator rewrites, or generic rewrites."""
    from game.gm import apply_response_policy_enforcement
    from game.prompt_context import build_response_policy
    from game.storage import get_scene_runtime

    _, world, session, _, _, _ = _dummy_state()
    resolution = {
        "kind": "question",
        "prompt": "Who signed the order?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
            "npc_name": "Captain Veyra",
            "npc_reply_expected": True,
        },
    }
    scene_rt = get_scene_runtime(session, "frontier_gate")
    scene_rt["momentum_exchanges_since"] = 3
    scene_rt["momentum_next_due_in"] = 2
    scene_rt["passive_action_streak"] = 3
    scene_rt["last_player_action_passive"] = True

    thin_reply = {
        "player_facing_text": "I can't answer that.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = apply_response_policy_enforcement(
        dict(thin_reply),
        response_policy=build_response_policy(),
        player_text="Who signed the order?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=resolution,
        discovered_clues=[],
    )
    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    tags = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert text.strip() == thin_reply["player_facing_text"].strip()
    assert "nothing in the scene" not in low
    assert "if you investigate" not in low
    assert "consequence / opportunity" not in low
    assert "next step:" not in low
    assert "for a breath" not in low
    assert "validator_voice_rewrite" not in tags
    assert "spoiler_guard" not in tags
    assert "scene_momentum:enforced_fallback" not in str(out.get("debug_notes") or "")
    assert "passive_scene_pressure" not in tags
    assert "topic_pressure_escalation" not in tags

    generic_gm = {
        "player_facing_text": "Trust is hard to come by.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out2 = apply_response_policy_enforcement(
        dict(generic_gm),
        response_policy=build_response_policy(),
        player_text="Who signed the order?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=resolution,
        discovered_clues=[],
    )
    assert out2["player_facing_text"] == generic_gm["player_facing_text"]
    assert "forbidden_generic_rewrite" not in (out2.get("tags") or [])

    leaky_gm = {
        "player_facing_text": (
            "An agent of a noble house is watching new arrivals for a smuggler contact looking for magical talent."
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out3 = apply_response_policy_enforcement(
        dict(leaky_gm),
        response_policy=build_response_policy(),
        player_text="Who is really watching the new arrivals?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=resolution,
        discovered_clues=[],
    )
    assert out3["player_facing_text"] == leaky_gm["player_facing_text"]
    assert "spoiler_guard" not in (out3.get("tags") or [])
