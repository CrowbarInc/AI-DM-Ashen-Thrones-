"""Tests for deterministic social resolution engine."""
import pytest
from game.social import (
    resolve_social_action,
    find_npc_by_target,
    parse_social_intent,
    SOCIAL_KINDS,
    apply_interaction_implied_heuristics,
    update_interaction_context_for_non_social,
)
from game.skill_checks import resolve_skill_check
from game.models import SocialEngineResult, social_result_to_dict
from game.storage import get_npc_runtime, get_interaction_context, clear_interaction_context
from game.defaults import default_world, default_character, default_session
from game.interaction_context import (
    rebuild_active_scene_entities,
    resolve_authoritative_social_target,
    set_social_target,
)
from game.storage import load_scene


ENGINE_RESULT_REQUIRED = frozenset({
    "kind", "action_id", "label", "prompt", "success", "resolved_transition",
    "target_scene_id", "clue_id", "discovered_clues", "world_updates", "state_changes", "hint", "social",
})


def _assert_social_result_shape(resolution: dict, expected_kind: str) -> None:
    """Assert resolution conforms to SocialEngineResult engine contract."""
    assert isinstance(resolution, dict)
    assert resolution["kind"] == expected_kind
    for key in ENGINE_RESULT_REQUIRED:
        assert key in resolution, f"Missing key: {key}"
    assert "social" in resolution
    assert isinstance(resolution["social"], dict)
    assert resolution["resolved_transition"] is False
    assert resolution["target_scene_id"] is None


def test_persuade_returns_engine_check_request():
    """Persuade is a social maneuver and should request a check (not auto-resolve)."""
    world = default_world()
    world["npcs"] = [
        {"id": "merchant", "name": "Merchant", "location": "market", "disposition": "neutral"},
    ]
    scene = {"scene": {"id": "market"}}
    session = {}
    character = default_character()
    character["skills"]["diplomacy"] = 20

    action = {
        "id": "persuade-merchant",
        "label": "Persuade the merchant",
        "type": "persuade",
        "prompt": "I persuade the merchant to lower the price.",
        "target_id": "merchant",
        "targetEntityId": "merchant",
    }
    resolution = resolve_social_action(
        scene, session, world, action,
        raw_player_text="Persuade the merchant",
        character=character,
        turn_counter=1,
    )
    _assert_social_result_shape(resolution, "persuade")
    assert resolution["success"] is None
    assert resolution["requires_check"] is True
    assert isinstance(resolution.get("check_request"), dict)
    assert resolution["check_request"]["skill"] == "diplomacy"
    assert "Roll" in (resolution["check_request"]["player_prompt"] or "")
    assert resolution["social"]["target_resolved"] is True
    assert resolution["social"]["npc_id"] == "merchant"
    assert resolution["social"]["social_intent_class"] == "social_maneuver"
    assert "skill_check" not in resolution


def test_intimidate_returns_engine_check_request():
    """Intimidate is a social maneuver and should request a check."""
    world = default_world()
    world["npcs"] = [
        {"id": "guard", "name": "Guard", "location": "gate", "disposition": "hostile"},
    ]
    scene = {"scene": {"id": "gate"}}
    session = {}
    character = default_character()
    character["skills"]["intimidate"] = -5

    action = {
        "id": "intimidate-guard",
        "label": "Intimidate the guard",
        "type": "intimidate",
        "prompt": "I intimidate the guard.",
        "target_id": "guard",
    }
    resolution = resolve_social_action(
        scene, session, world, action,
        character=character,
        turn_counter=1,
    )
    _assert_social_result_shape(resolution, "intimidate")
    assert resolution["success"] is None
    assert resolution["requires_check"] is True
    assert resolution["check_request"]["skill"] == "intimidate"
    assert resolution["social"]["social_intent_class"] == "social_maneuver"
    assert resolution["social"]["skill_check"] is None


