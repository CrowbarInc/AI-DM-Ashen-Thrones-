"""Transcript-style tests: multi-POST sequencing and session continuity (not single-turn correctness).

Single-turn routing, discovery shape, and combat engine details are covered by integration/unit tests
(e.g. ``test_turn_pipeline_shared``, ``test_exploration_resolution``, ``test_discovery_memory``,
``test_combat_resolution``). This module locks **ordering** across requests (state from turn N
must be visible on turn N+1) and a small slice of **retry-budget exhaustion** end-to-end on
``/api/action`` (terminal forward progress, not narration wording).

Retry **prompt string** contracts (``build_retry_prompt_for_failure``) live under
``tests/test_prompt_and_guard.py``; this file only checks retry exhaustion / terminal metadata smoke
plus player-facing usability (validator-voice detection smoke, not duplicate phrase families).

Strict-social **wording** and topic-pressure restore contracts live under ``test_social_exchange_emission.py``
and ``test_social_emission_quality.py``; transcript assertions here stay **consequence-first** (scene,
resolution kind, continuity) with light social-grounding smoke only.
"""
from __future__ import annotations

from game import storage
from game.api import app
from game.leads import LeadLifecycle, LeadStatus, create_lead, get_lead, upsert_lead
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.gm import MAX_TARGETED_RETRY_ATTEMPTS, detect_validator_voice
from game.storage import get_scene_runtime
from fastapi.testclient import TestClient

import pytest

pytestmark = [pytest.mark.transcript, pytest.mark.slow]

DESK_CLUE_ID = "desk_clue"

# Triggers ``validator_voice`` retry failures on every attempt (no ``?`` player line → no unresolved-question race).
_VALIDATOR_VOICE_TRAP_TEXT = (
    "Based on what's established, we can determine very little here."
)

FAKE_GPT_RESPONSE = {
    "player_facing_text": "[Narration]",
    "tags": [],
    "scene_update": None,
    "activate_scene_id": None,
    "new_scene_draft": None,
    "world_updates": None,
    "suggested_action": None,
    "debug_notes": "",
}


def _patch_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "BASE_DIR", tmp_path)
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "WORLD_PATH", storage.DATA_DIR / "world.json")
    monkeypatch.setattr(storage, "SCENES_DIR", storage.DATA_DIR / "scenes")
    monkeypatch.setattr(storage, "CHARACTER_PATH", storage.DATA_DIR / "character.json")
    monkeypatch.setattr(storage, "CAMPAIGN_PATH", storage.DATA_DIR / "campaign.json")
    monkeypatch.setattr(storage, "SESSION_PATH", storage.DATA_DIR / "session.json")
    monkeypatch.setattr(storage, "COMBAT_PATH", storage.DATA_DIR / "combat.json")
    monkeypatch.setattr(storage, "CONDITIONS_PATH", storage.DATA_DIR / "conditions.json")
    monkeypatch.setattr(storage, "SESSION_LOG_PATH", storage.DATA_DIR / "session_log.jsonl")
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)


def _seed_transcript_world(tmp_path, monkeypatch, **overrides):
    """Minimal graph: investigation scene, a<->b loop, isolated unreachable from a; optional goblin."""
    _patch_storage(tmp_path, monkeypatch)
    active = overrides.get("active", "scene_investigate")

    inv_scene = default_scene("scene_investigate")
    inv_scene["scene"]["id"] = "scene_investigate"
    inv_scene["scene"]["location"] = "Investigation room"
    inv_scene["scene"]["interactables"] = [
        {"id": "desk", "type": "investigate", "reveals_clue": DESK_CLUE_ID},
    ]
    inv_scene["scene"]["discoverable_clues"] = [
        {"id": DESK_CLUE_ID, "text": "A map indicates patrol locations."},
    ]
    if overrides.get("with_goblin"):
        inv_scene["scene"]["enemies"] = [
            {
                "id": "goblin_1",
                "name": "Goblin",
                "hp": {"current": 6, "max": 6},
                "initiative_bonus": -10,
                "creature_type": "humanoid",
                "hd": 1,
                "saves": {"will": 0},
                "attacks": [
                    {
                        "id": "dagger",
                        "name": "Dagger",
                        "attack_bonus": 1,
                        "damage": {"dice_count": 1, "dice_sides": 4, "bonus": 0, "type": "piercing"},
                    }
                ],
            }
        ]
    inv_scene["scene"]["exits"] = [{"label": "To Scene B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_investigate"), inv_scene)

    sa = default_scene("scene_a")
    sa["scene"]["id"] = "scene_a"
    sa["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_a"), sa)

    sb = default_scene("scene_b")
    sb["scene"]["id"] = "scene_b"
    sb["scene"]["exits"] = [{"label": "To A", "target_scene_id": "scene_a"}]
    storage._save_json(storage.scene_path("scene_b"), sb)

    si = default_scene("scene_isolated")
    si["scene"]["id"] = "scene_isolated"
    si["scene"]["exits"] = [{"label": "To B", "target_scene_id": "scene_b"}]
    storage._save_json(storage.scene_path("scene_isolated"), si)

    session = default_session()
    session["active_scene_id"] = active
    session["visited_scene_ids"] = ["scene_investigate", "scene_a", "scene_b", "scene_isolated"]
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _gm_response(text: str, *, tags=None, debug_notes: str = ""):
    return {
        "player_facing_text": text,
        "tags": list(tags or []),
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": debug_notes,
    }


