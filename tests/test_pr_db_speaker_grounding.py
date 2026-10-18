"""PR-DB conversational speaker grounding. Deterministic, no provider calls."""
from __future__ import annotations

from copy import deepcopy

import pytest

from game.campaign_state import create_fresh_session_document
from game.discourse_state import DISCOURSE_FOCUS_KEY, SLOT_INTERLOCUTOR, commit_discourse_focus
from game.interaction_context import (
    build_speaker_selection_contract,
    clear_for_scene_change,
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
    update_after_resolved_action,
)
from game.live_resolution import attach_interaction_obligation
from game.ordinary_semantic_ownership import select_ordinary_resolver
from game.social import SOCIAL_KINDS, resolve_social_action
from game.social_continuity_routing import apply_explicit_non_social_commitment_break
from game.storage import load_scene

pytestmark = pytest.mark.unit

TURN_1 = "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?"
TURN_2 = "Does the rain make it harder to keep watch?"
TURN_3 = "Does it get any easier after a while?"


def _gate_session_scene():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["turn_counter"] = 2
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    state = session["scene_state"]
    state["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    state.setdefault("entity_presence", {})
    state["entity_presence"].update({entity: "active" for entity in state["active_entities"]})
    world = {
        "npcs": [
            {
                "id": "guard_captain",
                "name": "Guard Captain",
                "location": "frontier_gate",
                "role": "guard",
                "availability": "available",
                "disposition": "neutral",
            },
            {
                "id": "tavern_runner",
                "name": "Tavern Runner",
                "location": "frontier_gate",
                "role": "runner",
                "availability": "available",
                "disposition": "neutral",
            },
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(state)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, scene, world


def _bind_guard(session: dict) -> None:
    ctx = session.setdefault("interaction_context", {})
    ctx["active_interaction_target_id"] = "guard_captain"
    ctx["active_interaction_kind"] = "social"
    ctx["interaction_mode"] = "social"
    ctx["engagement_level"] = "engaged"
    session.setdefault("scene_state", {})["current_interlocutor"] = "guard_captain"


def _focus(session: dict, npc_id: str, label: str) -> None:
    session[DISCOURSE_FOCUS_KEY] = {
        "version": 1,
        "scene_id": "frontier_gate",
        SLOT_INTERLOCUTOR: {
            "id": npc_id,
            "label": label,
            "kind": "interlocutor",
            "scene_id": "frontier_gate",
            "source": "resolution_contract",
        },
    }


def play_turn(session: dict, scene: dict, world: dict, text: str) -> dict:
    """Replay the chat social-entry boundary without a provider call."""
    entry = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    from game.intent_parser import parse_freeform_to_action
    from game.interaction_routing import _build_dialogue_first_action
    from game.social import parse_social_intent

    parsed = None
    if entry.get("should_route_social"):
        parsed = parse_social_intent(text, scene, world)
        if parsed is None:
            parsed = _build_dialogue_first_action(
                player_text=text,
                scene=scene,
                session=session,
                world=world,
                segmented_turn=None,
                canonical_social_entry=entry,
            )
    if not isinstance(parsed, dict):
        parsed = parse_freeform_to_action(text, scene)
    if not isinstance(parsed, dict):
        parsed = {"type": "custom", "label": text, "prompt": text}
    parsed = dict(parsed)
    parsed.setdefault("label", text)
    parsed.setdefault("prompt", text)
    parsed.setdefault("id", "pr_db_turn")
    apply_explicit_non_social_commitment_break(
        session,
        world,
        "frontier_gate",
        text,
        parsed,
        scene_envelope=scene,
    )
    kind = str(parsed.get("type") or "").strip().lower()
    social_route = bool(entry.get("should_route_social")) and kind in SOCIAL_KINDS
    if social_route:
        resolution = resolve_social_action(
            scene,
            session,
            world,
            parsed,
            raw_player_text=text,
            turn_counter=int(session.get("turn_counter") or 0),
        )
    else:
        resolution = {
            "kind": kind or "observe",
            "prompt": text,
            "social": {"npc_id": None, "target_resolved": False},
            "metadata": {},
        }
    if social_route:
        attach_interaction_obligation(
            resolution,
            player_text=text,
            session=session,
            normalized_action=parsed,
            scene_id="frontier_gate",
            scene=scene,
            world=world,
            enable_model_interpretation=False,
        )
        metadata = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        contract = metadata.get("resolution_contract") if isinstance(metadata.get("resolution_contract"), dict) else {}
        resolver, _family = select_ordinary_resolver(contract)
        metadata["selected_resolver"] = resolver
        metadata["ordinary_contract_established"] = True
        commit_discourse_focus(
            session,
            contract=contract,
            resolution=resolution,
            scene_id="frontier_gate",
        )
        resolved_kind = str(resolution.get("kind") or kind or "").strip().lower()
        if resolved_kind in SOCIAL_KINDS:
            update_after_resolved_action(session, resolved_kind, preserve_continuity=True)
    else:
        contract = {}
        resolver = None
    speaker = build_speaker_selection_contract(
        session,
        world,
        "frontier_gate",
        resolution=resolution if isinstance(resolution, dict) else None,
        normalized_action=parsed,
        scene_envelope=scene,
        merged_player_prompt=text,
    )
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    obligation = {}
    metadata = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    if isinstance(metadata.get("interaction_obligation"), dict):
        obligation = metadata["interaction_obligation"]
    ctx = session.get("interaction_context") if isinstance(session.get("interaction_context"), dict) else {}
    focus = session.get(DISCOURSE_FOCUS_KEY) if isinstance(session.get(DISCOURSE_FOCUS_KEY), dict) else {}
    active = focus.get(SLOT_INTERLOCUTOR) if isinstance(focus.get(SLOT_INTERLOCUTOR), dict) else {}
    return {
        "text": text,
        "entry_reason": entry.get("reason"),
        "entry_target": entry.get("target_actor_id"),
        "should_route_social": bool(entry.get("should_route_social")),
        "parsed_type": kind,
        "resolver": resolver,
        "contract_interlocutor": contract.get("interlocutor_id"),
        "contract_operation": contract.get("operation"),
        "social_npc_id": social.get("npc_id"),
        "social_target_resolved": social.get("target_resolved"),
        "reply_plan_kind": social.get("reply_plan_kind"),
        "obligation_interlocutor": obligation.get("interlocutor_id"),
        "obligation_mode": obligation.get("resolution_mode"),
        "allowed_speaker_ids": list(speaker.get("allowed_speaker_ids") or []),
        "speaker_reason": (speaker.get("debug") or {}).get("authoritative_reason")
        if isinstance(speaker.get("debug"), dict)
        else speaker.get("authoritative_reason"),
        "active_interaction_target_id": ctx.get("active_interaction_target_id"),
        "interaction_mode": ctx.get("interaction_mode"),
        "interaction_kind": ctx.get("active_interaction_kind"),
        "discourse_interlocutor": active.get("id"),
        "resolution": resolution,
        "speaker": speaker,
    }


def test_pr_db_followup_does_not_clear_guard_for_keep_watch_question() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    result = play_turn(session, scene, world, TURN_2)
    assert result["should_route_social"] is True
    assert result["resolver"] == "social"
    assert result["contract_interlocutor"] == "guard_captain"
    assert result["social_npc_id"] == "guard_captain"
    assert result["social_target_resolved"] is True
    assert result["obligation_interlocutor"] == "guard_captain"
    assert result["obligation_mode"] != "clarification_target_failure"
    assert result["allowed_speaker_ids"] == ["guard_captain"]
    assert result["active_interaction_target_id"] == "guard_captain"
    assert result["discourse_interlocutor"] == "guard_captain"
    assert result["interaction_mode"] == "social"


def test_pr_db_three_turn_continuity() -> None:
    session, scene, world = _gate_session_scene()
    turns = [play_turn(session, scene, world, text) for text in (TURN_1, TURN_2, TURN_3)]
    for result in turns:
        assert result["resolver"] == "social"
        assert result["contract_interlocutor"] == "guard_captain"
        assert result["social_npc_id"] == "guard_captain"
        assert result["social_target_resolved"] is True
        assert result["obligation_interlocutor"] == "guard_captain"
        assert result["allowed_speaker_ids"] == ["guard_captain"]
        assert result["active_interaction_target_id"] == "guard_captain"
        assert result["discourse_interlocutor"] == "guard_captain"


def test_pr_db_explicit_switch_replaces_guard() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    result = play_turn(session, scene, world, "Tavern Runner, do you prefer the stew or the rain?")
    assert result["social_npc_id"] == "tavern_runner"
    assert result["allowed_speaker_ids"] == ["tavern_runner"]
    assert result["active_interaction_target_id"] == "tavern_runner"
    assert "guard_captain" not in result["allowed_speaker_ids"]


def test_pr_db_self_directed_watch_still_clears_target() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    result = play_turn(session, scene, world, "He keeps watching the gate for anything unusual.")
    assert result["should_route_social"] is False
    assert result["active_interaction_target_id"] in (None, "")
    assert result["allowed_speaker_ids"] == []


def test_pr_db_scene_change_clears_target() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    clear_for_scene_change(session)
    result = play_turn(session, scene, world, TURN_2)
    assert result["allowed_speaker_ids"] == []
    assert result["social_npc_id"] in (None, "")
    assert result["active_interaction_target_id"] in (None, "")


def test_pr_db_departure_clears_stale_guard() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    scene = deepcopy(scene)
    scene["scene"]["addressables"] = [
        row for row in scene["scene"]["addressables"] if str(row.get("id") or "") != "guard_captain"
    ]
    scene["scene_state"]["active_entities"] = [
        entity for entity in scene["scene_state"]["active_entities"] if entity != "guard_captain"
    ]
    session["scene_state"]["active_entities"] = list(scene["scene_state"]["active_entities"])
    session["scene_state"]["entity_presence"]["guard_captain"] = "offscene"
    world["npcs"] = [npc for npc in world["npcs"] if npc["id"] != "guard_captain"]
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    assert session["interaction_context"]["active_interaction_target_id"] in (None, "")
    result = play_turn(session, scene, world, TURN_2)
    assert "guard_captain" not in result["allowed_speaker_ids"]
    assert result["social_npc_id"] != "guard_captain"


def test_pr_db_group_address_is_an_open_call_not_a_private_followup() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    result = play_turn(session, scene, world, "Can anyone tell me if the rain makes watch harder?")
    assert result["entry_reason"] == "open_social_solicitation"
    assert result["entry_target"] in (None, "")
    assert len(result["allowed_speaker_ids"]) <= 1
    assert set(result["allowed_speaker_ids"]).issubset({"guard_captain", "tavern_runner", "refugee", "threadbare_watcher"})


def test_pr_db_consequential_question_does_not_grant_harmless_speech() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    result = play_turn(
        session,
        scene,
        world,
        "Does the rain hide the cult's secret passage?",
    )
    assert result["reply_plan_kind"] != "harmless_subjective_response_permitted"
    assert result["social_npc_id"] in (None, "", "guard_captain")


def test_pr_db_hidden_and_authored_questions_do_not_select_reduced_context_plan() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    hidden = play_turn(session, scene, world, "What hidden signal is the threadbare watcher waiting on?")
    authored = play_turn(session, scene, world, "What happened to the missing patrol?")
    for result in (hidden, authored):
        assert result["reply_plan_kind"] != "harmless_subjective_response_permitted"


def test_pr_db_physical_and_combat_drop_dialogue_continuity() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    physical = play_turn(session, scene, world, "I climb the gate wall.")
    assert physical["should_route_social"] is False
    assert physical["active_interaction_target_id"] in (None, "")
    assert physical["allowed_speaker_ids"] == []
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    combat = play_turn(session, scene, world, "I attack the guard captain.")
    assert combat["should_route_social"] is False
    assert combat["active_interaction_target_id"] in (None, "")
    assert combat["interaction_mode"] == "activity"
    assert combat["interaction_kind"] == "attack"


def test_pr_db_missing_npc_and_unresolved_referent_authorize_nobody() -> None:
    session, scene, world = _gate_session_scene()
    ctx = session.setdefault("interaction_context", {})
    ctx["active_interaction_target_id"] = "not_a_real_npc"
    ctx["active_interaction_kind"] = "social"
    ctx["interaction_mode"] = "social"
    ctx["engagement_level"] = "engaged"
    missing = play_turn(session, scene, world, TURN_2)
    assert missing["allowed_speaker_ids"] == []
    assert missing["social_npc_id"] in (None, "")

    bare, bare_scene, bare_world = _gate_session_scene()
    unresolved = play_turn(bare, bare_scene, bare_world, "Does it get any easier after a while?")
    assert unresolved["allowed_speaker_ids"] == []
    assert unresolved["social_npc_id"] in (None, "")


def test_pr_db_contradictory_discourse_does_not_force_projection_speaker() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "tavern_runner", "Tavern Runner")
    result = play_turn(session, scene, world, TURN_2)
    same_speaker = (
        result["contract_interlocutor"]
        and result["contract_interlocutor"] == result["social_npc_id"]
        and result["allowed_speaker_ids"] == [result["contract_interlocutor"]]
    )
    if result["contract_interlocutor"] != result["social_npc_id"]:
        assert same_speaker is False
    assert result["allowed_speaker_ids"] in ([], ["guard_captain"], ["tavern_runner"])


def test_pr_db_multiple_addressees_do_not_authorize_both() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    result = play_turn(
        session,
        scene,
        world,
        "Guard Captain and Tavern Runner, which of you prefers the rain?",
    )
    assert len(result["allowed_speaker_ids"]) <= 1
