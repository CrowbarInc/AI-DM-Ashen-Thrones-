import json

from game.defaults import default_campaign, default_character, default_combat, default_scene, default_session, default_world
from game.gm import build_messages
from game.interaction_context import (
    apply_implied_hint,
    apply_explicit_non_social_commitment_break,
    clear_for_scene_change,
    inspect,
    set_engagement_level,
    set_interaction_mode,
    set_non_social_activity,
    set_privacy,
    set_social_target,
    should_break_social_commitment_for_input,
    update_after_resolved_action,
)
from game.storage import get_scene_runtime

import pytest

pytestmark = pytest.mark.unit

# feature: social, continuity


def test_set_social_target_set_and_update():
    session = default_session()

    set_social_target(session, "guard_captain")
    ctx = inspect(session)
    assert ctx["active_interaction_target_id"] == "guard_captain"
    assert ctx["active_interaction_kind"] == "social"
    assert ctx["interaction_mode"] == "social"
    assert ctx["engagement_level"] == "engaged"

    set_social_target(session, "tavern_runner")
    ctx = inspect(session)
    assert ctx["active_interaction_target_id"] == "tavern_runner"
    assert ctx["active_interaction_kind"] == "social"
    assert ctx["interaction_mode"] == "social"
    assert ctx["engagement_level"] == "engaged"


def test_set_privacy_update_and_clear():
    session = default_session()
    set_privacy(session, "lowered_voice")
    assert inspect(session)["conversation_privacy"] == "lowered_voice"

    set_privacy(session, None)
    assert inspect(session)["conversation_privacy"] is None


def test_apply_implied_hint_lowered_voice_and_seated():
    session = default_session()

    apply_implied_hint(session, "lowered_voice", target_id="guard_captain")
    ctx = inspect(session)
    assert ctx["conversation_privacy"] == "lowered_voice"
    assert ctx["active_interaction_target_id"] == "guard_captain"
    assert ctx["active_interaction_kind"] == "social"
    assert ctx["interaction_mode"] == "social"
    assert ctx["engagement_level"] == "engaged"

    apply_implied_hint(session, "seated_with_target", target_id="guard_captain")
    ctx = inspect(session)
    assert ctx["player_position_context"] == "seated_with_target"
    assert ctx["active_interaction_target_id"] == "guard_captain"


def test_set_non_social_activity_clears_social_continuity():
    session = default_session()
    set_social_target(session, "guard_captain")
    set_privacy(session, "lowered_voice")
    apply_implied_hint(session, "seated_with_target", target_id="guard_captain")

    set_non_social_activity(session, "investigate")
    ctx = inspect(session)
    assert ctx["active_interaction_target_id"] is None
    assert (session.get("scene_state") or {}).get("current_interlocutor") is None
    assert ctx["active_interaction_kind"] == "investigate"
    assert ctx["interaction_mode"] == "activity"
    assert ctx["engagement_level"] == "focused"
    assert ctx["conversation_privacy"] is None
    assert ctx["player_position_context"] is None


def test_clear_for_scene_change_resets_all_fields():
    session = default_session()
    set_social_target(session, "guard_captain")
    set_privacy(session, "lowered_voice")
    apply_implied_hint(session, "seated_with_target", target_id="guard_captain")

    clear_for_scene_change(session)
    ctx = inspect(session)
    assert ctx["active_interaction_target_id"] is None
    assert ctx["active_interaction_kind"] is None
    assert ctx["interaction_mode"] == "none"
    assert ctx["engagement_level"] == "none"
    assert ctx["conversation_privacy"] is None
    assert ctx["player_position_context"] is None


def test_prompt_payload_reflects_interaction_context_owner_state():
    campaign = default_campaign()
    world = default_world()
    character = default_character()
    combat = default_combat()
    session = default_session()
    scene = default_scene("frontier_gate")
    recent_log = []

    set_social_target(session, "guard_captain")
    set_privacy(session, "lowered_voice")
    apply_implied_hint(session, "seated_with_target", target_id="guard_captain")

    scene_rt = get_scene_runtime({"scene_runtime": {}}, "frontier_gate")
    msgs = build_messages(
        campaign,
        world,
        session,
        character,
        scene,
        combat,
        recent_log,
        "I keep speaking quietly with the guard captain.",
        None,
        scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    continuity = payload["interaction_continuity"]
    assert continuity["active_interaction_target_id"] == "guard_captain"
    assert continuity["active_interaction_kind"] == "social"
    assert continuity["interaction_mode"] == "social"
    assert continuity["engagement_level"] == "engaged"
    assert continuity["conversation_privacy"] == "lowered_voice"
    assert continuity["player_position_context"] == "seated_with_target"


def test_update_after_resolved_action_preserves_or_downgrades_deterministically():
    session = default_session()
    set_social_target(session, "guard_captain")
    set_privacy(session, "lowered_voice")

    # Follow-up non-social with implied continuity preserved should keep social lock.
    update_after_resolved_action(session, "investigate", preserve_continuity=True)
    ctx = inspect(session)
    assert ctx["active_interaction_target_id"] == "guard_captain"
    assert ctx["active_interaction_kind"] == "social"
    assert ctx["interaction_mode"] == "social"
    assert ctx["engagement_level"] == "engaged"

    # Leaving interaction without preservation should downgrade to non-social activity.
    update_after_resolved_action(session, "investigate", preserve_continuity=False)
    ctx = inspect(session)
    assert ctx["active_interaction_target_id"] is None
    assert ctx["active_interaction_kind"] == "investigate"
    assert ctx["interaction_mode"] == "activity"
    assert ctx["engagement_level"] == "focused"


def test_should_break_social_commitment_movement_and_investigate_not_at_interlocutor():
    session = default_session()
    world = default_world()
    set_social_target(session, "tavern_runner")

    ok, reason = should_break_social_commitment_for_input(
        session,
        'I stride directly toward the notice board.',
        {"type": "investigate", "label": "notice board", "prompt": "notice board", "target_id": "notice_board"},
        world=world,
    )
    assert ok is True
    assert reason

    ok2, _ = should_break_social_commitment_for_input(
        session,
        "What did you hear about the patrol?",
        {"type": "question", "prompt": "What did you hear?"},
        world=world,
    )
    assert ok2 is False


def test_apply_explicit_non_social_commitment_break_clears_target():
    session = default_session()
    world = default_world()
    set_social_target(session, "tavern_runner")
    out = apply_explicit_non_social_commitment_break(
        session,
        world,
        "frontier_gate",
        "I follow the path toward the square.",
        {"type": "travel", "label": "follow path", "prompt": "follow path"},
        scene_envelope=None,
    )
    assert out.get("commitment_broken") is True
    assert inspect(session)["active_interaction_target_id"] is None


def test_explicit_mode_and_engagement_helpers_normalize_literals():
    session = default_session()
    set_interaction_mode(session, "social")
    set_engagement_level(session, "engaged")
    ctx = inspect(session)
    assert ctx["interaction_mode"] == "social"
    assert ctx["engagement_level"] == "engaged"

    set_interaction_mode(session, "not_a_mode")
    set_engagement_level(session, "not_a_level")
    ctx = inspect(session)
    assert ctx["interaction_mode"] == "none"
    assert ctx["engagement_level"] == "none"