def _gm_with_non_authoritative_scene(target_scene_id: str) -> dict:
    out = _gm_response("You press on under a thin, watchful sky.")
    out["activate_scene_id"] = target_scene_id
    return out


def _seed_frontier_gate_eastern_square_stale_milestone_lead(tmp_path, monkeypatch):
    """Gate with exit to eastern_square + old_milestone; session holds a stale milestone pending lead."""
    _patch_storage(tmp_path, monkeypatch)
    gate = default_scene("frontier_gate")
    gate["scene"]["id"] = "frontier_gate"
    gate["scene"]["exits"] = [
        {"label": "Path to the eastern square", "target_scene_id": "eastern_square"},
        {"label": "Follow the missing patrol rumor", "target_scene_id": "old_milestone"},
    ]
    for ad in gate["scene"].get("addressables") or []:
        if isinstance(ad, dict):
            ad["scene_id"] = "frontier_gate"
    storage._save_json(storage.scene_path("frontier_gate"), gate)

    east = default_scene("tavern")
    east["scene"]["id"] = "eastern_square"
    east["scene"]["exits"] = []
    storage._save_json(storage.scene_path("eastern_square"), east)

    ms = default_scene("old_milestone")
    ms["scene"]["id"] = "old_milestone"
    storage._save_json(storage.scene_path("old_milestone"), ms)

    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    upsert_lead(
        session,
        create_lead(
            id="ms_lead",
            title="Patrol rumor",
            summary="",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            related_scene_ids=["old_milestone"],
        ),
    )
    rt = get_scene_runtime(session, "frontier_gate")
    rt["pending_leads"] = [
        {
            "clue_id": "c_patrol",
            "authoritative_lead_id": "ms_lead",
            "text": "The patrol was last seen at the old milestone",
            "leads_to_scene": "old_milestone",
        }
    ]
    storage._save_json(storage.SESSION_PATH, session)

    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [
                {
                    "id": "lirael_tip",
                    "text": "Lirael posts near the eastern square when she is not on the crier route.",
                    "clue_id": "c_lirael",
                }
            ],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _seed_tavern_patrol_lead_old_milestone(tmp_path, monkeypatch):
    """Tavern + milestone exit + runner topic that lands an actionable milestone lead (no pre-seeded pending)."""
    _patch_storage(tmp_path, monkeypatch)
    tavern = default_scene("tavern")
    tavern["scene"]["id"] = "tavern"
    tavern["scene"]["exits"] = [{"label": "Path to the old milestone", "target_scene_id": "old_milestone"}]
    for ad in tavern["scene"].get("addressables") or []:
        if isinstance(ad, dict):
            ad["scene_id"] = "tavern"
    storage._save_json(storage.scene_path("tavern"), tavern)
    ms = default_scene("old_milestone")
    ms["scene"]["id"] = "old_milestone"
    storage._save_json(storage.scene_path("old_milestone"), ms)

    session = default_session()
    session["active_scene_id"] = "tavern"
    session["visited_scene_ids"] = ["tavern"]
    storage._save_json(storage.SESSION_PATH, session)

    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "tavern",
            "topics": [
                {
                    "id": "patrol_milestone",
                    "text": "The patrol never came back from the old milestone.",
                    "clue_id": "c_patrol_milestone",
                    "leads_to_scene": "old_milestone",
                }
            ],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _seed_tavern_patrol_lead_with_second_npc(tmp_path, monkeypatch):
    _seed_tavern_patrol_lead_old_milestone(tmp_path, monkeypatch)
    world = storage.load_world()
    world["npcs"] = list(world.get("npcs") or []) + [
        {
            "id": "guard_captain",
            "name": "Guard Captain",
            "location": "tavern",
            "topics": [
                {
                    "id": "gate_scuffle",
                    "text": "The main gate is a mess whenever the fish carts clog the lane.",
                    "clue_id": "c_gate_scuffle",
                }
            ],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)


def _seed_transcript_world_with_runner(tmp_path, monkeypatch):
    """Transcript seed plus a single NPC for directed social turns on the investigation scene."""
    _seed_transcript_world(tmp_path, monkeypatch)
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


def _assert_player_facing_text_is_usable(text: str) -> None:
    t = (text or "").strip()
    assert t, "player-facing text must be non-empty"
    assert not t.startswith("{"), "player-facing text must not look like a raw JSON object"
    assert '"player_facing_text"' not in t, "player-facing text must not embed serialized payload keys"
    assert '"scene_update"' not in t


def _assert_terminal_retry_or_repair_metadata(gm: dict) -> None:
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    dbg = gm.get("debug_notes") if isinstance(gm.get("debug_notes"), str) else ""
    assert (
        gm.get("targeted_retry_terminal") is True
        or gm.get("retry_exhausted") is True
        or "forced_retry_fallback" in tags
        or "retry_escape_hatch" in tags
        or "retry_exhausted" in tags
        or "forced_retry_fallback" in dbg
        or "retry_escape_hatch" in dbg
    ), "expected terminal retry / escape-hatch signals on gm_output"


def _post_explore(client, exploration_action: dict, intent: str | None = None):
    payload = {"action_type": "exploration", "exploration_action": exploration_action}
    if intent:
        payload["intent"] = intent
    r = client.post("/api/action", json=payload)
    assert r.status_code == 200
    return r.json()


def _post_chat(client, text: str) -> dict:
    r = client.post("/api/chat", json={"text": text})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    return data


def _latest_user_text(messages) -> str:
    fallback = ""
    for msg in reversed(list(messages or [])):
        if not isinstance(msg, dict) or str(msg.get("role") or "").strip().lower() != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            try:
                payload = __import__("json").loads(content)
            except Exception:
                if not fallback:
                    fallback = content
                continue
            if isinstance(payload, dict):
                player_text = str(payload.get("player_text") or "").strip()
                if player_text:
                    return player_text
            if not fallback:
                fallback = content
            continue
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and str(item.get("type") or "").strip() == "text":
                    parts.append(str(item.get("text") or ""))
            joined = " ".join(parts).strip()
            if joined:
                return joined
    return fallback


def _assert_not_repeated_interruption_beat(text: str) -> None:
    low = str(text or "").lower()
    forbidden = (
        "starts to answer",
        "begins to answer",
        "begins to respond",
        "opens their mouth",
        "breaks off as a shout cuts across the square",
        "shouting breaks out in the crowd",
        "noise from the crowd pulls their attention away",
    )
    for frag in forbidden:
        assert frag not in low, f"unexpected interruption replay fragment: {frag!r} in {text!r}"


def _assert_socially_grounded_progression(text: str, *extra_markers: str) -> None:
    """Smoke: response still ties to the tavern/patrol thread (not a generic stub).

    Detailed NPC-voice / strict-social substring families belong in ``test_social_exchange_emission.py``
    and ``test_social_emission_quality.py``; callers may pass *extra_markers* for beat-specific tokens.
    """
    low = str(text or "").lower()
    markers = (
        "runner",
        "guard captain",
        "old milestone",
        "old millstone",
        "main gate",
        "ward clerk",
        "watchmen",
        "east gate",
        "leans closer",
        "stay with me",
    ) + tuple(m.lower() for m in extra_markers)
    assert any(marker in low for marker in markers), f"expected socially grounded progression in {text!r}"


def test_transcript_sequence_investigate_then_repeat_is_idempotent(tmp_path, monkeypatch):
    """Turn 1 discovers; turn 2 must see persisted runtime and return already_searched (not a second clue)."""
    _seed_transcript_world(tmp_path, monkeypatch)
    desk_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk",
    }
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        r1 = _post_explore(client, desk_action, intent="I investigate the desk")
        r2 = _post_explore(client, desk_action, intent="I investigate the desk")

    assert r1["resolution"]["kind"] == "discover_clue"
    assert r1["resolution"]["clue_id"] == DESK_CLUE_ID
    ids_1 = r1["session"]["scene_runtime"]["scene_investigate"]["discovered_clue_ids"]
    assert ids_1 == [DESK_CLUE_ID]

    assert r2["resolution"]["kind"] == "already_searched"
    assert r2["resolution"]["clue_id"] is None
    ids_2 = r2["session"]["scene_runtime"]["scene_investigate"]["discovered_clue_ids"]
    assert ids_2 == [DESK_CLUE_ID]
    assert r2["session"]["scene_runtime"]["scene_investigate"].get("repeated_action_count", 0) >= 2


