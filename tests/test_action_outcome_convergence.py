"""C1-C: action_outcome ownership-chain convergence regressions.

These tests focus on preventing prompt-layer narration bypasses when the plan selects
``narrative_mode == "action_outcome"``.
"""

from __future__ import annotations

import json

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.gm import build_messages
from game.narrative_planning import validate_action_outcome_plan_contract
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests


def _base_kwargs() -> dict:
    return {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 2,
            "visited_scene_ids": ["s1"],
            "interaction_context": {
                "active_interaction_target_id": None,
                "active_interaction_kind": None,
                "interaction_mode": "none",
            },
        },
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Look.",
        "resolution": {"kind": "travel", "label": "raw-travel"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"], "allow_discoverable_clues": True},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }


def _json_payload_from_messages(msgs: list[dict[str, str]]) -> dict:
    assert isinstance(msgs, list) and len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    payload = json.loads(msgs[1]["content"])
    assert isinstance(payload, dict)
    return payload


def test_validate_action_outcome_contract_dormant_ok_under_continuation_even_if_response_type_is_action_outcome() -> None:
    """Key caveat: do not enforce action_outcome structure solely from required_response_type."""
    plan = {
        "narrative_mode": "continuation",
        "action_outcome": {"present": False},
    }
    ok, reasons = validate_action_outcome_plan_contract(plan, response_type_required="action_outcome")
    assert ok is True
    assert reasons == []


def test_gm_build_messages_action_outcome_mode_does_not_forward_resolution_hint_or_prompt() -> None:
    """GM message assembly must not re-introduce legacy prose hints when prompt_context selected action_outcome mode."""
    session = dict(_base_kwargs()["session"])
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Attack.",
        builder_source="tests.c1c.gm.action_outcome",
        intent={"raw_text": "Attack.", "labels": ["attack"], "mode": "activity"},
        resolution={
            "kind": "attack",
            "action_id": "atk_sword",
            "label": "Attack",
            "prompt": "Player hit the orc... Narrate the outcome.",
            "metadata": {"response_type_contract": {"required_response_type": "action_outcome"}},
            "combat": {
                "actor_id": "pc_hero",
                "target_id": "enemy_orc",
                "damage_dealt": 3,
                "healing_applied": 0,
                "conditions_applied": [],
                "conditions_removed": [],
                "combat_ended": False,
                "winner": None,
                "rolls": {"attack_roll": 11, "attack_total": 15, "target_ac": 13},
            },
        },
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    try:
        kw = _base_kwargs()
        kw["session"] = session
        kw["user_text"] = "Attack."
        kw["resolution"] = {
            "kind": "attack",
            "hint": "Narrate the outcome.",
            "prompt": "Player hit the orc... Narrate the outcome.",
            "metadata": {"response_type_contract": {"required_response_type": "action_outcome"}},
        }
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "include_non_public_prompt_keys": True})
        msgs = build_messages(
            campaign=kw["campaign"],
            world=kw["world"],
            session=kw["session"],
            character=kw["character"],
            scene=kw["scene"],
            combat=kw["combat"],
            recent_log=kw["recent_log"],
            user_text=kw["user_text"],
            resolution=kw["resolution"],
            scene_runtime=kw["scene_runtime"],
            narration_context_call_kwargs={**kw, "include_non_public_prompt_keys": True},
        )
    finally:
        detach_ctir(session)

    payload = _json_payload_from_messages(msgs)
    mech = payload.get("mechanical_resolution")
    assert isinstance(mech, dict) and "action_outcome" in mech
    assert payload.get("resolved_combat_action") is None
    assert "Narrate the outcome" not in json.dumps(payload, ensure_ascii=False)