def test_question_reveals_topic_clue():
    """Question on NPC with topic reveals topic/clue."""
    world = default_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "gate",
            "disposition": "friendly",
            "topics": [{"id": "patrol", "text": "A patrol went missing near the old milestone.", "clue_id": "patrol_clue"}],
        },
    ]
    scene = {"scene": {"id": "gate"}}
    session = {}
    action = {
        "id": "question-runner",
        "label": "Ask the Tavern Runner",
        "type": "question",
        "prompt": "I ask the Tavern Runner about the area.",
        "target_id": "runner",
    }
    resolution = resolve_social_action(
        scene, session, world, action,
        character=default_character(),
        turn_counter=1,
    )
    _assert_social_result_shape(resolution, "question")
    assert resolution["success"] is True
    assert resolution["requires_check"] is False
    assert resolution.get("check_request") is None
    assert resolution["discovered_clues"] == ["A patrol went missing near the old milestone."]
    assert resolution["state_changes"].get("topic_revealed") is True
    assert resolution["social"]["social_intent_class"] == "social_exchange"
    assert resolution["social"].get("topic_revealed") is not None


def test_repeat_question_does_not_duplicate_reveal():
    """Repeated question on same NPC does not reveal same topic again."""
    world = default_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Runner",
            "location": "gate",
            "topics": [{"id": "one", "text": "First topic."}],
        },
    ]
    scene = {"scene": {"id": "gate"}}
    session = {}
    action = {"id": "q1", "label": "Ask Runner", "type": "question", "prompt": "Ask Runner", "target_id": "runner"}

    r1 = resolve_social_action(scene, session, world, action, character=default_character(), turn_counter=1)
    assert r1["success"] is True
    assert r1["discovered_clues"] == ["First topic."]

    r2 = resolve_social_action(scene, session, world, action, character=default_character(), turn_counter=2)
    assert r2["success"] is None
    assert r2["discovered_clues"] == []
    assert r2["social"].get("topic_revealed") is None


def test_direct_question_sets_npc_reply_expected_signal():
    world = default_world()
    world["npcs"] = [
        {
            "id": "scribe",
            "name": "Scribe",
            "location": "archive",
            "topics": [{"id": "ledger", "text": "The ledgers are kept under seal."}],
        },
    ]
    scene = {"scene": {"id": "archive"}}
    session = {}
    action = {
        "id": "ask-scribe",
        "label": "Ask the scribe",
        "type": "question",
        "prompt": 'Galinor asks, "Who keeps the ledgers?"',
        "target_id": "scribe",
    }
    resolution = resolve_social_action(
        scene,
        session,
        world,
        action,
        raw_player_text='Galinor asks, "Who keeps the ledgers?"',
        character=default_character(),
        turn_counter=1,
    )
    social = resolution["social"]
    assert social["npc_reply_expected"] is True
    assert social["reply_kind"] == "answer"


def test_listening_invitation_sets_reply_expected_explanation():
    world = default_world()
    world["npcs"] = [
        {"id": "runner", "name": "Tavern Runner", "location": "gate"},
    ]
    scene = {"scene": {"id": "gate"}}
    session = {}
    action = {
        "id": "probe-runner",
        "label": "Continue with runner",
        "type": "social_probe",
        "prompt": "I'm listening. Go on.",
        "target_id": "runner",
    }
    resolution = resolve_social_action(
        scene,
        session,
        world,
        action,
        raw_player_text="I'm listening. Go on.",
        character=default_character(),
        turn_counter=1,
    )
    social = resolution["social"]
    assert social["npc_reply_expected"] is True
    assert social["reply_kind"] == "explanation"


def test_question_without_topic_marks_refusal_and_substantive_hint():
    world = default_world()
    world["npcs"] = [
        {"id": "runner", "name": "Runner", "location": "gate", "topics": []},
    ]
    scene = {"scene": {"id": "gate"}}
    session = {}
    action = {
        "id": "ask-runner",
        "label": "Ask runner",
        "type": "question",
        "prompt": 'Galinor asks, "Where are they headed?"',
        "target_id": "runner",
    }
    resolution = resolve_social_action(
        scene,
        session,
        world,
        action,
        raw_player_text='Galinor asks, "Where are they headed?"',
        character=default_character(),
        turn_counter=1,
    )
    social = resolution["social"]
    assert social["npc_reply_expected"] is True
    assert social["reply_kind"] == "refusal"
    assert "substantive in-turn response" in resolution["hint"]


def test_follow_up_without_explicit_target_id_keeps_guard_captain_via_continuity():
    """Bare follow-ups must keep active_interaction_target_id through engine resolution (continuity path)."""
    world = default_world()
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = {"scene": {"id": "frontier_gate"}}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "guard_captain")
    action = {
        "id": "q-follow",
        "type": "question",
        "label": "follow-up",
        "prompt": "What did you mean by that?",
    }
    resolution = resolve_social_action(
        scene,
        session,
        world,
        action,
        raw_player_text=action["prompt"],
        character=default_character(),
        turn_counter=1,
    )
    assert resolution["social"]["npc_id"] == "guard_captain"
    assert resolution["social"]["target_resolved"] is True
    assert resolution["social"]["target_source"] == "continuity"
    assert resolution["social"]["target_candidate_id"] is None