def test_transcript_sequence_travel_then_blocked_respects_updated_scene(tmp_path, monkeypatch):
    """After a successful transition, the next request uses the new scene's exit graph (blocked hop stays put)."""
    _seed_transcript_world(tmp_path, monkeypatch, active="scene_a")
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        r_ok = _post_explore(
            client,
            {
                "id": "go-b",
                "label": "Go to B",
                "type": "scene_transition",
                "targetSceneId": "scene_b",
                "prompt": "I go to B.",
            },
        )
        r_bad = _post_explore(
            client,
            {
                "id": "go-isolated",
                "label": "Go to isolated",
                "type": "scene_transition",
                "targetSceneId": "scene_isolated",
                "prompt": "I go to the isolated area.",
            },
        )

    assert r_ok["session"]["active_scene_id"] == "scene_b"
    assert r_ok["resolution"]["resolved_transition"] is True

    assert r_bad["resolution"]["resolved_transition"] is False
    assert r_bad["session"]["active_scene_id"] == "scene_b"


def test_transcript_sequence_combat_initiative_then_attack(tmp_path, monkeypatch):
    """Combat state from roll_initiative must persist for the following attack POST."""
    _seed_transcript_world(tmp_path, monkeypatch, with_goblin=True)
    monkeypatch.setattr("game.utils.roll_die", lambda _: 15)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _: FAKE_GPT_RESPONSE)
        client = TestClient(app)
        r1 = client.post("/api/action", json={"action_type": "roll_initiative"})
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["ok"] and d1["resolution"]["kind"] == "initiative"
        assert d1["combat"]["in_combat"] is True

        r2 = client.post(
            "/api/action",
            json={
                "action_type": "attack",
                "attack_id": "quarterstaff",
                "target_id": "goblin_1",
            },
        )
        assert r2.status_code == 200
        d2 = r2.json()

    assert d2["ok"] is True
    res2 = d2["resolution"]
    assert res2["kind"] == "attack"
    assert res2["combat"]["combat_phase"] == "attack"
    assert res2["combat"]["actor"]["id"] == "galinor"
    assert res2["combat"]["target"]["id"] == "goblin_1"


