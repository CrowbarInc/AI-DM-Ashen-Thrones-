"""Confidence tests for the unified observational telemetry bundle (read-side, behavior-neutral locks).

Covers integration, bounded outputs, determinism, and safe handling of malformed inputs.
"""

from __future__ import annotations

import copy
from typing import Any

from game.final_emission_meta import (
    assemble_unified_observational_telemetry_bundle,
    build_fem_observability_events,
    normalize_final_emission_meta_for_observability,
    read_final_emission_meta_dict,
    stage_diff_narrative_authenticity_projection,
)
from game.narrative_authenticity_eval import (
    build_evaluator_observability_events,
    evaluate_narrative_authenticity,
)
from game.stage_diff_telemetry import STAGE_DIFF_BUNDLE_SURFACE_KEYS, build_stage_diff_observability_events
from game.telemetry_vocab import TELEMETRY_PHASE_EVALUATOR, TELEMETRY_PHASE_GATE, build_telemetry_event

_CANONICAL_EVENT_KEYS = frozenset({"phase", "owner", "action", "reasons", "scope", "data"})


def _assert_canonical_events(events: list[dict[str, Any]], *, allowed_phases: frozenset[str]) -> None:
    for ev in events:
        assert set(ev.keys()) == _CANONICAL_EVENT_KEYS
        assert ev["phase"] in allowed_phases
        assert isinstance(ev["reasons"], list)
        assert isinstance(ev["data"], dict)


def test_unified_bundle_realistic_integration_representative_payload() -> None:
    """Representative FEM + stage-diff + evaluator slice projects into one comparable bundle."""
    fem: dict[str, Any] = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": True,
        "narrative_authenticity_repair_applied": False,
        "narrative_authenticity_failure_reasons": ["dup", "dup"],
        "narrative_authenticity_reason_codes": ["rumor_overlap_jaccard_moderate"],
        "narrative_authenticity_status": "repaired",
        "narrative_authenticity_skip_reason": None,
        "narrative_authenticity_rumor_relaxed_low_signal": False,
        "answer_completeness_checked": True,
        "answer_completeness_failed": False,
        "answer_completeness_repaired": False,
        "answer_completeness_skip_reason": None,
        "response_delta_checked": True,
        "response_delta_failed": False,
        "response_delta_repaired": True,
        "response_delta_failure_reasons": ["echo"],
        "response_delta_skip_reason": None,
        "fallback_behavior_contract_present": True,
        "fallback_behavior_checked": True,
        "fallback_behavior_failed": False,
        "fallback_behavior_repaired": False,
        "fallback_behavior_skip_reason": None,
        "response_type_required": "dialogue",
        "response_type_contract_source": "resolution.metadata",
        "response_type_candidate_ok": True,
        "response_type_repair_used": False,
        "response_type_rejection_reasons": [],
        "dead_turn": {
            "is_dead_turn": False,
            "dead_turn_class": "none",
            "dead_turn_reason_codes": [],
            "validation_playable": True,
            "manual_test_valid": True,
        },
    }
    stage_diff: dict[str, Any] = {
        "snapshots": [
            {
                "stage": "post_repair",
                "repair_flags": ["narrative_authenticity_repaired", "response_delta_repaired"],
                "retry_flags": {"retry_exhausted": True, "targeted_retry_terminal": False},
                "fallback_kind": "uncertainty_brief",
                "fallback_source": "resolution",
                "fallback_stage": "gate_tail",
                "narrative_authenticity_status": "pass",
                "narrative_authenticity_skip_reason": "",
                "narrative_authenticity_reason_codes": ["na_tail_a"],
                "narrative_authenticity_rumor_relaxed_low_signal": True,
                "rumor_turn_active": True,
            }
        ],
        "transitions": [
            {
                "from": "pre_route",
                "to": "post_route",
                "diff": {
                    "text_fingerprint_changed": True,
                    "route_changed": True,
                    "fallback_changed": True,
                    "repair_flags_changed": True,
                    "resolution_kind_changed": False,
                    "retry_flags_changed": True,
                    "terminal_retry_activated": False,
                },
            }
        ],
    }
    evaluator_result: dict[str, Any] = {
        "passed": True,
        "narrative_authenticity_verdict": "repaired_pass",
        "scores": {"signal_gain": 5},
        "reasons": ["narrative_authenticity_repaired_signal_context", "rumor_overlap_jaccard_moderate"],
        "gameplay_validation": {"excluded_from_scoring": False, "invalidation_reason": None},
    }

    bundle = assemble_unified_observational_telemetry_bundle(
        fem=fem,
        stage_diff=stage_diff,
        evaluator_result=evaluator_result,
    )

    assert set(bundle.keys()) == {
        "final_emission_meta",
        "fem_observability_events",
        "stage_diff_observability_events",
        "evaluator_observability_events",
        "stage_diff_surface",
    }
    assert bundle["final_emission_meta"] == normalize_final_emission_meta_for_observability(fem)
    assert bundle["fem_observability_events"]
    assert bundle["stage_diff_observability_events"]
    assert bundle["evaluator_observability_events"]

    assert list(bundle["stage_diff_surface"].keys()) == sorted(STAGE_DIFF_BUNDLE_SURFACE_KEYS)
    assert set(bundle["stage_diff_surface"].keys()) <= STAGE_DIFF_BUNDLE_SURFACE_KEYS
    assert "prior_custom" not in bundle["stage_diff_surface"]

    gate_phases = frozenset({TELEMETRY_PHASE_GATE})
    eval_phases = frozenset({TELEMETRY_PHASE_EVALUATOR})
    _assert_canonical_events(bundle["fem_observability_events"], allowed_phases=gate_phases)
    _assert_canonical_events(bundle["stage_diff_observability_events"], allowed_phases=gate_phases)
    _assert_canonical_events(bundle["evaluator_observability_events"], allowed_phases=eval_phases)

    fem_owners = [e["owner"] for e in bundle["fem_observability_events"]]
    assert "narrative_authenticity" in fem_owners
    assert "answer_completeness" in fem_owners
    assert "response_delta" in fem_owners
    assert "fallback_behavior" in fem_owners
    assert "response_type" in fem_owners
    assert "dead_turn" in fem_owners

    na_ev = next(e for e in bundle["fem_observability_events"] if e["owner"] == "narrative_authenticity")
    assert na_ev["reasons"] == ["dup", "rumor_overlap_jaccard_moderate"]
    assert na_ev["data"]["repaired"] is True

    ev0 = bundle["evaluator_observability_events"][0]
    assert ev0["owner"] == "narrative_authenticity_eval"
    assert ev0["data"].get("verdict") == "repaired_pass"
    assert ev0["data"].get("passed") is True
    assert "narrative_authenticity_repaired_signal_context" in ev0["reasons"]


