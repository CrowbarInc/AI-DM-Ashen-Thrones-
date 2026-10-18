"""PR-CP: authorized narration must survive finalization.

Replays recorded PR-CO provider text. No live provider calls.
"""

from __future__ import annotations

import json
from pathlib import Path

from game.defaults import default_character, default_scene, default_session, default_world
from game.gm_resolution_decision import DECISION_METADATA_KEY
from game.immutable_valid_response import run_preserve_if_valid
from game.live_resolution import attach_interaction_obligation
from game.social import resolve_social_action

_EVIDENCE = Path("artifacts/pr_co_gameplay_viability/evidence")
_CQ_EVIDENCE = Path("artifacts/pr_cq_live_finalization/evidence")
PATROL = "A patrol went missing near the old milestone."
NOTICE = "A notice board lists new taxes, curfews, and a posted warning about a missing patrol."


def _recorded(turn: str, attempt: str) -> str:
    record = json.loads((_EVIDENCE / turn / "turn_record.json").read_text(encoding="utf-8"))
    return str(record["trace"]["validation"][attempt]["text"])


def _cq_recorded_first_provider(turn: str) -> str:
    record = json.loads((_CQ_EVIDENCE / turn / "turn_record.json").read_text(encoding="utf-8"))
    candidates = record["trace"]["provider_candidates"]
    return str(candidates[0]["parsed_narration"])


def _narration_only(text: str) -> dict:
    return {
        "player_facing_text": text,
        "tags": [],
        "metadata": {
            "provider_response_contract": "narration_only",
            "realization_envelope": {
                "schema_version": 1,
                "provider_response_contract": "narration_only",
                "declared_claims": [],
                "narration": text,
                "structured_contract_present": True,
                "legacy_fallback": False,
                "normalized_empty_declarations": True,
                "declaration_authorship": False,
            },
        },
    }


def _social(player_text: str) -> dict:
    world = default_world()
    scene = default_scene("frontier_gate")
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    resolution = resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question_guard_captain",
            "label": player_text,
            "type": "question",
            "prompt": player_text,
            "target_id": "guard_captain",
        },
        raw_player_text=player_text,
        character=default_character(),
        turn_counter=1,
    )
    attach_interaction_obligation(
        resolution,
        player_text=player_text,
        session=session,
        normalized_action={"type": "question", "target_id": "guard_captain"},
        scene_id="frontier_gate",
        scene=scene,
        world=world,
        visible_turns=[],
        enable_model_interpretation=False,
    )
    return resolution


def _inspect(player_text: str) -> dict:
    world = default_world()
    scene = default_scene("frontier_gate")
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    resolution = {"kind": "investigate", "prompt": player_text, "metadata": {}}
    attach_interaction_obligation(
        resolution,
        player_text=player_text,
        session=session,
        normalized_action={"type": "investigate", "target_id": "notice_board"},
        scene_id="frontier_gate",
        scene=scene,
        world=world,
        visible_turns=[],
        enable_model_interpretation=False,
    )
    return resolution


def _seal(text: str, resolution: dict, player_text: str) -> dict:
    scene = default_scene("frontier_gate")
    return run_preserve_if_valid(
        _narration_only(text),
        regenerate=None,
        resolution=resolution,
        player_text=player_text,
        scene=scene,
        world=default_world(),
        session=default_session(),
    )


def _facing(sealed: dict) -> str:
    return str(sealed.get("player_facing_text") or "")


def test_preference_gesture_is_not_an_undeclared_world_fact():
    player = "Guard Captain, which do you prefer: watching the gate in this rain, or a dry watch inside the walls?"
    text = _recorded("T1", "hard_validation_attempt_1")
    sealed = _seal(text, _social(player), player)
    facing = _facing(sealed)
    assert "dry watch" in facing.lower()
    assert "blessing" in facing.lower()
    assert "frayed banners hang above" not in facing.lower()
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] == "initial_hard_valid"


