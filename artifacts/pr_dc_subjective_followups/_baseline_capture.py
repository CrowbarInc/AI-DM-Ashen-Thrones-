"""PR-DC baseline capture. Read-only. No provider calls."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import game.gm as gm
from game.social import _bounded_social_reply_plan_for_missing_topic
from tests.test_pr_db_speaker_grounding import TURN_1, TURN_2, TURN_3, _bind_guard, _focus, _gate_session_scene, play_turn

_MEASURE_PATH = Path(__file__).resolve().parents[1] / "pr_db_speaker_grounding" / "_measure.py"
_spec = importlib.util.spec_from_file_location("pr_db_measure", _MEASURE_PATH)
_measure = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_measure)
_messages_for = _measure._messages_for
_payload_from_messages = _measure._payload_from_messages
_predicates = _measure._predicates

OUT = Path(__file__).resolve().parent

POSITIVE = [
    "Does the rain make it harder to keep watch?",
    "Does it get any easier after a while?",
    "Is standing in the cold uncomfortable?",
    "Do long shifts leave you tired?",
    "Do you enjoy working at the gate?",
    "Does the noise bother you?",
    "Is the work stressful?",
    "Why do you prefer somewhere dry?",
    "Does the baker find early mornings tiring?",
    "Does the innkeeper enjoy busy evenings?",
]
NEGATIVE = [
    "Does rain expose weaknesses in the gate?",
    "Can smugglers enter unnoticed during storms?",
    "Which guards abandon their posts?",
    "Where is the secret tunnel?",
    "Does the captain know the patrol's location?",
    "Does the captain have a hidden criminal past?",
    "Can the captain unlock the gate for me?",
    "Will the captain waive the entry fee?",
    "Can I persuade the captain to leave?",
    "Does the rain reveal hidden tracks?",
    "What defenses protect the gate?",
    "Is the captain secretly working for another faction?",
    "What happened to the missing patrol?",
    "Can the captain promise me safe passage?",
    "Does rain make it easier to assassinate the captain?",
]


def _social_view(result: dict) -> dict:
    social = (result.get("resolution") or {}).get("social") or {}
    speaker = result.get("speaker") or {}
    return {
        "text": result.get("text"),
        "resolver": result.get("resolver"),
        "entry_reason": result.get("entry_reason"),
        "parsed_type": result.get("parsed_type"),
        "contract_interlocutor": result.get("contract_interlocutor"),
        "social_npc_id": result.get("social_npc_id"),
        "social_target_resolved": result.get("social_target_resolved"),
        "reply_plan_kind": social.get("reply_plan_kind"),
        "reply_kind": social.get("reply_kind"),
        "incidental_subjective_allowed": social.get("incidental_subjective_allowed"),
        "npc_speech_authority": social.get("npc_speech_authority"),
        "objective_world_fact_authority": social.get("objective_world_fact_authority"),
        "durable_state_mutation_allowed": social.get("durable_state_mutation_allowed"),
        "declared_claims_expected": social.get("declared_claims_expected"),
        "absence_of_authored_topic_forces_refusal": social.get("absence_of_authored_topic_forces_refusal"),
        "allowed_speaker_ids": result.get("allowed_speaker_ids"),
        "primary_speaker_id": speaker.get("primary_speaker_id"),
        "obligation_interlocutor": result.get("obligation_interlocutor"),
        "obligation_mode": result.get("obligation_mode"),
        "active_interaction_target_id": result.get("active_interaction_target_id"),
        "discourse_interlocutor": result.get("discourse_interlocutor"),
        "hint": (result.get("resolution") or {}).get("hint"),
    }


def _direct(text: str) -> dict:
    plan = _bounded_social_reply_plan_for_missing_topic(
        action_type="question",
        player_text=text,
        npc={"disposition": "neutral"},
        topic_revealed=False,
    )
    return {"text": text, **plan}


def _prompt_case(label: str, setup) -> dict:
    session, scene, world, result, player = setup
    scene = dict(scene)
    scene.pop("_is_canon", None)
    messages = _messages_for(result, session, scene, world, player)
    blob, payload, _marker = _payload_from_messages(messages)
    envelope = gm._provider_response_contract_from_messages(messages)
    projected = None
    if isinstance(payload, dict):
        projected = gm._project_harmless_social_provider_context(
            dict(payload), provider_response_contract=envelope
        )
    rows = _predicates(payload or {}, envelope)
    first_fail = next((row for row in rows if not row["pass"]), None)
    projection = projected.get("provider_context_projection") if isinstance(projected, dict) else None
    social = {}
    if isinstance(payload, dict):
        mechanical = payload.get("mechanical_resolution") if isinstance(payload.get("mechanical_resolution"), dict) else {}
        social = mechanical.get("social") if isinstance(mechanical.get("social"), dict) else {}
    omitted = []
    if isinstance(projection, dict):
        omitted = projection.get("omitted_sections") or []
    return {
        "label": label,
        "player": player,
        "reply_plan_kind": social.get("reply_plan_kind") or result.get("reply_plan_kind"),
        "incidental_subjective_allowed": social.get("incidental_subjective_allowed"),
        "npc_speech_authority": social.get("npc_speech_authority"),
        "objective_world_fact_authority": social.get("objective_world_fact_authority"),
        "envelope": envelope,
        "serialized_bytes": len(blob.encode("utf-8")),
        "serialized_chars": len(blob),
        "estimated_tokens_ceil_chars_div_4": (len(blob) + 3) // 4,
        "tokenizer": "estimate_ceil_chars_div_4",
        "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "projection_selected": isinstance(projection, dict) and projection.get("selected") is True,
        "projection_mode": projection.get("mode") if isinstance(projection, dict) else None,
        "omitted_sections": omitted,
        "first_failing_predicate": None if first_fail is None else first_fail.get("predicate"),
        "first_fail_actual": None if first_fail is None else first_fail.get("actual"),
    }


def main() -> None:
    session, scene, world = _gate_session_scene()
    turns = []
    for text in (TURN_1, TURN_2, TURN_3):
        result = play_turn(session, scene, world, text)
        turns.append(_social_view(result))
        session["turn_counter"] = int(session.get("turn_counter") or 0) + 1

    routed = []
    for text in POSITIVE + NEGATIVE:
        live, live_scene, live_world = _gate_session_scene()
        _bind_guard(live)
        _focus(live, "guard_captain", "Guard Captain")
        result = play_turn(live, live_scene, live_world, text)
        routed.append(_social_view(result))

    # Prompt cases A-E on independent sessions.
    prompts = []

    s, sc, w = _gate_session_scene()
    r = play_turn(s, sc, w, TURN_1)
    prompts.append(_prompt_case("A_initial_preference", (s, sc, w, r, TURN_1)))

    s, sc, w = _gate_session_scene()
    play_turn(s, sc, w, TURN_1)
    r = play_turn(s, sc, w, TURN_2)
    prompts.append(_prompt_case("B_rain_difficulty", (s, sc, w, r, TURN_2)))

    s, sc, w = _gate_session_scene()
    play_turn(s, sc, w, TURN_1)
    play_turn(s, sc, w, TURN_2)
    r = play_turn(s, sc, w, TURN_3)
    prompts.append(_prompt_case("C_getting_used_to_it", (s, sc, w, r, TURN_3)))

    s, sc, w = _gate_session_scene()
    _bind_guard(s)
    _focus(s, "guard_captain", "Guard Captain")
    consequential = "Does rain make it easier to assassinate the captain?"
    r = play_turn(s, sc, w, consequential)
    prompts.append(_prompt_case("D_consequential_rain", (s, sc, w, r, consequential)))

    s, sc, w = _gate_session_scene()
    _bind_guard(s)
    _focus(s, "guard_captain", "Guard Captain")
    authored = "What happened to the missing patrol?"
    r = play_turn(s, sc, w, authored)
    prompts.append(_prompt_case("E_authored_patrol", (s, sc, w, r, authored)))

    phase = "after"
    payload = {
        "phase": phase,
        "turns": turns,
        "direct_positive": [_direct(text) for text in POSITIVE],
        "direct_negative": [_direct(text) for text in NEGATIVE],
        "routed_controls": routed,
        "prompts": prompts,
    }
    (OUT / "_after.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"turns": turns, "prompts": prompts}, indent=2, default=str))


if __name__ == "__main__":
    main()