def test_return_to_guard_follow_up_resolves_same_npc_via_generic_role():
    """Phrases like 'to the guard' hit generic-role precedence before continuity; target must stay in-scene."""
    world = default_world()
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = {"scene": {"id": "frontier_gate"}}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "guard_captain")
    action = {
        "id": "q-follow",
        "type": "question",
        "label": "follow-up",
        "prompt": "I return to the guard. What did you mean?",
    }
    resolution = resolve_social_action(
        scene,
        session,
        world,
        action,
        raw_player_text=action["prompt"],
        character=default_character(),
        turn_counter=1,
    )
    assert resolution["social"]["npc_id"] == "guard_captain"
    assert resolution["social"]["target_resolved"] is True
    assert resolution["social"]["target_source"] == "generic_role"


def test_missing_npc_target_handled_safely():
    """Missing or unreachable NPC returns clean failure."""
    world = default_world()
    world["npcs"] = [{"id": "guard", "name": "Guard", "location": "gate"}]
    scene = {"scene": {"id": "market"}}

    action = {"id": "persuade-guard", "label": "Persuade the guard", "type": "persuade", "target_id": "guard"}
    resolution = resolve_social_action(scene, {}, world, action, character=default_character(), turn_counter=1)
    _assert_social_result_shape(resolution, "persuade")
    assert resolution["success"] is False
    assert resolution["social"]["target_resolved"] is False
    assert resolution["social"]["npc_id"] == "guard"
    assert resolution["social"]["offscene_target"] is True

    action2 = {"id": "persuade-nobody", "label": "Persuade Nobody", "type": "persuade", "target_id": "nonexistent_npc"}
    resolution2 = resolve_social_action(scene, {}, world, action2, character=default_character(), turn_counter=1)
    assert resolution2["success"] is False
    assert resolution2["social"]["target_resolved"] is False


def test_social_result_dict_matches_engine_contract():
    """SocialEngineResult.to_dict() has all canonical keys."""
    r = SocialEngineResult(
        kind="question",
        action_id="q1",
        label="Ask",
        prompt="I ask.",
        success=True,
        social={"npc_id": "npc", "target_resolved": True},
    )
    d = social_result_to_dict(r)
    for key in ENGINE_RESULT_REQUIRED:
        assert key in d, f"Missing: {key}"
    assert d["kind"] == "question"
    assert d["social"]["npc_id"] == "npc"
    assert d["resolved_transition"] is False
    assert d["target_scene_id"] is None


def test_npc_runtime_trust_attitude_persistence():
    """Successful social actions update trust/attitude in session.npc_runtime."""
    world = default_world()
    world["npcs"] = [{"id": "npc", "name": "NPC", "location": "here"}]
    scene = {"scene": {"id": "here"}}
    session = default_session()
    character = default_character()
    character["skills"]["diplomacy"] = 20

    action = {"id": "p1", "label": "Persuade NPC", "type": "persuade", "target_id": "npc"}
    resolve_social_action(scene, session, world, action, character=character, turn_counter=1)

    rt = get_npc_runtime(session, "npc")
    assert "trust" in rt
    assert rt["trust"] >= 0
    assert "last_interaction_turn" in rt
    assert rt["last_interaction_turn"] == 1


def test_find_npc_by_target():
    """find_npc_by_target matches by id and name."""
    world = default_world()
    world["npcs"] = [
        {"id": "guard_captain", "name": "Guard Captain", "location": "gate"},
        {"id": "merchant", "name": "The Merchant", "location": "market"},
    ]
    assert find_npc_by_target(world, "guard_captain", "gate")["id"] == "guard_captain"
    assert find_npc_by_target(world, "Guard Captain", "gate")["id"] == "guard_captain"
    assert find_npc_by_target(world, "guard captain", "gate")["id"] == "guard_captain"
    assert find_npc_by_target(world, "merchant", "market")["id"] == "merchant"
    assert find_npc_by_target(world, "merchant", "gate") is None  # Wrong scene
    assert find_npc_by_target(world, "nobody", "gate") is None


