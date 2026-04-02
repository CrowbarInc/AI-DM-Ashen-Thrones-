"""Regression tests: authoritative social target preservation and generic-role overrides."""

from __future__ import annotations

import copy

import pytest

from game.defaults import default_character, default_session, default_world
from game.adjudication import resolve_adjudication_query
from game.interaction_context import (
    apply_explicit_non_social_commitment_break,
    assert_valid_speaker,
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    resolve_authoritative_social_target,
    session_allows_implicit_social_reply_authority,
    set_non_social_activity,
    set_social_target,
    should_break_social_commitment_for_input,
    synchronize_scene_addressability,
)
from game.social import can_actor_speak_in_current_exchange, resolve_social_action
from game.social_exchange_emission import (
    build_final_strict_social_response,
    player_line_triggers_strict_social_emission,
)
from game.storage import load_scene

pytestmark = [pytest.mark.integration, pytest.mark.regression]

STRANGER_PATROL_LINE = "Stranger, do you know anything about the missing patrol?"
WATCHMAN_CAPTAIN_LINE = "You, watchman. Where is your Captain?"


@pytest.fixture
def frontier_gate_empty_world_envelope():
    """Persisted frontier_gate JSON + empty world.npcs; active entities include gate roster."""
    world: dict = {"npcs": []}
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = load_scene("frontier_gate")
    st = session["scene_state"]
    st["active_scene_id"] = "frontier_gate"
    st["active_entities"] = [
        "guard_captain",
        "tavern_runner",
        "refugee",
        "threadbare_watcher",
    ]
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, world, scene


def test_explicit_normalized_target_survives_authoritative_social_resolution(
    frontier_gate_empty_world_envelope,
):
    session, world, scene = frontier_gate_empty_world_envelope
    normalized_action = {
        "id": "q-guard",
        "type": "question",
        "label": "Ask captain",
        "prompt": "What is the curfew?",
        "target_id": "guard_captain",
    }
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Something irrelevant to targeting.",
        normalized_action=normalized_action,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("npc_id") == "guard_captain", (
        f"expected npc_id guard_captain, got {auth.get('npc_id')!r}; full={auth!r}"
    )
    assert auth.get("target_resolved") is True, auth
    assert auth.get("source") == "explicit_target", auth


def test_generic_guard_address_overrides_prior_active_target(frontier_gate_empty_world_envelope):
    session, world, scene = frontier_gate_empty_world_envelope
    set_social_target(session, "tavern_runner")
    assert inspect_interaction_context(session).get("active_interaction_target_id") == "tavern_runner"

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text=WATCHMAN_CAPTAIN_LINE,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("npc_id") == "guard_captain", (
        f"expected guard_captain for watchman generic address, got {auth.get('npc_id')!r}; {auth!r}"
    )
    assert auth.get("source") == "generic_role", auth
    grb = auth.get("generic_role_rebind")
    assert isinstance(grb, dict), auth
    assert grb.get("continuity_overridden") is True, grb


def test_generic_refugee_address_does_not_fall_back_to_guard(frontier_gate_empty_world_envelope):
    session, world, scene = frontier_gate_empty_world_envelope
    set_social_target(session, "guard_captain")

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text=STRANGER_PATROL_LINE,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("npc_id") != "guard_captain", (
        f"stranger-address must not snap to prior guard_captain continuity; got {auth!r}"
    )
    assert auth.get("npc_id") == "refugee", auth
    assert auth.get("source") in ("spoken_vocative", "vocative", "generic_role"), auth


def test_generic_refugee_address_without_refugee_actor_is_unresolved_not_continuity():
    world: dict = {"npcs": []}
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    base = load_scene("frontier_gate")
    scene = copy.deepcopy(base)
    addr = scene.get("scene", {}).get("addressables")
    assert isinstance(addr, list)
    scene["scene"]["addressables"] = [a for a in addr if isinstance(a, dict) and a.get("id") != "refugee"]
    st = session["scene_state"]
    st["active_scene_id"] = "frontier_gate"
    st["active_entities"] = ["guard_captain", "tavern_runner", "threadbare_watcher"]
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "guard_captain")

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text=STRANGER_PATROL_LINE,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("npc_id") != "guard_captain", auth
    assert auth.get("target_resolved") is False, auth
    assert auth.get("source") == "none", (
        f"unmatched generic stranger must not use continuity; got {auth.get('source')!r} {auth!r}"
    )


