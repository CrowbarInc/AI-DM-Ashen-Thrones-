"""Shared turn-pipeline tests for /api/action and /api/chat.

These tests verify both endpoints exercise the same resolved-turn orchestration.

Per-test ``# feature: ...`` comments tag ownership for ``tools/test_audit.py``:
routing, retry, fallback, social, continuity, clues, leads, emission, legality.

Parametrized blocks (same setup + assertion shape): dialogue-lock route/output
variants; OOC adjudication without GPT; action vs chat runtime mutation before
model-request assembly.
Table-style dialogue-lock routing (pure ``choose_interaction_route``) lives in
``test_dialogue_routing_lock.py``; this module keeps HTTP pipeline locks only.
Explicit multi-turn / retry / emission-gate bug locks stay non-parametrized.

Emission authority boundary (Cycle AD-1):
- ``tests/test_final_emission_gate.py`` owns final-emission **orchestration** semantics
  (layer order, exact ``final_route`` / ``final_emitted_source`` / repair-kind tables,
  owner-bucket mapping, gate-private metadata).
- This module owns **downstream HTTP/API smoke** only: non-empty player text, obvious
  scaffold/procedural leakage bans, repair/replacement evidence, and response metadata
  needed to prove prompt→payload packaging through ``/api/chat`` and ``/api/action``.
- Prefer ``tests/helpers/emission_smoke_assertions.py`` for repeated smoke checks;
  do not restate exact gate internals here unless guarding HTTP packaging explicitly.
"""
from __future__ import annotations

from game.final_emission_meta import read_debug_notes_from_turn_payload
from game.narrative_authenticity_eval import _extract_final_emission_meta
from tests.helpers.emission_smoke_assertions import (
    assert_emission_repair_evidence,
    assert_global_visibility_stock_absent,
    assert_no_advisory_prose,
    assert_no_internal_scaffold_labels,
    assert_no_retry_coaching_leak_smoke,
    assert_no_social_visible_intro_filler_smoke,
    assert_no_uncertainty_fallback_stock_smoke,
    assert_no_unresolved_stock_phrases,
    assert_no_validator_voice_smoke,
    assert_player_text_present,
    assert_procedural_adjudication_smoke,
    assert_response_type_meta,
)
from tests.helpers.turn_pipeline_http_fixtures import (
    FAKE_GPT_RESPONSE,
    _gm_response,
    _patch_storage,
    _seed_runner_dialogue_context,
    _seed_shared_world,
)

import json
import copy

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from tests.debug_trace_utils import latest_compact_debug_trace_entry

pytestmark = pytest.mark.integration


def _assert_concrete_pressure(text: str) -> None:
    low = str(text or "").lower()
    assert any(
        phrase in low
        for phrase in (
            "\"",
            "cuts through the crowd",
            "stops at your shoulder",
            "comes straight to you",
            "squares up to you",
            "breaks the silence first",
            "if you're moving on this, move now",
            "question the runner",
            "work the notice",
            "east-road trail",
            "east road",
            "ask me now",
        )
    )


# feature: social, routing
def test_action_and_chat_social_use_equivalent_shared_turn_logic(tmp_path, monkeypatch):
    social_action = {
        "id": "question-runner",
        "label": "Talk to Tavern Runner",
        "type": "question",
        "prompt": "I talk to Tavern Runner.",
        "target_id": "runner",
        "targetEntityId": "runner",
    }

    def _seed_and_add_runner():
        _seed_shared_world(tmp_path, monkeypatch)
        world = storage.load_world()
        world["npcs"] = [
            {
                "id": "runner",
                "name": "Tavern Runner",
                "location": "scene_investigate",
                "topics": [{"id": "gate_rumor", "text": "The gate closes at dusk.", "clue_id": "gate_rumor"}],
            }
        ]
        storage._save_json(storage.WORLD_PATH, world)

    _seed_and_add_runner()
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        action_resp = client.post(
            "/api/action",
            json={"action_type": "social", "intent": "I talk to Tavern Runner.", "social_action": social_action},
        )
    assert action_resp.status_code == 200
    action_data = action_resp.json()

    _seed_and_add_runner()
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: social_action)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        chat_resp = client.post("/api/chat", json={"text": "I talk to Tavern Runner."})
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()

    assert action_data["ok"] is True
    assert chat_data["ok"] is True
    assert action_data["resolution"]["kind"] == "question"
    assert chat_data["resolution"]["kind"] == "question"
    assert action_data["resolution"]["requires_check"] is False
    assert chat_data["resolution"]["requires_check"] is False
    assert action_data["resolution"].get("check_request") is None
    assert chat_data["resolution"].get("check_request") is None
    assert action_data["resolution"]["social"]["npc_id"] == "runner"
    assert chat_data["resolution"]["social"]["npc_id"] == "runner"
    assert action_data["resolution"]["discovered_clues"] == chat_data["resolution"]["discovered_clues"]
    action_ctx = action_data.get("session", {}).get("interaction_context", {})
    chat_ctx = chat_data.get("session", {}).get("interaction_context", {})
    assert action_ctx.get("active_interaction_target_id") == "runner"
    assert chat_ctx.get("active_interaction_target_id") == "runner"
    assert action_ctx.get("active_interaction_kind") == "social"
    assert chat_ctx.get("active_interaction_kind") == "social"
    assert action_ctx.get("interaction_mode") == "social"
    assert chat_ctx.get("interaction_mode") == "social"
    assert action_ctx.get("engagement_level") == "engaged"
    assert chat_ctx.get("engagement_level") == "engaged"


# feature: clues
def test_action_and_chat_investigate_both_mark_runtime_discovery_memory(tmp_path, monkeypatch):
    explore_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }

    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        action_resp = client.post(
            "/api/action",
            json={"action_type": "exploration", "intent": "I investigate the desk.", "exploration_action": explore_action},
        )
    assert action_resp.status_code == 200
    action_data = action_resp.json()
    action_rt = action_data.get("session", {}).get("scene_runtime", {}).get("scene_investigate", {})

    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: explore_action)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        chat_resp = client.post("/api/chat", json={"text": "I investigate the desk."})
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    chat_rt = chat_data.get("session", {}).get("scene_runtime", {}).get("scene_investigate", {})

    assert action_data["resolution"]["kind"] == "discover_clue"
    assert chat_data["resolution"]["kind"] == "discover_clue"
    assert "A map indicates patrol locations." in (action_rt.get("discovered_clues") or [])
    assert "A map indicates patrol locations." in (chat_rt.get("discovered_clues") or [])
    # Ensure both endpoints mark the action id for discovery-memory relabeling.
    assert "inv-desk" in (action_rt.get("searched_targets") or [])
    assert "inv-desk" in (chat_rt.get("searched_targets") or [])