def test_mutating_bundle_copy_does_not_poison_sources_or_reprojection() -> None:
    """Mutating an assembled bundle must not alter sources; re-assembling from the same inputs is idempotent."""
    fem: dict[str, Any] = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": True,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_reason_codes": ["low_signal_generic_reply"],
        "narrative_authenticity_metrics": {"generic_filler_score": 0.7},
        "dead_turn": {"is_dead_turn": False, "dead_turn_class": "none"},
    }
    stage_diff: dict[str, Any] = {
        "snapshots": [{"stage": "s", "repair_flags": [], "retry_flags": {}}],
        "transitions": [{"from": "a", "to": "b", "diff": {"route_changed": True}}],
    }
    evaluator_result: dict[str, Any] = {
        "passed": False,
        "narrative_authenticity_verdict": "fail",
        "scores": {"signal_gain": 0},
        "reasons": ["narrative_authenticity_gate_failed_unrepaired"],
        "gameplay_validation": {"excluded_from_scoring": False},
    }

    fem_copy = copy.deepcopy(fem)
    sd_copy = copy.deepcopy(stage_diff)
    ev_copy = copy.deepcopy(evaluator_result)

    golden = assemble_unified_observational_telemetry_bundle(fem=fem_copy, stage_diff=sd_copy, evaluator_result=ev_copy)

    wreck = copy.deepcopy(golden)
    wreck["fem_observability_events"].append(
        {"phase": "gate", "owner": "bogus", "action": "applied", "reasons": [], "scope": "turn", "data": {}}
    )
    if wreck["evaluator_observability_events"]:
        wreck["evaluator_observability_events"][0]["data"]["passed"] = True
        wreck["evaluator_observability_events"][0]["data"]["verdict"] = "clean_pass"
        wreck["evaluator_observability_events"][0]["action"] = "observed"
    wreck["final_emission_meta"]["narrative_authenticity_checked"] = False
    wreck["stage_diff_surface"]["snapshots"] = [{"injected": True}]

    fresh = assemble_unified_observational_telemetry_bundle(fem=fem_copy, stage_diff=sd_copy, evaluator_result=ev_copy)
    assert fresh == golden
    assert fem_copy == fem
    assert sd_copy == stage_diff
    assert ev_copy == evaluator_result

    gm_payload = {"ok": True, "gm_output": {"player_facing_text": "x", "_final_emission_meta": copy.deepcopy(fem)}}
    meta = read_final_emission_meta_dict(gm_payload["gm_output"])
    r1 = evaluate_narrative_authenticity({}, gm_payload, meta)
    events = build_evaluator_observability_events(r1)
    if events:
        events[0]["data"]["passed"] = True
        events[0]["reasons"] = ["fake"]
    r2 = evaluate_narrative_authenticity({}, gm_payload, meta)
    assert r2 == r1
    assert r1["passed"] is r2["passed"]
    assert r1["narrative_authenticity_verdict"] == r2["narrative_authenticity_verdict"]