def test_followup_without_new_addressee_reuses_current_interlocutor():
    world = default_world()
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = {"scene": {"id": "frontier_gate"}}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "guard_captain")

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="What did you mean by that?",
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("npc_id") == "guard_captain", auth
    assert auth.get("source") == "continuity", auth
    assert auth.get("target_resolved") is True, auth
    assert session_allows_implicit_social_reply_authority(session) is True
    speak = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "guard_captain",
        auth,
    )
    assert speak.get("allowed") is True, speak
    assert speak.get("reason_code") == "authoritative_speaker_eligible", speak


def test_courtesy_preface_does_not_block_implicit_social_reply_authority():
    """Block 3: 'Thanks. Now tell me more…' stays dialogue-shaped; session must not enter activity block."""
    world = default_world()
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = {"scene": {"id": "frontier_gate"}}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "guard_captain")
    line = "Thanks. Now tell me more about the patrol."
    ok, _ = should_break_social_commitment_for_input(
        session,
        line,
        {"type": "custom", "label": "Reply", "prompt": line},
        world=world,
    )
    assert ok is False
    ctx = inspect_interaction_context(session)
    assert ctx.get("interaction_mode") == "social"
    assert ctx.get("active_interaction_target_id") == "guard_captain"
    assert session_allows_implicit_social_reply_authority(session) is True

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text=line,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("source") == "continuity", auth
    assert auth.get("npc_id") == "guard_captain", auth
    speak = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "guard_captain",
        auth,
    )
    assert speak.get("allowed") is True, speak
    assert speak.get("reason_code") != "implicit_social_reply_authority_blocked_non_social_turn", speak


def test_non_social_activity_blocks_implicit_continuity_and_bare_question_strict_gate():
    """Explicit non-social activity must not license continuity, first-roster, or bare-? strict-social."""
    world = default_world()
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = {"scene": {"id": "frontier_gate"}}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "tavern_runner")
    set_non_social_activity(session, "travel")

    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="qqqqq unknown placename?",
        scene_envelope=scene,
        allow_first_roster_fallback=True,
    )
    assert auth.get("source") not in ("continuity", "first_roster"), auth

    assert (
        player_line_triggers_strict_social_emission(
            "qqqqq unknown placename?",
            session,
            world,
            "frontier_gate",
        )
        is False
    )


def test_explicit_redirect_via_apply_explicit_breaks_stale_continuity_and_roster_paths():
    """Block 3: state-to-emission boundary — apply_explicit_non_social_commitment_break clears licensing paths."""
    world = default_world()
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = {"scene": {"id": "frontier_gate"}}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "tavern_runner")
    session.setdefault("scene_state", {})["current_interlocutor"] = "tavern_runner"

    out = apply_explicit_non_social_commitment_break(
        session,
        world,
        "frontier_gate",
        "I stride directly toward the notice board.",
        {"type": "investigate", "label": "notice board", "prompt": "notice board", "target_id": "notice_board"},
        scene_envelope=scene,
    )
    assert out.get("commitment_broken") is True
    ctx = inspect_interaction_context(session)
    assert ctx.get("interaction_mode") == "activity"
    assert ctx.get("active_interaction_kind") == "investigate"
    assert not str(ctx.get("active_interaction_target_id") or "").strip()
    st = session.get("scene_state") or {}
    assert st.get("current_interlocutor") in (None, "")

    vague = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="qqqqq unknown placename?",
        scene_envelope=scene,
        allow_first_roster_fallback=True,
    )
    assert vague.get("source") not in ("continuity", "first_roster"), vague
    assert vague.get("npc_id") != "tavern_runner", vague

    session2 = default_session()
    session2["active_scene_id"] = "frontier_gate"
    rebuild_active_scene_entities(session2, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session2, "tavern_runner")
    out2 = apply_explicit_non_social_commitment_break(
        session2,
        world,
        "frontier_gate",
        "I follow the path toward the square.",
        {"type": "travel", "label": "follow path", "prompt": "follow path"},
        scene_envelope=scene,
    )
    assert out2.get("commitment_broken") is True
    assert inspect_interaction_context(session2).get("interaction_mode") == "activity"
    vague2 = resolve_authoritative_social_target(
        session2,
        world,
        "frontier_gate",
        player_text="qqqqq unknown placename?",
        scene_envelope=scene,
        allow_first_roster_fallback=True,
    )
    assert vague2.get("source") not in ("continuity", "first_roster"), vague2
    assert vague2.get("npc_id") != "tavern_runner", vague2


