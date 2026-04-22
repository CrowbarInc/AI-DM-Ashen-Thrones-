from __future__ import annotations

from game.final_emission_meta import read_final_emission_meta_dict
from game.narrative_authenticity_eval import _extract_final_emission_meta

import json
import re

import pytest
from fastapi.testclient import TestClient

import game.final_emission_gate as feg
from game import storage
from game.api import app
from game.defaults import default_campaign, default_character, default_world
from game.gm import build_messages
from game.storage import get_scene_runtime
from tests.debug_trace_utils import latest_compact_debug_trace_entry
from tests.test_turn_pipeline_shared import _seed_shared_world

pytestmark = [pytest.mark.integration]


_SOCIAL_ACTION = {
    "id": "question-runner",
    "label": "Talk to Tavern Runner",
    "type": "question",
    "prompt": "I talk to Tavern Runner.",
    "target_id": "runner",
    "targetEntityId": "runner",
}


def _add_runner_npc() -> None:
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


def _quota_error_response() -> dict:
    return {
        "player_facing_text": "The game master is temporarily unavailable. Please try again.",
        "tags": [
            "error",
            "gpt_api_error:insufficient_quota",
            "gpt_api_error_nonretryable",
        ],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "call_gpt error: quota | api_error_class=insufficient_quota:retryable=False",
        "metadata": {
            "upstream_api_error": {
                "failure_class": "insufficient_quota",
                "retryable": False,
                "status_code": 429,
                "error_code": "insufficient_quota",
                "message_excerpt": "Quota exhausted.",
            }
        },
    }


def _seed_opening_fast_fallback_scene() -> None:
    scene = storage.load_scene("scene_investigate")
    scene["scene"]["location"] = "Frontier Gate"
    scene["scene"]["summary"] = "A rain-soaked checkpoint holds a nervous crowd at the gate."
    scene["scene"]["visible_facts"] = [
        "Several patrons exchange furtive glances.",
        "A notice board lists a missing patrol.",
        "Rain darkens the flagstones around the checkpoint.",
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)


def _seed_intent_aligned_fast_fallback_scene() -> None:
    scene = storage.load_scene("scene_investigate")
    scene["scene"]["location"] = "Frontier Gate"
    scene["scene"]["summary"] = "A rain-soaked checkpoint holds a nervous crowd at the gate."
    scene["scene"]["visible_facts"] = [
        "A knot of patrons keeps their voices low over the missing patrol.",
        "One merchant edges closer to catch the gossip.",
        "Muddy footprints trail past a stack of disturbed crates.",
        "Rain darkens the flagstones around the checkpoint.",
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)


def test_chat_nonretryable_quota_fails_fast_and_emits_latency_fields(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    _add_runner_npc()

    call_count = {"count": 0}

    def fake_call_gpt(_messages):
        call_count["count"] += 1
        return _quota_error_response()

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: dict(_SOCIAL_ACTION))
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I talk to Tavern Runner."})

    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True
    assert call_count["count"] == 1

    gm = body.get("gm_output") or {}
    tags = [str(t) for t in (gm.get("tags") or []) if isinstance(t, str)]
    assert "fast_fallback" in tags
    assert "upstream_api_fast_fallback" in tags

    traces = body.get("debug_traces") or []
    assert traces
    latency = ((latest_compact_debug_trace_entry(traces).get("turn_trace") or {}).get("latency_ms") or {})
    assert latency
    for key in (
        "intent_classification",
        "engine_resolution",
        "prompt_construction",
        "gpt_call",
        "retry_loop_total",
        "final_emission_gate",
        "fallback_repair",
        "total_turn",
    ):
        assert isinstance(latency.get(key), int)
        assert latency.get(key) >= 0


