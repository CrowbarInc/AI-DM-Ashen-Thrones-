"""PR-BR typed resolution contract and lightweight discourse focus."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from game.api import app
from game.api_turn_support import _preserve_resolution_contract_after_gate
from game.bounded_improvisation import validate_bounded_improvisation_proposal
from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus, note_emitted_npc_claim
from game.live_resolution import (
    attach_interaction_obligation,
    obligation_preserving_fallback_line,
    select_resolution_mode,
)
from game.playability_eval import evaluate_playability
from game.resolution_contract import assess_contract_satisfaction, construct_resolution_contract
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


def test_parser_label_echo_does_not_override_pronoun_focus():
    session = _focus(
        active_inspected={"id": "obj-4", "label": "iron latch", "kind": "object", "scene_id": "yard", "turn_index": 2}
    )
    contract = construct_resolution_contract(
        player_text="What does it smell like?",
        session=session,
        scene_id="yard",
        normalized_action={"type": "observe", "label": "What does it smell like?", "prompt": "What does it smell like?"},
    )
    assert contract.dimension == "smell"
    assert contract.referent_provenance == "inherited_discourse"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "obj-4"
    assert "latch" in (contract.target_ref.id_or_text or "")


def test_hear_that_follow_up_binds_claim_source_not_sound():
    session = _focus(active_claim={"id": "claim-2", "label": "The road is watched.", "kind": "claim", "turn_index": 2})
    contract = construct_resolution_contract(
        player_text="Where did you hear that?",
        session=session,
        scene_id="yard",
        normalized_action={"type": "question", "label": "Where did you hear that?"},
    )
    assert contract.dimension == "source"
    assert "sound" not in contract.dimensions
    assert "location" not in contract.dimensions
    assert contract.epistemic_mode == "npc_claim"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "claim-2"


def test_third_person_where_heard_is_source_not_the_utterance():
    contract = construct_resolution_contract(
        player_text="I ask the stew-seller where he heard the rumor he has been repeating.",
        session={"turn_counter": 3},
        scene_id="yard",
        normalized_action={
            "type": "question",
            "label": "I ask the stew-seller where he heard the rumor he has been repeating.",
        },
    )
    assert contract.dimension == "source"
    assert "sound" not in contract.dimensions
    assert contract.epistemic_mode == "npc_claim"
    assert contract.conversational_subject != contract.raw_input


def test_interlocutor_id_does_not_override_claim_follow_up():
    session = _focus(
        active_claim={"id": "claim-2", "label": "The road is watched.", "kind": "claim", "turn_index": 2},
        active_interlocutor={"id": "guard_captain", "label": "Guard Captain", "kind": "interlocutor", "turn_index": 2},
    )
    contract = construct_resolution_contract(
        player_text="That last part — who passed it to you?",
        session=session,
        scene_id="yard",
        normalized_action={"type": "question", "target_id": "guard_captain", "label": "That last part — who passed it to you?"},
    )
    assert contract.dimension == "source"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "claim-2"
    assert (contract.target_ref.id_or_text or "") != "guard_captain"


def test_handled_paper_is_wear_on_the_inspected_object():
    session = _focus(
        active_inspected={"id": "posting", "label": "the posted notice", "kind": "object", "scene_id": "yard", "turn_index": 2}
    )
    contract = construct_resolution_contract(
        player_text="Does the paper look recently handled, or has the weather had it for a while?",
        session=session,
        scene_id="yard",
        normalized_action={"type": "question", "target_id": "guard_captain", "label": "Does the paper look recently handled, or has the weather had it for a while?"},
    )
    assert contract.dimension in {"wear", "use"}
    assert contract.operation == "perceive"
    assert contract.referent_provenance == "inherited_discourse"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "posting"


def test_take_me_stays_an_action_not_an_npc_question():
    session = _focus(active_interlocutor={"id": "guard_captain", "label": "Guard Captain", "kind": "interlocutor", "turn_index": 4})
    contract = construct_resolution_contract(
        player_text="Take me as far as the gate allows toward that place.",
        session=session,
        scene_id="yard",
        normalized_action={"type": "question", "target_id": "guard_captain", "label": "Take me as far as the gate allows toward that place."},
    )
    assert contract.operation == "act"
    assert (contract.target_ref.id_or_text if contract.target_ref else "") != "guard_captain"


def test_see_from_here_is_not_forced_into_travel():
    contract = construct_resolution_contract(
        player_text="Before I commit, what can I see from here that confirms I am heading the right way?",
        session={"turn_counter": 6},
        scene_id="yard",
        normalized_action={"type": "travel", "target_id": "guard_captain", "label": "Before I commit, what can I see from here that confirms I am heading the right way?"},
    )
    assert contract.operation == "perceive"
    assert contract.dimension == "appearance"
    assert "location" not in contract.dimensions


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


def _assess(player: str, gm: str, **kwargs):
    contract = _contract(player, **kwargs).as_dict()
    return contract, assess_contract_satisfaction(gm, contract)


def test_confidence_echo_is_not_an_answer():
    _contract_obj, result = _assess("How sure are you?", "How sure are you?")
    assert result["status"] == "unsatisfied"
    assert "echo_not_answer" in result["reasons"]
    _contract_obj, paraphrased = _assess("How sure are you?", "You ask how sure he is.")
    assert paraphrased["status"] == "unsatisfied"


def test_smell_echo_is_not_an_answer():
    _contract_obj, result = _assess(
        "What does the cooking pot smell like?",
        "You wonder what the cooking pot smells like.",
    )
    assert result["status"] == "unsatisfied"
    assert "echo_not_answer" in result["reasons"]


def test_real_confidence_answer_is_satisfied():
    _contract_obj, result = _assess("How sure are you?", "I'm not certain. It's only gossip I won't stake much on.")
    assert result["status"] == "satisfied"


def test_action_topic_only_response_is_not_satisfied():
    session = _focus(active_actionable_lead={"id": "lead-1", "label": "the east lane", "kind": "lead", "turn_index": 1})
    contract, result = _assess("Take me there.", "Captain Thoran commands the watch tonight.", session=session)
    assert contract["operation"] == "act"
    assert result["status"] == "unsatisfied"
    assert "action_outcome_missing" in result["reasons"]


def test_action_success_refusal_condition_and_clarification():
    success = assess_contract_satisfaction("The guard nods and leads you toward the east gate.", _contract("Take me there.").as_dict())
    refusal = assess_contract_satisfaction("The guard shakes his head. 'I cannot leave my post.'", _contract("Take me there.").as_dict())
    condition = assess_contract_satisfaction("Not until my relief arrives.", _contract("Take me there.").as_dict())
    clarification = assess_contract_satisfaction("Which place do you mean?", _contract("Take me there.").as_dict())
    assert success["status"] == "satisfied"
    assert refusal["status"] == "legitimate_nonresolution"
    assert condition["status"] == "legitimate_nonresolution"
    assert clarification["status"] == "legitimate_nonresolution"


def test_accepted_emitted_claim_becomes_active_claim():
    session = {
        "active_scene_id": "yard",
        "bounded_improvisation": {
            "entries": [
                {
                    "id": "claim-3",
                    "kind": "npc_claim",
                    "status": "promoted",
                    "content": "A caravaner said something was moving near the old mill.",
                }
            ]
        },
    }
    emitted = 'The runner mutters, "Word is, a caravaner said something was moving near the old mill."'
    assert note_emitted_npc_claim(session, emitted_text=emitted, scene_id="yard") is True
    claim = session[DISCOURSE_FOCUS_KEY]["active_claim"]
    assert claim["id"] == "claim-3"
    assert claim["source"] == "claim_ledger"


def test_rejected_claim_is_not_promoted():
    session = {
        "active_scene_id": "yard",
        "bounded_improvisation": {
            "entries": [],
            "rejected": [
                {
                    "id": "claim-x",
                    "kind": "npc_claim",
                    "status": "rejected",
                    "content": "The captain is secretly the thief.",
                }
            ],
        },
    }
    emitted = 'Someone mutters, "Word is, the captain is secretly the thief."'
    assert note_emitted_npc_claim(session, emitted_text=emitted, scene_id="yard") is False
    claim = (session.get(DISCOURSE_FOCUS_KEY) or {}).get("active_claim")
    assert not claim


def test_claim_follow_ups_bind_source_confidence_location_and_time():
    session = _focus(
        active_claim={"id": "claim-3", "label": "A caravaner said something was moving near the old mill.", "kind": "claim", "turn_index": 1}
    )
    source = _contract("Who told you that?", session)
    confidence = _contract("How sure are you?", session)
    location = _contract("Where did they see that?", session)
    timed = _contract("When did that happen?", session)
    assert source.dimension == "source" and source.discourse_ref.id == "claim-3"
    assert confidence.dimension == "confidence" and confidence.discourse_ref.id == "claim-3"
    assert location.dimension == "location" and location.discourse_ref.id == "claim-3"
    assert timed.dimension == "time" and timed.discourse_ref.id == "claim-3"


def test_retry_echo_stays_unresolved_and_is_replaced():
    text = "How sure are you?"
    resolution = {"kind": "question", "prompt": text, "social": {"npc_name": "Mara"}}
    attach_interaction_obligation(
        resolution,
        player_text=text,
        session={"active_scene_id": "yard", "turn_counter": 2},
        scene_id="yard",
    )
    gm = {"player_facing_text": "You ask how sure he is.", "tags": [], "metadata": {}}
    _preserve_resolution_contract_after_gate(gm, resolution=resolution)
    assert "how sure" not in gm["player_facing_text"].lower()
    assert "resolution_contract_semantic_preserved" in gm["tags"]


def test_retry_action_topic_collapse_stays_unresolved():
    text = "Take me there."
    resolution = {"kind": "action", "prompt": text}
    attach_interaction_obligation(
        resolution,
        player_text=text,
        session={"active_scene_id": "yard", "turn_counter": 4},
        normalized_action={"type": "travel", "label": text},
        scene_id="yard",
    )
    gm = {"player_facing_text": "Captain Thoran commands the watch tonight.", "tags": [], "metadata": {}}
    _preserve_resolution_contract_after_gate(gm, resolution=resolution)
    lowered = gm["player_facing_text"].lower()
    assert "thoran" not in lowered
    assert "route" in lowered or "cannot" in lowered or "will not" in lowered


def test_evaluator_fails_echo_and_unresolved_action():
    confidence = _contract("How sure are you?").as_dict()
    echo = evaluate_playability(
        {"player_prompt": "How sure are you?", "gm_text": "You ask how sure he is.", "resolution_contract": confidence}
    )
    assert echo["semantic_result"] == "FAIL"
    assert echo["mandatory_gates"]["player_intent_addressed"]["evidence"]["resolution_contract"]["echo_detected"] is True
    action = _contract("Take me there.").as_dict()
    topical = evaluate_playability(
        {
            "player_prompt": "Take me there.",
            "gm_text": "Captain Thoran commands the watch tonight.",
            "resolution_contract": action,
        }
    )
    assert topical["semantic_result"] == "FAIL"


def test_real_path_promotes_emitted_claim_and_rejects_source_echo(tmp_path, monkeypatch):
    from tests.test_pr_bp_live_resolution_routing import _seed_runner_dialogue_context

    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    claim_reply = _gm_response('Tavern Runner says, "Travelers say carts have vanished along the east lane."')
    echo_reply = _gm_response("You ask who told him that.")

    def fake_gpt(messages, **_kwargs):
        blob = json.dumps(messages).lower()
        if "who told" in blob:
            return echo_reply
        return claim_reply

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "What rumors have you heard?"}).json()
        second = client.post("/api/chat", json={"text": "Who told you that?"}).json()

    claim = ((first.get("session") or {}).get("discourse_focus") or {}).get("active_claim") or {}
    assert "carts" in str(claim.get("label") or "").lower() or "vanished" in str(claim.get("label") or "").lower()
    contract = ((second.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
    assert contract.get("dimension") == "source"
    assert (contract.get("discourse_ref") or {}).get("id")
    visible = second["gm_output"]["player_facing_text"].lower()
    assert "who told you that" not in visible


def _claim_session():
    return _focus(
        active_claim={
            "id": "claim-3",
            "label": "A caravaner said something was moving near the old mill.",
            "kind": "claim",
            "turn_index": 1,
        },
        active_interlocutor={"id": "runner", "label": "Tavern Runner", "kind": "interlocutor", "turn_index": 1},
    )


def test_indirect_source_confidence_location_and_time_follow_ups():
    session = _claim_session()
    cases = (
        ("Who told him?", "source"),
        ("Who did he hear that from?", "source"),
        ("How does she know that?", "source"),
        ("How sure is he?", "confidence"),
        ("Does he believe it?", "confidence"),
        ("Does she trust the story?", "confidence"),
        ("Where did they see it?", "location"),
        ("How long ago was that?", "time"),
        ("Was that today?", "time"),
        ("What place was he talking about?", "location"),
    )
    for text, dimension in cases:
        contract = _contract(text, session)
        assert contract.dimension == dimension, text
        assert contract.discourse_ref is not None, text
        assert contract.discourse_ref.id == "claim-3", text
        assert contract.construction["active_claim_inherited"] is True
        assert "pronoun" in contract.construction["cues"] or dimension == "source" and "Who told him?" == text


def test_named_object_is_not_an_ambiguous_pronoun():
    session = _focus(
        active_interlocutor={"id": "runner", "label": "Tavern Runner", "kind": "interlocutor", "scene_id": "yard"},
        active_actionable_lead={"id": "lead-1", "label": "east lane", "kind": "lead", "scene_id": "yard"},
    )
    contract = _contract("I stop at the posted sheet and look it over.", session)
    assert contract.ambiguous is False
    assert contract.referent_provenance == "explicit_player"
    assert "sheet" in (contract.target_ref.id_or_text or "")
    resolution = {
        "kind": "question",
        "prompt": "What about that?",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner"},
    }
    attach_interaction_obligation(
        resolution,
        player_text="What about that?",
        session=_focus(
            active_inspected={"id": "obj-1", "label": "iron latch", "kind": "object", "scene_id": "yard"},
            active_actionable_lead={"id": "lead-1", "label": "east lane", "kind": "lead", "scene_id": "yard"},
        ),
        scene_id="yard",
    )
    line = obligation_preserving_fallback_line(resolution)
    assert "Tavern Runner says" in line
    assert "Which do you mean?" in line


def test_referential_action_binds_unique_lead_and_clarifies_when_split():
    lead = {"id": "lead-7", "label": "check the east lane", "kind": "lead", "scene_id": "yard", "turn_index": 2}
    unique = _focus(active_actionable_lead=lead)
    step = _contract("I take that step.", unique)
    assert step.request_kind == "action"
    assert step.operation == "act"
    assert step.expected_resolution == "action_outcome"
    assert step.discourse_ref is not None
    assert step.discourse_ref.id == "lead-7"
    assert step.construction["actionable_inherited"] is True
    do_that = _contract("I do that.", unique)
    assert do_that.request_kind == "action"
    assert do_that.discourse_ref.id == "lead-7"
    split = _focus(
        active_actionable_lead=lead,
        last_attempted_action={"id": "act-1", "label": "I try the latch.", "kind": "act", "scene_id": "yard", "turn_index": 1},
    )
    ambiguous = _contract("I do that.", split)
    assert ambiguous.ambiguous is True
    assert ambiguous.expected_resolution == "clarification"
    assert ambiguous.discourse_ref is None
    assert ambiguous.construction["ambiguity_detected"] is True


def test_wear_and_recent_use_stay_perception_and_reject_social_fallback():
    session = _focus(
        active_inspected={"id": "posting", "label": "the posted notice", "kind": "object", "scene_id": "yard", "turn_index": 2}
    )
    worn = _contract("Does it look worn?", session)
    assert worn.operation == "perceive"
    assert "wear" in worn.dimensions
    assert worn.discourse_ref.id == "posting"
    recent = _contract("Does it look like this was handled recently?", session)
    assert recent.operation == "perceive"
    assert set(recent.dimensions) & {"wear", "use", "change"}
    assert recent.dimension != "appearance"
    resolution = {"kind": "question", "prompt": "Does it look worn?"}
    attach_interaction_obligation(resolution, player_text="Does it look worn?", session=session, scene_id="yard")
    line = obligation_preserving_fallback_line(resolution)
    assert "wear" in line.lower()
    assert "another source" not in line.lower()
    social = assess_contract_satisfaction(
        "No reliable source here can verify that; another source is needed.",
        worn.as_dict(),
    )
    assert social["status"] == "unsatisfied"
    assert "perception_routed_to_social_fallback" in social["reasons"]
    evaluated = evaluate_playability(
        {
            "player_prompt": "Does it look worn?",
            "gm_text": "No reliable source here can verify that; another source is needed.",
            "resolution_contract": worn.as_dict(),
        }
    )
    evidence = evaluated["mandatory_gates"]["player_intent_addressed"]["evidence"]["resolution_contract"]
    assert evaluated["semantic_result"] == "FAIL"
    assert evidence["failure_locus"] == "response_missed_contract"
    assert "wear" in (evidence.get("construction") or {}).get("cues", [])


def test_retry_preserves_claim_dimension_and_request_kind():
    text = "Who did he hear that from?"
    resolution = {"kind": "question", "prompt": text, "social": {"npc_id": "runner", "npc_name": "Tavern Runner"}}
    session = _claim_session()
    attach_interaction_obligation(resolution, player_text=text, session=session, scene_id="yard")
    first = dict(resolution["metadata"]["resolution_contract"])
    attach_interaction_obligation(
        resolution,
        player_text="What color is the sky?",
        session=session,
        scene_id="yard",
    )
    second = resolution["metadata"]["resolution_contract"]
    assert second["retry_preserved"] is True
    assert second["dimension"] == "source"
    assert second["request_kind"] == first["request_kind"]
    assert (second.get("discourse_ref") or {}).get("id") == "claim-3"
    assert second["contract_id"] == first["contract_id"]


def test_real_path_promoted_claim_accepts_indirect_follow_ups(tmp_path, monkeypatch):
    from game import storage
    from tests.test_pr_bp_live_resolution_routing import _seed_runner_dialogue_context

    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    claim_reply = _gm_response('Tavern Runner says, "Travelers say carts have vanished along the east lane."')
    source_reply = _gm_response('Tavern Runner says, "A drover on the east lane told me."')
    confidence_reply = _gm_response('Tavern Runner says, "I believe it, though I am not certain."')

    def fake_gpt(messages, **_kwargs):
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        low = user.lower()
        if "trust the story" in low:
            return confidence_reply
        if "hear that from" in low:
            return source_reply
        return claim_reply

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "What rumors have you heard?"}).json()
        second = client.post("/api/chat", json={"text": "Who did he hear that from?"}).json()
        third = client.post("/api/chat", json={"text": "Does she trust the story?"}).json()

    claim = ((first.get("session") or {}).get("discourse_focus") or {}).get("active_claim") or {}
    assert claim.get("id")
    assert claim.get("source") in {"claim_ledger", "emitted_npc_claim"}
    assert "vanished" in str(claim.get("label") or "").lower() or "carts" in str(claim.get("label") or "").lower()
    ledger = storage.load_session().get("bounded_improvisation") or {}
    entries = [entry for entry in (ledger.get("entries") or []) if isinstance(entry, dict) and entry.get("kind") == "npc_claim"]
    assert entries
    assert entries[-1]["truth_status"] == "not_world_truth"
    source = ((second.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
    confidence = ((third.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
    assert source.get("dimension") == "source"
    assert (source.get("discourse_ref") or {}).get("type") == "claim"
    assert (source.get("construction") or {}).get("active_claim_inherited") is True
    assert confidence.get("dimension") == "confidence"
    assert (confidence.get("discourse_ref") or {}).get("id") == (source.get("discourse_ref") or {}).get("id")
    source_text = second["gm_output"]["player_facing_text"].lower()
    confidence_text = third["gm_output"]["player_facing_text"].lower()
    assert "who did he hear that from" not in source_text
    assert any(word in source_text for word in ("drover", "told", "source", "certainty"))
    assert any(word in confidence_text for word in ("believe", "certain", "trust", "certainty"))


def test_real_path_refusal_does_not_promote_active_claim(tmp_path, monkeypatch):
    from tests.test_pr_bp_live_resolution_routing import _seed_runner_dialogue_context

    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response('Tavern Runner says, "I do not know enough to answer that."')

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        payload = client.post("/api/chat", json={"text": "What rumors have you heard?"}).json()

    claim = ((payload.get("session") or {}).get("discourse_focus") or {}).get("active_claim")
    assert not claim


def test_real_path_wear_question_does_not_emit_social_fallback(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response("You will need another source for that.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        payload = TestClient(app).post("/api/chat", json={"text": "Does the posted sheet look worn?"}).json()

    contract = ((payload.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
    assert contract.get("operation") == "perceive"
    assert "wear" in (contract.get("dimensions") or [])
    visible = payload["gm_output"]["player_facing_text"].lower()
    assert "another source" not in visible
    assert "wear" in visible or "marks" in visible


def _source_resolution(text: str = "Who did he hear that from?"):
    session = _claim_session()
    contract = construct_resolution_contract(player_text=text, session=session, scene_id="yard")
    resolution = {
        "kind": "question",
        "prompt": text,
        "success": None,
        "social": {"npc_name": "Gate Serjeant", "npc_reply_expected": True},
        "metadata": {
            "resolution_contract": contract.as_dict(),
            "interaction_obligation": {"kind": "follow_up", "subject": "the earlier claim"},
        },
    }
    return resolution, contract


def test_valid_source_answer_is_not_replaced_by_unrelated_fact():
    from game.social_exchange_emission import build_final_strict_social_response

    resolution, _contract = _source_resolution()
    candidate = 'Gate Serjeant says, "It was from them. The runner passed that word."'
    session = {
        "clue_knowledge": {
            "patrol_route_change": {
                "source_scene": "yard",
                "text": "The patrol route changed after the Ash Compact census choke worsened.",
                "presentation": "actionable",
            }
        }
    }
    text, details = build_final_strict_social_response(
        candidate,
        resolution=resolution,
        session=session,
        scene_id="yard",
    )
    low = text.lower()
    assert "from them" in low or "runner" in low
    assert "census choke" not in low
    assert details.get("semantic_payload_preserved") is True


def test_source_speaker_repair_keeps_the_source_payload():
    from game.social_exchange_emission import build_final_strict_social_response

    resolution, _contract = _source_resolution()
    candidate = (
        'The yard watches. "It was from the runner; he heard it from them." '
        "A hidden passage under the gate is the true motive."
    )
    text, details = build_final_strict_social_response(
        candidate,
        resolution=resolution,
        session={},
        scene_id="yard",
    )
    low = text.lower()
    assert "from the runner" in low or "from them" in low or "heard it" in low
    assert "hidden passage" not in low
    assert "true motive" not in low
    assert details.get("repair_attempted") is True


def test_unrelated_grounded_fact_is_rejected_for_source_contract():
    from game.social import apply_authored_knowledge_realization_to_gm

    resolution, _contract = _source_resolution()
    gm = {
        "player_facing_text": 'Gate Serjeant says, "It was from them."',
        "metadata": {},
    }
    resolution["social"]["topic_revealed"] = {
        "text": "The patrol route changed after the Ash Compact census choke worsened."
    }
    out = apply_authored_knowledge_realization_to_gm(
        gm,
        player_text="Who did he hear that from?",
        resolution=resolution,
        session={"scene_runtime": {}},
        world={},
        scene={"scene": {"id": "yard"}},
        scene_id="yard",
        extra_facts=["The patrol route changed after the Ash Compact census choke worsened."],
    )
    assert "from them" in out["player_facing_text"].lower()
    assert "census choke" not in out["player_facing_text"].lower()


def test_source_inability_is_allowed_when_source_cannot_be_established():
    from game.live_resolution import obligation_preserving_fallback_line
    from game.resolution_contract import semantic_line_view

    resolution, _contract = _source_resolution()
    line = obligation_preserving_fallback_line(resolution)
    view = semantic_line_view(line, resolution)
    assert view["compatible"] is True
    assert "census" not in line.lower()
    assert "source" in line.lower() or "cannot verify" in line.lower()


def test_inspection_description_survives_and_social_inability_does_not_count():
    from game.social_exchange_emission import build_final_strict_social_response

    text = "I stop at the posted sheet and look it over."
    contract = construct_resolution_contract(player_text=text, session=_focus(), scene_id="yard")
    assert contract.operation == "inspect"
    resolution = {
        "kind": "question",
        "prompt": text,
        "social": {"npc_name": "Gate Serjeant"},
        "metadata": {
            "resolution_contract": contract.as_dict(),
            "interaction_obligation": {"kind": "inspection", "subject": "posted sheet"},
        },
    }
    candidate = 'Gate Serjeant says, "The posted sheet lists the curfew, the tax notice, and a patrol warning."'
    emitted, details = build_final_strict_social_response(candidate, resolution=resolution, session={}, scene_id="yard")
    assert "posted sheet" in emitted.lower() or "curfew" in emitted.lower()
    assert "another source" not in emitted.lower()
    assert details.get("semantic_payload_preserved") is True
    social = assess_contract_satisfaction(
        'Gate Serjeant says, "I couldn\'t tell you the requested information; you will need another source."',
        contract.as_dict(),
    )
    assert social["status"] == "unsatisfied"


def test_inspection_strips_consequential_sentence_and_keeps_description():
    from game.social_exchange_emission import build_final_strict_social_response

    text = "I examine the posted sheet."
    contract = construct_resolution_contract(player_text=text, session=_focus(), scene_id="yard")
    resolution = {
        "kind": "question",
        "prompt": text,
        "social": {"npc_name": "Gate Serjeant"},
        "metadata": {"resolution_contract": contract.as_dict(), "interaction_obligation": {"kind": "inspection"}},
    }
    candidate = (
        'Gate Serjeant says, "The posted sheet is rain-spotted and lists the curfew." '
        "The true motive is a conspiracy."
    )
    emitted, _details = build_final_strict_social_response(candidate, resolution=resolution, session={}, scene_id="yard")
    low = emitted.lower()
    assert "curfew" in low or "posted sheet" in low
    assert "conspiracy" not in low
    assert "true motive" not in low


def test_action_answer_is_not_replaced_by_topical_information():
    from game.resolution_contract import retain_resolved_contract_text

    lead = {"id": "lead-7", "label": "check the east lane", "kind": "lead", "scene_id": "yard", "turn_index": 2}
    contract = construct_resolution_contract(player_text="I take that step.", session=_focus(active_actionable_lead=lead), scene_id="yard")
    resolution = {"metadata": {"resolution_contract": contract.as_dict()}}
    kept, preserved = retain_resolved_contract_text(
        "The serjeant leads you toward the east lane.",
        "Word is, the patrol route changed after the Ash Compact census choke worsened.",
        resolution,
    )
    assert preserved is True
    assert "east lane" in kept.lower()
    assert "census" not in kept.lower()


def test_retry_keeps_source_answer_when_retry_text_drops_it():
    from game.resolution_contract import retain_resolved_contract_text

    resolution, _contract = _source_resolution()
    kept, preserved = retain_resolved_contract_text(
        'Gate Serjeant says, "It was from them."',
        "Word is, the patrol route changed after the Ash Compact census choke worsened.",
        resolution,
    )
    assert preserved is True
    assert "from them" in kept.lower()


def test_hedge_with_say_is_not_promoted_and_real_assertion_is():
    session = {"discourse_focus": {"scene_id": "yard"}}
    assert note_emitted_npc_claim(
        session,
        emitted_text='Gate Serjeant says, "I can\'t say for sure if I trust it."',
        scene_id="yard",
    ) is False
    assert not (session.get("discourse_focus") or {}).get("active_claim")
    asserted = {}
    assert note_emitted_npc_claim(
        asserted,
        emitted_text='Tavern Runner says, "Travelers say carts have vanished along the east lane."',
        scene_id="yard",
    ) is True
    claim = asserted["discourse_focus"]["active_claim"]
    assert "vanished" in claim["label"].lower() or "carts" in claim["label"].lower()
    discarded = {"discourse_focus": {}}
    assert note_emitted_npc_claim(
        discarded,
        emitted_text='Gate Serjeant says, "I cannot verify the source or certainty of that earlier claim."',
        scene_id="yard",
    ) is False


def test_look_it_over_establishes_inspected_object_for_later_it():
    first_text = "I stop at the posted sheet and look it over."
    first = construct_resolution_contract(player_text=first_text, session=_focus(), scene_id="yard")
    assert first.operation == "inspect"
    assert "sheet" in (first.target_ref.id_or_text or "")
    session = {"discourse_focus": {"scene_id": "yard"}}
    commit_discourse_focus(session, contract=first.as_dict(), scene_id="yard")
    inspected = session["discourse_focus"]["active_inspected"]
    assert inspected
    assert "sheet" in str(inspected.get("label") or "").lower()
    follow = construct_resolution_contract(
        player_text="Does it look like people use this often?",
        session=session,
        scene_id="yard",
    )
    assert "use" in follow.dimensions or follow.dimension in {"use", "wear"}
    assert follow.discourse_ref is not None
    assert follow.discourse_ref.id == inspected.get("id") or "sheet" in str(follow.discourse_ref.label or "").lower()


def test_come_through_is_not_wear_and_real_use_still_is():
    travelers = construct_resolution_contract(
        player_text="I ask the gate serjeant what travelers have been repeating as they come through.",
        session=_focus(),
        scene_id="yard",
    )
    assert "wear" not in travelers.dimensions
    assert "use" not in travelers.dimensions
    assert travelers.operation != "perceive"
    used = construct_resolution_contract(
        player_text="Does it look like people use this often?",
        session=_focus(active_inspected={"id": "sheet", "label": "posted sheet", "kind": "object", "scene_id": "yard"}),
        scene_id="yard",
    )
    assert "use" in used.dimensions


def test_real_path_source_answer_survives_unrelated_authored_fact(tmp_path, monkeypatch):
    from game import storage
    from tests.test_pr_bp_live_resolution_routing import _seed_runner_dialogue_context

    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    claim_reply = _gm_response('Tavern Runner says, "Travelers say carts have vanished along the east lane."')
    source_reply = _gm_response('Tavern Runner says, "It was from them. A drover passed that word."')

    def fake_gpt(messages, **_kwargs):
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        if "hear that from" in user.lower():
            return source_reply
        return claim_reply

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        client.post("/api/chat", json={"text": "What rumors have you heard?"})
        session = storage.load_session()
        session["clue_knowledge"] = {
            "patrol_route_change": {
                "source_scene": "frontier_gate",
                "text": "The patrol route changed after the Ash Compact census choke worsened.",
                "presentation": "actionable",
            }
        }
        storage.save_session(session)
        second = client.post("/api/chat", json={"text": "Who did he hear that from?"}).json()

    visible = second["gm_output"]["player_facing_text"].lower()
    contract = ((second.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
    assert contract.get("dimension") == "source"
    assert "census choke" not in visible
    assert any(word in visible for word in ("drover", "from them", "runner", "told"))


def test_real_path_look_it_over_keeps_the_description(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response(
            'The posted sheet is rain-spotted. It lists the curfew, a tax notice, and a warning about the missing patrol.'
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        payload = TestClient(app).post(
            "/api/chat",
            json={"text": "I stop at the posted sheet and look it over."},
        ).json()

    contract = ((payload.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
    visible = payload["gm_output"]["player_facing_text"].lower()
    focus = ((payload.get("session") or {}).get("discourse_focus") or {})
    assert contract.get("operation") == "inspect"
    assert "another source" not in visible
    assert "couldn't tell you the requested" not in visible
    assert "could not tell you the requested" not in visible
    assert any(
        token in visible
        for token in ("curfew", "posted sheet", "patrol", "sheet", "paper", "shelves", "look")
    )
    inspected = focus.get("active_inspected") or {}
    assert "sheet" in str(inspected.get("label") or "").lower()


def _sheet_session():
    return _focus(
        active_inspected={"id": "sheet", "label": "posted sheet", "kind": "object", "scene_id": "yard", "turn_index": 2},
        active_interlocutor={"id": "gate_serjeant", "label": "Gate Serjeant", "kind": "interlocutor", "scene_id": "yard"},
        active_claim={
            "id": "claim-1",
            "label": "carts have vanished along the east lane",
            "kind": "claim",
            "scene_id": "yard",
            "turn_index": 1,
        },
    )


def test_dimensionless_rumor_distinguishes_answer_ack_inability_and_unrelated_fact():
    contract = _contract("What rumor are travelers repeating?").as_dict()
    assert contract["operation"] == "ask"
    assert contract["dimension"] == "content"
    answered = assess_contract_satisfaction(
        "Travelers say carts have vanished along the east lane.",
        contract,
    )
    assert answered["status"] == "satisfied"
    assert answered["operation_compatible"] is True
    acknowledgement = assess_contract_satisfaction("There has been talk.", contract)
    assert acknowledgement["status"] == "unsatisfied"
    assert "topic_acknowledgement" in acknowledgement["reasons"]
    inability = assess_contract_satisfaction("I do not know what rumor is being repeated.", contract)
    assert inability["status"] == "legitimate_nonresolution"
    assert inability["resolution_kind"] == "inability"
    unrelated = assess_contract_satisfaction("The gate serjeant stands watch over the square.", contract)
    assert unrelated["status"] == "unsatisfied"
    hedge = assess_contract_satisfaction("I have heard talk, but I cannot verify it.", contract)
    assert hedge["status"] == "unsatisfied"


def test_repeat_requires_the_same_claim_and_rejects_a_generic_action_refusal():
    contract = _contract("Repeat that rumor.", _sheet_session()).as_dict()
    assert contract["operation"] == "repeat"
    assert "east lane" in str((contract.get("discourse_ref") or {}).get("label") or "")
    same = assess_contract_satisfaction("Carts vanished on the east lane.", contract)
    assert same["status"] == "satisfied"
    different = assess_contract_satisfaction("The well in the lower town has run dry.", contract)
    assert different["status"] == "unsatisfied"
    generic = assess_contract_satisfaction(
        "I will not carry out that request; you will need another route.",
        contract,
    )
    assert generic["status"] == "unsatisfied"
    assert generic["resolution_kind"] != "answer"
    refusal = assess_contract_satisfaction("I will not repeat that rumor.", contract)
    assert refusal["status"] == "legitimate_nonresolution"
    assert refusal["resolution_kind"] == "refusal"


def test_inspection_satisfaction_is_target_aware_and_ignores_length():
    contract = _contract("Look the posted sheet over.").as_dict()
    assert contract["operation"] == "inspect"
    assert "sheet" in str((contract.get("target_ref") or {}).get("id_or_text") or "")
    right = assess_contract_satisfaction(
        "The sheet lists a curfew, tax notices, and a missing patrol.",
        contract,
    )
    assert right["status"] == "satisfied"
    assert right["target_compatible"] is True
    wrong = assess_contract_satisfaction(
        "The inspection establishes no further reliable detail about gate_serjeant.",
        contract,
    )
    assert wrong["status"] == "unsatisfied"
    assert wrong["target_compatible"] is False
    long_wrong = assess_contract_satisfaction(
        "The gate serjeant adjusts his cloak and watches the road while the crowd moves through the square.",
        contract,
    )
    assert long_wrong["status"] == "unsatisfied"
    short = assess_contract_satisfaction("The sheet is blank.", contract)
    assert short["status"] == "satisfied"
    sealed = assess_contract_satisfaction("You can't read the posted sheet while it is sealed.", contract)
    assert sealed["status"] == "legitimate_nonresolution"
    assert sealed["resolution_kind"] == "inability"


def test_content_follow_up_inherits_active_inspected_and_clarifies_two_objects():
    session = _sheet_session()
    said = _contract("What does it actually say?", session)
    assert said.operation in {"ask", "inspect"}
    assert "content" in said.dimensions
    assert said.ambiguous is False
    assert "sheet" in str(said.target_ref.id_or_text or "")
    written = _contract("What is written on it?", session)
    assert "sheet" in str(written.target_ref.id_or_text or "")
    assert written.ambiguous is False
    split = _contract("What does the sheet or the ledger actually say?", session)
    assert split.ambiguous is True
    assert split.expected_resolution == "clarification"
    person = _contract("What did he say?", session)
    assert person.discourse_ref is None or person.discourse_ref.type != "object"


def test_use_follow_up_still_binds_the_inspected_sheet():
    used = _contract("Does it look like people use this often?", _sheet_session())
    assert "use" in used.dimensions
    assert "sheet" in str(used.target_ref.id_or_text or "")
    answer = assess_contract_satisfaction("It looks heavily used by many hands.", used.as_dict())
    assert answer["status"] in {"satisfied", "partial"}
    assert answer["target_compatible"] is not False


def test_source_answer_still_satisfies_and_generic_refusal_does_not():
    resolution, contract = _source_resolution()
    payload = contract.as_dict() if hasattr(contract, "as_dict") else contract
    answer = assess_contract_satisfaction('Gate Serjeant says, "It was from them."', payload)
    assert answer["status"] == "satisfied"
    refusal = assess_contract_satisfaction(
        "I will not carry out that request; you will need another route.",
        payload,
    )
    assert refusal["status"] == "unsatisfied"
    assert semantic_compatible(resolution)


def semantic_compatible(resolution):
    from game.resolution_contract import semantic_line_view

    view = semantic_line_view('Gate Serjeant says, "It was from them."', resolution)
    assert view["keeps_answer"] is True
    return True


def test_action_resolution_stays_structural():
    success = assess_contract_satisfaction(
        "The guard nods and leads you toward the east gate.",
        _contract("Take me there.").as_dict(),
    )
    assert success["status"] == "satisfied"
    topic = assess_contract_satisfaction(
        "Word is, the patrol route changed after the census.",
        _contract("Take me there.").as_dict(),
    )
    assert topic["status"] == "unsatisfied"


def test_fallback_about_the_wrong_target_is_not_satisfied_and_sheet_inability_is():
    text = "Look the posted sheet over."
    contract = construct_resolution_contract(player_text=text, session=_focus(), scene_id="yard")
    resolution = {
        "kind": "question",
        "prompt": text,
        "social": {"npc_id": "gate_serjeant", "npc_name": "Gate Serjeant"},
        "metadata": {
            "resolution_contract": contract.as_dict(),
            "interaction_obligation": {"kind": "inspection", "subject": "gate_serjeant"},
        },
    }
    line = obligation_preserving_fallback_line(resolution)
    assert "gate_serjeant" not in line.lower()
    assert "sheet" in line.lower()
    assessment = assess_contract_satisfaction(line, contract.as_dict())
    assert assessment["status"] == "legitimate_nonresolution"
    wrong = assess_contract_satisfaction(
        "The inspection establishes no further reliable detail about gate_serjeant.",
        contract.as_dict(),
    )
    assert wrong["status"] == "unsatisfied"


def test_satisfying_sheet_quote_is_not_replaced_by_a_wrong_target_stock_line():
    from game.social_exchange_emission import build_final_strict_social_response

    text = "Look the posted sheet over."
    contract = construct_resolution_contract(player_text=text, session=_focus(), scene_id="yard")
    resolution = {
        "kind": "question",
        "prompt": text,
        "social": {"npc_name": "Gate Serjeant"},
        "metadata": {
            "resolution_contract": contract.as_dict(),
            "interaction_obligation": {"kind": "inspection", "subject": "posted sheet"},
        },
    }
    candidate = (
        'The gate serjeant glances at the posted sheet. '
        '"The notice lists taxes, a curfew, and the missing patrol," they say.'
    )
    emitted, details = build_final_strict_social_response(candidate, resolution=resolution, session={}, scene_id="yard")
    low = emitted.lower()
    assert any(token in low for token in ("notice", "curfew", "taxes", "patrol", "sheet"))
    assert "gate_serjeant" not in low
    assert details.get("semantic_payload_preserved") is True or "curfew" in low or "taxes" in low


def test_evaluator_uses_satisfaction_for_rumor_repeat_and_inspection_targets():
    rumor = _contract("What rumor are travelers repeating?").as_dict()
    answered = evaluate_playability(
        {
            "player_prompt": rumor["raw_input"],
            "gm_text": "Travelers say carts have vanished along the east lane.",
            "resolution_contract": rumor,
        }
    )
    assert answered["semantic_result"] == "PASS"
    ack = evaluate_playability(
        {
            "player_prompt": rumor["raw_input"],
            "gm_text": "There has been talk.",
            "resolution_contract": rumor,
        }
    )
    assert ack["semantic_result"] == "FAIL"
    sheet = _contract("Look the posted sheet over.").as_dict()
    wrong = evaluate_playability(
        {
            "player_prompt": sheet["raw_input"],
            "gm_text": "The inspection establishes no further reliable detail about gate_serjeant.",
            "resolution_contract": sheet,
        }
    )
    assert wrong["semantic_result"] == "FAIL"
    right = evaluate_playability(
        {
            "player_prompt": sheet["raw_input"],
            "gm_text": "The sheet lists a curfew and a tax notice.",
            "resolution_contract": sheet,
        }
    )
    assert right["semantic_result"] == "PASS"
    inability = evaluate_playability(
        {
            "player_prompt": sheet["raw_input"],
            "gm_text": "You can't read the posted sheet while it is sealed.",
            "resolution_contract": sheet,
        }
    )
    assert inability["semantic_result"] == "PASS"


def test_real_path_rumor_repeat_and_sheet_content(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    rumor = 'Tavern Runner says, "Travelers say carts have vanished along the east lane."'
    repeated = 'Tavern Runner says, "Carts vanished on the east lane."'
    sheet = 'The notice lists taxes, a curfew, and a missing patrol.'
    content = 'The posted sheet says the curfew starts at dusk, with a tax notice under it.'
    wear = "It looks heavily used. The corners are soft from many hands."

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
        if "what rumor are travelers repeating" in low:
            return _gm_response(rumor)
        return _gm_response(rumor)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "What rumor are travelers repeating?"}).json()
        second = client.post("/api/chat", json={"text": "Repeat that rumor."}).json()
        third = client.post("/api/chat", json={"text": "Look the posted sheet over."}).json()
        fourth = client.post("/api/chat", json={"text": "What does it actually say?"}).json()
        fifth = client.post("/api/chat", json={"text": "Does it look like people use this often?"}).json()

    def visible(payload):
        return payload["gm_output"]["player_facing_text"].lower()

    def contract_of(payload):
        return ((payload.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}

    assert "east lane" in visible(first) or "vanished" in visible(first) or "carts" in visible(first)
    assert "have heard talk" not in visible(first)
    repeat_contract = contract_of(second)
    assert repeat_contract.get("operation") == "repeat"
    assert "east lane" in visible(second) or "vanished" in visible(second) or "carts" in visible(second)
    assert "another route" not in visible(second)
    sheet_contract = contract_of(third)
    assert sheet_contract.get("operation") == "inspect"
    assert "sheet" in str((sheet_contract.get("target_ref") or {}).get("id_or_text") or "")
    assert "gate_serjeant" not in visible(third)
    assert any(token in visible(third) for token in ("curfew", "tax", "notice", "patrol", "sheet"))
    content_contract = contract_of(fourth)
    assert "sheet" in str((content_contract.get("target_ref") or {}).get("id_or_text") or "").lower()
    assert content_contract.get("ambiguous") is not True
    assert "which do you mean" not in visible(fourth)
    use_contract = contract_of(fifth)
    assert "use" in (use_contract.get("dimensions") or [])
    assert "sheet" in str((use_contract.get("target_ref") or {}).get("id_or_text") or "").lower()
    assert "used" in visible(fifth) or "hands" in visible(fifth)
