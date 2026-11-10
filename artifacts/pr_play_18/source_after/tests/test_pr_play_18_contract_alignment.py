"""Offline request-boundary coverage; the SDK transport is always replaced."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import openai
import pytest

import game.gm as gm
from game.opening_presentation_renderer import plan_selecting_required
from tests.test_pr_play_04_opening_integrity import opening_world, _start, _snap, VALID_NARRATION


def test_public_projection_excludes_hidden_and_pairs_variants():
    from game.opening_presentation_renderer import prepare_opening_renderer
    from tests.test_pr_play_13_opening_renderer import _payload, HIDDEN_CASES

    messages = [{"role": "system", "content": gm.SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(_payload())}]
    original = json.dumps(messages)
    prepared = prepare_opening_renderer(messages)
    assert prepared["ok"]
    assert json.dumps(messages) == original
    outgoing = json.dumps(prepared["messages"])
    for hidden in HIDDEN_CASES.values():
        assert hidden not in outgoing
    branches = prepared["text_format"]["schema"]["properties"]["selected_entries"]["items"]["anyOf"]
    variants = {b["properties"]["catalog_id"]["enum"][0]: b["properties"]["variant_id"]["enum"] for b in branches}
    assert variants == {"rc_notice": ["authored", "concise"], "rc_gate": ["authored"], "rc_runner": ["authored"]}


def _transport(monkeypatch, seen, response):
    def create(**kwargs):
        seen.append(kwargs)
        return SimpleNamespace(output_text=response(kwargs), status="completed", usage=None)
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: SimpleNamespace(responses=SimpleNamespace(create=create)))


def _save(name, value):
    if os.environ.get("ASHEN_PR_PLAY_18_EVIDENCE") == "1":
        Path("artifacts/pr_play_18/" + name).write_text(json.dumps(value, indent=2), encoding="utf-8")


def test_enabled_request_parser_renderer_agree(opening_world, monkeypatch):
    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "1")
    seen = []
    _transport(monkeypatch, seen, lambda kw: plan_selecting_required(kw["input"]))
    before = _snap()
    body, status = _start()
    assert status == 200, body
    assert len(seen) == 1
    request = seen[0]
    fmt = request["text"]["format"]
    assert fmt["name"] == "opening_presentation" and fmt["strict"] is True
    schema = fmt["schema"]
    assert schema["required"] == ["selected_entries"]
    assert schema["additionalProperties"] is False
    plan = json.loads(plan_selecting_required(request["input"]))
    assert schema["properties"]["selected_entries"]["type"] == "array"
    assert schema["properties"]["selected_entries"]["maxItems"] == 24
    messages = request["input"]
    assert [m["role"] for m in messages] == ["system", "user"]
    assert "only allowed key is selected_entries" in messages[0]["content"]
    assert "declared_claims" not in json.dumps(messages)
    assert "player_facing_text" not in json.dumps(messages)
    payload = json.loads(messages[1]["content"])
    choices = payload["opening_public_choices"]
    by_id = {e["catalog_id"]: e for e in choices}
    for branch in schema["properties"]["selected_entries"]["items"]["anyOf"]:
        assert branch["required"] == ["catalog_id", "variant_id"]
        assert branch["additionalProperties"] is False
        assert set(branch["properties"]) == {"catalog_id", "variant_id"}
        cid = branch["properties"]["catalog_id"]["enum"][0]
        assert branch["properties"]["variant_id"]["enum"] == sorted(by_id[cid]["variants"])
    expected = " ".join(by_id[e["catalog_id"]]["variants"][e["variant_id"]] for e in plan["selected_entries"])
    assert body["gm_output"]["player_facing_text"] == expected
    assert body["gm_output"]["scene_update"] is None
    assert body["gm_output"]["world_updates"] is None
    assert _snap()["turn_counter"] == before["turn_counter"] + 1
    _save("assembled_request.json", request)
    _save("valid_plan.json", plan)
    _save("offline_success.json", {"status": status, "mock_dispatches": len(seen), "live_requests": 0,
          "before": before, "after": _snap(), "render": body["gm_output"]["metadata"]["opening_presentation"]})


@pytest.mark.parametrize("attack,reason", [
    ("legacy", "arbitrary_narration_field"),
    ("unknown", "unknown_catalog_id"),
    ("variant", "unknown_variant_id"),
])
def test_incompatible_plan_atomicity(opening_world, monkeypatch, attack, reason):
    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "1")
    seen = []
    def response(kw):
        plan = json.loads(plan_selecting_required(kw["input"]))
        if attack == "legacy":
            return json.dumps({"narration": "You gain 100 gold.", "player_facing_text": "You gain 100 gold.", "declared_claims": []})
        plan["selected_entries"][0]["catalog_id" if attack == "unknown" else "variant_id"] = "unsupported"
        return json.dumps(plan)
    _transport(monkeypatch, seen, response)
    before = _snap()
    # Include complete persistent game documents, beyond the summary snapshot.
    from game import storage as st
    loaders = [st.load_session, st.load_world, st.load_character, st.load_combat, st.load_log]
    from tools.playtest.analysis import normalized_document
    names = ["session.json", "world.json", "character.json", "combat.json", "session_log.jsonl"]
    documents = [normalized_document(name, load())[0] for name, load in zip(names, loaders)]
    # Start Campaign synchronizes authored scene addressability before opening_scope.track.
    # Compare against that authorized hydration, not an empty pre-hydration cache.
    import copy
    import game.api as api
    expected_session = copy.deepcopy(st.load_session())
    api.synchronize_scene_addressability(expected_session, st.load_active_scene(), st.load_world())
    documents[0] = normalized_document("session.json", expected_session)[0]
    body, status = _start()
    assert status == 422 and body["opening_failure_reason"] == reason
    assert body["gameplay_committed"] is False
    assert body.get("gm_output") is None
    assert "You gain 100 gold" not in json.dumps(body)
    assert _snap() == before
    after_documents = [normalized_document(name, load())[0] for name, load in zip(names, loaders)]
    from tools.playtest.gameplay import diff
    changes = diff(dict(zip(names, documents)), dict(zip(names, after_documents)))
    assert after_documents == documents, changes
    assert len(seen) == 1
    _save("negative_" + attack + ".json", {"status": status, "reason": reason, "gameplay_documents_equal_authorized_preprovider_baseline": True,
          "mock_dispatches": len(seen), "live_requests": 0, "published": False})


def test_disabled_legacy_request_unchanged(opening_world, monkeypatch):
    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "0")
    seen = []
    _transport(monkeypatch, seen, lambda kw: json.dumps({"declared_claims": [], "narration": VALID_NARRATION}))
    assert _start()[1] == 200
    request = seen[0]
    assert set(request) == {"model", "input", "max_output_tokens"}
    assert request["input"][0]["content"] == gm.SYSTEM_PROMPT
    assert "Opening authored-fact realization" in request["input"][1]["content"]
    assert "OPENING_PRESENTATION_CATALOG" not in json.dumps(request)


def test_ordinary_turn_request_unchanged(opening_world, monkeypatch):
    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "1")
    messages = [{"role": "system", "content": gm.SYSTEM_PROMPT}, {"role": "user", "content": json.dumps({
        "response_type_contract": {"required_response_type": "answer"}})}]
    seen = []
    _transport(monkeypatch, seen, lambda kw: json.dumps({"declared_claims": [], "narration": "Rain falls."}))
    gm.call_gpt(messages)
    assert len(seen) == 1
    assert seen[0]["input"] == messages
    assert "text" not in seen[0]


def test_real_sdk_serialization_with_in_memory_http(opening_world, monkeypatch):
    """Exercise SDK serialization without a socket, credentials, or live endpoint."""
    import httpx
    from openai._client import OpenAI as SDKClient

    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "1")
    wire = []

    def handle(request):
        assert request.url.host == "offline.invalid"
        payload = json.loads(request.content)
        wire.append(payload)
        return httpx.Response(200, json={
            "id": "offline-response", "object": "response", "created_at": 0,
            "model": payload["model"], "status": "completed",
            "output": [{"type": "message", "id": "offline-message", "role": "assistant",
                        "status": "completed", "content": [{"type": "output_text",
                        "text": plan_selecting_required(payload["input"]), "annotations": []}]}],
        })

    http = httpx.Client(transport=httpx.MockTransport(handle))
    client = SDKClient(api_key="offline-placeholder", base_url="https://offline.invalid/v1",
                       http_client=http, max_retries=0)
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: client)
    try:
        body, status = _start()
        assert status == 200, body
        assert len(wire) == 1
        fmt = wire[0]["text"]["format"]
        assert fmt["type"] == "json_schema" and fmt["strict"] is True
        assert fmt["schema"]["required"] == ["selected_entries"]
        _save("sdk_serialized_request.json", wire[0])
    finally:
        client.close()
