"""Practical primary direct-owner tests for stage-diff telemetry observability semantics.

Direct `game.stage_diff_telemetry` helper/accessor behavior belongs here.
Packet/gate/retry and narrative-authenticity suites may consume emitted telemetry,
but they should not re-own snapshot/diff packaging semantics.
"""

from __future__ import annotations

from typing import Any, Dict

# Import :mod:`game.gm` before :mod:`game.gm_retry` to avoid partial-init cycles (see test_turn_packet_accessors).
from game.gm import build_retry_prompt_for_failure as _gm_retry_import_order_anchor  # noqa: F401

from game import stage_diff_telemetry as sdt
from game.final_emission_gate import apply_final_emission_gate
from game.gm_retry import apply_deterministic_retry_fallback, force_terminal_retry_fallback
from game.turn_packet import TURN_PACKET_METADATA_KEY, attach_turn_packet, build_turn_packet, resolve_turn_packet_for_gate


# Direct telemetry helper/accessor semantics belong in this suite.
def test_snapshot_turn_stage_fingerprints_without_full_text() -> None:
    long = "word " * 80
    gm: Dict[str, Any] = {"player_facing_text": long, "metadata": {}}
    snap = sdt.snapshot_turn_stage(gm, "t1")
    assert snap["player_facing_fingerprint"] == sdt.compact_text_fingerprint(long)
    assert len(snap["player_facing_preview"]) <= 120
    assert long not in snap["player_facing_preview"] or len(long) <= 120
    assert snap["text_len"] == len(long)


def test_diff_turn_stage_detects_changes() -> None:
    a = sdt.snapshot_turn_stage(
        {"player_facing_text": "alpha", "metadata": {}, "fallback_kind": None},
        "s1",
    )
    b = sdt.snapshot_turn_stage(
        {
            "player_facing_text": "beta",
            "metadata": {},
            "final_route": "x",
            "fallback_kind": "fk",
        },
        "s2",
    )
    d = sdt.diff_turn_stage(a, b)
    assert d["text_fingerprint_changed"] is True
    assert d["route_changed"] is True
    assert d["fallback_changed"] is True

    r1 = {**a, "repair_flags": ["answer_completeness_repaired"]}
    r2 = {**a, "repair_flags": ["tone_escalation_repaired"]}
    dr = sdt.diff_turn_stage(r1, r2)
    assert dr["repair_flags_changed"] is True


def test_snapshot_turn_stage_reads_packet_fields_for_observability() -> None:
    pkt = build_turn_packet(
        scene_id="scene_investigate",
        resolution={"kind": "observe"},
        interaction_continuity={"active_interaction_target_id": "npc_route_probe"},
        narration_obligations={"active_npc_reply_kind": "observe"},
        response_policy={"response_type": "observe"},
    )
    gm: Dict[str, Any] = {
        "player_facing_text": "Rain drums on the slate roof.",
        "metadata": {TURN_PACKET_METADATA_KEY: pkt},
    }

    snap = sdt.snapshot_turn_stage(gm, "packet_probe")

    assert snap["resolution_kind"] == "observe"
    assert snap["active_target_id"] == "npc_route_probe"
    assert snap["reply_kind"] == "observe"
    assert snap["response_type"] == "observe"


def test_snapshot_turn_stage_handles_partial_packet_fields_safely() -> None:
    partial = build_turn_packet(scene_id="partial_scene")
    partial.pop("resolution_kind", None)
    partial["route"] = {"active_target_id": None}
    gm: Dict[str, Any] = {
        "player_facing_text": "A short line.",
        "metadata": {TURN_PACKET_METADATA_KEY: partial},
    }

    snap = sdt.snapshot_turn_stage(gm, "partial_probe")

    assert snap["stage"] == "partial_probe"
    assert snap["text_len"] == len("A short line.")
    assert snap["resolution_kind"] is None
    assert snap["active_target_id"] is None
    assert snap["reply_kind"] is None


def test_record_stage_snapshot_bounded() -> None:
    gm: Dict[str, Any] = {"metadata": {}}
    for i in range(20):
        sdt.record_stage_snapshot(gm, f"st_{i}")
    tel = gm["metadata"][sdt.STAGE_DIFF_METADATA_KEY]
    assert len(tel["snapshots"]) == 12


def test_record_stage_snapshot_preserves_existing_telemetry_subtrees() -> None:
    gm: Dict[str, Any] = {
        "metadata": {
            sdt.STAGE_DIFF_METADATA_KEY: {
                "prior_custom": {"k": 1},
                "snapshots": [],
                "transitions": [],
            }
        }
    }
    sdt.record_stage_snapshot(gm, "probe")
    tel = gm["metadata"][sdt.STAGE_DIFF_METADATA_KEY]
    assert tel["prior_custom"] == {"k": 1}
    assert any(s.get("stage") == "probe" for s in tel["snapshots"])


