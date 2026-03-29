"""Stage 0 regression: compact per-turn debug trace persisted in session.debug_traces.

Freezes the minimum ``turn_trace`` shape inside each appended entry so routing, state,
emission, and content failures stay diagnosable without new tracing infrastructure.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.output_sanitizer import resembles_serialized_response_payload
from tests.test_turn_pipeline_shared import FAKE_GPT_RESPONSE, _seed_shared_world

pytestmark = pytest.mark.integration

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


def _walk_turn_trace_for_leaks(obj: object, *, path: str = "turn_trace") -> None:
    """Reject prompt dumps and raw chat-style message arrays inside the compact trace."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            if kl == "messages" and isinstance(v, list) and len(v) > 8:
                pytest.fail(f"unexpected bulk messages list at {path}.{k} (len={len(v)})")
            if kl in ("system_prompt", "developer_prompt", "full_prompt", "raw_prompt") and isinstance(v, str) and len(v) > 8000:
                pytest.fail(f"unexpected large prompt field at {path}.{k}")
            _walk_turn_trace_for_leaks(v, path=f"{path}.{k}")
    elif isinstance(obj, list):
        if len(obj) >= 6 and all(isinstance(it, dict) for it in obj):
            role_content = sum(1 for it in obj if isinstance(it, dict) and "role" in it and "content" in it)
            if role_content >= max(4, len(obj) - 1):
                pytest.fail(f"unexpected OpenAI-style message transcript at {path} (len={len(obj)})")
        for i, it in enumerate(obj):
            _walk_turn_trace_for_leaks(it, path=f"{path}[{i}]")
    elif isinstance(obj, str) and len(obj) > 20000:
        pytest.fail(f"unexpected huge string at {path} (len={len(obj)})")


def _assert_minimal_turn_trace_contract(tt: dict, *, source: str, expect_parsed_intent: bool) -> None:
    assert isinstance(tt, dict)
    assert tt.get("source") == source
    assert isinstance(tt.get("player_input"), str)

    intent = tt.get("intent")
    assert isinstance(intent, dict)
    if expect_parsed_intent:
        assert isinstance(intent.get("parsed"), dict)
    else:
        assert intent.get("parsed") is None
        assert isinstance(intent.get("normalized"), dict)

    clf = tt.get("classification")
    assert isinstance(clf, dict)
    assert isinstance(clf.get("action_type"), str) and clf["action_type"].strip()
    assert "resolved_kind" in clf

    rp = tt.get("resolution_path")
    assert isinstance(rp, str) and rp.strip()

    asc = tt.get("authoritative_state_changes")
    assert isinstance(asc, dict)
    for k in ("scene_transition", "resolution_state_changes", "resolution_world_updates", "check_request"):
        assert k in asc

    ia = tt.get("interaction_after")
    assert isinstance(ia, dict)

    clues = tt.get("clues")
    assert isinstance(clues, dict)
    assert isinstance(clues.get("discovered_texts"), list)
    assert isinstance(clues.get("presentation_changes"), list)
    assert isinstance(clues.get("known_counts"), dict)

    assert isinstance(tt.get("affordances_after"), list)


# feature: debug trace, routing
@pytest.mark.parametrize(
    "endpoint,source,expect_parsed",
    [
        ("action", "action", False),
        ("chat", "chat", True),
    ],
)
def test_compact_turn_trace_contract_action_and_chat(tmp_path, monkeypatch, endpoint, source, expect_parsed):
    _seed_shared_world(tmp_path, monkeypatch)
    _add_runner_npc()

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        if endpoint == "chat":
            m.setattr("game.api.parse_social_intent", lambda *_a, **_k: dict(_SOCIAL_ACTION))
            m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
            m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        if endpoint == "action":
            resp = client.post(
                "/api/action",
                json={
                    "action_type": "social",
                    "intent": "I talk to Tavern Runner.",
                    "social_action": _SOCIAL_ACTION,
                },
            )
        else:
            resp = client.post("/api/chat", json={"text": "I talk to Tavern Runner."})

    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True

    gm = body.get("gm_output") or {}
    ptext = gm.get("player_facing_text") or ""
    assert not resembles_serialized_response_payload(str(ptext)), (
        "player-facing surface must not expose raw serialized model payloads"
    )

    api_traces = body.get("debug_traces") or []
    assert api_traces, "turn API responses should include debug_traces via compose_state"
    entry = api_traces[-1]
    assert entry.get("response_ok") is True
    assert "error" in entry
    tt = entry.get("turn_trace")
    _assert_minimal_turn_trace_contract(tt, source=source, expect_parsed_intent=expect_parsed)
    _walk_turn_trace_for_leaks(tt)

    session = storage.load_session()
    disk_traces = session.get("debug_traces") or []
    assert disk_traces, "trace should be persisted to session storage"
    disk_entry = disk_traces[-1]
    assert disk_entry.get("response_ok") is True
    _assert_minimal_turn_trace_contract(
        disk_entry.get("turn_trace"),
        source=source,
        expect_parsed_intent=expect_parsed,
    )
    _walk_turn_trace_for_leaks(disk_entry.get("turn_trace"))
