"""Regression: empty strict-social terminal output is repaired; continuity and API sweep stay live."""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.gm import (
    _gm_has_usable_player_facing_text,
    _is_placeholder_only_player_facing_text,
    ensure_minimal_nonsocial_resolution,
    ensure_minimal_social_resolution,
    force_terminal_retry_fallback,
)
from tests.test_turn_pipeline_shared import _gm_response, _seed_runner_dialogue_context

pytestmark = [pytest.mark.integration, pytest.mark.regression]


def _social_authority_session(*, npc_id: str = "tavern_runner") -> dict[str, Any]:
    return {
        "interaction_context": {
            "active_interaction_target_id": npc_id,
            "interaction_mode": "social",
        }
    }


def _minimal_social_resolution(*, npc_id: str = "tavern_runner") -> dict[str, Any]:
    return {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": npc_id,
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
    }


def _scene_envelope(*, scene_id: str = "scene_investigate") -> dict[str, Any]:
    return {"scene": {"id": scene_id}}


def test_force_terminal_retry_fallback_repairs_empty_social_candidate(monkeypatch: Any) -> None:
    """apply_social returns {}; first minimal call empty -> ensure_minimal repairs with second minimal line."""
    monkeypatch.setattr("game.gm.apply_social_exchange_retry_fallback_gm", lambda *a, **k: {})
    calls = {"n": 0}

    def _minimal(res: Any) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            return ""
        return 'Renna says, "Hard to say."'

    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", _minimal)

    session = _social_authority_session(npc_id="tavern_runner")
    resolution = _minimal_social_resolution()
    out = force_terminal_retry_fallback(
        session=session,
        original_text="",
        failure={"failure_class": "scene_stall", "reasons": ["stall"]},
        player_text="What did you hear?",
        scene_envelope=_scene_envelope(),
        world={},
        resolution=resolution,
        base_gm={"player_facing_text": "", "tags": []},
    )

    assert _gm_has_usable_player_facing_text(out)
    pft_fb = str(out.get("player_facing_text") or "")
    assert "renna" in pft_fb.lower()
    assert not _is_placeholder_only_player_facing_text(pft_fb)
    assert out.get("targeted_retry_terminal") is True
    assert out.get("fallback_kind") == "social_empty_resolution_repair" or out.get(
        "accepted_via"
    ) == "social_resolution_repair"


def test_force_terminal_retry_fallback_preserves_final_emission_meta_continuity(monkeypatch: Any) -> None:
    monkeypatch.setattr("game.gm.apply_social_exchange_retry_fallback_gm", lambda *a, **k: {})
    calls = {"n": 0}

    def _minimal(_res: Any) -> str:
        calls["n"] += 1
        return "" if calls["n"] == 1 else "They shrug."

    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", _minimal)

    session = _social_authority_session(npc_id="continuity_npc")
    resolution = _minimal_social_resolution(npc_id="continuity_npc")
    base_gm: dict[str, Any] = {
        "player_facing_text": "",
        "tags": [],
        "_final_emission_meta": {
            "active_interlocutor_id": "continuity_npc",
            "npc_id": "continuity_npc",
            "reply_kind": "answer",
        },
    }
    out = force_terminal_retry_fallback(
        session=session,
        original_text="",
        failure={"failure_class": "validator_voice", "reasons": ["validator_voice"]},
        player_text="Tell me the truth.",
        scene_envelope=_scene_envelope(),
        world={},
        resolution=resolution,
        base_gm=base_gm,
    )
    meta = out.get("_final_emission_meta")
    assert isinstance(meta, dict)
    assert meta.get("active_interlocutor_id") == "continuity_npc"
    assert meta.get("npc_id") == "continuity_npc"


def test_ensure_minimal_nonsocial_resolution_fills_empty_text() -> None:
    out = ensure_minimal_nonsocial_resolution(
        gm={"player_facing_text": "", "tags": []},
        session={"active_scene_id": ""},
    )
    assert _gm_has_usable_player_facing_text(out)
    assert out.get("fallback_kind") == "nonsocial_empty_resolution_repair"
    assert out.get("accepted_via") == "nonsocial_resolution_repair"
    assert out.get("targeted_retry_terminal") is True
    assert out.get("retry_exhausted") is True
    assert out.get("final_route") == "nonsocial_fallback_minimal"


def test_nonsocial_contextual_repair_pressure_forward_without_scene_detail() -> None:
    out = ensure_minimal_nonsocial_resolution(
        gm={"player_facing_text": ""},
        session={
            "active_scene_id": "",
            "player_input": "I search the rubble for tracks.",
        },
    )
    assert _gm_has_usable_player_facing_text(out)
    assert "nonsocial_contextual_repair:pressure_forward" in str(out.get("debug_notes") or "")


def test_ensure_minimal_social_resolution_survives_total_minimal_helper_failure(monkeypatch: Any) -> None:
    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", lambda *_a, **_k: "")

    session = _social_authority_session()
    resolution = _minimal_social_resolution()
    out = ensure_minimal_social_resolution(
        gm={"player_facing_text": ""},
        session=session,
        reason="test_total_helper_failure",
        world={},
        resolution=resolution,
        scene_envelope=_scene_envelope(),
    )
    assert _gm_has_usable_player_facing_text(out)
    assert "They answer cautiously" in str(out.get("player_facing_text") or "")
    assert out.get("fallback_kind") == "social_empty_resolution_repair"
    assert out.get("accepted_via") == "social_resolution_repair"
    assert out.get("targeted_retry_terminal") is True
    assert out.get("retry_exhausted") is True


def test_api_repairs_empty_social_after_force_terminal_retry_fallback(monkeypatch: Any, tmp_path: Any) -> None:
    """If the escape hatch returns unusable strict-social gm, api post-hook must repair before return."""
    _seed_runner_dialogue_context(tmp_path, monkeypatch)
    captured: list[int] = []

    def _call_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        captured.append(1)
        return _gm_response(
            "I can't answer that. Based on what's established, we can determine very little here."
        )

    def _broken_force_terminal(**_kwargs: Any) -> dict[str, Any]:
        return {
            "player_facing_text": "",
            "tags": [],
            "final_route": "forced_retry_fallback",
            "fallback_kind": "retry_escape_hatch",
            "accepted_via": "forced_fallback",
        }

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _call_gpt)
        m.setattr("game.api.force_terminal_retry_fallback", _broken_force_terminal)
        m.setattr("game.api.MAX_TARGETED_RETRY_ATTEMPTS", 0)
        m.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
        m.setattr("game.api.parse_intent", lambda *_a, **_k: None)
        client = TestClient(app)
        resp = client.post(
            "/api/chat",
            json={"text": "Runner, where were they seen last—east lanes or the river road?"},
        )

    assert resp.status_code == 200
    assert len(captured) == 1
    gm_out = (resp.json() or {}).get("gm_output") or {}
    assert _gm_has_usable_player_facing_text(gm_out)
    pft_api = str(gm_out.get("player_facing_text") or "")
    assert pft_api.strip()
    assert not _is_placeholder_only_player_facing_text(pft_api)
