"""Tests for :mod:`game.turn_packet` and retry/gate integration."""

from __future__ import annotations

from typing import Any, Dict

# Import :mod:`game.gm` before :mod:`game.gm_retry` so ``gm`` finishes its ``gm_retry`` tail import
# (see ``game/gm.py``); avoids partial-init cycles when tests load ``gm_retry`` alone.
from game.gm import build_retry_prompt_for_failure as _gm_retry_import_order_anchor  # noqa: F401

import game.gm_retry as gm_retry
from game.turn_packet import (
    TURN_PACKET_METADATA_KEY,
    attach_turn_packet,
    build_turn_packet,
    ensure_turn_packet,
    get_turn_packet,
    resolve_turn_packet_for_gate,
    resolve_turn_packet_contract,
    resolve_turn_packet_field,
)


def test_build_turn_packet_minimal_stable() -> None:
    p = build_turn_packet()
    assert p["version"] == 1
    assert p["turn_id"] is None
    assert p["scene_id"] is None
    assert p["contracts"]["answer_completeness"] is None
    assert isinstance(p["debug"]["missing_contracts"], list)
    assert isinstance(p["response_policy"], dict)
    p2 = build_turn_packet()
    assert set(p.keys()) == set(p2.keys())


def test_attach_turn_packet_non_destructive() -> None:
    gm: Dict[str, Any] = {"metadata": {"other": 1}, "player_facing_text": "x"}
    packet = build_turn_packet(player_text="hello")
    attach_turn_packet(gm, packet)
    md = gm["metadata"]
    assert md["other"] == 1
    assert isinstance(md[TURN_PACKET_METADATA_KEY], dict)
    assert md[TURN_PACKET_METADATA_KEY]["player_text"] == "hello"


def test_get_turn_packet_direct_and_metadata() -> None:
    pkt = build_turn_packet(player_text="direct")
    gm: Dict[str, Any] = {TURN_PACKET_METADATA_KEY: pkt}
    assert get_turn_packet(gm) is pkt
    gm2: Dict[str, Any] = {"metadata": {TURN_PACKET_METADATA_KEY: pkt}}
    assert get_turn_packet(gm2) is pkt


def test_get_turn_packet_prompt_context_nested() -> None:
    pkt = build_turn_packet(player_text="nested")
    gm: Dict[str, Any] = {"prompt_context": {"turn_packet": pkt}}
    assert get_turn_packet(gm) is pkt


def test_resolve_turn_packet_contract() -> None:
    rp: Dict[str, Any] = {
        "answer_completeness": {"enabled": True},
        "tone_escalation": {"debug_inputs": {}, "max_allowed_tone": "x"},
    }
    pkt = build_turn_packet(response_policy=rp)
    ac = resolve_turn_packet_contract(pkt, "answer_completeness")
    assert isinstance(ac, dict) and ac.get("enabled") is True
    assert resolve_turn_packet_contract(pkt, "missing_name_xyz") is None


def test_resolve_turn_packet_field() -> None:
    pkt = build_turn_packet(scene_id="s1")
    assert resolve_turn_packet_field(pkt, "scene_id") == "s1"
    assert resolve_turn_packet_field(pkt, "route.scene_id") is None
    assert resolve_turn_packet_field(pkt, "route.interaction_mode") is None


def test_ensure_turn_packet_builds_once() -> None:
    gm: Dict[str, Any] = {}
    a = ensure_turn_packet(gm, player_text="p")
    b = ensure_turn_packet(gm, player_text="ignored")
    assert a is b
    assert get_turn_packet(gm) is a


def test_resolve_turn_packet_for_gate_prefers_cache() -> None:
    pkt = build_turn_packet(scene_id="cached")
    gm: Dict[str, Any] = {
        "metadata": {TURN_PACKET_METADATA_KEY: build_turn_packet(scene_id="meta")},
        "_gate_turn_packet_cache": pkt,
    }
    assert resolve_turn_packet_for_gate(gm) is pkt


def _usable_tone() -> Dict[str, Any]:
    return {
        "enabled": True,
        "debug_inputs": {},
        "max_allowed_tone": "neutral",
        "allow_explicit_threat": True,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
    }


def _full_anti_railroading() -> Dict[str, Any]:
    return {
        "enabled": True,
        "forbid_player_decision_override": True,
    }


def _full_context_separation() -> Dict[str, Any]:
    return {
        "enabled": True,
        "forbid_topic_hijack": True,
        "max_pressure_sentences_without_player_prompt": 1,
        "debug_inputs": {},
    }


def test_gm_retry_tone_prefers_packet_over_policy() -> None:
    weak_policy = {"tone_escalation": {"enabled": True}}
    strong_packet = build_turn_packet(
        response_policy={
            "tone_escalation": _usable_tone(),
        },
    )
    gm: Dict[str, Any] = {
        "metadata": {TURN_PACKET_METADATA_KEY: strong_packet},
        "response_policy": weak_policy,
    }
    te = gm_retry._resolve_retry_tone_escalation_contract(gm, weak_policy)
    assert te is not None
    assert te.get("allow_explicit_threat") is True


def test_gm_retry_anti_railroading_prefers_packet() -> None:
    policy = {"anti_railroading": {"enabled": False, "forbid_player_decision_override": True}}
    pkt = build_turn_packet(
        response_policy={"anti_railroading": _full_anti_railroading()},
    )
    gm: Dict[str, Any] = {"metadata": {TURN_PACKET_METADATA_KEY: pkt}, "response_policy": policy}
    arc = gm_retry._resolve_anti_railroading_contract_for_retry(policy, gm)
    assert arc is not None
    assert arc.get("enabled") is True


def test_gm_retry_context_separation_prefers_packet() -> None:
    policy: Dict[str, Any] = {"context_separation": _full_context_separation()}
    pkt = build_turn_packet(response_policy=policy)
    gm: Dict[str, Any] = {"metadata": {TURN_PACKET_METADATA_KEY: pkt}}
    ctr, src = gm_retry._resolve_context_separation_contract_for_retry(gm, None)
    assert ctr is not None
    assert src == "turn_packet.contracts.context_separation"


def test_gm_retry_fallback_without_packet() -> None:
    te = _usable_tone()
    gm: Dict[str, Any] = {"response_policy": {"tone_escalation": te}}
    got = gm_retry._resolve_retry_tone_escalation_contract(gm, gm["response_policy"])
    assert got is te