def test_assemble_unified_bundle_malformed_inputs_no_exceptions_bounded_outputs() -> None:
    """Malformed inputs must not raise and must not widen the bundle surface beyond allow-lists."""

    def run_case(
        *,
        fem: Any,
        stage_diff: Any,
        evaluator_result: Any,
    ) -> dict[str, Any]:
        return assemble_unified_observational_telemetry_bundle(
            fem=fem,
            stage_diff=stage_diff,
            evaluator_result=evaluator_result,
        )

    b0 = run_case(fem=None, stage_diff="not-a-dict", evaluator_result=[])
    assert isinstance(b0["final_emission_meta"], dict)
    assert [e["owner"] for e in b0["fem_observability_events"]] == ["dead_turn"]
    assert b0["stage_diff_observability_events"] == []
    assert b0["evaluator_observability_events"] == []
    assert b0["stage_diff_surface"] == {}

    b1 = run_case(
        fem={"dead_turn": "not-a-mapping", "narrative_authenticity_metrics": [1, 2, 3]},
        stage_diff={"snapshots": "bad", "transitions": None, "extra_leak": {"x": 1}},
        evaluator_result={"passed": "not-bool", "narrative_authenticity_verdict": None, "reasons": {"nested": 1}},
    )
    assert isinstance(b1["final_emission_meta"].get("dead_turn"), dict)
    assert b1["final_emission_meta"]["narrative_authenticity_metrics"] == {}
    assert "extra_leak" not in b1["stage_diff_surface"]
    assert b1["stage_diff_surface"] == {}
    ev = b1["evaluator_observability_events"]
    if ev:
        assert ev[0]["data"].get("passed") is None

    b2 = run_case(
        fem={
            "narrative_authenticity_checked": True,
            "narrative_authenticity_failure_reasons": {"not": "a list"},
            "narrative_authenticity_reason_codes": None,
        },
        stage_diff={
            "snapshots": [
                "not-a-snapshot",
                {"stage": 1, "repair_flags": "nope", "retry_flags": []},
            ],
            "transitions": [
                "bad",
                {"from": "a", "to": "b", "diff": "not-a-diff"},
                {"from": "c", "to": "d", "diff": {"route_changed": True}},
            ],
        },
        evaluator_result={"scores": {}, "gameplay_validation": "bad"},
    )
    assert len(b2["fem_observability_events"]) <= 6
    assert len(b2["stage_diff_observability_events"]) <= 6
    for e in b2["fem_observability_events"] + b2["stage_diff_observability_events"]:
        assert set(e.keys()) == _CANONICAL_EVENT_KEYS
    surf = b2["stage_diff_surface"]
    assert set(surf.keys()) <= STAGE_DIFF_BUNDLE_SURFACE_KEYS
    for k, v in surf.items():
        assert isinstance(v, list)
        if k == "snapshots":
            assert any(isinstance(x, dict) for x in v)

    b3 = run_case(
        fem={},
        stage_diff={},
        evaluator_result={"notes_only": True},
    )
    assert b3["evaluator_observability_events"] == []

    b4 = run_case(
        fem={},
        stage_diff={},
        evaluator_result={"passed": True, "reasons": {"not": "a sequence of strings"}},
    )
    assert len(b4["evaluator_observability_events"]) <= 1
    if b4["evaluator_observability_events"]:
        assert b4["evaluator_observability_events"][0]["reasons"] == []