def test_transcript_social_retry_exhaustion_terminal_forward_progress(tmp_path, monkeypatch):
    """Social POST: every GPT attempt fails ``validator_voice`` until the budget is exhausted; response still completes."""
    _seed_transcript_world_with_runner(tmp_path, monkeypatch)
    social_action = {
        "id": "greet-runner",
        "label": "Acknowledge the runner",
        "type": "question",
        "prompt": "I nod to the Tavern Runner, giving them room to speak.",
        "target_id": "runner",
        "targetEntityId": "runner",
    }
    gpt_calls: list = []

    def _always_fail_validator_voice(_messages):
        gpt_calls.append(_messages)
        return _gm_response(_VALIDATOR_VOICE_TRAP_TEXT)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _always_fail_validator_voice)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={
                "action_type": "social",
                "intent": "I nod to the Tavern Runner, giving them room to speak.",
                "social_action": social_action,
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    gm = data.get("gm_output") or {}
    pft = gm.get("player_facing_text")
    pft_s = str(pft or "")
    _assert_player_facing_text_is_usable(pft_s)
    assert detect_validator_voice(pft_s) == []
    _assert_terminal_retry_or_repair_metadata(gm)

    assert len(gpt_calls) == 1 + MAX_TARGETED_RETRY_ATTEMPTS

    ctx = (data.get("session") or {}).get("interaction_context") or {}
    assert ctx.get("active_interaction_target_id") == "runner"
    assert ctx.get("active_interaction_kind") == "social"
    assert ctx.get("interaction_mode") == "social"
    assert (ctx.get("engagement_level") or "").strip().lower() == "engaged"

    res = data.get("resolution") or {}
    assert res.get("kind") == "question"
    assert (res.get("social") or {}).get("npc_id") == "runner"


def test_transcript_nonsocial_retry_exhaustion_terminal_forward_progress(tmp_path, monkeypatch):
    """Exploration POST: retry budget exhausts on repeated ``validator_voice``; clue discovery and narration still complete."""
    _seed_transcript_world(tmp_path, monkeypatch)
    desk_action = {
        "id": "inv-desk",
        "label": "Investigate the desk",
        "type": "investigate",
        "prompt": "I investigate the desk",
    }
    gpt_calls: list = []

    def _always_fail_validator_voice(_messages):
        gpt_calls.append(_messages)
        return _gm_response(_VALIDATOR_VOICE_TRAP_TEXT)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _always_fail_validator_voice)
        client = TestClient(app)
        resp = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "I investigate the desk",
                "exploration_action": desk_action,
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    gm = data.get("gm_output") or {}
    pft_ns = str(gm.get("player_facing_text") or "")
    _assert_player_facing_text_is_usable(pft_ns)
    assert detect_validator_voice(pft_ns) == []
    _assert_terminal_retry_or_repair_metadata(gm)
    assert len(gpt_calls) == 1 + MAX_TARGETED_RETRY_ATTEMPTS

    assert (data.get("session") or {}).get("active_scene_id") == "scene_investigate"
    res = data.get("resolution") or {}
    assert res.get("kind") == "discover_clue"
    assert res.get("clue_id") == DESK_CLUE_ID
    rt = (data.get("session") or {}).get("scene_runtime", {}).get("scene_investigate") or {}
    assert DESK_CLUE_ID in (rt.get("discovered_clue_ids") or [])


