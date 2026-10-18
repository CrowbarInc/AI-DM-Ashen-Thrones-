"""PR-BR continuation 7: resolution-outcome precedence and post-resolution integrity."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from game.api import app
from game.playability_eval import evaluate_playability
from game.resolution_contract import (
    assess_contract_satisfaction,
    continuation_preserves_resolution,
    prefer_stronger_resolution,
    select_preserved_answer,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world
from tests.test_pr_br_resolution_contract import _contract, _sheet_session


def _rumor_contract():
    return _contract("What rumor are travelers repeating?").as_dict()


def _repeat_contract():
    return _contract("Repeat that rumor.", _sheet_session()).as_dict()


def _content_contract():
    return _contract("What does it actually say?", _sheet_session()).as_dict()


def _wear_contract():
    return _contract("Does it look like people use this often?", _sheet_session()).as_dict()


def test_a_actual_rumor_answer_is_satisfied():
    result = assess_contract_satisfaction(
        "Travelers say a patrol vanished on the east lane.",
        _rumor_contract(),
    )
    assert result["status"] == "satisfied"
    assert result["resolution_kind"] == "answer"


def test_b_explicit_nonanswer_is_not_an_answer():
    result = assess_contract_satisfaction(
        "No one answers the question.",
        _rumor_contract(),
    )
    assert result["status"] != "satisfied"
    assert result["resolution_kind"] != "answer"
    assert result["status"] == "legitimate_nonresolution"


def test_c_topical_nonanswer_is_not_a_satisfied_answer():
    result = assess_contract_satisfaction(
        "No one at hand answers that directly—the question hangs in the noise.",
        _rumor_contract(),
    )
    assert result["resolution_kind"] != "answer"
    assert result["status"] != "satisfied"
    assert "explicit_nonanswer" in result["reasons"]


def test_d_valid_answer_is_not_replaced_by_inability():
    contract = _rumor_contract()
    resolution = {"metadata": {"resolution_contract": contract}}
    answer = "Travelers say a patrol vanished on the east lane."
    inability = "No one at hand answers that directly—the question hangs in the noise."
    kept, info = prefer_stronger_resolution(answer, inability, resolution)
    assert "east lane" in kept
    assert info["downgrade_rejected"] is True


def test_e_consequential_answer_may_still_be_rejected():
    contract = _rumor_contract()
    resolution = {"metadata": {"resolution_contract": contract}}
    invented = "The captain is secretly the traitor who murdered the patrol."
    inability = "I do not know what rumor is being repeated."
    kept, info = prefer_stronger_resolution(invented, inability, resolution)
    assert "traitor" not in kept.lower()
    assert info["downgrade_reason"] == "candidate_invalid"


def test_f_faithful_paraphrase_is_satisfied():
    result = assess_contract_satisfaction("Carts vanished on the east lane.", _repeat_contract())
    assert result["status"] == "satisfied"
    assert "repeat_contaminated" not in result["reasons"]


def test_g_unrelated_claim_is_not_a_repeat():
    result = assess_contract_satisfaction("The well in the lower town has run dry.", _repeat_contract())
    assert result["status"] == "unsatisfied"


def test_h_claim_plus_unrelated_append_is_degraded():
    result = assess_contract_satisfaction(
        "Carts vanished on the east lane sharpens when you look again, and ash census delays have tightened the caravan choke point still competes for notice.",
        _repeat_contract(),
    )
    assert result["status"] != "satisfied"
    assert "repeat_contaminated" in result["reasons"]


def test_i_claim_plus_atmosphere_stays_satisfied():
    result = assess_contract_satisfaction(
        "Carts vanished on the east lane. Rain keeps falling.",
        _repeat_contract(),
    )
    assert result["status"] == "satisfied"
    assert "repeat_contaminated" not in result["reasons"]


def test_j_and_k_content_answer_survives_unjustified_nonresolution():
    contract = _content_contract()
    resolution = {"metadata": {"resolution_contract": contract}}
    answer = "The posted sheet lists taxes, a curfew, and a missing patrol."
    inability = "The inspection establishes no further reliable detail about posted sheet."
    kept, info = prefer_stronger_resolution(answer, inability, resolution)
    assert "curfew" in kept
    assert info["downgrade_rejected"] is True
    final, recovered = select_preserved_answer(answer, inability, resolution, stashed=answer)
    assert "curfew" in final
    assert recovered["recovery_used"] is True
    assert recovered["destroyed"] is False


def test_l_genuine_content_inability_is_allowed():
    result = assess_contract_satisfaction(
        "You can't read the posted sheet while it is sealed.",
        _content_contract(),
    )
    assert result["status"] == "legitimate_nonresolution"
    assert result["resolution_kind"] == "inability"


def test_m_compatible_continuation_preserves_the_answer():
    contract = _repeat_contract()
    resolution = {"metadata": {"resolution_contract": contract}}
    answer = "Carts vanished on the east lane."
    assert continuation_preserves_resolution(answer, "Rain keeps falling.", resolution) is True
    combined = assess_contract_satisfaction(answer + "\n\nRain keeps falling.", contract)
    assert combined["status"] == "satisfied"


def test_n_corrupting_splice_is_not_preserved():
    contract = _repeat_contract()
    resolution = {"metadata": {"resolution_contract": contract}}
    answer = "Carts vanished on the east lane."
    splice = "Carts vanished on the east lane sharpens when you look again, and ash census delays have tightened the caravan choke point still competes for notice."
    assert continuation_preserves_resolution(answer, splice, resolution) is False
    final, info = select_preserved_answer(answer, splice, resolution)
    assert final == answer
    assert info["recovery_used"] is True


def test_o_destroyed_signal_is_not_a_successful_resolution():
    contract = _rumor_contract()
    evaluation = evaluate_playability(
        {
            "player_text": "What rumor are travelers repeating?",
            "gm_text": "No one at hand answers that directly—the question hangs in the noise.",
            "gm_output": {
                "player_facing_text": "No one at hand answers that directly—the question hangs in the noise.",
                "metadata": {
                    "emission_debug": {
                        "resolution_contract": contract,
                        "outcome_precedence": {"destroyed": True},
                    }
                },
            },
            "resolution_contract": contract,
        }
    )
    assert evaluation["semantic_result"] != "PASS"


def test_p_explicit_inability_is_not_labeled_an_answer():
    result = assess_contract_satisfaction(
        "No one at hand answers that directly—the question hangs in the noise.",
        _rumor_contract(),
    )
    assert result["resolution_kind"] == "inability"
    evaluation = evaluate_playability(
        {
            "player_text": "What rumor are travelers repeating?",
            "gm_text": "No one at hand answers that directly—the question hangs in the noise.",
            "resolution_contract": _rumor_contract(),
        }
    )
    assert evaluation["semantic_result"] != "PASS"


def test_q_wear_use_observation_stays_healthy():
    result = assess_contract_satisfaction(
        "The posted sheet looks heavily used. The corners are soft from many hands.",
        _wear_contract(),
    )
    assert result["status"] in {"satisfied", "partial"}
    assert result["resolution_kind"] == "answer"
    assert result["target_compatible"] is True


def test_r_target_aware_inspection_stays_healthy():
    contract = _contract("Look the posted sheet over.").as_dict()
    right = assess_contract_satisfaction(
        "The sheet lists a curfew, tax notices, and a missing patrol.",
        contract,
    )
    wrong = assess_contract_satisfaction(
        "The inspection establishes no further reliable detail about gate_serjeant.",
        contract,
    )
    assert right["status"] == "satisfied"
    assert wrong["status"] == "unsatisfied"


def test_real_path_preserves_rumor_repeat_and_sheet_content(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    rumor = (
        "I can tell that the notice board has added a warning about a missing patrol, "
        "which travelers are murmuring about. Watching closely, you notice threadbare watchers "
        "clustered near the gate."
    )
    repeated = "Travelers are still murmuring that a missing patrol was posted on the notice board."
    sheet = "The posted sheet lists taxes, a curfew, and a warning about a missing patrol."
    content = (
        "The notice board displays taxes, updated curfew rules, and a posted warning about a missing patrol. "
        "Ask the guard captain if you want the rest."
    )
    wear = "The posted sheet looks frequently used. The edges are worn from many hands."

    def fake_gpt(messages, **_kwargs):
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        try:
            payload = json.loads(user)
            current = str(payload.get("player_input") or payload.get("raw_player_input") or "")
        except (TypeError, ValueError, json.JSONDecodeError):
            current = user
        low = current.lower()
        if "repeat that rumor" in low:
            return _gm_response(repeated)
        if "what does it actually say" in low:
            return _gm_response(content)
        if "use this often" in low:
            return _gm_response(wear)
        if "look the posted sheet over" in low:
            return _gm_response(sheet)
        return _gm_response(rumor)

    with monkeypatch.context() as ctx:
        ctx.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "What rumor are travelers repeating?"}).json()
        second = client.post("/api/chat", json={"text": "Repeat that rumor."}).json()
        third = client.post("/api/chat", json={"text": "Look the posted sheet over."}).json()
        fourth = client.post("/api/chat", json={"text": "What does it actually say?"}).json()
        fifth = client.post("/api/chat", json={"text": "Does it look like people use this often?"}).json()

    def visible(payload):
        return payload["gm_output"]["player_facing_text"]

    assert "patrol" in visible(first).lower()
    assert "hangs in the noise" not in visible(first).lower()
    assert "sharpens when you look again" not in visible(second).lower()
    assert "patrol" in visible(second).lower() or "notice" in visible(second).lower()
    assert "sheet" in visible(third).lower() or "notice" in visible(third).lower() or "curfew" in visible(third).lower()
    assert "no further reliable detail" not in visible(fourth).lower()
    assert any(token in visible(fourth).lower() for token in ("tax", "curfew", "patrol"))
    assert "used" in visible(fifth).lower() or "worn" in visible(fifth).lower() or "hands" in visible(fifth).lower()