def test_bundle_event_caps_sorted_surface_and_replay_determinism() -> None:
    """Event caps, sorted ``stage_diff_surface`` keys, replay stability, and canonical top-level keys only."""
    many_reasons = [f"r{i}" for i in range(40)]
    fem: dict[str, Any] = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_failure_reasons": many_reasons,
        "narrative_authenticity_reason_codes": many_reasons,
        "answer_completeness_checked": True,
        "response_delta_checked": True,
        "fallback_behavior_checked": True,
        "response_type_required": "observe",
        "response_type_candidate_ok": True,
        "dead_turn": {"is_dead_turn": False, "dead_turn_class": "none"},
    }
    transitions = [
        {
            "from": f"t{i}",
            "to": f"t{i + 1}",
            "diff": {
                "route_changed": bool(i % 2 == 0),
                "fallback_changed": bool(i % 3 == 0),
                "repair_flags_changed": bool(i % 5 == 0),
                "retry_flags_changed": True,
                "terminal_retry_activated": bool(i == 19),
            },
        }
        for i in range(20)
    ]
    snapshots = [{"stage": f"s{i}", "repair_flags": [], "retry_flags": {}} for i in range(20)]
    stage_diff = {"transitions": transitions, "snapshots": snapshots}
    evaluator_result = {
        "passed": False,
        "narrative_authenticity_verdict": "fail",
        "scores": {"signal_gain": 0},
        "reasons": many_reasons,
        "gameplay_validation": {"excluded_from_scoring": False},
    }

    a = assemble_unified_observational_telemetry_bundle(fem=fem, stage_diff=stage_diff, evaluator_result=evaluator_result)
    b = assemble_unified_observational_telemetry_bundle(fem=fem, stage_diff=stage_diff, evaluator_result=evaluator_result)
    assert a == b
    assert len(a["fem_observability_events"]) <= 6
    assert len(a["stage_diff_observability_events"]) <= 6
    assert len(a["evaluator_observability_events"]) <= 1
    assert list(a["stage_diff_surface"].keys()) == sorted(STAGE_DIFF_BUNDLE_SURFACE_KEYS)

    na_fem = next(x for x in a["fem_observability_events"] if x["owner"] == "narrative_authenticity")
    assert len(na_fem["reasons"]) <= 16

    long_skip = "x" * 200
    fem_clip = {
        "narrative_authenticity_checked": False,
        "narrative_authenticity_skip_reason": long_skip,
    }
    clip_events = build_fem_observability_events(normalize_final_emission_meta_for_observability(fem_clip))
    skip_val = clip_events[0]["data"].get("skip_reason")
    assert isinstance(skip_val, str)
    assert len(skip_val) <= 121
    assert skip_val.endswith("…")


def test_alias_and_reason_merge_anti_drift_stable_canonical_projection() -> None:
    """Lock verb-ish action aliases and FEM failure/reason list merge into canonical vocabulary."""
    ev_alias = build_telemetry_event(phase="gate", owner="o", action="observe", reasons=[], scope="turn", data={})
    assert ev_alias["action"] == "observed"

    fem: dict[str, Any] = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_failure_reasons": ["z", "a"],
        "narrative_authenticity_reason_codes": ["a", "b"],
        "dead_turn": {"is_dead_turn": False, "dead_turn_class": "none"},
    }
    events = build_fem_observability_events(normalize_final_emission_meta_for_observability(fem))
    na = next(e for e in events if e["owner"] == "narrative_authenticity")
    assert na["reasons"] == ["z", "a", "b"]

    proj = stage_diff_narrative_authenticity_projection(fem)
    assert proj.get("narrative_authenticity_reason_codes") == ["a", "b", "z"]


def test_stage_diff_event_builder_ordering_determinism_for_fixed_aggregates() -> None:
    """Cluster events follow fixed append order for identical aggregate inputs."""
    sd: dict[str, Any] = {
        "transitions": [
            {
                "from": "a",
                "to": "b",
                "diff": {
                    "route_changed": True,
                    "fallback_changed": True,
                    "repair_flags_changed": True,
                    "retry_flags_changed": True,
                    "terminal_retry_activated": True,
                },
            }
        ],
        "snapshots": [
            {
                "stage": "tail",
                "repair_flags": ["answer_completeness_repaired"],
                "retry_flags": {"retry_exhausted": True, "targeted_retry_terminal": True},
                "fallback_kind": "k",
                "fallback_source": "s",
                "narrative_authenticity_status": "pass",
                "narrative_authenticity_reason_codes": ["c1"],
            }
        ],
    }
    u = build_stage_diff_observability_events(sd)
    v = build_stage_diff_observability_events(sd)
    assert u == v
    assert [e["reasons"] for e in u] == [e["reasons"] for e in v]
