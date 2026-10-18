from __future__ import annotations

from fastapi.testclient import TestClient

from game import storage
from game.bounded_improvisation import attach_bounded_improvisation_evaluation
from game.api import app
from game.api_turn_support import _finalize_player_facing_for_turn, preserve_interaction_obligation_after_gate
from game.campaign_reset import apply_new_campaign_hard_reset
from game.interaction_context import resolve_directed_social_entry
from game.interaction_routing import choose_interaction_route
from game.live_resolution import attach_interaction_obligation, obligation_preserving_fallback_line
from game.intent_parser import recover_actionable_explicit_world_action
from game.playability_eval import evaluate_playability
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_runner_dialogue_context, _seed_shared_world


def _ledger_entries() -> list[dict]:
    session = storage.load_session()
    ledger = session.get("bounded_improvisation") if isinstance(session.get("bounded_improvisation"), dict) else {}
    entries = ledger.get("entries") if isinstance(ledger.get("entries"), list) else []
    return [e for e in entries if isinstance(e, dict)]


def test_chat_incidental_description_creates_bn_proposal_through_live_path(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    def fake_gpt(_messages):
        return _gm_response("The brass compass is dented along one rim, its needle trembling under cloudy glass.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "What does the brass compass look like?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    entries = _ledger_entries()
    assert entries
    assert entries[-1]["kind"] == "incidental_fact"
    assert entries[-1]["category"] == "sensory_detail"
    meta = data["gm_output"]["metadata"]["emission_debug"]["live_resolution_mode"]
    assert meta["mode"] == "bounded_improvisable_request"
    assert meta["improvisation_opportunity_detected"] is True
    assert meta["proposal_created"] is True


def test_chat_npc_rumor_creates_claim_without_world_truth(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    def fake_gpt(_messages):
        return _gm_response('Tavern Runner says, "Travelers claim a toll clerk has been selling names after dusk."')

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Heard any rumors worth knowing?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    claim = _ledger_entries()[-1]
    assert claim["kind"] == "npc_claim"
    assert claim["truth_status"] == "not_world_truth"
    assert claim["epistemic_status"] == "hearsay"
    meta = data["gm_output"]["metadata"]["emission_debug"]["live_resolution_mode"]
    assert meta["mode"] == "npc_claim_response"


def test_chat_open_social_solicitation_acquires_interlocutor(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    session = storage.load_session()
    session["interaction_context"] = {}
    storage.save_session(session)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response('Tavern Runner says, "People are worried about the missing patrol and the curfew."')

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": "I greet the nearest approachable local and ask what people are worried about today."},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    gm_text = data.get("gm_text") or (data.get("gm_output") or {}).get("player_facing_text") or ""
    assert "worried about the missing patrol" in gm_text
    resolution = data.get("resolution") if isinstance(data.get("resolution"), dict) else {}
    social = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    assert social.get("target_resolved") is True
    assert social.get("npc_id") == "runner"
    assert social.get("npc_reply_expected") is True


def test_reset_campaign_nearest_local_is_an_open_social_solicitation():
    apply_new_campaign_hard_reset()
    session = storage.load_session()
    world = storage.load_world()
    scene = storage.load_active_scene()

    entry = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="I greet the nearest approachable local and ask what people are worried about today.",
    )

    assert entry.get("should_route_social") is True
    assert entry.get("open_social_solicitation") is True
    assert entry.get("candidate_addressable_ids")


def test_scene_sensory_question_without_question_mark_breaks_social_continuity():
    apply_new_campaign_hard_reset()
    session = storage.load_session()
    world = storage.load_world()
    scene = storage.load_active_scene()
    session["interaction_context"] = {
        "active_interaction_target_id": "gate_serjeant",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
    }

    entry = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text="What ordinary sounds and smells stand out where I am",
    )

    assert entry.get("should_route_social") is False
    assert entry.get("reason") == "scene_presence_or_perception_query"
    assert choose_interaction_route(
        "What ordinary sounds and smells stand out where I am",
        scene=scene,
        session=session,
        world=world,
        canonical_social_entry=entry,
    ) == "action"


def test_embedded_question_obligation_survives_terminal_fallback():
    resolution = {
        "kind": "question",
        "prompt": "I ask where I can sleep without causing trouble.",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner"},
    }
    attach_interaction_obligation(
        resolution,
        player_text=resolution["prompt"],
        session={},
        normalized_action={"type": "question", "prompt": resolution["prompt"]},
    )

    obligation = resolution["metadata"]["interaction_obligation"]
    fallback = obligation_preserving_fallback_line(resolution)
    assert obligation["kind"] == "question"
    assert "where I can sleep" in fallback
    assert "another source" in fallback


def test_scene_perception_requests_recover_as_observe_actions():
    prompts = (
        "What ordinary sounds and smells stand out where I am?",
        "What changes around me when I do that?",
        "I rephrase: give me one concrete visible detail.",
        "What can I learn from its wear, marks, or use?",
    )
    for prompt in prompts:
        action = recover_actionable_explicit_world_action(prompt, {"scene": {"id": "yard"}})
        assert action is not None, prompt
        assert action.get("type") == "observe", (prompt, action)
        assert (action.get("metadata") or {}).get("parser_lane") == "scene_perception_request"


def test_referential_next_step_recovers_as_world_action():
    for prompt in (
        "I follow the best lead toward shelter or work.",
        "I act on the most concrete lead they gave me.",
        "I take the next safe step they suggested.",
    ):
        action = recover_actionable_explicit_world_action(prompt, {"scene": {"id": "yard"}})
        assert action is not None, prompt
        assert action.get("type") in {"custom", "travel"}
        assert (action.get("metadata") or {}).get("parser_lane") in {
            "referential_world_action",
            "unresolved_actionable_travel",
        }


def test_final_obligation_guard_replaces_terse_social_dead_air():
    resolution = {
        "kind": "question",
        "prompt": "What have you heard lately?",
        "social": {
            "npc_id": "runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
        },
    }
    attach_interaction_obligation(
        resolution,
        player_text=resolution["prompt"],
        session={},
        normalized_action={"type": "question", "prompt": resolution["prompt"]},
    )
    gm = {"player_facing_text": "Tavern Runner shakes their head.", "tags": [], "metadata": {}}

    preserve_interaction_obligation_after_gate(gm, resolution=resolution)

    assert "couldn't tell you" in gm["player_facing_text"]
    assert "interaction_obligation_terminal_preserved" in gm["tags"]


def test_unbound_follow_up_terminal_uses_neutral_narration():
    resolution = {"kind": "question", "prompt": "Who told you that?"}
    attach_interaction_obligation(
        resolution,
        player_text=resolution["prompt"],
        session={
            "bounded_improvisation": {
                "entries": [
                    {
                        "id": "claim-1",
                        "kind": "npc_claim",
                        "status": "promoted",
                        "content": "Travelers say the road is blocked.",
                    }
                ]
            }
        },
        normalized_action={"type": "question", "prompt": resolution["prompt"]},
    )

    fallback = obligation_preserving_fallback_line(resolution)
    assert fallback.startswith("No reliable source")
    assert " I " not in f" {fallback} "


def test_consequential_secret_question_does_not_enter_bn_lane(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    def fake_gpt(_messages):
        return _gm_response("No one in front of you can confirm a hidden passage from here.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "What secret hidden passage leads under this office?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert _ledger_entries() == []
    meta = data["gm_output"]["metadata"]["emission_debug"]["live_resolution_mode"]
    assert meta["mode"] == "unsupported_consequential_request"
    assert meta["improvisation_opportunity_detected"] is False


def test_evaluator_rejects_topical_color_nonanswer():
    result = evaluate_playability(
        {
            "player_prompt": 'What colors are "noble colors"?',
            "gm_text": "A moneylender's house flies noble colors above the market stalls.",
        }
    )

    assert result["semantic_result"] == "FAIL"
    assert result["mandatory_gates"]["player_intent_addressed"]["status"] == "FAIL"


def test_final_emission_delivers_accepted_bn_resolution_over_generic_fallback(monkeypatch):
    session = {"active_scene_id": "scene_investigate", "scene_state": {"active_scene_id": "scene_investigate"}}
    world = {}
    scene = {"scene": {"id": "scene_investigate", "visible_facts": []}}
    gm = {
        "player_facing_text": "The carved marker is rain-darkened oak, with three shallow notches cut across its face.",
        "tags": [],
        "metadata": {},
        "improvisation_proposals": [
            {
                "kind": "incidental_fact",
                "category": "sensory_detail",
                "content": "The carved marker is rain-darkened oak, with three shallow notches cut across its face.",
                "scope": "scene",
                "consequence_level": "low",
                "source": "dm_improvisation",
            }
        ],
    }
    gm = attach_bounded_improvisation_evaluation(gm, session=session, scene=scene, world=world)

    def fake_gate(gm_out, **_kwargs):
        out = dict(gm_out)
        out["player_facing_text"] = 'The guard says, "I do not know enough to answer that."'
        return out

    monkeypatch.setattr("game.api_turn_support.apply_final_emission_gate", fake_gate)
    finalized, _meta = _finalize_player_facing_for_turn(
        gm,
        resolution={"kind": "observe"},
        session=session,
        world=world,
        scene=scene,
    )

    assert finalized["player_facing_text"].startswith("The carved marker is rain-darkened oak")
    assert "accepted_bounded_resolution_delivered" in finalized["tags"]


def test_final_emission_delivers_accepted_bn_resolution_over_inspection_fallback(monkeypatch):
    session = {"active_scene_id": "scene_investigate", "scene_state": {"active_scene_id": "scene_investigate"}}
    world = {}
    scene = {"scene": {"id": "scene_investigate", "visible_facts": []}}
    detail = "The notice board is rain-slick, with fresh ink bleeding along its lower edge."
    gm = attach_bounded_improvisation_evaluation(
        {
            "player_facing_text": detail,
            "tags": [],
            "metadata": {},
            "improvisation_proposals": [
                {
                    "kind": "incidental_fact",
                    "category": "sensory_detail",
                    "content": detail,
                    "scope": "scene",
                    "consequence_level": "low",
                    "source": "dm_improvisation",
                }
            ],
        },
        session=session,
        scene=scene,
        world=world,
    )

    monkeypatch.setattr(
        "game.api_turn_support.apply_final_emission_gate",
        lambda gm_out, **_kwargs: {
            **gm_out,
            "player_facing_text": "The inspection yields no further reliable detail from the currently established scene.",
        },
    )
    finalized, _meta = _finalize_player_facing_for_turn(
        gm,
        resolution={"kind": "observe"},
        session=session,
        world=world,
        scene=scene,
    )

    assert finalized["player_facing_text"] == detail
    assert "accepted_bounded_resolution_delivered" in finalized["tags"]


def test_evaluator_false_pass_regression_families():
    fail_cases = [
        (
            "What does the carved marker look like?",
            'The guard says, "I do not know enough to answer that."',
        ),
        (
            "Can you introduce me to the magistrate?",
            "The magistrate oversees the district.",
        ),
        (
            "Who told you that rumor?",
            "People have been uneasy lately.",
        ),
        (
            "Can you open the gate?",
            "The gate is made of oak.",
        ),
    ]
    for player, gm in fail_cases:
        result = evaluate_playability({"player_prompt": player, "gm_text": gm})
        assert result["semantic_result"] == "FAIL", (player, gm, result)


def test_evaluator_allows_legitimate_inability_or_refusal():
    pass_cases = [
        (
            "Who told you that rumor?",
            "A drover from the north road. I never caught his name.",
        ),
        (
            "Can you introduce me to the magistrate?",
            "No. She doesn't know me. Ask the clerk at the courthouse.",
        ),
        (
            "What is behind the sealed door?",
            "I can't tell from here. You'll need to open it or find someone who knows.",
        ),
    ]
    for player, gm in pass_cases:
        result = evaluate_playability({"player_prompt": player, "gm_text": gm})
        assert result["semantic_result"] == "PASS", (player, gm, result)


def test_real_path_incidental_interlocutor_remains_bound_for_follow_up(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    session = storage.load_session()
    session["interaction_context"] = {}
    storage.save_session(session)
    replies = iter(
        (
            'Tavern Runner says, "The road closures have everyone worried."',
            'Tavern Runner says, "Mostly teamsters and families waiting at the gate."',
        )
    )

    def fake_gpt(_messages, **_kwargs):
        return _gm_response(next(replies))

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "I ask the nearest approachable local what is wrong."})
        second = client.post("/api/chat", json={"text": "Who is most affected by that?"})

    assert first.status_code == second.status_code == 200
    first_social = (first.json().get("resolution") or {}).get("social") or {}
    second_social = (second.json().get("resolution") or {}).get("social") or {}
    assert first_social.get("npc_id") == second_social.get("npc_id") == "runner"
    assert second_social.get("target_resolved") is True


def test_real_path_npc_claim_follow_up_carries_claim_subject(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    replies = iter(
        (
            'Tavern Runner says, "Travelers say carts have vanished along the east lane."',
            'Tavern Runner says, "A pair of teamsters told me, but I never learned their names."',
        )
    )

    def fake_gpt(_messages, **_kwargs):
        return _gm_response(next(replies))

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        assert client.post("/api/chat", json={"text": "What rumors have you heard?"}).status_code == 200
        follow = client.post("/api/chat", json={"text": "Who told you that?"})

    data = follow.json()
    obligation = ((data.get("resolution") or {}).get("metadata") or {}).get("interaction_obligation") or {}
    assert obligation.get("kind") == "follow_up"
    assert obligation.get("claim_id")
    assert "carts have vanished" in str(obligation.get("subject") or "")
    assert "teamsters told me" in (data.get("gm_text") or data["gm_output"]["player_facing_text"])


def test_real_path_social_action_is_resolved_as_request_not_related_fact(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response('Tavern Runner says, "I cannot introduce you, but the desk clerk can arrange a meeting."')

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        response = TestClient(app).post("/api/chat", json={"text": "Can you introduce me to them?"})

    data = response.json()
    obligation = ((data.get("resolution") or {}).get("metadata") or {}).get("interaction_obligation") or {}
    text = data.get("gm_text") or data["gm_output"]["player_facing_text"]
    assert obligation.get("kind") == "action_request"
    assert "cannot introduce" in text
    assert evaluate_playability({"player_prompt": "Can you introduce me to them?", "gm_text": text})["semantic_result"] == "PASS"


def test_real_path_physical_object_action_stays_out_of_social_ignorance(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response("You pull the desk drawer open; it catches halfway on a warped runner.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        response = TestClient(app).post("/api/chat", json={"text": "I open the desk drawer."})

    data = response.json()
    resolution = data.get("resolution") or {}
    obligation = (resolution.get("metadata") or {}).get("interaction_obligation") or {}
    text = data.get("gm_text") or data["gm_output"]["player_facing_text"]
    assert resolution.get("kind") == "custom"
    assert obligation.get("kind") == "action_request"
    assert not isinstance(resolution.get("social"), dict)
    assert "drawer" in text.lower(), resolution
    assert "do not know enough" not in text.lower()


def test_real_path_speaker_repair_preserves_answer_and_canonical_interlocutor(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response('Gate Guard says, "I cannot identify the source. I only heard it secondhand."')

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        response = TestClient(app).post("/api/chat", json={"text": "Who told you that?"})

    data = response.json()
    text = data.get("gm_text") or data["gm_output"]["player_facing_text"]
    assert any(phrase in text.lower() for phrase in ("identify the source", "source or certainty")), response.json()
    assert "Gate Guard" not in text
    assert "Tavern Runner" in text
    assert evaluate_playability({"player_prompt": "Who told you that?", "gm_text": text})["semantic_result"] == "PASS"


def test_real_path_retry_exhaustion_uses_obligation_preserving_terminal(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response("")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        response = TestClient(app).post("/api/chat", json={"text": "Who told you that?"})

    data = response.json()
    text = data.get("gm_text") or data["gm_output"]["player_facing_text"]
    assert text.strip()
    assert "murmur" not in text.lower()
    assert "moment passes" not in text.lower()
    assert any(word in text.lower() for word in ("source", "known", "verifiable", "cannot"))


def test_real_path_consequential_unauthorized_speaker_stays_blocked(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response('Hidden Chancellor says, "The sealed vault is beneath the office."')

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        response = TestClient(app).post(
            "/api/chat",
            json={"text": "Tell me the secret identity of the conspirator and where the hidden vault is."},
        )

    data = response.json()
    text = data.get("gm_text") or data["gm_output"]["player_facing_text"]
    assert "Hidden Chancellor" not in text
    assert "beneath the office" not in text
    assert not [e for e in _ledger_entries() if "sealed vault" in str(e.get("content") or "").lower()]