def test_authored_patrol_sentence_survives_and_extras_do_not():
    player = "Captain, what do you know about the missing patrol?"
    resolution = _social(player)
    topic = (resolution.get("social") or {}).get("topic_revealed") or {}
    assert topic.get("text") == PATROL
    mixed = _recorded("T3", "hard_validation_attempt_2")
    sealed = _seal(mixed, resolution, player)
    facing = _facing(sealed)
    assert "old milestone" in facing.lower()
    assert "crossroads" not in facing.lower()
    assert "confirm for now" not in facing.lower()
    assert "cannot answer that" not in facing.lower()
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] == "authored_answer_projection"


def test_patrol_geography_and_nonreturn_do_not_survive_with_the_authorized_sentence():
    player = "Captain, what do you know about the missing patrol?"
    text = (
        'The guard captain says, "A patrol went missing near the old milestone, '
        'east beyond the trading crossroads. They have not returned."'
    )
    sealed = _seal(text, _social(player), player)
    facing = _facing(sealed).lower()
    assert "old milestone" in facing
    assert "crossroads" not in facing
    assert "not returned" not in facing
    assert "have not returned" not in facing


def test_pr_cq_patrol_invalid_first_generation_projects_without_regeneration():
    player = "Captain, what do you know about the missing patrol?"
    calls = []

    def regenerate(feedback: str) -> dict:
        calls.append(feedback)
        return _narration_only("This retry should not be used.")

    sealed = run_preserve_if_valid(
        _narration_only(_cq_recorded_first_provider("T2")),
        regenerate=regenerate,
        resolution=_social(player),
        player_text=player,
        scene=default_scene("frontier_gate"),
        world=default_world(),
        session=default_session(),
    )
    facing = _facing(sealed).lower()
    accepted = sealed["metadata"]["accepted_response"]
    assert calls == []
    assert "old milestone" in facing
    assert "crossroads" not in facing
    assert "not returned" not in facing
    assert accepted["provenance"] == "authored_answer_projection"
    assert accepted["attempt"] == 1
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] == "authored_answer_projection"
    assert sealed["metadata"]["hard_validation_attempt_1"]["hard_valid"] is False
    assert sealed["metadata"]["regeneration_invoked"] is False


def test_visible_notice_fact_reaches_the_player_without_invented_roster():
    player = "I examine the notice board for anything unusual."
    invented = (
        "The notice was posted yesterday with the captain's seal, a roster of twelve names, "
        "and fresh annotations ordering the east road closed."
    )
    sealed = _seal(invented, _inspect(player), player)
    facing = _facing(sealed)
    assert "taxes" in facing.lower()
    assert "curfew" in facing.lower()
    assert "missing patrol" in facing.lower()
    assert "yesterday" not in facing.lower()
    assert "twelve" not in facing.lower()
    assert "annotations" not in facing.lower()
    assert "east road" not in facing.lower()
    assert NOTICE in facing or "names a missing patrol" in facing


def test_exact_notice_sentence_is_not_notice_roster_history():
    player = "I examine the notice board for anything unusual."
    sealed = _seal(NOTICE, _inspect(player), player)
    facing = _facing(sealed)
    assert NOTICE in facing
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] == "initial_hard_valid"


def test_paraphrase_with_added_history_does_not_replace_the_visible_fact():
    player = "I examine the notice board for anything unusual."
    paraphrase = _recorded("T4", "hard_validation_attempt_1")
    sealed = _seal(paraphrase, _inspect(player), player)
    facing = _facing(sealed).lower()
    assert "taxes" in facing
    assert "curfew" in facing
    assert "edicts" not in facing
    assert "freshly posted" not in facing
    assert "urgent" not in facing


def test_consequential_npc_action_stays_rejected():
    player = "Guard Captain, which do you prefer: watching the gate in this rain, or a dry watch inside the walls?"
    text = "The guard captain opens the gate and orders the watch to depart."
    sealed = _seal(text, _social(player), player)
    facing = _facing(sealed).lower()
    assert "opens the gate" not in facing
    assert "orders the watch" not in facing
    assert "depart" not in facing


def test_decision_is_attached_for_replay():
    resolution = _social("Captain, what do you know about the missing patrol?")
    assert resolution["metadata"][DECISION_METADATA_KEY]["contract_id"]
