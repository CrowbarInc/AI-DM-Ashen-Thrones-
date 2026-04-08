"""BLOCK 14: contextual minimal repair improves wording without inventing state."""
from __future__ import annotations

import copy
import re
from typing import Any

import pytest

import game.gm as gm_module
from game.gm import (
    _gm_has_usable_player_facing_text,
    _is_placeholder_only_player_facing_text,
    ensure_minimal_nonsocial_resolution,
    ensure_minimal_social_resolution,
)
from game.social_exchange_emission import is_route_illegal_global_or_sanitizer_fallback_text
from game.storage import get_scene_runtime
from game.tone_escalation import validate_tone_escalation

pytestmark = [pytest.mark.unit, pytest.mark.regression]


def _norm_pft(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower().rstrip(".!?"))


def _assert_repair_line_legal(pft: str) -> None:
    assert isinstance(pft, str) and pft.strip()
    assert is_route_illegal_global_or_sanitizer_fallback_text(pft) is False
    assert _is_placeholder_only_player_facing_text(pft) is False
    assert _gm_has_usable_player_facing_text({"player_facing_text": pft})


def _social_authority_session(*, npc_id: str = "tavern_runner") -> dict[str, Any]:
    return {
        "active_scene_id": "tavern",
        "interaction_context": {
            "active_interaction_target_id": npc_id,
            "interaction_mode": "social",
        },
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


def _scene_envelope(*, scene_id: str = "tavern") -> dict[str, Any]:
    return {"scene": {"id": scene_id}}


def test_social_contextual_repair_question_aware_when_minimal_helper_fails(monkeypatch: Any) -> None:
    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", lambda *_a, **_k: "")
    session = _social_authority_session()
    rt = get_scene_runtime(session, "tavern")
    rt["last_player_action_text"] = "Where did the patrol go last night?"
    resolution = _minimal_social_resolution()
    gm_before: dict[str, Any] = {"player_facing_text": ""}
    out = ensure_minimal_social_resolution(
        gm=copy.deepcopy(gm_before),
        session=session,
        reason="block14_question",
        world={},
        resolution=resolution,
        scene_envelope=_scene_envelope(),
    )
    pft = str(out.get("player_facing_text") or "")
    _assert_repair_line_legal(pft)
    assert "they answer cautiously" not in pft.lower()
    assert "social_contextual_repair:question_ack" in str(out.get("debug_notes") or "")
    hard = _norm_pft(gm_module._SOCIAL_EMPTY_REPAIR_HARD_LINE)
    assert _norm_pft(pft) != hard
    new_keys = set(out) - set(gm_before)
    for k in new_keys:
        assert "clue" not in k.lower()
        assert "discoverable" not in k.lower()


def test_social_contextual_repair_scene_anchor_without_question_signal(monkeypatch: Any) -> None:
    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", lambda *_a, **_k: "")
    session = _social_authority_session()
    rt = get_scene_runtime(session, "tavern")
    rt["last_player_action_text"] = "I hold eye contact and wait."
    resolution = _minimal_social_resolution()
    out = ensure_minimal_social_resolution(
        gm={"player_facing_text": ""},
        session=session,
        reason="block14_scene_social",
        world={},
        resolution=resolution,
        scene_envelope=_scene_envelope(),
    )
    pft = str(out.get("player_facing_text") or "").lower()
    assert "social_contextual_repair:scene_anchor" in str(out.get("debug_notes") or "")
    _assert_repair_line_legal(str(out.get("player_facing_text") or ""))
    assert "tavern" in pft or "locals" in pft or "lantern" in pft or "frames what you hear" in pft


def test_nonsocial_minimal_repair_by_context() -> None:
    """Anchored tavern repair vs empty-session hard line (merged former two cases)."""
    out_tavern = ensure_minimal_nonsocial_resolution(
        gm={"player_facing_text": "", "tags": []},
        session={"active_scene_id": "tavern"},
    )
    pft_t = str(out_tavern.get("player_facing_text") or "")
    _assert_repair_line_legal(pft_t)
    hard = _norm_pft(gm_module._NONSOCIAL_EMPTY_REPAIR_HARD_LINE)
    assert _norm_pft(pft_t) != hard
    low_t = pft_t.lower()
    assert "something shifts" not in low_t
    assert "tavern" in low_t or "locals" in low_t or "notice board" in low_t or "lantern" in low_t

    out_empty = ensure_minimal_nonsocial_resolution(
        gm={"player_facing_text": ""},
        session={},
    )
    pft_e = str(out_empty.get("player_facing_text") or "")
    _assert_repair_line_legal(pft_e)
    assert _norm_pft(pft_e) == hard


def test_contextual_minimal_repair_does_not_add_clue_or_resolution_payload(monkeypatch: Any) -> None:
    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", lambda *_a, **_k: "")
    session = _social_authority_session()
    rt = get_scene_runtime(session, "tavern")
    rt["last_player_action_text"] = "Who saw them leave?"
    gm_before: dict[str, Any] = {
        "player_facing_text": "",
        "tags": ["x"],
    }
    out_s = ensure_minimal_social_resolution(
        gm=copy.deepcopy(gm_before),
        session=session,
        reason="block14_invention",
        world={},
        resolution=_minimal_social_resolution(),
        scene_envelope=_scene_envelope(),
    )
    assert out_s.get("clues") is None and out_s.get("scene_update") is None
    assert out_s.get("discoverable_clues") is None
    allowed_social = {
        "player_facing_text",
        "final_route",
        "fallback_kind",
        "accepted_via",
        "targeted_retry_terminal",
        "retry_exhausted",
        "tags",
        "debug_notes",
        "_final_emission_meta",
        "preserved_social_continuity_fields",
    }
    assert set(out_s) - set(gm_before) <= allowed_social

    monkeypatch.setattr(
        "game.gm._nonsocial_minimal_resolution_line",
        lambda **_k: gm_module._NONSOCIAL_EMPTY_REPAIR_HARD_LINE,
    )
    out_n = ensure_minimal_nonsocial_resolution(
        gm={"player_facing_text": ""},
        session={"active_scene_id": "tavern"},
    )
    assert out_n.get("clues") is None and out_n.get("scene_update") is None
    allowed_ns = {
        "player_facing_text",
        "final_route",
        "fallback_kind",
        "accepted_via",
        "targeted_retry_terminal",
        "retry_exhausted",
        "tags",
        "debug_notes",
    }
    assert set(out_n) <= allowed_ns


def test_contextual_repair_lines_pass_legality_checks(monkeypatch: Any) -> None:
    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", lambda *_a, **_k: "")
    session = _social_authority_session()
    rt = get_scene_runtime(session, "tavern")
    rt["last_player_action_text"] = "What did you hear?"
    out_s = ensure_minimal_social_resolution(
        gm={"player_facing_text": ""},
        session=session,
        reason="block14_legal_social",
        world={},
        resolution=_minimal_social_resolution(),
        scene_envelope=_scene_envelope(),
    )
    _assert_repair_line_legal(str(out_s.get("player_facing_text") or ""))

    monkeypatch.setattr(
        "game.gm._nonsocial_minimal_resolution_line",
        lambda **_k: gm_module._NONSOCIAL_EMPTY_REPAIR_HARD_LINE,
    )
    out_n = ensure_minimal_nonsocial_resolution(
        gm={"player_facing_text": ""},
        session={"active_scene_id": "tavern"},
    )
    pft_n = str(out_n.get("player_facing_text") or "")
    _assert_repair_line_legal(pft_n)
    assert "nonsocial_contextual_repair:scene_anchor" in str(out_n.get("debug_notes") or "")


def test_minimal_repair_hard_lines_respect_guarded_tone_contract() -> None:
    """Terminal repair lines must not introduce disallowed threat/violence under a guarded ceiling."""
    ctr = {
        "enabled": True,
        "base_tone": "neutral",
        "max_allowed_tone": "guarded",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
    }
    for line in (
        gm_module._SOCIAL_EMPTY_REPAIR_HARD_LINE,
        gm_module._NONSOCIAL_EMPTY_REPAIR_HARD_LINE,
    ):
        v = validate_tone_escalation(line, contract=ctr)
        assert v.get("ok") is True, (line, v)