def test_chat_begin_nonretryable_quota_repairs_malformed_opening_fast_fallback(tmp_path, monkeypatch):
    """C2: fast-fallback composition is validate-only; malformed upstream join may ship with trace, not boundary rewrite."""
    _seed_shared_world(tmp_path, monkeypatch)
    _seed_opening_fast_fallback_scene()

    call_count = {"count": 0}

    def fake_call_gpt(_messages):
        call_count["count"] += 1
        return _quota_error_response()

    malformed = (
        "Emergent Lord Aldric Several patrons exchange furtive glances. "
        "The rain holds; beside it, a notice board lists a missing patrol."
    )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        m.setattr("game.gm_retry._nonsocial_forced_retry_progress_line", lambda *_a, **_k: malformed)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "Begin."})

    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True
    assert call_count["count"] == 1

    gm = body.get("gm_output") or {}
    tags = [str(t) for t in (gm.get("tags") or []) if isinstance(t, str)]
    assert "fast_fallback" in tags
    assert "upstream_api_fast_fallback" in tags

    text = str(gm.get("player_facing_text") or "")
    low = text.lower()
    assert any(token in low for token in ("checkpoint", "gate", "patrol", "rain", "patrons"))
    assert len([s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]) <= 3

    meta = _extract_final_emission_meta(body) or {}
    assert meta.get("fast_fallback_neutral_composition_malformed_detected") is True
    assert meta.get("fast_fallback_neutral_composition_repaired") is False

    traces = body.get("debug_traces") or []
    assert traces
    latency = ((latest_compact_debug_trace_entry(traces).get("turn_trace") or {}).get("latency_ms") or {})
    assert isinstance(latency.get("gpt_call"), int)
    assert isinstance(latency.get("total_turn"), int)
    assert latency.get("total_turn") >= 0


def test_chat_listen_in_nonretryable_quota_prefers_gossip_aligned_fallback(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    _seed_intent_aligned_fast_fallback_scene()

    def fake_call_gpt(_messages):
        return _quota_error_response()

    player_text = "I move closer to the gossiping group and listen in."

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: {"kind": "observe", "prompt": player_text})
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": player_text})

    assert resp.status_code == 200
    gm = (resp.json().get("gm_output") or {})
    tags = [str(t) for t in (gm.get("tags") or []) if isinstance(t, str)]
    assert "fast_fallback" in tags
    assert "upstream_api_fast_fallback" in tags

    text = str(gm.get("player_facing_text") or "")
    low = text.lower()
    assert any(token in low for token in ("patron", "voice", "gossip", "missing patrol"))
    assert "footprint" not in low
    assert "crate" not in low
    assert len([s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]) <= 2


def test_chat_inspect_clue_nonretryable_quota_prefers_physical_fallback(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    _seed_intent_aligned_fast_fallback_scene()

    def fake_call_gpt(_messages):
        return _quota_error_response()

    player_text = "I inspect the footprints by the disturbed crates."

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: {"kind": "observe", "prompt": player_text})
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": player_text})

    assert resp.status_code == 200
    gm = (resp.json().get("gm_output") or {})
    tags = [str(t) for t in (gm.get("tags") or []) if isinstance(t, str)]
    assert "fast_fallback" in tags
    assert "upstream_api_fast_fallback" in tags

    text = str(gm.get("player_facing_text") or "")
    low = text.lower()
    assert "footprint" in low or "crate" in low or "disturbed" in low
    assert "voices low" not in low
    assert len([s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]) <= 2


