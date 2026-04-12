"""Playability smoke: full ``/api/chat`` stack; scoring only via ``evaluate_playability``."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.playability_eval import evaluate_playability
from tests.test_turn_pipeline_shared import _gm_response, _seed_runner_dialogue_context

pytestmark = pytest.mark.integration


def _player_facing(resp) -> str:
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _prompt_blob(messages: list | None) -> str:
    parts: list[str] = []
    for m in messages or []:
        if isinstance(m, dict):
            parts.append(str(m.get("content") or ""))
    return "\n".join(parts).lower()


def _install_social_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.api.parse_intent", lambda *_a, **_k: None)


def _patch_api_retry_and_uncertainty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Narrow test-only shims so deterministic ``call_gpt`` fixtures survive the live API stack."""

    def _empty_failures(**_: object) -> list:
        return []

    monkeypatch.setattr("game.api.detect_retry_failures", _empty_failures)
    monkeypatch.setattr("game.gm.resolve_known_fact_before_uncertainty", lambda *_a, **_k: None)
    monkeypatch.setattr("game.gm.enforce_question_resolution_rule", lambda gm, **_k: gm)


_GM_PATROL_NOTICE_FIRST = (
    "Tavern Runner says the notices mention curfew and a patrol sweep; "
    "rumors cluster around the east gate, but hearsay is messy tonight."
)

_GM_PATROL_WHERE_CLARIFIED = (
    "Tavern Runner leans in. There is a clear anchor: exactly along the east gate yard is where witnesses last placed "
    "the squad before the curfew bells; if timing is unclear, ask the sergeant; he was on the wall shift."
)


def _call_gpt_patrol_notice_flow(msgs: list | None):
    blob = _prompt_blob(msgs)
    if "where exactly were they last seen" in blob:
        return _gm_response(_GM_PATROL_WHERE_CLARIFIED)
    return _gm_response(_GM_PATROL_NOTICE_FIRST)


def test_playability_smoke_direct_answer_pressure(tmp_path, monkeypatch):
    """Specific question then a clarity follow-up; direct-answer axis must clear."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    prior_player = "Runner, what do you hear about the missing patrol?"
    player = "I press in plain terms: where exactly were they last seen?"

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt_patrol_notice_flow)
        _install_social_routing(m)
        _patch_api_retry_and_uncertainty(m)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": prior_player})
        prior_gm = _player_facing(first)
        second = client.post("/api/chat", json={"text": player})

    t2 = _player_facing(second)
    out = evaluate_playability(
        {
            "player_prompt": player,
            "gm_output": {"player_facing_text": t2},
            "prior_player_prompt": prior_player,
            "prior_gm_text": prior_gm,
        }
    )
    da = out["axes"]["direct_answer"]
    assert da["passed"] is True
    assert da["score"] >= 15
    assert out["overall"]["passed"] is True
    assert "east gate yard" in t2.lower()


def test_playability_smoke_narrowing_player_intent(tmp_path, monkeypatch):
    """Narrowing follow-up (``where exactly``) must stay on-thread per evaluator."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    prior_player = "Runner, what do you hear about the missing patrol?"
    player = "I press in plain terms: where exactly were they last seen?"

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt_patrol_notice_flow)
        _install_social_routing(m)
        _patch_api_retry_and_uncertainty(m)
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": prior_player})
        prior_gm = _player_facing(first)
        second = client.post("/api/chat", json={"text": player})

    t2 = _player_facing(second)
    out = evaluate_playability(
        {
            "player_prompt": player,
            "gm_output": {"player_facing_text": t2},
            "prior_player_prompt": prior_player,
            "prior_gm_text": prior_gm,
        }
    )
    intent = out["axes"]["player_intent"]
    assert intent["passed"] is True
    assert not any("thread drift" in str(r).lower() for r in intent.get("reasons", []))
    assert out["overall"]["passed"] is True


def test_playability_smoke_escalation_under_pressure(tmp_path, monkeypatch):
    """Several pressured beats; logical escalation must pass with evaluator change signals."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    p1 = "Runner, who attacked the patrol?"
    p2 = "Do not dodge me - who paid for the blades in the alley?"
    p3 = "Who ordered the strike on the patrol - I need a name now."

    def call_gpt(msgs):
        blob = _prompt_blob(msgs)
        if "who ordered the strike on the patrol" in blob:
            return _gm_response(
                "Tavern Runner taps your sleeve once. There is a separate paper trail: the magistrate seal office "
                "copied names onto a river-house ledger before the night clerk ever touched coin at the west market."
            )
        if "who paid for the blades" in blob:
            return _gm_response(
                "Tavern Runner flinches. There is a chain you can chase: gold moved through the dock factor's hands "
                "first, and the alley crew only took the contract after that."
            )
        return _gm_response(
            "Tavern Runner says there is noise but a direction: the square talk is all rumor, crowd noise, "
            "no clean witness, but the east lane crew was loud about blades before curfew."
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", call_gpt)
        _install_social_routing(m)
        _patch_api_retry_and_uncertainty(m)
        # Strict-social emission otherwise collapses pressured follow-ups to the same repair skeleton,
        # which makes ``logical_escalation`` (correctly) fail on stale repetition.
        m.setattr(
            "game.api_turn_support.apply_final_emission_gate",
            lambda gm, **_kw: dict(gm) if isinstance(gm, dict) else gm,
        )
        client = TestClient(app)
        r1 = client.post("/api/chat", json={"text": p1})
        g1 = _player_facing(r1)
        r2 = client.post("/api/chat", json={"text": p2})
        g2 = _player_facing(r2)
        r3 = client.post("/api/chat", json={"text": p3})
        g3 = _player_facing(r3)

    out = evaluate_playability(
        {
            "player_prompt": p3,
            "gm_output": {"player_facing_text": g3},
            "prior_player_prompt": p2,
            "prior_gm_text": g2,
        }
    )
    esc = out["axes"]["logical_escalation"]
    assert esc["passed"] is True
    assert esc["score"] >= 15
    assert esc["signals"].get("prior_gm_present") is True
    assert int(esc["signals"].get("net_new_terms") or 0) >= 4
    assert not any("stale repetition" in str(r).lower() for r in esc.get("reasons", []))
    assert out["overall"]["passed"] is True


def test_playability_smoke_immersion_guard_adversarial_upstream(tmp_path, monkeypatch):
    """Upstream tries to leak scaffolding; immersion gate or overall failure must match evaluator."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    player = "Runner, what does the posted notice say about curfew?"

    def call_gpt(_msgs):
        return _gm_response(
            "The validator flagged established state drift; the router wants a cleaner scene anchor "
            "before the system prompt can settle the east gate rumor."
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", call_gpt)
        _install_social_routing(m)
        _patch_api_retry_and_uncertainty(m)
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": player})

    out = evaluate_playability(
        {
            "player_prompt": player,
            "gm_output": {"player_facing_text": _player_facing(resp)},
        }
    )
    imm = out["axes"]["immersion"]
    overall = out["overall"]
    assert imm["passed"] or (overall["passed"] is False and imm["score"] < 10)