def test_record_stage_transition_bounded() -> None:
    gm: Dict[str, Any] = {"metadata": {}}
    for i in range(20):
        sdt.record_stage_transition(
            gm,
            f"a_{i}",
            f"b_{i}",
            {"stage": f"a_{i}", "player_facing_fingerprint": str(i)},
            {"stage": f"b_{i}", "player_facing_fingerprint": str(i + 1)},
        )
    tel = gm["metadata"][sdt.STAGE_DIFF_METADATA_KEY]
    assert len(tel["transitions"]) == 12


def test_stage_diff_telemetry_records_gate_entry_exit_snapshots() -> None:
    out = apply_final_emission_gate(
        {"player_facing_text": "Rain drums on the slate roof.", "tags": []},
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="scene_investigate",
        world={},
    )
    tel = (out.get("metadata") or {}).get(sdt.STAGE_DIFF_METADATA_KEY) or {}
    stages = [s.get("stage") for s in tel.get("snapshots", [])]
    assert "final_emission_gate_entry" in stages
    assert "final_emission_gate_exit" in stages


def test_retry_deterministic_accepted_snapshot() -> None:
    gm: Dict[str, Any] = {
        "player_facing_text": "stub",
        "tags": [],
        "metadata": {},
    }
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
    out = apply_deterministic_retry_fallback(
        gm,
        failure=failure,
        player_text="What does the sign say?",
        scene_envelope=scene_envelope,
        session=session,
        world=world,
        resolution=resolution,
        segmented_turn=None,
    )
    tel = (out.get("metadata") or {}).get(sdt.STAGE_DIFF_METADATA_KEY) or {}
    stages = [s.get("stage") for s in tel.get("snapshots", [])]
    assert "retry_pre_deterministic_fallback" in stages
    assert "retry_deterministic_fallback_applied" in stages


def test_terminal_retry_fallback_snapshot() -> None:
    base: Dict[str, Any] = {
        "player_facing_text": "",
        "tags": [],
        "metadata": {},
    }
    session: Dict[str, Any] = {
        "player_input": "Where is the door?",
        "social_authority": True,
        "active_scene_id": "missing_scene_xyz",
    }
    world: Dict[str, Any] = {"places": {}}
    scene_envelope: Dict[str, Any] = {"scene": {"id": "s1"}}
    resolution: Dict[str, Any] = {
        "kind": "question",
        "social": {"npc_id": "npc_x", "reply_kind": "answer"},
    }
    out = force_terminal_retry_fallback(
        session=session,
        original_text="",
        failure={"failure_class": "unresolved_question", "reasons": ["q"]},
        retry_failures=[],
        player_text="Where is the door?",
        scene_envelope=scene_envelope,
        world=world,
        resolution=resolution,
        base_gm=base,
        segmented_turn=None,
    )
    tel = (out.get("metadata") or {}).get(sdt.STAGE_DIFF_METADATA_KEY) or {}
    stages = [s.get("stage") for s in tel.get("snapshots", [])]
    assert "retry_terminal_fallback_entry" in stages
    assert "retry_terminal_fallback_result" in stages
    assert out.get("retry_exhausted") is True


def test_telemetry_coexists_with_existing_metadata() -> None:
    pkt = build_turn_packet(player_text="hello", scene_id="s9")
    gm: Dict[str, Any] = {
        "player_facing_text": "Short line.",
        "tags": [],
        "metadata": {"existing_key": 42, TURN_PACKET_METADATA_KEY: pkt},
    }
    attach_turn_packet(gm, pkt)
    sdt.record_stage_snapshot(gm, "coexist_probe")
    md = gm["metadata"]
    assert md["existing_key"] == 42
    assert isinstance(md[TURN_PACKET_METADATA_KEY], dict)
    assert isinstance(md[sdt.STAGE_DIFF_METADATA_KEY], dict)


def test_resolve_gate_turn_packet_prefers_cache() -> None:
    pkt = build_turn_packet(scene_id="cached")
    gm: Dict[str, Any] = {
        "metadata": {TURN_PACKET_METADATA_KEY: build_turn_packet(scene_id="meta")},
        "_gate_turn_packet_cache": pkt,
    }
    assert resolve_turn_packet_for_gate(gm) is pkt
    assert sdt.resolve_gate_turn_packet(gm) is pkt


def test_compact_preview_limit() -> None:
    t = "abcdefgh" * 20
    p = sdt.compact_preview(t, limit=25)
    assert len(p) == 25
    assert p.endswith("…")