def test_parse_social_intent():
    """parse_social_intent returns structured action when pattern and NPC match."""
    world = default_world()
    world["npcs"] = [{"id": "guard", "name": "Guard", "location": "gate"}]
    scene = {"scene": {"id": "gate"}}

    parsed = parse_social_intent("talk to the guard", scene, world)
    assert parsed is not None
    assert parsed["type"] == "question"
    assert parsed["target_id"] == "guard"

    parsed2 = parse_social_intent("persuade the guard", scene, world)
    assert parsed2 is not None
    assert parsed2["type"] == "persuade"

    parsed3 = parse_social_intent("look at the sky", scene, world)
    assert parsed3 is None


def test_resolve_social_skill_check():
    """resolve_skill_check (skill_checks) returns roll, modifier, total, difficulty/dc, success."""
    character = default_character()
    ctx = {"seed_parts": ["test", "diplomacy", 10]}
    result = resolve_skill_check("diplomacy", 10, character, ctx)
    assert "roll" in result
    assert "modifier" in result
    assert "total" in result
    assert "dc" in result
    assert "difficulty" in result
    assert "success" in result
    assert result["difficulty"] == 10
    assert result["dc"] == 10
    assert 1 <= result["roll"] <= 20
    assert result["total"] == result["roll"] + result["modifier"]
    assert result["success"] == (result["total"] >= 10)


def test_active_interaction_target_set_and_switches_on_social_exchange():
    world = default_world()
    world["npcs"] = [
        {"id": "guard", "name": "Guard", "location": "gate", "topics": [{"id": "t1", "text": "One."}]},
        {"id": "runner", "name": "Runner", "location": "gate", "topics": [{"id": "t2", "text": "Two."}]},
    ]
    scene = {"scene": {"id": "gate"}}
    session = default_session()

    resolve_social_action(
        scene,
        session,
        world,
        {"id": "q-guard", "label": "Ask guard", "type": "question", "prompt": "I ask the guard.", "target_id": "guard"},
        character=default_character(),
        turn_counter=1,
    )
    ctx = get_interaction_context(session)
    assert ctx["active_interaction_target_id"] == "guard"
    assert ctx["active_interaction_kind"] == "social"
    assert ctx["interaction_mode"] == "social"
    assert ctx["engagement_level"] == "engaged"

    resolve_social_action(
        scene,
        session,
        world,
        {"id": "q-runner", "label": "Ask runner", "type": "question", "prompt": "I ask the runner.", "target_id": "runner"},
        character=default_character(),
        turn_counter=2,
    )
    ctx = get_interaction_context(session)
    assert ctx["active_interaction_target_id"] == "runner"
    assert ctx["active_interaction_kind"] == "social"
    assert ctx["interaction_mode"] == "social"
    assert ctx["engagement_level"] == "engaged"


def test_non_social_context_update_clears_target():
    session = default_session()
    ctx = get_interaction_context(session)
    ctx["active_interaction_target_id"] = "guard"
    ctx["active_interaction_kind"] = "social"
    ctx["conversation_privacy"] = "lowered_voice"
    ctx["player_position_context"] = "seated_with_target"

    update_interaction_context_for_non_social(session, "investigate")
    ctx = get_interaction_context(session)
    assert ctx["active_interaction_target_id"] is None
    assert ctx["active_interaction_kind"] == "investigate"
    assert ctx["interaction_mode"] == "activity"
    assert ctx["engagement_level"] == "focused"
    assert ctx["conversation_privacy"] is None
    assert ctx["player_position_context"] is None


def test_implied_lowered_voice_updates_privacy_context():
    session = default_session()
    world = default_world()
    scene_id = "frontier_gate"
    get_interaction_context(session)["active_interaction_target_id"] = "guard_captain"

    result = apply_interaction_implied_heuristics(session, world, scene_id, "I lower my voice and whisper.")
    assert result["applied"] is True
    ctx = get_interaction_context(session)
    assert ctx["conversation_privacy"] == "lowered_voice"


def test_implied_sitting_with_target_updates_position_context():
    session = default_session()
    world = default_world()
    world["npcs"] = [
        {"id": "runner", "name": "Tavern Runner", "location": "frontier_gate", "position": "booth"},
    ]
    scene_id = "frontier_gate"

    result = apply_interaction_implied_heuristics(
        session,
        world,
        scene_id,
        "I sit down with the tavern runner at the booth.",
    )
    assert result["applied"] is True
    ctx = get_interaction_context(session)
    assert ctx["active_interaction_target_id"] == "runner"
    assert ctx["player_position_context"] == "seated_with_target"
    assert ctx["active_interaction_kind"] == "social"