# feature: fallback
def test_chat_fallback_preserves_endpoint_specific_no_resolution_shape(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "hello there"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data.get("resolution") is None
    assert "gm_output" in data


# feature: retry, legality
def test_chat_targeted_retry_validator_voice_only(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Based on what's established, we can determine very little here.")
        return _gm_response("Rain beads on the gate stones while Captain Veyra watches the refugee line.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Describe the gate."})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    retry_messages = captured_inputs[1]
    retry_tail = retry_messages[-1]["content"]
    assert "Retry target: validator_voice." in retry_tail
    assert "unresolved_question" not in retry_tail
    text = (data.get("gm_output") or {}).get("player_facing_text", "")
    assert_no_validator_voice_smoke(text)
    assert "retry_strategy:selected=validator_voice" in read_debug_notes_from_turn_payload(data)


# feature: legality
def test_chat_pipeline_ships_no_validator_voice_policy(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        return _gm_response("Rain beads on the gate stones while Captain Veyra watches the refugee line.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Describe the gate."})

    assert resp.status_code == 200
    assert len(captured_inputs) == 1
    payload = json.loads(captured_inputs[0][1]["content"])
    assert "no_validator_voice" in (payload.get("response_policy") or {})
    assert payload["response_policy"]["no_validator_voice"]["enabled"] is True
    assert payload["response_policy"]["no_validator_voice"]["applies_to"] == "standard_narration"


# feature: routing, emission
def test_chat_social_route_ships_dialogue_contract_through_request_debug_and_trace(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        return _gm_response('"The runner grimaces. ""No names,"" he says."')

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    assert captured_inputs
    payload = json.loads(captured_inputs[0][1]["content"])
    payload_contract = payload.get("response_type_contract") or {}
    policy_contract = (payload.get("response_policy") or {}).get("response_type_contract") or {}
    debug_contract = (data.get("debug") or {}).get("response_type_contract") or {}
    trace_contract = (
        (latest_compact_debug_trace_entry(data.get("debug_traces") or []).get("turn_trace") or {}).get("response_type_contract")
        or {}
    )

    assert payload_contract.get("required_response_type") == "dialogue"
    assert policy_contract.get("required_response_type") == "dialogue"
    assert debug_contract.get("required_response_type") == "dialogue"
    assert trace_contract.get("required_response_type") == "dialogue"


# feature: routing, emission
@pytest.mark.parametrize(
    "bad_text",
    [
        pytest.param(
            "For a breath, the scene holds while voices shift around you.",
            id="scene_hold_filler",
        ),
        pytest.param(
            "Tavern Runner stands nearby under the torn awning.",
            id="visible_intro_filler",
        ),
    ],
)
def test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta(
    tmp_path, monkeypatch, bad_text
):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response(bad_text))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Runner, who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    gm_output = data.get("gm_output") or {}
    text = str(gm_output.get("player_facing_text") or "")
    low = text.lower()
    debug_contract = (data.get("debug") or {}).get("response_type_contract") or {}
    trace_contract = (
        (latest_compact_debug_trace_entry(data.get("debug_traces") or []).get("turn_trace") or {}).get("response_type_contract")
        or {}
    )
    resolution_contract = (resolution.get("metadata") or {}).get("response_type_contract") or {}

    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"
    if "scene holds" in bad_text.lower():
        assert_global_visibility_stock_absent(text)
    assert_no_social_visible_intro_filler_smoke(text)
    assert "tavern runner" in low
    assert ('"' in text) or ("don't know" in low) or ("do not know" in low) or ("starts to answer" in low)
    # Downstream smoke: player-facing output beat generic filler; exact FEM source/route owned by gate.
    assert debug_contract.get("required_response_type") == "dialogue"
    assert trace_contract.get("required_response_type") == "dialogue"
    assert resolution_contract.get("required_response_type") == "dialogue"


# feature: routing, emission, social
def test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback(
    tmp_path, monkeypatch
):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        gm = _gm_response("For a breath, the scene holds while voices shift around you.")
        gm["response_policy"] = {
            "response_type_contract": {"required_response_type": "neutral_narration"},
            "social_response_structure": {
                "enabled": False,
                "required_response_type": "neutral_narration",
                "debug_reason": "response_type_not_dialogue:neutral_narration",
            },
        }
        return gm

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Runner, who attacked the patrol?"})

    assert resp.status_code == 200
    data = resp.json()
    assert captured_inputs

    payload = json.loads(captured_inputs[0][1]["content"])
    prompt_contract = payload.get("response_type_contract") or {}
    prompt_policy = payload.get("response_policy") or {}
    prompt_policy_contract = prompt_policy.get("response_type_contract") or {}
    prompt_srs = prompt_policy.get("social_response_structure") or {}
    prompt_ac = prompt_policy.get("answer_completeness") or {}

    resolution = data.get("resolution") or {}
    social = resolution.get("social") or {}
    gm_output = data.get("gm_output") or {}
    text = str(gm_output.get("player_facing_text") or "")
    low = text.lower()
    meta = _extract_final_emission_meta(data) or {}
    response_policy_meta = (gm_output.get("response_policy") or {}).get("response_type_contract") or {}

    assert resolution.get("kind") == "question"
    assert social.get("npc_id") == "runner"
    assert social.get("npc_reply_expected") is True
    assert social.get("reply_kind") in {"answer", "refusal", "explanation"}

    assert prompt_contract.get("required_response_type") == "dialogue"
    assert prompt_policy_contract.get("required_response_type") == "dialogue"
    assert response_policy_meta.get("required_response_type") == "dialogue"
    # HTTP packaging smoke: dialogue contract threaded through prompt and emitted meta.
    assert_response_type_meta(meta, required="dialogue")

    assert prompt_srs.get("enabled") is True
    assert prompt_srs.get("required_response_type") == "dialogue"
    assert meta.get("social_response_structure_checked") is True
    assert meta.get("social_response_structure_applicable") is True
    assert meta.get("social_response_structure_skip_reason") is None

    assert prompt_ac.get("enabled") is True
    assert prompt_ac.get("answer_required") is True
    assert meta.get("answer_completeness_skip_reason") is None
    assert meta.get("answer_completeness_checked") is True

    assert "do not know a name" not in low
    assert "name anyone" not in low
    assert any(
        phrase in low
        for phrase in ("answer that", "that part", "don't know", "do not know", "cannot answer", "hard to swear")
    ), text


# feature: leads
def test_chat_persists_recent_contextual_leads_from_gm_reply(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "Lady Misia waits near the tavern entrance while nearby guards keep glancing back to the missing patrol notice."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who should I watch here?"})

    assert resp.status_code == 200
    data = resp.json()
    rt = data.get("session", {}).get("scene_runtime", {}).get("scene_investigate", {})
    recent = rt.get("recent_contextual_leads") or []
    assert any(entry.get("subject") == "Lady Misia" and entry.get("position") == "near the tavern entrance" for entry in recent)
    assert any("missing patrol" in str(entry.get("subject") or "").lower() for entry in recent)


# feature: fallback, leads
def test_chat_known_follow_up_bypasses_uncertainty_fallback(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    session = storage.load_session()
    scene_runtime = session.setdefault("scene_runtime", {}).setdefault("scene_investigate", {})
    scene_runtime["recent_contextual_leads"] = [
        {
            "key": "lady-misia-near-the-tavern-entrance",
            "kind": "recent_named_figure",
            "subject": "Lady Misia",
            "position": "near the tavern entrance",
            "named": True,
            "positioned": True,
        }
    ]
    storage.save_session(session)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "Captain Veyra folds her arms and watches the road."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where do I find that person?"})

    assert resp.status_code == 200
    data = resp.json()
    gm_output = data.get("gm_output") or {}
    assert_no_uncertainty_fallback_stock_smoke(gm_output.get("player_facing_text") or "")
    assert not any(str(tag).startswith("uncertainty:") for tag in (gm_output.get("tags") or []))
    assert "retry_strategy:selected=unresolved_question" in read_debug_notes_from_turn_payload(data)


# feature: retry, legality
def test_chat_targeted_retry_unresolved_question_only(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response(
                "Rain beats along the roofline while distant bells blur under street noise."
            )
        return _gm_response(
            "The report is usually copied to the notice board before dusk, though no one here will swear the last sheet is still hanging there. "
            "Best lead: read the posted notices and ask Captain Veyra who took the last copy."
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where is the missing patrol report?"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    retry_tail = captured_inputs[1][-1]["content"]
    assert "Retry target: unresolved_question." in retry_tail
    assert "validator_voice" not in retry_tail
    assert "Sentence one MUST directly answer the exact player question." in retry_tail
    assert "Do not begin with atmosphere, scene summary, or recap." in retry_tail
    assert "No advisory phrasing" in retry_tail
    text = (data.get("gm_output") or {}).get("player_facing_text", "")
    low = text.lower()
    assert_no_validator_voice_smoke(text)
    assert_no_retry_coaching_leak_smoke(text)
    assert_no_uncertainty_fallback_stock_smoke(text)
    assert low.startswith("the report is") or "filing shelves" in low or "notice board" in low
    assert "retry_strategy:selected=unresolved_question" in read_debug_notes_from_turn_payload(data)


# feature: retry
def test_chat_targeted_retry_prefers_highest_priority_failure_first(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("I can't answer that. Based on what's established, we can determine very little here.")
        return _gm_response(
            "No one here has pinned the report to one locked drawer, but Captain Veyra says the gate board carried the last official notice before dusk. "
            "Best lead: check the board, then press her on who removed the fresh copy."
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where is the missing patrol report?"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    retry_tail = captured_inputs[1][-1]["content"]
    assert "Retry target: unresolved_question." in retry_tail
    assert "Retry target: validator_voice." not in retry_tail
    text = (data.get("gm_output") or {}).get("player_facing_text", "")
    assert_no_validator_voice_smoke(text)
    assert "retry_strategy:selected=unresolved_question" in read_debug_notes_from_turn_payload(data)


# feature: retry, fallback
def test_chat_unresolved_retry_failure_uses_deterministic_known_fact_fallback(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Rain rolls over the checkpoint and the crowd shifts under dripping banners.")
        return _gm_response("The checkpoint feels tense and crowded as boots splash through mud.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where are we?"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    gm_output = data.get("gm_output") or {}
    text = (gm_output.get("player_facing_text") or "").lower()
    assert text.startswith("you are in") or "investigator" in text or "filing shelves" in text
    assert "checkpoint feels tense" not in text
    # Pipeline retry smoke: tag + debug evidence that retry fallback fired (not gate source tables).
    assert_emission_repair_evidence(
        data,
        tag_markers=("question_retry_fallback",),
        debug_notes_reader=read_debug_notes_from_turn_payload,
    )
    assert "known_fact_guard" in (gm_output.get("tags") or [])
    dbg = read_debug_notes_from_turn_payload(data)
    assert "retry_strategy:selected=unresolved_question" in dbg
    assert "retry_fallback:unresolved_question:known_fact_guard:current_scene_state" in dbg


# feature: retry, fallback
def test_chat_unresolved_retry_failure_uses_speaker_grounded_uncertainty_fallback(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Rain rattles over the shutters while everyone keeps their own counsel.")
        return _gm_response("Fog hangs low by the gate and no one steps forward first.")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    gm_output = data.get("gm_output") or {}
    text = gm_output.get("player_facing_text") or ""
    low = text.lower()
    assert "fog hangs low" not in low
    assert "tavern runner" in low
    assert_emission_repair_evidence(
        data,
        tag_markers=("question_retry_fallback",),
        debug_notes_reader=read_debug_notes_from_turn_payload,
    )
    assert "retry_fallback:unresolved_question" in read_debug_notes_from_turn_payload(data)
    assert "retry_strategy:selected=unresolved_question" in read_debug_notes_from_turn_payload(data)


# feature: retry
def test_chat_targeted_retry_scene_stall_only(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    session = storage.load_session()
    scene_runtime = session.setdefault("scene_runtime", {}).setdefault("scene_investigate", {})
    scene_runtime["momentum_exchanges_since"] = 2
    scene_runtime["momentum_next_due_in"] = 3
    storage.save_session(session)
    captured_inputs = []

    def _fake_call_gpt(messages):
        captured_inputs.append(messages)
        if len(captured_inputs) == 1:
            return _gm_response("Captain Veyra studies you in silence.")
        return _gm_response(
            "A runner splashes up from the road with a torn dispatch and thrusts it toward Captain Veyra. "
            "\"East road, half an hour old,\" he pants, giving you a fresh trail to follow.",
            tags=["scene_momentum:new_information"],
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I wait."})

    assert resp.status_code == 200
    data = resp.json()
    assert len(captured_inputs) == 2
    retry_tail = captured_inputs[1][-1]["content"]
    assert "Retry target: scene_stall." in retry_tail
    assert "validator_voice" not in retry_tail
    text = (data.get("gm_output") or {}).get("player_facing_text", "")
    assert_no_retry_coaching_leak_smoke(text)
    assert "retry_strategy:selected=scene_stall" in read_debug_notes_from_turn_payload(data)


# feature: social, continuity
def test_chat_single_wait_in_tense_scene_forces_interaction_pressure(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    scene = copy.deepcopy(storage.load_scene("scene_investigate"))
    scene.pop("_is_canon", None)
    scene["scene"]["visible_facts"] = [
        "Guards keep glancing at a missing patrol notice beside the checkpoint.",
        "A tavern runner lingers under an awning, selling rumors for coin.",
    ]
    storage.save_scene(scene)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("Rain beads on the checkpoint while nobody moves first."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I wait."})

    assert resp.status_code == 200
    data = resp.json()
    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    _assert_concrete_pressure(text)
    assert "passive_scene_pressure" in ((data.get("gm_output") or {}).get("tags") or [])


# feature: social
def test_chat_repeated_passive_actions_do_not_stall_into_atmosphere(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    scene = copy.deepcopy(storage.load_scene("scene_investigate"))
    scene.pop("_is_canon", None)
    scene["scene"]["visible_facts"] = [
        "A guard leans near the checkpoint, watching the road.",
        "A missing patrol notice curls in the damp beside him.",
    ]
    storage.save_scene(scene)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The damp air hangs over the gate as everyone watches everyone else."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "I wait."})
        second = client.post("/api/chat", json={"text": "I hold position and watch."})

    assert first.status_code == 200
    assert second.status_code == 200
    data = second.json()
    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    _assert_concrete_pressure(text)
    debug_notes = read_debug_notes_from_turn_payload(data)
    assert "passive_scene_pressure:" in debug_notes
    assert "streak=2" in debug_notes


# feature: social
def test_chat_passive_scene_prefers_already_introduced_suspicious_figure(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    session = storage.load_session()
    scene_runtime = session.setdefault("scene_runtime", {}).setdefault("scene_investigate", {})
    scene_runtime["recent_contextual_leads"] = [
        {
            "key": "tattered-man-by-the-shuttered-well",
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
            "named": False,
            "positioned": True,
            "mentions": 2,
            "last_turn": 1,
        }
    ]
    storage.save_session(session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The square stays hushed except for the scrape of boots on wet stone."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I remain silent and observe."})

    assert resp.status_code == 200
    data = resp.json()
    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    assert "the tattered man" in text.lower()
    _assert_concrete_pressure(text)
    assert "passive_scene_pressure:lead_figure" in read_debug_notes_from_turn_payload(data)


def test_chat_passive_wait_with_recent_suspicious_figure_replaces_weak_atmosphere(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    session = storage.load_session()
    scene_runtime = session.setdefault("scene_runtime", {}).setdefault("scene_investigate", {})
    scene_runtime["recent_contextual_leads"] = [
        {
            "key": "tattered-man-by-the-shuttered-well",
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
            "named": False,
            "positioned": True,
            "mentions": 2,
            "last_turn": 1,
        }
    ]
    storage.save_session(session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The square stays hushed except for the scrape of boots on wet stone."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I wait."})

    assert resp.status_code == 200
    data = resp.json()
    text = (data.get("gm_output") or {}).get("player_facing_text") or ""
    low = text.lower()
    assert "the tattered man" in low
    assert_global_visibility_stock_absent(text)
    _assert_concrete_pressure(text)


# feature: emission
def test_chat_roll_requirement_question_routes_to_adjudication_without_gpt(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Is Sleight of Hand needed?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    adjudication = (data.get("resolution") or {}).get("adjudication") or {}
    assert adjudication.get("category") == "roll_requirement_query"
    assert adjudication.get("answer_type") == "check_required"
    assert (data.get("resolution") or {}).get("requires_check") is True
    check_request = (data.get("resolution") or {}).get("check_request") or {}
    assert check_request.get("requires_check") is True
    assert isinstance(check_request.get("player_prompt"), str)
    assert "adjudication_query" in (data.get("gm_output") or {}).get("tags", [])


# feature: emission, routing
def test_chat_adjudication_question_with_active_interlocutor_stays_answer_shaped(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "OOC: does this need a roll?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    gm_output = data.get("gm_output") or {}
    text = str(gm_output.get("player_facing_text") or "")
    low = text.lower()
    meta = _extract_final_emission_meta(data) or {}

    assert resolution.get("kind") == "adjudication_query"
    assert (
        "lead" in low
        or "concrete move" in low
        or "answer has not formed yet" in low
        or "that's all" in low
        or "i do not know enough" in low
    )
    assert_response_type_meta(
        meta,
        required="answer",
        candidate_ok=True,
        repair_used=True,
        repair_kinds=(
            "dialogue_minimal_repair",
            "answer_upstream_prepared_repair",
            "strict_social_dialogue_repair",
        ),
    )


# feature: routing, social
def test_chat_active_target_location_question_routes_to_social_exchange(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where can I find them?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"


# feature: routing, social
@pytest.mark.parametrize(
    "user_text",
    [
        pytest.param(
            "Runner, do you know where can I find those figures?",
            id="runner_direct_address",
        ),
        pytest.param("Who attacked them?", id="pronoun_who_attacked"),
        pytest.param("What are they planning?", id="pronoun_what_planning"),
        pytest.param("Who saw this happen?", id="who_saw"),
    ],
)
def test_chat_dialogue_lock_routes_npc_directed_question_regressions(tmp_path, monkeypatch, user_text):
    """Pipeline lock: directed / pronominal questions stay social_exchange on active runner."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": user_text})
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"
    # GM legality for procedural phrasing is covered by sanitizer / emission-gate tests below.


# feature: routing, social
@pytest.mark.parametrize(
    "user_text",
    [
        pytest.param("Well? What should I do next?", id="what_next_well"),
        pytest.param("So? What's the next step?", id="next_step_so"),
        pytest.param("Where does this lead?", id="where_lead"),
    ],
)
def test_chat_dialogue_lock_routes_ambiguous_next_step_questions_to_active_npc(
    tmp_path, monkeypatch, user_text
):
    """Meta / ambiguous follow-ups stay dialogue lane (question or social_probe), not adjudication."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": user_text})
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") in {"question", "social_probe"}
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"


# feature: social
def test_chat_repeated_social_questions_keep_npc_uncertainty_voice(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("Rain rattles over the shutters while the crowd churns."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        prompts = ["Who attacked them?", "Who is behind it?"]
        for prompt in prompts:
            resp = client.post("/api/chat", json={"text": prompt})
            assert resp.status_code == 200
            data = resp.json()
            text = ((data.get("gm_output") or {}).get("player_facing_text") or "")
            low = text.lower()
            assert "tavern runner" in low
            assert '"' in text
            assert_procedural_adjudication_smoke(text)


# feature: social
def test_chat_repeated_topic_questions_skip_policy_topic_pressure_for_strict_social(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage.save_session(session)

    stale = _gm_response(
        "The runner rubs his neck. Rumor says the crossroads turned ugly, but no one can name the culprits yet "
        "and people keep repeating the same whispers without anything solid."
    )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: stale)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.gm.resolve_known_fact_before_uncertainty", lambda *_args, **_kwargs: None)
        m.setattr(
            "game.gm.question_resolution_rule_check",
            lambda **_kwargs: {"applies": False, "ok": True, "reasons": []},
        )
        m.setattr("game.gm.enforce_question_resolution_rule", lambda gm, **_kwargs: gm)
        client = TestClient(app)
        prompts = [
            "Who is behind the crossroads attack?",
            "Who is really behind it?",
            "Who ordered it?",
            "Who funds them?",
        ]
        for idx, prompt in enumerate(prompts, start=1):
            resp = client.post("/api/chat", json={"text": prompt})
            assert resp.status_code == 200
            data = resp.json()
            gm_output = data.get("gm_output") or {}
            tags = gm_output.get("tags") or []
            if idx >= 4:
                assert "topic_pressure_escalation" not in tags
                assert not any(str(tag).startswith("scene_momentum:") for tag in tags)


# feature: routing, social
@pytest.mark.parametrize(
    "user_text",
    [
        pytest.param("I lean in and ask quietly who saw it.", id="lean_in_quiet_question"),
        pytest.param("I scan the crowd while asking who saw it.", id="scan_crowd_question"),
    ],
)
def test_chat_dialogue_lock_mixed_questioning_keeps_dialogue_lane(tmp_path, monkeypatch, user_text):
    """Action-flavored wording with a question still routes to dialogue, not world/adjudication."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": user_text})
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") in {"question", "social_probe"}
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"


# feature: routing
def test_chat_dialogue_lock_does_not_override_forceful_world_action(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I follow the runner."})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") != "question"
    assert resolution.get("kind") != "social_probe"
    assert resolution.get("kind") != "adjudication_query"


# feature: routing, social
def test_chat_social_pressure_line_prefers_dialogue_over_adjudication(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Footman? I require an audience."})

    assert resp.status_code == 200
    data = resp.json()
    gm_out = data.get("gm_output") or {}
    assert data.get("resolution") is None
    assert "adjudication_query" not in (gm_out.get("tags") or [])
    assert str(gm_out.get("player_facing_text") or "").strip()


# feature: routing, social
def test_chat_active_target_direct_command_routes_to_social_exchange(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "They were seen near the east lanes.", "clue_id": "east_lanes"}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage.save_session(session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Tell me plainly."})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "social_probe"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    assert (resolution.get("social") or {}).get("npc_id") == "runner"


# feature: routing, emission
@pytest.mark.parametrize(
    "user_text, expected_category",
    [
        pytest.param("OOC: does this need a roll?", "roll_requirement_query", id="ooc_roll_question"),
        pytest.param("OOC, what actions are available?", None, id="ooc_actions_available"),
    ],
)
def test_chat_explicit_ooc_stays_adjudication_without_gpt(
    tmp_path, monkeypatch, user_text, expected_category
):
    """Explicit OOC/mechanical questions bypass dialogue lock and resolve as adjudication (no GPT)."""
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": user_text})

    assert resp.status_code == 200
    data = resp.json()
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    if expected_category is not None:
        adjudication = (data.get("resolution") or {}).get("adjudication") or {}
        assert adjudication.get("category") == expected_category


# feature: emission
def test_chat_earshot_question_routes_to_adjudication_with_state_answer(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {"id": "runner", "name": "Tavern Runner", "location": "scene_investigate"},
        {"id": "guard", "name": "Guard Captain", "location": "scene_investigate"},
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    storage.save_session(session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Is anyone else in earshot?"})

    assert resp.status_code == 200
    data = resp.json()
    adjudication = (data.get("resolution") or {}).get("adjudication") or {}
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    assert adjudication.get("category") == "perception_query"
    assert adjudication.get("answer_type") == "direct_answer"
    assert "Guard Captain" in ((data.get("gm_output") or {}).get("player_facing_text") or "")


# feature: emission
def test_chat_adjudication_refuses_over_answer_without_basis(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "How far away is he?"})

    assert resp.status_code == 200
    data = resp.json()
    adjudication = (data.get("resolution") or {}).get("adjudication") or {}
    assert (data.get("resolution") or {}).get("kind") == "adjudication_query"
    assert adjudication.get("answer_type") == "needs_concrete_action"
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    assert_procedural_adjudication_smoke(text)
    assert text.strip()


# feature: continuity, emission
def test_chat_mixed_turn_preserves_embedded_adjudication_metadata(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": "I investigate the desk (Is Perception needed?)"},
        )
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") in {"discover_clue", "investigate"}
    metadata = resolution.get("metadata") or {}
    embedded = metadata.get("embedded_adjudication") or {}
    assert embedded.get("category") == "roll_requirement_query"
    assert embedded.get("requires_check") is True
    assert "Perception" in (embedded.get("question") or "")


# feature: routing, clues, emission
@pytest.mark.parametrize(
    ("player_text", "target_id", "question_text"),
    [
        (
            "Approaching the notice board, Galinor studies the posting about the missing patrol. Does it have any other details?",
            "notice_board",
            "Does it have any other details?",
        ),
        ("I check the notice. Is there more written below?", "notice_board", "Is there more written below?"),
        (
            "I examine the broken lantern; does it show signs of tampering?",
            "broken_lantern",
            "does it show signs of tampering?",
        ),
        ("I study the strange brass device. Anything unusual?", "brass_device", "Anything unusual?"),
    ],
)
def test_chat_mixed_scene_object_investigation_question_recovers_action_outcome(
    tmp_path,
    monkeypatch,
    player_text,
    target_id,
    question_text,
):
    _seed_shared_world(tmp_path, monkeypatch)
    scene = copy.deepcopy(storage.load_scene("scene_investigate"))
    scene["scene"]["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "posting about the missing patrol"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_details",
        },
        {
            "id": "broken_lantern",
            "label": "Broken lantern",
            "type": "investigate",
            "reveals_clue": "lantern_tampering",
        },
        {
            "id": "brass_device",
            "label": "Strange brass device",
            "type": "investigate",
            "reveals_clue": "brass_device_anomaly",
        },
    ]
    scene["scene"]["visible_facts"] = [
        "A notice board carries a posting about the missing patrol.",
        "A broken lantern lies near the threshold.",
        "A strange brass device ticks on the table.",
    ]
    scene["scene"]["discoverable_clues"] = [
        {"id": "notice_patrol_details", "text": "The missing patrol was last seen below the east ridge."},
        {"id": "lantern_tampering", "text": "The lantern's hinge was forced open with a narrow tool."},
        {"id": "brass_device_anomaly", "text": "The brass device is warmer on the side facing the old road."},
    ]
    scene["scene"]["suggested_actions"] = [
        {"id": "study-notice", "label": "Study the notice board"},
        {"id": "inspect-lantern", "label": "Inspect the broken lantern"},
        {"id": "study-device", "label": "Study the strange brass device"},
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The scene pauses without offering anything concrete."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": player_text})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    metadata = resolution.get("metadata") or {}
    debug = data.get("debug") or {}
    normalized_action = debug.get("normalized_action") or {}
    gm_text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = gm_text.lower()
    final_meta = _extract_final_emission_meta(data) or {}

    assert resolution.get("kind") in {"investigate", "discover_clue"}
    assert resolution.get("kind") != "question"
    assert normalized_action.get("type") == "investigate"
    assert normalized_action.get("targetEntityId") == target_id or resolution.get("action_id") == target_id
    assert metadata.get("parser_lane") == "mixed_scene_object_investigation"
    assert metadata.get("mixed_turn_detail_question") == question_text
    assert metadata.get("adjudication_or_detail_question_text") == question_text
    assert metadata.get("recovered_action_clause")
    assert_response_type_meta(final_meta, required="action_outcome")
    assert "scene pauses" not in low
    assert "nothing concrete" not in low


# feature: emission, continuity
def test_chat_action_outcome_contract_survives_inside_active_social_scene(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    explore_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("For a breath, the scene holds while voices shift around you."),
        )
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "I investigate the desk.",
                "exploration_action": explore_action,
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    gm_output = data.get("gm_output") or {}
    text = str(gm_output.get("player_facing_text") or "")
    low = text.lower()
    meta = _extract_final_emission_meta(data) or {}

    assert resolution.get("kind") == "discover_clue"
    assert "tavern runner" not in low
    assert "desk" in low
    assert "concrete clue" in low or "map indicates patrol locations" in low
    assert_global_visibility_stock_absent(text)
    # HTTP smoke: action_outcome contract survived; exact repair source/kind is gate-owned.
    assert_response_type_meta(meta, required="action_outcome", candidate_ok=True, repair_used=True)


# feature: routing, social
def test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "alleys", "text": "Try the alley by the bathhouse.", "clue_id": "bathhouse_alley"}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    storage.save_session(session)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": '"Where can I find them?" (Does that require Sleight of Hand?)'},
        )

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "question"
    assert (resolution.get("social") or {}).get("social_intent_class") == "social_exchange"
    metadata = resolution.get("metadata") or {}
    embedded = metadata.get("embedded_adjudication") or {}
    assert embedded.get("category") == "roll_requirement_query"
    assert embedded.get("requires_check") is True


# feature: emission
def test_chat_persuasion_returns_engine_check_prompt_without_gpt(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {"id": "guard", "name": "Gate Guard", "location": "scene_investigate"},
    ]
    storage._save_json(storage.WORLD_PATH, world)
    social_action = {
        "id": "persuade-guard",
        "label": "Persuade the guard",
        "type": "persuade",
        "prompt": "I persuade the gate guard to let me pass.",
        "target_id": "guard",
        "targetEntityId": "guard",
    }

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: social_action)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I persuade the gate guard to let me pass."})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "persuade"
    assert resolution.get("requires_check") is True

    check_request = resolution.get("check_request") or {}
    assert check_request.get("requires_check") is True
    assert check_request.get("skill") == "diplomacy"
    assert "Roll" in (check_request.get("player_prompt") or "")
    assert "Gate Guard" in (check_request.get("player_prompt") or "")

    gm_output = data.get("gm_output") or {}
    tags = gm_output.get("tags") or []
    crowd_text = gm_output.get("player_facing_text") or ""

    assert "check_required" in tags
    assert "gate guard" in crowd_text.lower()
    assert crowd_text.strip()


# feature: emission
def test_chat_covert_concealment_under_observation_prompts_engine_check(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("GPT should not be called")))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Is a roll needed if I conceal the letter while the guard is watching?"})

    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("kind") == "adjudication_query"
    assert resolution.get("requires_check") is True
    check_request = resolution.get("check_request") or {}
    assert check_request.get("requires_check") is True
    assert check_request.get("skill") == "sleight_of_hand"
    assert "covert" in (check_request.get("reason") or "")
    assert "Roll" in (check_request.get("player_prompt") or "")
    tags = ((data.get("gm_output") or {}).get("tags") or [])
    assert ("check_required" in tags) or ("adjudication_query" in tags)


# feature: legality
def test_chat_final_output_sanitizer_blocks_internal_scaffold_labels(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("Planner: route via router. Validator: unresolved."),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Where should I start?"})

    assert resp.status_code == 200
    data = resp.json()
    text = assert_player_text_present(data)
    assert_no_internal_scaffold_labels(text)


# feature: emission
def test_resolved_turn_trace_is_compact_and_authoritative(tmp_path, monkeypatch):
    explore_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }
    _seed_shared_world(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={"action_type": "exploration", "intent": "I investigate the desk.", "exploration_action": explore_action},
        )

    assert resp.status_code == 200
    data = resp.json()
    traces = data.get("debug_traces") or []
    assert traces
    latest = latest_compact_debug_trace_entry(traces)
    turn_trace = latest.get("turn_trace") or {}

    assert turn_trace.get("player_input") == "I investigate the desk."
    assert (turn_trace.get("classification") or {}).get("resolved_kind") == "discover_clue"
    assert turn_trace.get("resolution_path") == "exploration_engine"

    clues = turn_trace.get("clues") or {}
    assert "A map indicates patrol locations." in (clues.get("discovered_texts") or [])
    clue_counts = clues.get("known_counts") or {}
    assert clue_counts.get("explicit", 0) >= 1

    interaction_after = turn_trace.get("interaction_after") or {}
    session_ctx = data.get("session", {}).get("interaction_context", {})
    assert interaction_after.get("interaction_mode") == session_ctx.get("interaction_mode")

    affordances_after = turn_trace.get("affordances_after") or []
    assert any(a.get("id") == "desk" for a in affordances_after if isinstance(a, dict))


# feature: emission
@pytest.mark.parametrize(
    "channel",
    [
        pytest.param("action", id="via_api_action"),
        pytest.param("chat", id="via_api_chat"),
    ],
)
def test_action_and_chat_mutate_runtime_before_request_build(
    tmp_path, monkeypatch, channel
):
    """Exploration resolution updates scene_runtime before request assembly sees it."""
    explore_action = {
        "id": "desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }
    _seed_shared_world(tmp_path, monkeypatch)
    captured: dict = {}

    def _fake_build_messages(*_args, **kwargs):
        scene_runtime = kwargs.get("scene_runtime") or {}
        captured["discovered_clues"] = list(scene_runtime.get("discovered_clues") or [])
        captured["searched_targets"] = list(scene_runtime.get("searched_targets") or [])
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    with monkeypatch.context() as m:
        m.setattr("game.api.build_messages", _fake_build_messages)
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        if channel == "action":
            resp = client.post(
                "/api/action",
                json={
                    "action_type": "exploration",
                    "intent": "I investigate the desk.",
                    "exploration_action": explore_action,
                },
            )
        else:
            m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
            m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: explore_action)
            m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
            resp = client.post("/api/chat", json={"text": "I investigate the desk."})

    assert resp.status_code == 200
    assert "A map indicates patrol locations." in (captured.get("discovered_clues") or [])
    assert "desk" in (captured.get("searched_targets") or [])


# feature: emission
def test_affordances_are_state_derived_not_from_gpt_text(tmp_path, monkeypatch):
    explore_action = {
        "id": "desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk.",
    }
    _seed_shared_world(tmp_path, monkeypatch)
    gm_with_unrelated_text = {
        "player_facing_text": "A mysterious red button appears in your mind.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": {"id": "push-red-button", "label": "Push the red button", "type": "interact", "prompt": "I push the red button."},
        "debug_notes": "",
    }
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: gm_with_unrelated_text)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={"action_type": "exploration", "intent": "I investigate the desk.", "exploration_action": explore_action},
        )

    assert resp.status_code == 200
    data = resp.json()
    affordances = data.get("ui", {}).get("affordances") or []
    affordance_ids = {a.get("id") for a in affordances if isinstance(a, dict)}
    assert "push-red-button" not in affordance_ids
    desk_affs = [a for a in affordances if isinstance(a, dict) and a.get("id") == "desk"]
    assert desk_affs
    assert "(already searched)" in str(desk_affs[0].get("label") or "")


# feature: social
def test_chat_implied_lowered_voice_reaches_request_build_context(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    captured: dict = {}

    def _fake_build_messages(*args, **_kwargs):
        session = args[2]
        ctx = (session.get("interaction_context") or {}).copy()
        captured["conversation_privacy"] = ctx.get("conversation_privacy")
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    with monkeypatch.context() as m:
        m.setattr("game.api.build_messages", _fake_build_messages)
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I lower my voice and ask quietly about the gate."})

    assert resp.status_code == 200
    assert captured.get("conversation_privacy") == "lowered_voice"


# feature: social
def test_chat_implied_sit_with_target_reaches_request_build_context(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = [
        {"id": "runner", "name": "Tavern Runner", "location": "scene_investigate"},
    ]
    storage._save_json(storage.WORLD_PATH, world)
    captured: dict = {}
    social_action = {
        "id": "question-runner",
        "label": "Talk to Tavern Runner",
        "type": "question",
        "prompt": "I talk to Tavern Runner.",
        "target_id": "runner",
        "targetEntityId": "runner",
    }

    def _fake_build_messages(*args, **_kwargs):
        session = args[2]
        ctx = (session.get("interaction_context") or {}).copy()
        captured["player_position_context"] = ctx.get("player_position_context")
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    with monkeypatch.context() as m:
        m.setattr("game.api.build_messages", _fake_build_messages)
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: social_action)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I sit down with the tavern runner and ask about the gate."})

    assert resp.status_code == 200
    assert captured.get("player_position_context") == "seated_with_target"


# feature: emission
def test_chat_social_exchange_invalid_blob_is_repaired_before_emit(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "From here, no certain answer presents itself. "
                "The runner keeps repeating the same rumors while rain hits the shutters."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    gm_out = data.get("gm_output") or {}
    text = str(gm_out.get("player_facing_text") or "")
    low = text.lower()
    assert_no_unresolved_stock_phrases(text)
    assert "tavern runner" in low
    assert_emission_repair_evidence(
        data,
        debug_notes_reader=read_debug_notes_from_turn_payload,
    )


# feature: emission, legality
def test_chat_social_exchange_blocks_advisory_prose_before_emit(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "I'd suggest you question the notice board clerk before the lane goes cold."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert_no_advisory_prose(text)
    assert_emission_repair_evidence(
        data,
        debug_notes_reader=read_debug_notes_from_turn_payload,
    )


# feature: emission
def test_chat_social_exchange_interruption_output_stays_coherent(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                'Tavern Runner says, "No names. Only rumors." A shout erupts in the crowd. '
                "I'd suggest you ask the captain and check the board."
            ),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert_no_advisory_prose(text)
    assert "check the board" not in low
    assert any(
        phrase in low
        for phrase in (
            "shouting breaks out",
            "shout cuts across the square",
            "\"i don't know.\"",
            "\"no names. only rumors.\"",
            "no names",
            "rumors",
            "that's all i've got",
            "word is",
            "grimace",
            "shake",
            "do not know enough",
            "do not know a name",
        )
    ) or ("tavern runner" in low and "mutters" in low)


# feature: emission, continuity
def test_chat_repeated_interruption_progresses_without_losing_dialogue_contract(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    interruption = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response(interruption))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "Who attacked them?"})
        second = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert first.status_code == 200
    assert second.status_code == 200

    first_text = str((first.json().get("gm_output") or {}).get("player_facing_text") or "")
    second_data = second.json()
    second_output = second_data.get("gm_output") or {}
    second_text = str(second_output.get("player_facing_text") or "")
    low1 = first_text.lower()
    low2 = second_text.lower()
    meta = _extract_final_emission_meta(second_data) or {}

    assert "tavern runner" in low1
    assert second_text != first_text
    assert "tavern runner" in low2 or '"' in second_text
    assert "that's all i've got" not in low2
    assert (
        "heard talk" in low2
        or "not names" in low2
        or "do not know enough" in low2
        or "do not know a name" in low2
        or "ward clerk" in low2
        or "main gate" in low2
        or "gate roster" in low2
        or "duty sergeant" in low2
        or "old crossroads" in low2
        or "old millstone" in low2
    )
    assert_response_type_meta(meta, required="dialogue", candidate_ok=True)


# feature: emission
def test_chat_repeated_questioning_can_end_clean_refusal_after_emit_repair(tmp_path, monkeypatch):
    _seed_runner_dialogue_context(tmp_path, monkeypatch)

    stale_blob = _gm_response(
        "From here, no certain answer presents itself. "
        "The runner says no names and then lists rumors while I'd suggest you check the board."
    )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: stale_blob)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        client.post("/api/chat", json={"text": "Who attacked them?"})
        client.post("/api/chat", json={"text": "Who is really behind it?"})
        third = client.post("/api/chat", json={"text": "Who ordered it?"})

    assert third.status_code == 200
    data = third.json()
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "")
    low = text.lower()
    assert any(
        phrase in low
        for phrase in (
            "i've told you what i know",
            "no more questions",
            "shout cuts across the square",
            "shouting breaks out",
            "don't know",
            "do not know",
            "couldn't tell you",
            "only rumors",
            "heard talk",
            "not names",
            "tightens their jaw",
            "all you're getting from me",
            "that's all i've got",
            "frowns",
        )
    )


# feature: emission, speaker_contract
def test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical(tmp_path, monkeypatch):
    """Thin E2E: continuity-locked contract repairs wrong explicit attribution to canonical NPC."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    wrong = 'Merchant says, "I know nothing about that."'

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response(wrong))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    gm_out = data.get("gm_output") or {}
    text = str(gm_out.get("player_facing_text") or "")
    low = text.lower()
    assert "merchant" not in low
    assert "tavern runner" in low
    meta = _extract_final_emission_meta(data) or {}
    # HTTP smoke: speaker enforcement ran; exact reason codes owned by speaker/gate suites.
    assert meta.get("speaker_contract_enforcement_reason")


# feature: emission, speaker_contract
def test_pipeline_strict_social_ragged_stranger_fallback_repaired(tmp_path, monkeypatch):
    """Thin E2E: forbidden generic speaker label is repaired toward canonical ownership."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    bad = 'Ragged stranger says, "Maybe you should ask the ward clerk."'

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response(bad))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    gm_out = data.get("gm_output") or {}
    text = str(gm_out.get("player_facing_text") or "")
    low = text.lower()
    assert "ragged stranger" not in low
    assert "tavern runner" in low
    meta = _extract_final_emission_meta(data) or {}
    assert meta.get("speaker_contract_enforcement_reason")


# feature: emission, interruption
def test_pipeline_interruption_denial_still_emits_coherent_strict_social(tmp_path, monkeypatch):
    """Denied-interruption repair: stock advice stripped; strict-social output stays coherent."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    blob = (
        'Tavern Runner says, "No names." Shouting breaks out in the crowd. '
        "I'd suggest you check the board and ask the captain."
    )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response(blob))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Who attacked them?"})

    assert resp.status_code == 200
    data = resp.json()
    gm_out = data.get("gm_output") or {}
    text = str(gm_out.get("player_facing_text") or "")
    low = text.lower()
    assert "check the board" not in low
    assert "tavern runner" in low or '"' in text


def test_emission_smoke_helpers_reject_global_visibility_stock():
    with pytest.raises(AssertionError):
        assert_global_visibility_stock_absent(
            "For a breath, the scene holds while voices shift around you."
        )


def test_emission_smoke_helpers_reject_advisory_prose():
    with pytest.raises(AssertionError):
        assert_no_advisory_prose("I'd suggest you ask the captain.")


def test_emission_smoke_helpers_reject_procedural_adjudication_leak():
    with pytest.raises(AssertionError):
        assert_procedural_adjudication_smoke(
            "State exactly what you do; the scene offers no clear answer yet."
        )


def test_emission_smoke_helpers_accept_repair_evidence_from_tags_or_debug():
    assert_emission_repair_evidence(
        {"gm_output": {"tags": ["final_emission_gate_replaced"]}},
    )
    assert_emission_repair_evidence(
        {"debug_notes": "retry_fallback:unresolved_question"},
        debug_notes_reader=lambda payload: str(payload.get("debug_notes") or ""),
    )
