import json

import pytest


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


def _assert_bounded_uncertainty(text: str, *, forbidden_terms: tuple[str, ...] = ()) -> None:
    low = text.lower()
    assert "i can't answer" not in low
    assert "i cannot answer" not in low
    assert "based on what's established" not in low
    assert "training data" not in low
    assert "tools" not in low
    assert "best lead:" not in low
    assert "no one here can" not in low
    assert "no one here will" not in low
    assert "the exact place is still blurred" not in low
    assert "the means are still obscured" not in low
    assert "the effect is plain enough" not in low
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
    _assert_bounded_uncertainty(
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
        _assert_bounded_uncertainty(text)
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
    assert known["text"] == "Lady Misia is near the tavern entrance."
    assert known["source"] == "recent_dialogue_continuity"

    uncertainty = classify_uncertainty(
        "Where do I find that person?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session_no_active,
        world=world,
        resolution=resolution,
    )
    assert uncertainty["category"] == ""
    assert render_uncertainty_response(uncertainty) == "Lady Misia is near the tavern entrance."

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
    assert payload["known_answer_hint"]["text"] == "Lady Misia is near the tavern entrance."


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
    assert known["text"] == "Refugees crowd the muddy approach road."
    assert known["source"] == "observable_scene_fact"

    uncertainty = classify_uncertainty(
        "Where are the refugees?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
    )
    assert uncertainty["category"] == ""
    assert render_uncertainty_response(uncertainty) == "Refugees crowd the muddy approach road."


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
    assert known["text"] == "A notice board lists new taxes, curfews, and a missing patrol."
    assert known["source"] == "observable_scene_fact"

    uncertainty = classify_uncertainty(
        "What is on the notice board?",
        scene_envelope=FRONTIER_GATE_SCENE,
        session=session,
        world=world,
        resolution=None,
    )
    assert uncertainty["category"] == ""
    assert render_uncertainty_response(uncertainty) == "A notice board lists new taxes, curfews, and a missing patrol."


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
    from game.gm import enforce_no_validator_voice

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
    low = out["player_facing_text"].lower()
    _assert_bounded_uncertainty(low)
    assert "we can determine" not in low
    assert "validator_voice_rewrite" in out.get("tags", [])
    assert "uncertainty:unknown_location" in out.get("tags", [])


def test_validator_voice_enforcement_keeps_clean_diegetic_sentences_when_possible():
    from game.gm import enforce_no_validator_voice

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
    assert "as an ai" not in low
    assert "don't have access" not in low
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
    assert "Consequence / Opportunity:" in out.get("player_facing_text", "")

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
    from game.gm import apply_response_policy_enforcement
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
    assert "trust is hard to come by" not in out["player_facing_text"].lower()
    assert "captain veyra" in low
    _assert_local_anchor(out["player_facing_text"])


def test_rule_priority_answers_without_leaking_hidden_facts():
    from game.gm import apply_response_policy_enforcement
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
    assert "i can't answer" not in low


def test_rule_priority_keeps_momentum_when_certainty_is_incomplete():
    from game.gm import apply_response_policy_enforcement
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
    assert "i can't answer that" not in out["player_facing_text"].lower()
    assert any(isinstance(tag, str) and tag.startswith("scene_momentum:") for tag in out.get("tags", []))
