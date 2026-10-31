"""PR-BR typed resolution contract and lightweight discourse focus."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from game.api import app
from game.api_turn_support import _preserve_resolution_contract_after_gate
from game.bounded_improvisation import validate_bounded_improvisation_proposal
from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus
from game.live_resolution import attach_interaction_obligation, select_resolution_mode
from game.playability_eval import evaluate_playability
from game.resolution_contract import construct_resolution_contract
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world


def _focus(**slots):
    focus = {
        "version": 1,
        "scene_id": "yard",
        "active_interlocutor": None,
        "active_claim": None,
        "active_actionable_lead": None,
        "active_inspected": None,
        "last_attempted_action": None,
    }
    focus.update(slots)
    return {"active_scene_id": "yard", DISCOURSE_FOCUS_KEY: focus}


def _contract(text: str, session: dict | None = None, **kwargs):
    return construct_resolution_contract(player_text=text, session=session or {"active_scene_id": "yard"}, scene_id="yard", **kwargs)


def test_appearance_dimension_is_preserved():
    contract = _contract("What does the canvas awning look like?")
    assert contract.dimension == "appearance"
    assert contract.operation == "perceive"
    assert contract.target_ref is not None
    assert "awning" in (contract.target_ref.id_or_text or "")
    assert contract.referent_provenance == "explicit_player"


def test_sound_dimension_is_preserved():
    contract = _contract("I listen through the shutter.")
    assert contract.dimension == "sound"
    assert contract.operation == "perceive"
    assert contract.target_ref is not None
    assert "shutter" in (contract.target_ref.id_or_text or "")


def test_smell_dimension_is_preserved():
    contract = _contract("What does the cooking pot smell like?")
    assert contract.dimension == "smell"
    assert "pot" in (contract.target_ref.id_or_text or "")


def test_wear_and_use_dimensions_are_preserved():
    session = _focus(
        active_inspected={"id": "obj-1", "label": "iron latch", "kind": "object", "scene_id": "yard", "turn_index": 1}
    )
    contract = _contract("What can I learn from its wear, marks, or use?", session)
    assert "wear" in contract.dimensions
    assert "use" in contract.dimensions
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "obj-1"
    assert contract.referent_provenance == "inherited_discourse"


def test_claim_source_follow_up_binds_previous_claim():
    session = {
        "active_scene_id": "yard",
        "bounded_improvisation": {
            "entries": [
                {
                    "id": "claim-9",
                    "kind": "npc_claim",
                    "status": "accepted",
                    "content": "Carts vanished on the east lane.",
                }
            ]
        },
    }
    contract = _contract("Who told you that?", session)
    assert contract.dimension == "source"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.type == "claim"
    assert contract.discourse_ref.id == "claim-9"
    assert contract.epistemic_mode == "npc_claim"


def test_claim_confidence_follow_up_binds_previous_claim():
    session = _focus(active_claim={"id": "claim-2", "label": "The road is watched.", "kind": "claim", "turn_index": 2})
    contract = _contract("Do you believe them?", session)
    assert contract.dimension == "confidence"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "claim-2"


def test_claim_location_follow_up_binds_previous_claim():
    session = _focus(active_claim={"id": "claim-3", "label": "A cart vanished.", "kind": "claim", "turn_index": 2})
    contract = _contract("Where did that happen?", session)
    assert contract.dimension == "location"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "claim-3"


def test_actionable_lead_resolves_that_lead():
    session = _focus(
        active_actionable_lead={"id": "lead-7", "label": "shelter at the east lane", "kind": "lead", "scene_id": "yard", "turn_index": 3}
    )
    contract = _contract("I follow that lead.", session)
    assert contract.operation == "follow"
    assert contract.request_kind == "action"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "lead-7"
    assert contract.expected_resolution == "action_outcome"


def test_inspected_referent_resolves_it():
    session = _focus(
        active_inspected={"id": "obj-4", "label": "iron latch", "kind": "object", "scene_id": "yard", "turn_index": 2}
    )
    contract = _contract("What does it smell like?", session)
    assert contract.dimension == "smell"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "obj-4"


def test_prior_action_resolves_when_i_did_that():
    session = _focus(
        last_attempted_action={"id": "act-1", "label": "I try the latch.", "kind": "act", "scene_id": "yard", "turn_index": 4}
    )
    contract = _contract("What changed when I did that?", session)
    assert contract.dimension == "change"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.type == "action"
    assert contract.discourse_ref.id == "act-1"


def test_action_request_stays_action_oriented():
    session = _focus(active_interlocutor={"id": "runner", "label": "Runner", "kind": "interlocutor", "scene_id": "yard"})
    contract = _contract("Can you point me toward them?", session)
    assert contract.request_kind == "social_action"
    assert contract.operation == "act"
    assert contract.expected_resolution == "action_outcome"


def test_ambiguous_referent_does_not_bind_arbitrarily():
    session = _focus(
        active_inspected={"id": "obj-1", "label": "iron latch", "kind": "object", "scene_id": "yard"},
        active_actionable_lead={"id": "lead-1", "label": "east lane shelter", "kind": "lead", "scene_id": "yard"},
    )
    contract = _contract("What about that?", session)
    assert contract.ambiguous is True
    assert contract.expected_resolution == "clarification"
    assert contract.discourse_ref is None
    assert contract.target_ref is None


def test_scene_change_drops_old_inspected_focus():
    session = _focus(
        active_inspected={"id": "obj-1", "label": "iron latch", "kind": "object", "scene_id": "yard", "turn_index": 1}
    )
    contract = construct_resolution_contract(
        player_text="What does it smell like?",
        session=session,
        scene_id="market",
    )
    assert contract.discourse_ref is None
    assert contract.referent_provenance in {"unresolved", "ambiguous"}
    assert contract.expected_resolution == "clarification"


def test_explicit_target_overrides_inherited_focus():
    session = _focus(
        active_inspected={"id": "obj-1", "label": "iron latch", "kind": "object", "scene_id": "yard"}
    )
    contract = _contract("What does the canvas awning smell like?", session)
    assert contract.referent_provenance == "explicit_player"
    assert "awning" in (contract.target_ref.id_or_text or "")
    assert contract.discourse_ref is None


def test_consequential_information_does_not_enter_incidental_authority():
    text = "What is the secret allegiance of the figure beside me?"
    resolution = {"kind": "question", "prompt": text}
    attach_interaction_obligation(resolution, player_text=text, session={"active_scene_id": "yard"}, scene_id="yard")
    contract = resolution["metadata"]["resolution_contract"]
    assert contract["epistemic_mode"] == "consequential_protected"
    decision = select_resolution_mode(
        player_text=text,
        scene={"scene": {"id": "yard"}},
        session={"active_scene_id": "yard"},
        resolution=resolution,
    )
    assert decision.mode == "unsupported_consequential_request"
    assert decision.proposal_kind is None
    checked = validate_bounded_improvisation_proposal(
        {
            "kind": "incidental_fact",
            "category": "sensory_detail",
            "content": "The figure wears a faded blue ribbon.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session={},
        scene={"scene": {"id": "yard"}},
        world={},
        resolution=resolution,
    )
    assert checked.accepted is False
    assert "contract:consequential_protected" in checked.reason_codes


def test_retry_does_not_replace_the_resolution_contract():
    resolution = {"kind": "question", "prompt": "What does the pot smell like?"}
    attach_interaction_obligation(
        resolution,
        player_text="What does the pot smell like?",
        session={"active_scene_id": "yard", "turn_counter": 3},
        scene_id="yard",
    )
    first = dict(resolution["metadata"]["resolution_contract"])
    attach_interaction_obligation(
        resolution,
        player_text="What color is the sky?",
        session={"active_scene_id": "yard", "turn_counter": 3},
        scene_id="yard",
    )
    second = resolution["metadata"]["resolution_contract"]
    assert second["contract_id"] == first["contract_id"]
    assert second["dimension"] == "smell"
    assert second["retry_preserved"] is True
    assert resolution["metadata"]["interaction_obligation"]["resolution_contract_id"] == first["contract_id"]


def test_final_emission_rejects_generic_scene_for_sound_contract():
    text = "What ordinary sounds stand out where I am?"
    resolution = {"kind": "observe", "prompt": text}
    attach_interaction_obligation(
        resolution,
        player_text=text,
        session={"active_scene_id": "yard"},
        normalized_action={"type": "observe", "prompt": text},
        scene_id="yard",
    )
    gm = {
        "player_facing_text": "Watchers crowd the gate while the serjeant stands in the square.",
        "tags": [],
        "metadata": {},
    }
    _preserve_resolution_contract_after_gate(gm, resolution=resolution)
    assert "sound" in gm["player_facing_text"].lower()
    assert "resolution_contract_semantic_preserved" in gm["tags"]
    assert gm["metadata"]["emission_debug"]["resolution_contract_semantic"]["replaced"] is True


def test_evaluator_uses_shared_contract_and_does_not_trust_a_bare_flag():
    contract = _contract("What does the stew smell like?").as_dict()
    generic = "The stew sits among the watchers at the gate in the square."
    failed = evaluate_playability(
        {
            "player_prompt": "What does the stew smell like?",
            "gm_text": generic,
            "resolution_contract": contract,
            "obligation_resolved": True,
        }
    )
    assert failed["semantic_result"] == "FAIL"
    evidence = failed["mandatory_gates"]["player_intent_addressed"]["evidence"]["resolution_contract"]
    assert evidence["assessment_status"] == "unsatisfied"
    assert evidence["contract_id"] == contract["contract_id"]

    answered = evaluate_playability(
        {
            "player_prompt": "What does the stew smell like?",
            "gm_text": "The stew smells of onion and woodsmoke.",
            "resolution_contract": contract,
        }
    )
    assert answered["mandatory_gates"]["player_intent_addressed"]["status"] == "PASS"
    assert (
        answered["mandatory_gates"]["player_intent_addressed"]["evidence"]["resolution_contract"]["assessment_status"]
        == "satisfied"
    )


def test_discourse_commit_survives_a_second_call_for_the_same_contract():
    session = {"active_scene_id": "yard", "turn_counter": 2}
    contract = _contract("I examine the iron latch.", session)
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="yard")
    assert session[DISCOURSE_FOCUS_KEY]["active_inspected"]["label"] == "iron latch"
    session[DISCOURSE_FOCUS_KEY]["active_inspected"]["label"] = "iron latch"
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="yard")
    assert session[DISCOURSE_FOCUS_KEY]["active_inspected"]["label"] == "iron latch"
    assert session[DISCOURSE_FOCUS_KEY]["last_committed_contract_id"] == contract.contract_id


def test_real_path_builds_contract_referent_prompt_and_evaluator(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured: dict[str, list] = {}

    def fake_gpt(messages, **_kwargs):
        captured["messages"] = messages
        user = messages[1]["content"] if len(messages) > 1 else ""
        if "smell" in user.lower():
            return _gm_response("The iron latch smells of cold oil and smoke.")
        return _gm_response("The iron latch is a small cold fitting set into the post.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "I examine the iron latch."})
        second = client.post("/api/chat", json={"text": "What does it smell like?"})

    assert first.status_code == 200
    assert second.status_code == 200
    data = second.json()
    contract = ((data.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
    assert contract.get("dimension") == "smell"
    assert contract.get("referent_provenance") == "inherited_discourse"
    assert "latch" in str((contract.get("target_ref") or {}).get("id_or_text") or "").lower()
    obligation = ((data.get("resolution") or {}).get("metadata") or {}).get("interaction_obligation") or {}
    assert obligation.get("resolution_contract_id") == contract.get("contract_id")
    user_payload = json.loads(captured["messages"][1]["content"])
    assert user_payload["resolution_contract"]["dimension"] == "smell"
    assert "latch" in str(user_payload["resolution_contract"]["target"]).lower()
    evaluation = evaluate_playability(
        {
            "player_prompt": "What does it smell like?",
            "gm_text": data["gm_output"]["player_facing_text"],
            "resolution_contract": contract,
        }
    )
    assert evaluation["mandatory_gates"]["player_intent_addressed"]["evidence"]["resolution_contract"]["contract_id"] == contract["contract_id"]
    assert evaluation["mandatory_gates"]["player_intent_addressed"]["evidence"]["resolution_contract"]["assessment_status"] == "satisfied"


def test_real_path_emission_replaces_generic_scene_for_smell(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response("Watchers crowd the gate while the serjeant stands in the square.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        response = TestClient(app).post("/api/chat", json={"text": "What does the cooking pot smell like?"})

    data = response.json()
    text = data["gm_output"]["player_facing_text"]
    assert "watchers crowd the gate" not in text.lower()
    assert "smell" in text.lower() or "scent" in text.lower()
    semantic = data["gm_output"]["metadata"]["emission_debug"]["resolution_contract_semantic"]
    assert semantic["status"] in {"legitimate_nonresolution", "satisfied"}
