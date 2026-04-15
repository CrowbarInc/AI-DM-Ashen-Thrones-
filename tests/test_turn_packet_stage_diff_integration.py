"""Downstream turn-packet + emitted observability integration coverage for gate/retry consumers."""

from __future__ import annotations

from typing import Any, Dict

import pytest

# Import :mod:`game.gm` before :mod:`game.gm_retry` (partial-init ordering).
from game.gm import build_retry_prompt_for_failure as _gm_retry_import_order_anchor  # noqa: F401

import game.final_emission_gate as feg
from game.fallback_provenance_debug import METADATA_KEY as FB_PROV_KEY, attach_upstream_fast_fallback_provenance
from game.final_emission_gate import apply_final_emission_gate
from game.gm_retry import apply_deterministic_retry_fallback, force_terminal_retry_fallback
from game.turn_packet import TURN_PACKET_METADATA_KEY, attach_turn_packet, build_turn_packet

pytestmark = pytest.mark.unit
STAGE_DIFF_METADATA_KEY = "stage_diff_telemetry"


def _usable_tone() -> Dict[str, Any]:
    return {
        "enabled": True,
        "debug_inputs": {},
        "max_allowed_tone": "neutral",
        "allow_explicit_threat": True,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
    }


def test_gate_exit_records_observability_before_cache_pop(monkeypatch: pytest.MonkeyPatch) -> None:
    """A: downstream gate observability runs before the packet cache is cleared."""
    exit_cache_visible: list[bool] = []
    orig = feg.record_stage_snapshot

    def _wrap(out: Dict[str, Any], stage: str, **kwargs: Any) -> None:
        if stage == "final_emission_gate_exit":
            exit_cache_visible.append("_gate_turn_packet_cache" in out)
        return orig(out, stage, **kwargs)

    monkeypatch.setattr(feg, "record_stage_snapshot", _wrap)

    pkt = build_turn_packet(
        scene_id="scene_investigate",
        resolution={"kind": "observe"},
        interaction_continuity={"active_interaction_target_id": "npc_route_probe"},
        narration_obligations={"active_npc_reply_kind": "observe"},
        response_policy={"tone_escalation": _usable_tone()},
    )
    gm: Dict[str, Any] = {
        "player_facing_text": "Rain drums on the slate roof.",
        "tags": [],
        "metadata": {},
    }
    attach_turn_packet(gm, pkt)

    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="scene_investigate",
        world={},
    )

    assert exit_cache_visible == [True]
    assert "_gate_turn_packet_cache" not in out

    tel = (out.get("metadata") or {}).get(STAGE_DIFF_METADATA_KEY) or {}
    snaps = tel.get("snapshots") or []
    stages = [s.get("stage") for s in snaps]
    assert "final_emission_gate_entry" in stages
    assert "final_emission_gate_exit" in stages


def test_gate_and_retry_consumers_prefer_packet_when_mirror_conflicts() -> None:
    """B: downstream gate/retry consumers use the canonical packet when mirrors disagree."""
    weak_mirror_te = {"enabled": True}
    pkt = build_turn_packet(response_policy={"tone_escalation": _usable_tone()})
    gm_gate: Dict[str, Any] = {
        "metadata": {TURN_PACKET_METADATA_KEY: pkt},
        "response_policy": {"tone_escalation": weak_mirror_te},
    }
    te_gate = feg._resolve_tone_escalation_contract(gm_gate)
    assert te_gate is not None
    assert te_gate.get("allow_explicit_threat") is True

    gm_retry: Dict[str, Any] = {
        "metadata": {TURN_PACKET_METADATA_KEY: pkt},
        "response_policy": {"tone_escalation": weak_mirror_te},
    }
    import game.gm_retry as gm_retry_mod

    te_retry = gm_retry_mod._resolve_retry_tone_escalation_contract(gm_retry, weak_mirror_te)
    assert te_retry is not None
    assert te_retry.get("allow_explicit_threat") is True

    gm_no_packet: Dict[str, Any] = {"response_policy": {"tone_escalation": _usable_tone()}}
    assert feg._resolve_tone_escalation_contract(gm_no_packet) is not None
    assert gm_retry_mod._resolve_retry_tone_escalation_contract(gm_no_packet, gm_no_packet["response_policy"]) is not None


