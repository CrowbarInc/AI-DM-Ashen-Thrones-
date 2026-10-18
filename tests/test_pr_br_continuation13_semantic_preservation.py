"""Post-generation semantic monotonicity. No paid inference.

Continuation 12 turns 2, 3, and 6 are replayed from the recorded candidates.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from game.api import app
from game.discourse_state import DISCOURSE_FOCUS_KEY
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world
from game.live_resolution import obligation_preserving_fallback_line
from game.playability_eval import evaluate_playability
from game.resolution_contract import (
    assess_contract_satisfaction,
    construct_resolution_contract,
    enforce_emitted_contract_monotonicity,
    generation_projection,
    prefer_stronger_resolution,
    remember_satisfied_candidate,
    retain_resolved_contract_text,
    select_preserved_answer,
    semantic_line_view,
)


NOTICE = {"type": "object", "id": "notice_board", "label": "Notice board", "aliases": ["notice", "posted notice", "posted sheet"], "source": "scene"}
GUARD = {"type": "interlocutor", "id": "gate_guard", "label": "Gate Guard", "aliases": ["guard"], "source": "scene"}

TEMPORAL = (
    "The exact timing of when the missing patrol warning appeared on the notice board is unclear "
    "to the gate serjeant by the eastern gate. From what you can tell, it is a recent development, "
    "but details are fragmented."
)
SOURCE_TEMPLATE = "No reliable source can verify who began the earlier claim or how certain it is."
INSPECTION = (
    "The notice board is plastered with several official postings. A list details the newly imposed taxes "
    "affecting the gate district. Another poster sets out the curfew rules, emphasizing strict enforcement "
    "after dusk. A warning about a patrol is pinned there: the patrol has gone missing."
)
SCENE_FRAME = (
    "The new ground shows itself: rain, choke traffic, a notice board, and gate watch pressure frame "
    "the missing patrol inquiry The missing patrol was last seen taking the northwest mud track past the crates."
)
ATMOSPHERE = (
    "No one among the gate serjeant, gate guard, or the ragged figures steps forward to explain "
    "tonight's entry conditions."
)
CLUE = "The missing patrol was last seen taking the northwest mud track past the crates."


def _focus(**slots):
    focus = {
        "version": 1,
        "scene_id": "frontier_gate",
        "active_interlocutor": None,
        "active_claim": None,
        "active_actionable_lead": None,
        "active_inspected": None,
        "last_attempted_action": None,
    }
    focus.update(slots)
    return {"active_scene_id": "frontier_gate", "turn_counter": 2, DISCOURSE_FOCUS_KEY: focus}


def _contract(text, session=None, interpreter=None):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id="frontier_gate",
        canonical_referents=[NOTICE, GUARD],
        model_interpreter=interpreter,
    )


def _resolution(contract, *, player_text: str, speaker: str = "Gate Guard"):
    resolution = {
        "kind": "question",
        "prompt": player_text,
        "social": {"npc_id": "gate_guard", "npc_name": speaker, "npc_reply_expected": True},
        "metadata": {"resolution_contract": contract.as_dict()},
    }
    from game.live_resolution import derive_interaction_obligation

    obligation = derive_interaction_obligation(
        player_text=player_text,
        session=_focus(),
        resolution=resolution,
    )
    resolution["metadata"]["interaction_obligation"] = {
        "kind": obligation.kind,
        "target": obligation.target,
        "interlocutor_id": obligation.interlocutor_id or "gate_guard",
        "subject": obligation.subject,
        "requested_outcome": obligation.requested_outcome,
    }
    return resolution


def _time_contract():
    def interpret(_context):
        return {
            "status": "proposed",
            "proposal": {
                "primary_operation": "ask",
                "supporting_operations": [],
                "proposed_target_id": "gate_guard",
                "interlocutor_id": "gate_guard",
                "conversational_subject": "curfew or entry conditions",
                "dimension": "time",
                "dimensions": ["time"],
                "clarification_required": False,
                "ambiguous": False,
            },
            "api_calls": 0,
        }

    return _contract("How recently?", _focus(), interpret)


def _ask_contract():
    def interpret(_context):
        return {
            "status": "proposed",
            "proposal": {
                "primary_operation": "ask",
                "supporting_operations": [],
                "proposed_target_id": "gate_guard",
                "interlocutor_id": "gate_guard",
                "conversational_subject": "what it takes to enter tonight",
                "clarification_required": False,
                "ambiguous": False,
            },
            "api_calls": 0,
        }

    return _contract(
        "I look for whoever is minding the gate and ask what it takes to get inside tonight.",
        _focus(),
        interpret,
    )


def test_recorded_turn_2_temporal_answer_survives_the_source_template():
    contract = _time_contract()
    assert contract.dimension == "time"
    resolution = _resolution(contract, player_text="How recently?")
    temporal = assess_contract_satisfaction(TEMPORAL, contract.as_dict())
    swapped = assess_contract_satisfaction(SOURCE_TEMPLATE, contract.as_dict())
    assert temporal["status"] == "satisfied"
    assert temporal["dimension_compatible"] is True
    assert swapped["status"] == "unsatisfied"
    assert "dimension_substituted" in swapped["reasons"]
    kept, info = prefer_stronger_resolution(TEMPORAL, SOURCE_TEMPLATE, resolution)
    assert "recent" in kept.lower() or "timing" in kept.lower()
    assert "who began" not in kept.lower()
    assert info["downgrade_rejected"] is True
    final, recovered = select_preserved_answer(TEMPORAL, SOURCE_TEMPLATE, resolution, stashed=TEMPORAL)
    assert "recent" in final.lower() or "timing" in final.lower()
    assert recovered["recovery_used"] is True
    gm = {"player_facing_text": TEMPORAL, "metadata": {}}
    remember_satisfied_candidate(gm, TEMPORAL, resolution)
    gm["player_facing_text"] = SOURCE_TEMPLATE
    enforce_emitted_contract_monotonicity(gm, resolution)
    visible = gm["player_facing_text"].lower()
    assert "recent" in visible or "timing" in visible
    assert "who began the earlier claim" not in visible
    fallback = obligation_preserving_fallback_line(resolution).lower()
    assert "recent" in fallback
    assert "who began the earlier claim" not in fallback
    retried, preserved = retain_resolved_contract_text(TEMPORAL, SOURCE_TEMPLATE, resolution)
    assert preserved is True
    assert "recent" in retried.lower() or "timing" in retried.lower()


def test_recorded_turn_3_inspection_survives_scene_and_clue_frame():
    contract = _contract("I examine the notice board.")
    assert contract.operation == "inspect"
    resolution = _resolution(contract, player_text="I examine the notice board.")
    useful = assess_contract_satisfaction(INSPECTION, contract.as_dict())
    framed = assess_contract_satisfaction(SCENE_FRAME, contract.as_dict())
    assert useful["status"] == "satisfied"
    assert framed["status"] == "unsatisfied"
    kept, _info = prefer_stronger_resolution(INSPECTION, SCENE_FRAME, resolution)
    assert "curfew" in kept.lower() or "tax" in kept.lower()
    assert "new ground shows itself" not in kept.lower()
    gm = {"player_facing_text": INSPECTION, "metadata": {}}
    remember_satisfied_candidate(gm, INSPECTION, resolution)
    gm["player_facing_text"] = f"{INSPECTION} {CLUE}"
    enforce_emitted_contract_monotonicity(gm, resolution)
    assert "curfew" in gm["player_facing_text"].lower() or "tax" in gm["player_facing_text"].lower()
    gm["player_facing_text"] = SCENE_FRAME
    enforce_emitted_contract_monotonicity(gm, resolution)
    visible = gm["player_facing_text"].lower()
    assert "curfew" in visible or "tax" in visible
    assert "new ground shows itself" not in visible


def test_recorded_turn_6_clue_cannot_satisfy_the_social_request():
    contract = _ask_contract()
    assert contract.operation == "ask"
    assert contract.interlocutor_id == "gate_guard"
    resolution = _resolution(contract, player_text=contract.raw_input)
    clue_view = semantic_line_view(CLUE, resolution)
    atmosphere_view = semantic_line_view(ATMOSPHERE, resolution)
    assert clue_view["keeps_answer"] is False
    assert clue_view["status"] == "unsatisfied"
    assert atmosphere_view["status"] == "unsatisfied"
    assert "atmospheric_avoidance" in atmosphere_view["reasons"]
    kept, _info = prefer_stronger_resolution(ATMOSPHERE, CLUE, resolution)
    assert semantic_line_view(kept, resolution)["keeps_answer"] is False
    inability = 'Gate Guard says, "I do not know tonight\'s entry rule. Ask the guard captain."'
    better, _info = prefer_stronger_resolution(CLUE, inability, resolution)
    assert "do not know" in better.lower()
    assert semantic_line_view(better, resolution)["status"] != "unsatisfied"
    gm = {"player_facing_text": CLUE, "metadata": {}}
    enforce_emitted_contract_monotonicity(gm, resolution)
    assert semantic_line_view(gm["player_facing_text"], resolution)["keeps_answer"] is False


def test_dimension_preservation_blocks_cross_dimension_replacement():
    source = _contract(
        "Who told him?",
        _focus(active_claim={"id": "claim-9", "label": "The toll changed last night.", "kind": "claim", "turn_index": 1}),
    )
    assert source.dimension == "source"
    resolution = _resolution(source, player_text="Who told him?")
    answer = 'Gate Guard says, "It was from them. The runner passed that word."'
    other = "That was yesterday, just after dusk."
    kept, _info = prefer_stronger_resolution(answer, other, resolution)
    assert "runner" in kept.lower()
    confidence = _contract(
        "How sure is he?",
        _focus(active_claim={"id": "claim-9", "label": "The toll changed last night.", "kind": "claim", "turn_index": 1}),
    )
    assert confidence.dimension == "confidence"
    sure = 'Gate Guard says, "I am not sure. I doubt the warning."'
    assert assess_contract_satisfaction(sure, confidence.as_dict())["status"] == "satisfied"
    kept_confidence, _info = prefer_stronger_resolution(sure, "That was yesterday, just after dusk.", {"metadata": {"resolution_contract": confidence.as_dict()}})
    assert "sure" in kept_confidence.lower() or "doubt" in kept_confidence.lower()


def test_social_resolution_fixtures_for_a_canonical_guard():
    contract = _ask_contract()
    payload = contract.as_dict()
    cases = {
        "answer": (
            "You need a night pass and your name on the roster before the gate opens.",
            "satisfied",
        ),
        "inability": (
            'Gate Guard says, "I do not know the night rule. The guard captain would."',
            "legitimate_nonresolution",
        ),
        "refusal": (
            'Gate Guard says, "I will not answer that. Move along."',
            "resolved",
        ),
        "clarification": (
            'Gate Guard asks, "Which gate are you trying to enter?"',
            "resolved",
        ),
        "atmosphere": (
            "No one steps forward to answer.",
            "unsatisfied",
        ),
        "clue": (
            CLUE,
            "unsatisfied",
        ),
    }
    for name, (text, status) in cases.items():
        result = assess_contract_satisfaction(text, payload)
        if status == "resolved":
            assert result["status"] in {"satisfied", "legitimate_nonresolution"}, name
            assert "atmospheric_avoidance" not in result["reasons"]
            assert "social_not_resolved" not in result["reasons"]
        else:
            assert result["status"] == status, name
    atmosphere = assess_contract_satisfaction(cases["atmosphere"][0], payload)
    assert "atmospheric_avoidance" in atmosphere["reasons"]
    clue = assess_contract_satisfaction(cases["clue"][0], payload)
    assert "social_not_resolved" in clue["reasons"]


def test_evaluator_rejects_dimension_social_and_inspection_mismatches():
    time_contract = _time_contract().as_dict()
    time_fail = evaluate_playability(
        {
            "player_text": "How recently?",
            "gm_text": SOURCE_TEMPLATE,
            "gm_output": {"player_facing_text": SOURCE_TEMPLATE, "metadata": {"emission_debug": {"resolution_contract": time_contract}}},
        }
    )
    assert time_fail["semantic_result"] == "FAIL"
    ask = _ask_contract().as_dict()
    social_fail = evaluate_playability(
        {
            "player_text": "I ask the gate guard what it takes to get inside tonight.",
            "gm_text": ATMOSPHERE,
            "gm_output": {"player_facing_text": ATMOSPHERE, "metadata": {"emission_debug": {"resolution_contract": ask}}},
        }
    )
    assert social_fail["semantic_result"] == "FAIL"
    clue_fail = evaluate_playability(
        {
            "player_text": "I ask the gate guard what it takes to get inside tonight.",
            "gm_text": CLUE,
            "gm_output": {"player_facing_text": CLUE, "metadata": {"emission_debug": {"resolution_contract": ask}}},
        }
    )
    assert clue_fail["semantic_result"] == "FAIL"
    inspected = _contract("I examine the notice board.").as_dict()
    frame_fail = evaluate_playability(
        {
            "player_text": "I examine the notice board.",
            "gm_text": SCENE_FRAME,
            "gm_output": {"player_facing_text": SCENE_FRAME, "metadata": {"emission_debug": {"resolution_contract": inspected}}},
        }
    )
    assert frame_fail["semantic_result"] == "FAIL"
    useful = evaluate_playability(
        {
            "player_text": "I examine the notice board.",
            "gm_text": INSPECTION,
            "gm_output": {"player_facing_text": INSPECTION, "metadata": {"emission_debug": {"resolution_contract": inspected}}},
        }
    )
    assert useful["semantic_result"] == "PASS"


def test_generation_constraint_requires_a_real_interlocutor_response():
    contract = _ask_contract()
    projection = generation_projection(contract.as_dict())
    text = str((projection or {}).get("constraint") or "").lower()
    assert "steps forward" in text
    assert "refuse" in text


def test_scene_momentum_cannot_replace_a_satisfied_inspection():
    contract = _contract("I examine the notice board.")
    resolution = _resolution(contract, player_text="I examine the notice board.")
    from game.resolution_contract import continuation_preserves_resolution

    assert continuation_preserves_resolution(INSPECTION, "Rain keeps falling.", resolution) is True
    kept, _info = prefer_stronger_resolution(INSPECTION, SCENE_FRAME, resolution)
    assert "curfew" in kept.lower() or "tax" in kept.lower()
    assert "new ground shows itself" not in kept.lower()


def test_raw_chat_keeps_a_useful_inspection_and_rejects_atmospheric_avoidance(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    from game import storage

    scene = storage.load_scene("scene_investigate")
    scene["scene"]["interactables"] = [
        {"id": "notice_board", "label": "Notice board", "aliases": ["notice", "posted notice"]},
    ]
    scene["scene"]["addressables"] = [
        {"id": "gate_guard", "name": "Gate Guard", "addressable": True, "address_roles": ["guard"]},
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)

    def interpret(context):
        raw = str(context.get("raw_input") or "")
        if "steps" in raw or "minding" in raw:
            return {
                "status": "proposed",
                "proposal": {
                    "primary_operation": "ask",
                    "supporting_operations": [],
                    "proposed_target_id": "gate_guard",
                    "interlocutor_id": "gate_guard",
                    "conversational_subject": "what it takes to enter tonight",
                    "clarification_required": False,
                    "ambiguous": False,
                },
                "api_calls": 0,
            }
        return {"status": "failed", "reason": "unexpected", "api_calls": 0}

    answers = {
        "examine": INSPECTION,
        "minding": "Yet, no one steps forward immediately to answer your question about what it takes to enter tonight.",
    }

    def fake_gpt(messages, **_kwargs):
        blob = " ".join(str(item.get("content") or "") for item in messages if isinstance(item, dict))
        if "examine" in blob.lower() or "notice board" in blob.lower():
            return _gm_response(answers["examine"])
        return _gm_response(answers["minding"])

    monkeypatch.setattr("game.semantic_interpreter.interpret_for_contract", interpret)
    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    client = TestClient(app)
    inspected = client.post("/api/chat", json={"text": "I examine the notice board."}).json()
    visible = inspected["gm_output"]["player_facing_text"].lower()
    assert "curfew" in visible or "tax" in visible
    assert "new ground shows itself" not in visible
    assert inspected["session"]["discourse_focus"]["active_claim"] is None

    asked = client.post(
        "/api/chat",
        json={"text": "I look for whoever is minding the gate and ask what it takes to get inside tonight."},
    ).json()
    asked_text = asked["gm_output"]["player_facing_text"]
    contract = asked["resolution"]["metadata"]["resolution_contract"]
    assert contract["operation"] == "ask"
    assert contract["interlocutor_id"] == "gate_guard"
    view = semantic_line_view(asked_text, asked["resolution"])
    assert view["keeps_answer"] is False or "steps forward" not in asked_text.lower()
    assert "was last seen" not in asked_text.lower() or view["status"] == "unsatisfied"