def test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload():
    campaign = default_campaign()
    world = default_world()
    world["npcs"] = [
        {
            "id": "guard_captain",
            "name": "Captain Veyra",
            "location": "frontier_gate",
            "stance_toward_player": "wary",
            "information_reliability": "partial",
            "knowledge_scope": ["scene:frontier_gate", "missing_patrol"],
            "current_agenda": "screen arrivals",
        }
    ]
    session = {
        "scene_runtime": {},
        "visited_scene_ids": ["frontier_gate"],
        "turn_counter": 7,
        "interaction_context": {
            "active_interaction_target_id": "guard_captain",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
            "conversation_privacy": "lowered_voice",
            "player_position_context": "at_gate_table",
        },
    }
    scene = {
        "scene": {
            "id": "frontier_gate",
            "location": "Frontier Gate",
            "summary": "A rain-soaked checkpoint watches a crowd of refugees and merchants.",
            "visible_facts": [
                "Refugees crowd the approach road.",
                "A notice board lists a missing patrol.",
                "Captain Veyra questions arrivals at a narrow table.",
                "A tavern runner hawks stew and rumors nearby.",
                "Rain darkens the flagstones around the gate.",
                "A wagon train waits under watchful guards.",
            ],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    recent_log = [
        {
            "log_meta": {"player_input": "What happened to the missing patrol?"},
            "gm_output": {"player_facing_text": "Captain Veyra says, \"They vanished east of the toll stones two nights ago.\""},
        },
        {
            "log_meta": {"player_input": "Who was on that patrol?"},
            "gm_output": {"player_facing_text": "Captain Veyra says, \"Sergeant Pell and four gate spears.\""},
        },
    ]
    character = default_character()
    combat = {"in_combat": False}
    scene_rt = get_scene_runtime(session, "frontier_gate")

    compact_msgs = build_messages(
        campaign,
        world,
        session,
        character,
        scene,
        combat,
        recent_log,
        "Where should I start looking for them?",
        {
            "kind": "question",
            "prompt": "Where should I start looking for them?",
            "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "npc_reply_expected": True},
        },
        scene_runtime=scene_rt,
        prompt_profile="manual_play_compact",
    )
    full_msgs = build_messages(
        campaign,
        world,
        session,
        character,
        scene,
        combat,
        recent_log,
        "Where should I start looking for them?",
        {
            "kind": "question",
            "prompt": "Where should I start looking for them?",
            "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra", "npc_reply_expected": True},
        },
        scene_runtime=scene_rt,
        prompt_profile="full",
    )

    compact_payload = json.loads(compact_msgs[1]["content"])
    full_payload = json.loads(full_msgs[1]["content"])

    assert "prompt_debug" not in compact_payload
    assert "prompt_debug" not in full_payload
    assert compact_payload["active_interlocutor"]["npc_id"] == "guard_captain"
    assert compact_payload["interaction_continuity"]["active_interaction_target_id"] == "guard_captain"
    assert compact_payload["scene_state_anchor_contract"]["enabled"] is True
    assert compact_payload["response_policy"]["answer_completeness"]["answer_required"] is True
    assert compact_payload["social_context"]["answer_style_hints"]
    assert len(compact_payload["scene"]["public"]["visible_facts"]) <= 5
    assert len(compact_payload["selected_conversational_memory"]) <= 6
    assert len(compact_payload["recent_log"]) <= 4
    assert "fallback_behavior" not in compact_payload
    assert "interaction_continuity_contract" not in compact_payload
    assert len(compact_msgs[1]["content"]) < len(full_msgs[1]["content"])


def test_final_emission_fast_path_skips_optional_smoothing():
    out = {
        "player_facing_text": "Captain Veyra says, \"Start at the toll stones.\"",
        "tags": [],
        "_final_emission_meta": {
            "final_route": "accept_candidate",
            "response_type_candidate_ok": True,
            "answer_completeness_failed": False,
            "narrative_authority_failed": False,
            "fallback_behavior_failed": False,
            "fallback_behavior_repaired": False,
            "fallback_behavior_uncertainty_active": False,
            "response_type_repair_used": False,
            "answer_completeness_repaired": False,
            "response_delta_repaired": False,
            "social_response_structure_repair_applied": False,
            "tone_escalation_repaired": False,
            "anti_railroading_repaired": False,
            "context_separation_repaired": False,
            "player_facing_narration_purity_repaired": False,
            "answer_shape_primacy_repaired": False,
            "candidate_quality_degraded": False,
            "speaker_contract_enforcement_reason": None,
        },
    }

    assert feg._final_emission_fast_path_eligible(out) is True
    finalized = feg._finalize_emission_output(
        dict(out),
        pre_gate_text=out["player_facing_text"],
        fast_path=feg._final_emission_fast_path_eligible(out),
    )
    meta = read_final_emission_meta_dict(finalized) or {}
    assert meta.get("final_emission_fast_path_used") is True
    assert meta.get("sentence_decompression_applied") is False
    assert meta.get("sentence_fragment_repair_applied") is False
    assert meta.get("sentence_micro_smoothing_applied") is False