def test_implied_bring_drink_reinforces_current_target():
    session = default_session()
    world = default_world()
    scene_id = "frontier_gate"
    ctx = get_interaction_context(session)
    ctx["active_interaction_target_id"] = "tavern_runner"
    ctx["active_interaction_kind"] = "social"

    result = apply_interaction_implied_heuristics(
        session,
        world,
        scene_id,
        "I bring a drink over to the tavern runner.",
    )
    assert result["applied"] is True
    ctx = get_interaction_context(session)
    assert ctx["active_interaction_target_id"] == "tavern_runner"
    assert ctx["active_interaction_kind"] == "social"


def test_implied_ambiguous_phrasing_is_noop():
    session = default_session()
    world = default_world()
    scene_id = "frontier_gate"
    ctx = get_interaction_context(session)
    ctx["active_interaction_target_id"] = "guard_captain"
    ctx["active_interaction_kind"] = "social"
    ctx["conversation_privacy"] = None
    ctx["player_position_context"] = None

    result = apply_interaction_implied_heuristics(
        session,
        world,
        scene_id,
        "I drift closer and keep things smooth.",
    )
    assert result["applied"] is False
    assert result["cases"] == []
    ctx = get_interaction_context(session)
    assert ctx["conversation_privacy"] is None
    assert ctx["player_position_context"] is None
    assert ctx["active_interaction_target_id"] == "guard_captain"


def test_frontier_gate_generic_addressing_smoke_authoritative():
    """Scene addressables + empty world.npcs: watchman/stranger/runner bind; follow-up uses continuity."""
    world: dict = {"npcs": []}
    session = default_session()
    st = session["scene_state"]
    st["active_scene_id"] = "frontier_gate"
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)

    auth_w = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="You, watchman. Where is your Captain?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth_w["npc_id"] == "guard_captain"
    assert auth_w["source"] == "generic_role"
    grw = auth_w.get("generic_role_rebind")
    assert isinstance(grw, dict)
    assert grw.get("matched_role") == "guard"
    assert grw.get("matched_actor_id") == "guard_captain"

    set_social_target(session, "guard_captain")
    auth_s = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Stranger, do you know anything about the missing patrol?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth_s["npc_id"] == "refugee"
    # Comma vocative on "Stranger" resolves before generic-role patterns (same correct target).
    assert auth_s["source"] in ("spoken_vocative", "vocative", "generic_role")
    if auth_s["source"] == "generic_role":
        grs = auth_s.get("generic_role_rebind")
        assert isinstance(grs, dict)
        assert grs.get("continuity_overridden") is True

    auth_s_gen = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="To the stranger — anything about the missing patrol?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth_s_gen["npc_id"] == "refugee"
    assert auth_s_gen["source"] == "generic_role"
    grsg = auth_s_gen.get("generic_role_rebind")
    assert isinstance(grsg, dict)
    assert grsg.get("continuity_overridden") is True

    auth_r = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Runner, what rumor are you selling?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth_r["npc_id"] == "tavern_runner"
    assert auth_r["source"] in ("spoken_vocative", "vocative", "generic_role")

    auth_r_gen = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="To the runner - what rumor are you selling?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth_r_gen["npc_id"] == "tavern_runner"
    assert auth_r_gen["source"] == "generic_role"

    set_social_target(session, "refugee")
    auth_f = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="And the west road?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth_f["npc_id"] == "refugee"
    assert auth_f["source"] == "continuity"


def test_clear_interaction_context_resets_all_fields():
    session = default_session()
    ctx = get_interaction_context(session)
    ctx["active_interaction_target_id"] = "npc"
    ctx["active_interaction_kind"] = "social"
    ctx["conversation_privacy"] = "lowered_voice"
    ctx["player_position_context"] = "at_booth"

    clear_interaction_context(session)
    ctx = get_interaction_context(session)
    assert ctx["active_interaction_target_id"] is None
    assert ctx["active_interaction_kind"] is None
    assert ctx["interaction_mode"] == "none"
    assert ctx["engagement_level"] == "none"
    assert ctx["conversation_privacy"] is None
    assert ctx["player_position_context"] is None