def test_snapshot_turn_stage_includes_narrative_authenticity_telemetry() -> None:
    """AER3: ``_final_emission_meta`` NA status / rumor fields surface in turn snapshots."""
    gm: Dict[str, Any] = {
        "player_facing_text": "stub",
        "metadata": {},
        "_final_emission_meta": {
            "narrative_authenticity_status": "repaired",
            "narrative_authenticity_reason_codes": ["rumor_uses_identical_phrasing_for_known_fact"],
            "narrative_authenticity_skip_reason": "",
            "narrative_authenticity_rumor_relaxed_low_signal": True,
            "narrative_authenticity_trace": {"rumor_turn_active": True},
        },
    }
    snap = sdt.snapshot_turn_stage(gm, "na_snap")
    assert snap["narrative_authenticity_status"] == "repaired"
    assert snap["narrative_authenticity_rumor_relaxed_low_signal"] is True
    assert snap["rumor_turn_active"] is True
    assert "rumor_uses_identical" in snap["narrative_authenticity_reason_codes"][0]


def test_build_stage_diff_observability_events_canonical_shape_and_clusters() -> None:
    stage_diff = {
        "transitions": [
            {
                "from": "a",
                "to": "b",
                "diff": {
                    "route_changed": True,
                    "fallback_changed": True,
                    "repair_flags_changed": True,
                    "retry_flags_changed": False,
                    "terminal_retry_activated": True,
                },
            }
        ],
        "snapshots": [
            {
                "stage": "exit",
                "repair_flags": ["answer_completeness_repaired"],
                "retry_flags": {"retry_exhausted": True, "targeted_retry_terminal": True},
                "fallback_kind": "fk",
                "fallback_source": "resolution",
                "narrative_authenticity_status": "pass",
                "narrative_authenticity_reason_codes": ["code_a", "code_a"],
            }
        ],
    }
    ev = sdt.build_stage_diff_observability_events(stage_diff)
    assert len(ev) >= 4
    for e in ev:
        assert set(e.keys()) == {"phase", "owner", "action", "reasons", "scope", "data"}
        assert e["phase"] == "gate"
        assert e["owner"] == "stage_diff_telemetry"
        assert e["scope"] == "turn"
    route_ev = next(x for x in ev if x["reasons"] == ["stage_diff_route_changed"])
    assert route_ev["action"] == "observed"
    assert route_ev["data"] == {"route_changed": True}
    fb_ev = next(x for x in ev if "stage_diff_fallback_changed" in x["reasons"])
    assert fb_ev["data"]["transition_fallback_changed"] is True
    rep_ev = next(x for x in ev if "stage_diff_repair_flags_changed" in x["reasons"])
    assert rep_ev["action"] == "repaired"
    na_ev = next(x for x in ev if "code_a" in x["reasons"])
    assert na_ev["reasons"] == ["code_a"]
    assert "player_facing_preview" not in str(na_ev["data"])


def test_build_stage_diff_observability_events_malformed_and_empty_safe() -> None:
    assert sdt.build_stage_diff_observability_events(None) == []
    assert sdt.build_stage_diff_observability_events("bad") == []
    assert sdt.build_stage_diff_observability_events({}) == []


def test_build_stage_diff_observability_events_does_not_mutate_input() -> None:
    inner = {
        "diff": {"route_changed": True},
    }
    stage_diff = {"transitions": [inner], "snapshots": []}
    before = repr(stage_diff)
    _ = sdt.build_stage_diff_observability_events(stage_diff)
    assert repr(stage_diff) == before
    assert inner["diff"]["route_changed"] is True


def test_snapshot_turn_stage_does_not_widen_na_surface_with_nested_dicts_or_unknown_keys() -> None:
    """Stage-diff must only consume the curated NA projection surface."""
    gm: Dict[str, Any] = {
        "player_facing_text": "stub",
        "metadata": {},
        "_final_emission_meta": {
            "narrative_authenticity_status": "pass",
            "narrative_authenticity_reason_codes": ["a"],
            # Nested telemetry should not be passed through into stage snapshots.
            "narrative_authenticity_metrics": {"generic_filler_score": 0.2},
            "narrative_authenticity_evidence": {"blob": {"nested": "nope"}},
            # Unknown keys should never appear.
            "narrative_authenticity_private_blob": {"x": 1},
        },
    }
    snap = sdt.snapshot_turn_stage(gm, "na_surface_probe")
    assert snap.get("narrative_authenticity_status") == "pass"
    assert snap.get("narrative_authenticity_reason_codes") == ["a"]
    assert "narrative_authenticity_metrics" not in snap
    assert "narrative_authenticity_evidence" not in snap
    assert "narrative_authenticity_private_blob" not in snap