def test_transcript_old_milestone_chat_flow_stays_authoritative_end_to_end(tmp_path, monkeypatch):
    """Patrol question → actionable milestone lead → mixed farewell + travel; scene from resolver, not GPT scene id."""
    _seed_tavern_patrol_lead_old_milestone(tmp_path, monkeypatch)

    gpt_calls: list[int] = []

    def _call_gpt(_messages):
        gpt_calls.append(len(gpt_calls))
        if gpt_calls[-1] == 0:
            return _gm_response(
                "The runner leans in: the last reliable sign of the patrol points toward the old milestone."
            )
        return _gm_with_non_authoritative_scene("bogus_gpt_scene")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt)
        client = TestClient(app)
        r1 = client.post(
            "/api/chat",
            json={"text": "Tavern Runner, what happened to the patrol?"},
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1.get("ok") is True
        s1 = d1.get("session") or {}
        rt1 = get_scene_runtime(s1, "tavern")
        pending = rt1.get("pending_leads") or []
        assert any(str(p.get("leads_to_scene") or "").strip() == "old_milestone" for p in pending if isinstance(p, dict))

        r2 = client.post(
            "/api/chat",
            json={
                "text": (
                    '"Thank you." Galinor leaves the runner for the old milestone.'
                )
            },
        )

    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("ok") is True
    assert d2.get("session", {}).get("active_scene_id") == "old_milestone"
    assert d2.get("scene", {}).get("scene", {}).get("id") == "old_milestone"
    res = d2.get("resolution") or {}
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "old_milestone"
    assert res.get("kind") == "scene_transition"
    gm2 = d2.get("gm_output") or {}
    assert gm2.get("activate_scene_id") == "bogus_gpt_scene"
    assert gm2.get("activate_scene_id") != res.get("target_scene_id")
    meta = res.get("metadata") or {}
    aid = str(meta.get("authoritative_lead_id") or "").strip()
    assert aid
    assert get_lead(d2.get("session") or {}, aid) is not None


def test_transcript_lirael_clue_then_mixed_travel_eastern_square_authoritative(tmp_path, monkeypatch):
    """Ask about Lirael, hear eastern square, then mixed farewell + declared travel; resolver beats GPT scene id."""
    _seed_frontier_gate_eastern_square_stale_milestone_lead(tmp_path, monkeypatch)

    gpt_calls: list[int] = []

    def _call_gpt(_messages):
        gpt_calls.append(len(gpt_calls))
        if gpt_calls[-1] == 0:
            return _gm_response(
                "The runner leans in: Lirael works the eastern square when she is not on the crier route."
            )
        return _gm_with_non_authoritative_scene("bogus_gpt_scene")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt)
        client = TestClient(app)
        r1 = client.post(
            "/api/chat",
            json={"text": "Tavern Runner, where can I find Lirael?"},
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1.get("ok") is True

        r2 = client.post(
            "/api/chat",
            json={
                "text": (
                    '"Thanks for the tip." I asked about Lirael earlier. '
                    "Galinor leaves for the eastern square."
                )
            },
        )

    assert r2.status_code == 200
    d2 = r2.json()
    assert d2.get("ok") is True
    assert d2.get("session", {}).get("active_scene_id") == "eastern_square", (
        f"active_scene_id: expected 'eastern_square', got {d2.get('session', {}).get('active_scene_id')!r}"
    )
    assert d2.get("scene", {}).get("scene", {}).get("id") == "eastern_square"
    res = d2.get("resolution") or {}
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "eastern_square", (
        f"resolver target_scene_id: expected 'eastern_square', got {res.get('target_scene_id')!r}"
    )
    assert res.get("kind") == "scene_transition"
    gm2 = d2.get("gm_output") or {}
    assert gm2.get("activate_scene_id") == "bogus_gpt_scene"
    assert gm2.get("activate_scene_id") != res.get("target_scene_id"), (
        "gm_output.activate_scene_id is advisory; authoritative transition follows resolver only"
    )
    assert (res.get("metadata") or {}).get("authoritative_lead_id") in (None, "")


def test_transcript_tavern_runner_patrol_wait_beat_then_follow_up_question(tmp_path, monkeypatch):
    """Patrol question → passive wait for distraction → must not loop social/interruption; next directed question works."""
    _seed_tavern_patrol_lead_old_milestone(tmp_path, monkeypatch)

    gpt_calls: list[int] = []

    def _call_gpt(_messages):
        gpt_calls.append(len(gpt_calls))
        if gpt_calls[-1] == 0:
            return _gm_response(
                "A drunk staggers between tables; the runner's eyes flick to the commotion, then back to you."
            )
        if gpt_calls[-1] == 1:
            return _gm_response(
                "The shout dies down; tankards settle. The runner exhales, attention returning to the room."
            )
        return _gm_response(
            "The runner murmurs, low: last reliable sign pointed toward the old milestone, past the east gate."
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt)
        client = TestClient(app)
        r1 = client.post(
            "/api/chat",
            json={"text": "Tavern Runner, what happened to the patrol?"},
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1.get("ok") is True
        res1 = d1.get("resolution") or {}
        assert res1.get("kind") in ("question", "social_probe")
        assert (res1.get("social") or {}).get("npc_id") == "tavern_runner"

        r2 = client.post(
            "/api/chat",
            json={"text": "Galinor waits for the commotion to pass."},
        )
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("ok") is True
        res2 = d2.get("resolution") or {}
        assert res2.get("kind") == "observe"
        assert (res2.get("metadata") or {}).get("passive_interruption_wait") is True
        assert res2.get("social") in (None, {})
        gm2 = d2.get("gm_output") or {}
        txt2 = str(gm2.get("player_facing_text") or "")
        _assert_not_repeated_interruption_beat(txt2)
        _assert_socially_grounded_progression(txt2, "attention returning", "shout dies down")
        ctx2 = (d2.get("session") or {}).get("interaction_context") or {}
        assert not str(ctx2.get("active_interaction_target_id") or "").strip()
        assert str(ctx2.get("interaction_mode") or "").strip().lower() == "activity"

        r3 = client.post(
            "/api/chat",
            json={
                "text": (
                    '"Runner," Galinor asks, "where were they last seen?"'
                )
            },
        )
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3.get("ok") is True
        res3 = d3.get("resolution") or {}
        assert res3.get("kind") in ("question", "social_probe")
        assert (res3.get("social") or {}).get("npc_id") == "tavern_runner"

    assert len(gpt_calls) >= 3


def test_transcript_runner_repeated_interruption_beat_forces_progression(tmp_path, monkeypatch):
    """Repeated interrupted patrol answers must advance instead of replaying the same beat."""
    _seed_tavern_patrol_lead_old_milestone(tmp_path, monkeypatch)

    gpt_calls: list[int] = []

    def _call_gpt(_messages):
        n = len(gpt_calls)
        gpt_calls.append(n)
        if n == 0:
            return _gm_response(
                "The runner starts to answer, then glances past you as shouting breaks out in the crowd."
            )
        if n == 1:
            return _gm_response(
                "The runner opens their mouth, then breaks off as a shout cuts across the square."
            )
        return _gm_response(
            "The runner begins to respond before noise from the crowd pulls their attention away."
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt)
        client = TestClient(app)

        r1 = client.post(
            "/api/chat",
            json={"text": "Tavern Runner, what happened to the patrol?"},
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1.get("ok") is True
        gm1 = d1.get("gm_output") or {}
        txt1 = str(gm1.get("player_facing_text") or "")
        low1 = txt1.lower()
        # C2: first beat may be raw upstream interruption prose, or validate/replace terminal social stock.
        assert (
            "shouting" in low1
            or "breaks out" in low1
            or "breaks off" in low1
            or "starts to answer" in low1
            or "glances past" in low1
            or ("tavern runner" in low1 and ("frown" in low1 or "that's all i've got" in low1))
        )
        res1 = d1.get("resolution") or {}
        assert res1.get("kind") in ("question", "social_probe")
        assert (res1.get("social") or {}).get("npc_id") == "tavern_runner"

        r2 = client.post(
            "/api/chat",
            json={"text": '"Runner," Galinor presses, "what were you about to say about the patrol?"'},
        )
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("ok") is True
        gm2 = d2.get("gm_output") or {}
        txt2 = str(gm2.get("player_facing_text") or "")
        low2 = txt2.lower()
        res2 = d2.get("resolution") or {}
        assert res2.get("kind") in ("question", "social_probe")
        assert (res2.get("social") or {}).get("npc_id") == "tavern_runner"
        _assert_not_repeated_interruption_beat(txt2)
        _assert_socially_grounded_progression(txt2)

        r3 = client.post(
            "/api/chat",
            json={"text": '"Runner," Galinor says, "ignore the noise and tell me about the patrol."'},
        )
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3.get("ok") is True
        gm3 = d3.get("gm_output") or {}
        txt3 = str(gm3.get("player_facing_text") or "")
        low3 = txt3.lower()
        res3 = d3.get("resolution") or {}
        assert res3.get("kind") in ("question", "social_probe")
        assert (res3.get("social") or {}).get("npc_id") == "tavern_runner"
        _assert_not_repeated_interruption_beat(txt3)
        _assert_socially_grounded_progression(txt3)

    assert len(gpt_calls) >= 3


def test_transcript_combined_patrol_wait_decline_old_milestone_no_false_transition(
    tmp_path, monkeypatch,
):
    """Patrol question → wait beat → re-ask (milestone surfaces) → explicit decline: stay put; GPT scene id cannot move you."""
    _seed_tavern_patrol_lead_old_milestone(tmp_path, monkeypatch)

    gpt_calls: list[int] = []

    def _call_gpt(_messages):
        n = len(gpt_calls)
        gpt_calls.append(n)
        if n == 0:
            return _gm_response(
                "A drunk staggers between tables; the runner's eyes flick to the commotion, then back to you."
            )
        if n == 1:
            return _gm_response(
                "The shout dies down; tankards settle. The runner exhales, attention returning to the room."
            )
        if n == 2:
            return _gm_response(
                "The runner murmurs, low: last reliable sign pointed toward the old milestone, past the east gate."
            )
        return _gm_with_non_authoritative_scene("old_milestone")

    decline = (
        '"Thanks anyway." Galinor decides against traveling to the old milestone for now '
        "and stays to finish his drink."
    )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt)
        client = TestClient(app)
        r1 = client.post(
            "/api/chat",
            json={"text": "Tavern Runner, what happened to the patrol?"},
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1.get("ok") is True

        r2 = client.post(
            "/api/chat",
            json={"text": "Galinor waits for the commotion to pass."},
        )
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("ok") is True
        res2 = d2.get("resolution") or {}
        assert res2.get("kind") == "observe", (
            f"wait beat: expected resolution.kind 'observe', got {res2.get('kind')!r}"
        )
        assert (res2.get("metadata") or {}).get("passive_interruption_wait") is True

        r3 = client.post(
            "/api/chat",
            json={"text": '"Runner," Galinor asks, "where were they last seen?"'},
        )
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3.get("ok") is True
        s3 = d3.get("session") or {}
        rt3 = get_scene_runtime(s3, "tavern")
        pending3 = rt3.get("pending_leads") or []
        assert any(
            str(p.get("leads_to_scene") or "").strip() == "old_milestone"
            for p in pending3
            if isinstance(p, dict)
        ), "after re-ask, runtime should surface the milestone lead (pending_leads)"

        r4 = client.post("/api/chat", json={"text": decline})
        assert r4.status_code == 200
        d4 = r4.json()

    assert d4.get("ok") is True
    s4 = d4.get("session") or {}
    assert s4.get("active_scene_id") == "tavern", (
        f"active_scene_id: expected 'tavern' after explicit decline, got {s4.get('active_scene_id')!r}"
    )
    assert d4.get("scene", {}).get("scene", {}).get("id") == "tavern"
    res4 = d4.get("resolution") or {}
    assert res4.get("resolved_transition") is not True, (
        "declining the milestone must not produce an authoritative scene transition"
    )
    assert res4.get("target_scene_id") != "old_milestone", (
        f"resolver target_scene_id must not fall back to old_milestone; got {res4.get('target_scene_id')!r}"
    )
    assert res4.get("kind") != "scene_transition", (
        f"normalized action kind must not be scene_transition; got {res4.get('kind')!r}"
    )
    gm4 = d4.get("gm_output") or {}
    assert gm4.get("activate_scene_id") == "old_milestone"
    assert gm4.get("activate_scene_id") != res4.get("target_scene_id"), (
        "gm_output.activate_scene_id is advisory; declined travel must not follow it"
    )


def test_transcript_passive_wait_then_followup_then_departure_stays_coherent(tmp_path, monkeypatch):
    """Wait → follow-up → declared travel: resolver (not GPT) sets scene; no return to passive-wait / social-follow-up glitch."""
    _seed_tavern_patrol_lead_old_milestone(tmp_path, monkeypatch)

    gpt_calls: list[int] = []

    def _call_gpt(_messages):
        n = len(gpt_calls)
        gpt_calls.append(n)
        if n == 0:
            return _gm_response(
                "A drunk staggers between tables; the runner's eyes flick to the commotion, then back to you."
            )
        if n == 1:
            return _gm_response(
                "The shout dies down; tankards settle. The runner exhales, attention returning to the room."
            )
        if n == 2:
            return _gm_response(
                "The runner murmurs, low: last reliable sign pointed toward the old milestone, past the east gate."
            )
        return _gm_with_non_authoritative_scene("bogus_gpt_scene")

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt)
        client = TestClient(app)
        r1 = client.post(
            "/api/chat",
            json={"text": "Tavern Runner, what happened to the patrol?"},
        )
        assert r1.status_code == 200

        r2 = client.post(
            "/api/chat",
            json={"text": "Galinor waits for the commotion to pass."},
        )
        assert r2.status_code == 200
        d2 = r2.json()
        res2 = d2.get("resolution") or {}
        assert res2.get("kind") == "observe"
        assert (res2.get("metadata") or {}).get("passive_interruption_wait") is True

        r3 = client.post(
            "/api/chat",
            json={
                "text": '"Runner," Galinor asks, "where were they last seen?"',
            },
        )
        assert r3.status_code == 200
        d3 = r3.json()
        res3 = d3.get("resolution") or {}
        assert res3.get("kind") in ("question", "social_probe")
        assert (res3.get("social") or {}).get("npc_id") == "tavern_runner"

        r4 = client.post(
            "/api/chat",
            json={
                "text": (
                    '"Thank you." Galinor leaves the runner for the old milestone.'
                )
            },
        )
        assert r4.status_code == 200
        d4 = r4.json()

    assert d4.get("ok") is True
    res4 = d4.get("resolution") or {}
    assert res4.get("kind") == "scene_transition", (
        f"departure turn: expected resolution.kind 'scene_transition', not passive-wait replay; got {res4.get('kind')!r}"
    )
    assert (res4.get("metadata") or {}).get("passive_interruption_wait") is not True
    assert res4.get("resolved_transition") is True
    assert res4.get("target_scene_id") == "old_milestone", (
        f"resolver target_scene_id: expected 'old_milestone', got {res4.get('target_scene_id')!r}"
    )
    s4 = d4.get("session") or {}
    assert s4.get("active_scene_id") == "old_milestone", (
        f"active_scene_id: expected 'old_milestone' after affirmed travel, got {s4.get('active_scene_id')!r}"
    )
    gm4 = d4.get("gm_output") or {}
    assert gm4.get("activate_scene_id") == "bogus_gpt_scene"
    assert gm4.get("activate_scene_id") != res4.get("target_scene_id"), (
        "authoritative scene follows resolver target_scene_id, not gm_output.activate_scene_id"
    )
    ctx4 = s4.get("interaction_context") or {}
    assert ctx4.get("interaction_mode") != "social" or not str(
        ctx4.get("active_interaction_target_id") or ""
    ).strip(), (
        "after travel, session should not read as still mid-runner social loop from the wait beat"
    )