def test_gate_output_keeps_provenance_packet_and_observability_metadata_together() -> None:
    """C: downstream gate output preserves provenance, packet, telemetry, and emission metadata."""
    text = "Rain drums on the slate roof consistently for the test."
    gm: Dict[str, Any] = {"player_facing_text": text, "tags": [], "metadata": {}}
    attach_upstream_fast_fallback_provenance(gm)
    pkt = build_turn_packet(player_text="listen", scene_id="scene_investigate", resolution={"kind": "observe"})
    attach_turn_packet(gm, pkt)
    gm.setdefault("metadata", {})["preexisting_emission_debug_note"] = "keep-me"

    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="scene_investigate",
        world={},
    )
    md = out.get("metadata") or {}
    prov = md.get(FB_PROV_KEY)
    assert isinstance(prov, dict)
    assert prov.get("source") == "fallback"
    assert isinstance(md.get(TURN_PACKET_METADATA_KEY), dict)
    assert isinstance(md.get(STAGE_DIFF_METADATA_KEY), dict)
    assert md.get("preexisting_emission_debug_note") == "keep-me"
    fem = out.get("_final_emission_meta") or {}
    assert isinstance(fem, dict) and "final_route" in fem


def test_retry_paths_emit_expected_transition_records() -> None:
    """D: downstream retry paths emit the expected transition records for telemetry consumers."""
    gm: Dict[str, Any] = {"player_facing_text": "stub", "tags": [], "metadata": {}}
    failure: Dict[str, Any] = {
        "failure_class": "answer",
        "priority": 1,
        "reasons": [],
        "known_fact_context": {
            "answer": "The sign reads north.",
            "source": "test",
            "subject": "sign",
            "position": "here",
        },
    }
    scene_envelope: Dict[str, Any] = {"scene": {"id": "s1"}}
    session: Dict[str, Any] = {"player_input": "What does the sign say?"}
    world: Dict[str, Any] = {}
    resolution: Dict[str, Any] = {
        "kind": "question",
        "social": {"open_social_solicitation": True, "npc_id": "npc_a", "reply_kind": "answer"},
    }
    det = apply_deterministic_retry_fallback(
        gm,
        failure=failure,
        player_text="What does the sign say?",
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
        segmented_turn=None,
    )
    tel_d = (det.get("metadata") or {}).get(STAGE_DIFF_METADATA_KEY) or {}
    trans_d = tel_d.get("transitions") or []
    assert trans_d
    last_d = trans_d[-1]
    assert last_d.get("from") == "retry_pre_deterministic_fallback"
    assert last_d.get("to") == "retry_deterministic_fallback_applied"
    assert isinstance(last_d.get("diff"), dict)

    base: Dict[str, Any] = {"player_facing_text": "", "tags": [], "metadata": {}}
    term = force_terminal_retry_fallback(
        session={
            "player_input": "Where is the door?",
            "social_authority": True,
            "active_scene_id": "missing_scene_xyz",
        },
        original_text="",
        failure={"failure_class": "unresolved_question", "reasons": ["q"]},
        retry_failures=[],
        player_text="Where is the door?",
        scene_envelope=scene_envelope,
        world={"places": {}},
        resolution={"kind": "question", "social": {"npc_id": "npc_x", "reply_kind": "answer"}},
        base_gm=base,
        segmented_turn=None,
    )
    tel_t = (term.get("metadata") or {}).get(STAGE_DIFF_METADATA_KEY) or {}
    trans_t = tel_t.get("transitions") or []
    assert trans_t
    diff_t = trans_t[-1].get("diff") or {}
    assert diff_t.get("terminal_retry_activated") is True


def test_gate_paths_remain_resilient_with_missing_or_partial_packet() -> None:
    """E: downstream gate consumers still run when the packet is missing or only partially populated."""
    out = apply_final_emission_gate(
        {"player_facing_text": "Mist curls through the pines.", "tags": [], "metadata": {}},
        resolution={"kind": "observe", "prompt": "I watch the mist."},
        session={},
        scene_id="scene_investigate",
        world={},
    )
    assert "_gate_turn_packet_cache" not in out
    assert isinstance((out.get("metadata") or {}).get(STAGE_DIFF_METADATA_KEY), dict)

    partial = build_turn_packet(scene_id="partial_scene")
    partial.pop("resolution_kind", None)
    partial["route"] = {"active_target_id": None}
    gm2: Dict[str, Any] = {
        "player_facing_text": "A short line.",
        "tags": [],
        "metadata": {TURN_PACKET_METADATA_KEY: partial},
    }
    out2 = apply_final_emission_gate(
        gm2,
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="partial_scene",
        world={},
    )
    assert isinstance(out2.get("player_facing_text"), str)
    assert isinstance((out2.get("metadata") or {}).get(STAGE_DIFF_METADATA_KEY), dict)
