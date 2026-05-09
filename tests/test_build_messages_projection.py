"""Projection-only regression tests for ``game.gm.build_messages``."""
from __future__ import annotations

import copy
import json

import pytest

import game.gm as gm
from game.realization_provenance import (
    REALIZATION_FALLBACK_FAMILY_FIELD,
    UPSTREAM_PREPARED_EMISSION,
)

pytestmark = pytest.mark.unit


def _minimal_state() -> tuple[dict, dict, dict, dict, dict, dict, list]:
    campaign = {"id": "campaign_projection"}
    world = {
        "world_state": {
            "flags": {"gate_locked": True},
            "counters": {"warnings": 1},
        }
    }
    session = {
        "active_scene_id": "",
        "scene_runtime": {},
        "response_mode": "standard",
        "interaction_context": {
            "active_interaction_target_id": None,
            "active_interaction_kind": None,
            "interaction_mode": "none",
            "engagement_level": "none",
            "conversation_privacy": None,
            "player_position_context": None,
        },
    }
    character = {"name": "Test PC"}
    scene = {
        "scene": {
            "id": "frontier_gate",
            "location": "Frontier Gate",
            "visible_facts": ["A posted watch list hangs beside the gate."],
            "hidden_facts": ["The courier already left."],
            "discoverable_clues": [],
        }
    }
    combat = {"active": False}
    recent_log: list[dict] = []
    return campaign, world, session, character, scene, combat, recent_log


def _narration_kwargs(
    *,
    campaign: dict,
    world: dict,
    session: dict,
    character: dict,
    scene: dict,
    combat: dict,
    recent_log: list,
    user_text: str,
    resolution: dict | None,
) -> dict:
    return {
        "campaign": campaign,
        "world": world,
        "session": session,
        "character": character,
        "scene": scene,
        "combat": combat,
        "recent_log": recent_log,
        "user_text": user_text,
        "resolution": resolution,
        "scene_runtime": {},
        "public_scene": {
            "id": "frontier_gate",
            "location": "Frontier Gate",
            "visible_facts": ["A posted watch list hangs beside the gate."],
        },
        "discoverable_clues": [],
        "gm_only_hidden_facts": ["The courier already left."],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"raw_text": user_text, "labels": ["question"], "mode": "social"},
        "world_state_view": {"flags": {"gate_locked": True}, "counters": {"warnings": 1}},
        "mode_instruction": "Narration mode: standard.",
        "recent_log_for_prompt": [],
    }


def _install_projection_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_build_narration_context(**kwargs):
        resolution = kwargs["resolution"]
        return {
            "instructions": ["Project only the supplied authoritative prompt context."],
            "resolution_projection": {
                "kind": resolution.get("kind"),
                "app_field": resolution.get("app_field"),
                "planner_field": resolution.get("planner_field"),
            },
            "planner_projection": copy.deepcopy(resolution.get("planner_field")),
            "app_projection": copy.deepcopy(resolution.get("app_field")),
            "scene": {"public": copy.deepcopy(kwargs["public_scene"])},
            "session": {"active_scene_id": kwargs["session"].get("active_scene_id")},
            "world": copy.deepcopy(kwargs["world_state_view"]),
        }

    monkeypatch.setattr(gm, "build_narration_context", _fake_build_narration_context)


def test_build_messages_projects_supplied_fields_without_fallback_authorship(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_projection_payload(monkeypatch)
    campaign, world, session, character, scene, combat, recent_log = _minimal_state()
    resolution = {
        "kind": "question",
        "hint": "Legacy prompt hint: ask the guard captain to answer from known facts.",
        "app_field": {"resolved_by": "app", "action_id": "ask_guard"},
        "planner_field": {"plan_id": "plan-7", "obligation": "answer_guard_question"},
    }
    before = {
        "resolution": copy.deepcopy(resolution),
        "session": copy.deepcopy(session),
        "world": copy.deepcopy(world),
    }

    msgs = gm.build_messages(
        campaign,
        world,
        session,
        character,
        scene,
        combat,
        recent_log,
        "What does the guard know?",
        resolution,
        scene_runtime={},
        narration_context_call_kwargs=_narration_kwargs(
            campaign=campaign,
            world=world,
            session=session,
            character=character,
            scene=scene,
            combat=combat,
            recent_log=recent_log,
            user_text="What does the guard know?",
            resolution=resolution,
        ),
    )

    assert [m["role"] for m in msgs] == ["system", "user"]
    payload = json.loads(msgs[1]["content"])
    assert payload["resolution_projection"] == {
        "kind": "question",
        "app_field": {"resolved_by": "app", "action_id": "ask_guard"},
        "planner_field": {"plan_id": "plan-7", "obligation": "answer_guard_question"},
    }
    assert payload["planner_projection"] == resolution["planner_field"]
    assert payload["app_projection"] == resolution["app_field"]

    assert "player_facing_text" not in payload
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in payload
    assert UPSTREAM_PREPARED_EMISSION not in payload
    assert "fallback_provenance" not in payload
    assert "upstream_prepared_emission" not in payload

    assert resolution == before["resolution"]
    assert session == before["session"]
    assert world == before["world"]


def test_build_messages_resolution_hint_is_legacy_prompt_instruction_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_projection_payload(monkeypatch)
    campaign, world, session, character, scene, combat, recent_log = _minimal_state()
    resolution = {
        "kind": "question",
        "hint": "Legacy prompt hint: keep the reply bounded to what the guard can know.",
        "app_field": {"resolved_by": "app"},
        "planner_field": {"obligation": "bounded_answer"},
    }
    before_resolution = copy.deepcopy(resolution)

    msgs = gm.build_messages(
        campaign,
        world,
        session,
        character,
        scene,
        combat,
        recent_log,
        "What can the guard confirm?",
        resolution,
        scene_runtime={},
        narration_context_call_kwargs=_narration_kwargs(
            campaign=campaign,
            world=world,
            session=session,
            character=character,
            scene=scene,
            combat=combat,
            recent_log=recent_log,
            user_text="What can the guard confirm?",
            resolution=resolution,
        ),
    )

    payload = json.loads(msgs[1]["content"])
    assert payload["instructions"][-1] == "Legacy prompt hint: keep the reply bounded to what the guard can know."
    assert payload["instructions"].count(resolution["hint"]) == 1
    assert "player_facing_text" not in payload
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in payload
    assert "upstream_prepared_emission" not in payload
    assert "fallback_provenance" not in payload
    assert resolution == before_resolution