def test_explicit_normalized_target_still_authorizes_when_implicit_social_paths_are_blocked():
    """Block 3: explicit target_id must survive implicit-authority tightening on activity turns."""
    world = default_world()
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = {"scene": {"id": "frontier_gate"}}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "tavern_runner")
    set_non_social_activity(session, "travel")

    normalized_action = {
        "id": "q-guard",
        "type": "question",
        "label": "Ask captain",
        "prompt": "What is the curfew?",
        "target_id": "guard_captain",
    }
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text="Captain, what is the curfew tonight?",
        normalized_action=normalized_action,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("source") == "explicit_target", auth
    assert auth.get("npc_id") == "guard_captain", auth
    speak = can_actor_speak_in_current_exchange(
        session,
        world,
        "frontier_gate",
        scene,
        "guard_captain",
        auth,
    )
    assert speak.get("allowed") is True, speak
    assert speak.get("reason_code") != "implicit_social_reply_authority_blocked_non_social_turn", speak


def test_scene_local_actor_can_be_valid_speaker_without_world_npc_entry(
    frontier_gate_empty_world_envelope,
):
    session, world, scene = frontier_gate_empty_world_envelope
    assert world.get("npcs") == []
    ok = assert_valid_speaker("guard_captain", session)
    assert ok is True, (
        "scene-local addressable in active_entities must be a valid strict-social speaker; "
        f"scene_state={session.get('scene_state')!r}"
    )


def test_emission_validation_does_not_null_authoritatively_resolved_target():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    scene = {"scene": {"id": sid}}
    session["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    set_social_target(session, "guard_captain")

    resolution = {
        "kind": "question",
        "prompt": "Where did they go?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
            "npc_name": "Guard Captain",
            "target_resolved": True,
            "npc_reply_expected": True,
            "reply_kind": "answer",
        },
    }
    before_id = resolution["social"]["npc_id"]
    # SOCIAL-classified beat that still fails hard_reject (question first-sentence contract), forcing internal fallback.
    illegal = "Guard Captain frowns."
    _text, meta = build_final_strict_social_response(
        illegal,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    assert meta.get("used_internal_fallback") is True, meta
    assert meta.get("rejection_reasons"), meta
    after_id = resolution["social"]["npc_id"]
    assert after_id == before_id == "guard_captain", (
        f"emission path must not clear resolution.social.npc_id; before={before_id!r} after={after_id!r} meta={meta!r}"
    )


def test_synchronize_clears_interlocutor_when_target_not_addressable(frontier_gate_empty_world_envelope):
    session, world, scene = frontier_gate_empty_world_envelope
    set_social_target(session, "definitely_not_an_npc_id")
    meta = synchronize_scene_addressability(session, scene, world)
    assert meta.get("stale_interlocutor_cleared") is True, meta
    # Rebuild drops unknown ids from active scope and clears continuity; target must not linger.
    assert not str(inspect_interaction_context(session).get("active_interaction_target_id") or "").strip()
    st = session.get("scene_state") if isinstance(session.get("scene_state"), dict) else {}
    assert st.get("current_interlocutor") in (None, "")


def test_adjudication_nearby_lists_scene_addressables_with_empty_world_npcs():
    world: dict = {"npcs": []}
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    scene = load_scene("frontier_gate")
    synchronize_scene_addressability(session, scene, world)
    character = default_character()
    out = resolve_adjudication_query(
        "Who is nearby?",
        scene=scene,
        session=session,
        world=world,
        character=character,
        has_active_interaction=False,
    )
    assert isinstance(out, dict), out
    text = str(out.get("player_facing_text") or "").lower()
    assert "no nearby npc presence" not in text, out


def test_resolve_social_includes_addressability_debug_metadata(frontier_gate_empty_world_envelope):
    session, world, scene = frontier_gate_empty_world_envelope
    normalized_action = {
        "id": "q-guard",
        "type": "question",
        "label": "Ask captain",
        "prompt": "What is the curfew?",
        "target_id": "guard_captain",
    }
    result = resolve_social_action(scene, session, world, normalized_action, raw_player_text="What is the curfew?")
    social = result.get("social") if isinstance(result.get("social"), dict) else {}
    assert "stale_interlocutor_cleared" in social
    assert "addressability_checked_against" in social
    assert social.get("actor_addressable") is True
