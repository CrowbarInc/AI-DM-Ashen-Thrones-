"""Reproduce PR-EG-R3-R1 historical failures against the pre-repair code."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from game.conversational_continuity import _best_exchange, record_delivered_exchange
from game.dialogue_authority import build_dialogue_authority, select_host_speech
from game.expressive_dialogue import build_expression_contract, validate_expression
from game.social import _next_topic_to_reveal

OUT = Path(__file__).resolve().parent


def main() -> None:
    contract = build_expression_contract(
        player_text="Why do you prefer the evening?",
        speaker_name="Sergeant Mara",
        speaker_id="sergeant_mara",
        fallback_line='Sergeant Mara says, "I prefer the evening."',
        fallback_source="conversational_continuity.bounded_personal_line",
        resolution={
            "social": {
                "npc_id": "sergeant_mara",
                "npc_name": "Sergeant Mara",
                "dialogue_authority": {
                    "knowledge_posture": "belief",
                    "requested_information": "opinion",
                    "npc_id": "sergeant_mara",
                    "npc_name": "Sergeant Mara",
                },
            }
        },
    )
    candidate_a = (
        "I prefer the evening because I find it a little easier to think "
        "when the day is winding down and everything feels calm and peaceful."
    )
    verdict_a = validate_expression(candidate_a, contract)
    session = {}
    social = {"npc_id": "sergeant_mara", "npc_name": "Sergeant Mara", "topic_revealed": {"id": "road", "text": "The street beyond the gate is the north road."}}
    record_delivered_exchange(
        session,
        player_text="What is the street called?",
        delivered_text='Sergeant Mara says, "Word is, the street beyond the gate is the north road."',
        social=social,
        turn=1,
    )
    record_delivered_exchange(
        session,
        player_text="Say that in simpler words.",
        delivered_text='Sergeant Mara says, "The street just past the gate is called the north road."',
        social={"npc_id": "sergeant_mara", "npc_name": "Sergeant Mara"},
        turn=2,
    )
    found = _best_exchange("What did you mean by the north road?", session["conversational_context"]["delivered_exchanges"], "sergeant_mara")
    fact = "Guards watch the north gate throughout the night."
    npc = {"id": "sergeant_mara", "name": "Sergeant Mara", "topics": [{"id": "watch", "text": fact}]}
    question = "Is the north gate ever left unattended?"
    selected = _next_topic_to_reveal(npc, {}, player_text=question)
    authority = build_dialogue_authority(question, npc=npc, social={"npc_id": npc["id"], "npc_name": npc["name"], "target_resolved": True})
    speech = select_host_speech(
        {
            "kind": "social_exchange",
            "requires_check": False,
            "social": {"target_resolved": True, "npc_id": npc["id"], "npc_name": npc["name"], "dialogue_authority": authority},
            "metadata": {"resolution_contract": {"operation": "ask", "interlocutor_id": npc["id"]}},
        },
        player_text=question,
    )
    renamed = validate_expression("The north street.", contract if False else build_expression_contract(
        player_text="Say that in simpler words.",
        speaker_name="Sergeant Mara",
        speaker_id="sergeant_mara",
        fallback_line='Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."',
        fallback_source="conversational_decision:repeat_delivered_statement",
        forced_operation="faithful_paraphrase",
    ))
    unsafe = validate_expression(
        "I prefer the evening because the guards usually leave the north gate unattended.",
        contract,
    )
    report = {
        "A_characterization": {"adopt": verdict_a["adopt"], "reasons": verdict_a["reasons"], "candidate": candidate_a},
        "B_equivalent_paraphrases": {"result": found if isinstance(found, str) else {"supplied": found.get("supplied_text"), "topic_id": found.get("topic_id")}},
        "C_partial_question": {
            "selected_topic": None if selected is None else selected.get("id"),
            "player_line": authority.get("player_line"),
            "answer_relation": authority.get("answer_relation"),
            "delivered": None if speech is None else speech[0],
        },
        "D_entity_rename": {"adopt": renamed["adopt"], "reasons": renamed["reasons"]},
        "E_security_characterization": {"adopt": unsafe["adopt"], "reasons": unsafe["reasons"]},
        "contract_keys": sorted(contract),
    }
    (OUT / "historical_reproduction.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
