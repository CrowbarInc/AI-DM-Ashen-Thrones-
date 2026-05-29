"""DTD2: validation/evaluation consumes ``_final_emission_meta['dead_turn']`` only (no local classification)."""

from __future__ import annotations

import importlib
import sys

from game.final_emission_meta import (
    assemble_unified_observational_telemetry_bundle,
    read_final_emission_meta_dict,
    read_final_emission_meta_from_turn_payload,
)

import pytest

from game.narrative_authenticity_eval import evaluate_narrative_authenticity
from game.playability_eval import evaluate_playability
from tests.helpers.behavioral_gauntlet_eval import evaluate_behavioral_gauntlet
from tests.helpers.transcript_snapshots import snapshot_from_chat_payload

pytestmark = pytest.mark.unit


def _resp_na(*, text: str, fem: dict) -> dict:
    return {"ok": True, "gm_output": {"player_facing_text": text, "_final_emission_meta": fem}}


def test_transcript_snapshot_helper_import_does_not_load_live_api_stack() -> None:
    module_names = (
        "game.api",
        "game.gm",
        "game.config",
        "tests.helpers.transcript_snapshots",
    )
    saved = {name: sys.modules[name] for name in module_names if name in sys.modules}
    try:
        for name in module_names:
            sys.modules.pop(name, None)

        imported = importlib.import_module("tests.helpers.transcript_snapshots")

        assert hasattr(imported, "snapshot_from_chat_payload")
        assert "game.api" not in sys.modules
        assert "game.gm" not in sys.modules
        assert "game.config" not in sys.modules
    finally:
        sys.modules.pop("tests.helpers.transcript_snapshots", None)
        for name, module in saved.items():
            sys.modules[name] = module


def test_transcript_snapshot_carries_final_emission_meta_for_manual_gauntlet_rows() -> None:
    payload = {
        "ok": True,
        "gm_output": {
            "player_facing_text": "Gate mist holds.",
            "_final_emission_meta": {
                "dead_turn": {
                    "is_dead_turn": True,
                    "dead_turn_class": "upstream_api_failure",
                    "dead_turn_reason_codes": ["upstream_api_error"],
                    "validation_playable": False,
                    "manual_test_valid": False,
                }
            },
        },
        "scene": {"scene": {"id": "frontier_gate"}},
        "session": {"scene_state": {}},
        "resolution": None,
        "journal": None,
        "world": None,
    }
    snap = snapshot_from_chat_payload(0, "What do I see?", payload)
    fem = read_final_emission_meta_dict(snap)
    assert isinstance(fem, dict)
    dt = (fem.get("dead_turn") or {})
    assert dt.get("is_dead_turn") is True

    fem_for_bundle = read_final_emission_meta_from_turn_payload(payload)
    na_eval = evaluate_narrative_authenticity({}, payload, fem_for_bundle)
    bundle = assemble_unified_observational_telemetry_bundle(
        fem=fem_for_bundle,
        stage_diff=(payload.get("gm_output") or {}).get("metadata", {}).get("stage_diff_telemetry"),
        evaluator_result=na_eval,
    )
    assert set(bundle.keys()) == {
        "final_emission_meta",
        "fem_observability_events",
        "fem_runtime_lineage_events",
        "stage_diff_observability_events",
        "evaluator_observability_events",
        "stage_diff_surface",
    }
    assert isinstance(bundle["fem_runtime_lineage_events"], list)
    assert bundle["evaluator_observability_events"]
    assert any(e.get("owner") == "dead_turn" for e in bundle["fem_observability_events"])


def test_behavioral_gauntlet_marks_run_invalid_when_one_turn_is_dead() -> None:
    turns = [
        {"player_text": "What do I see?", "gm_text": "Mist and a posted notice; guards watch quietly."},
        {
            "player_text": "I read the notice.",
            "gm_text": "Curfew orders are posted.",
            "_final_emission_meta": {
                "dead_turn": {
                    "is_dead_turn": True,
                    "dead_turn_class": "retry_terminal_fallback",
                    "dead_turn_reason_codes": ["upstream_api_error", "fast_fallback_lane"],
                    "validation_playable": False,
                    "manual_test_valid": False,
                }
            },
        },
    ]
    out = evaluate_behavioral_gauntlet(turns, expected_axis={"neutrality"})
    assert out["axes"]["neutrality"]["passed"] is True
    assert out["overall_passed"] is False
    gv = out["gameplay_validation"]
    assert gv["excluded_from_scoring"] is True
    assert gv["dead_turn_count"] == 1
    assert gv["dead_turn_indexes"] == [1]
    assert "dead_turn" in gv["per_turn"][-1]
    assert (gv.get("dead_turn_banner") or "").startswith("DEAD TURN DETECTED")
    assert gv["dead_turn_by_class"] == {"retry_terminal_fallback": 1}
    dtr = out["dead_turn_run_report"]
    assert dtr["dead_turn_indexes"] == [1]
    assert "retry_terminal_fallback" in (dtr.get("banner") or "")


def test_narrative_authenticity_eval_respects_dtd1_dead_turn_not_upstream_inspection() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_status": "pass",
        "narrative_authenticity_reason_codes": [],
        "narrative_authenticity_metrics": {"generic_filler_score": 0.12, "signal_markers_detected": 2},
        "dead_turn": {
            "is_dead_turn": True,
            "dead_turn_class": "upstream_api_failure",
            "dead_turn_reason_codes": ["upstream_api_error"],
            "validation_playable": False,
            "manual_test_valid": False,
        },
    }
    r = evaluate_narrative_authenticity({}, _resp_na(text="Captain nods toward the yard.", fem=fem), fem)
    assert r["gameplay_validation"]["excluded_from_scoring"] is True
    assert r["passed"] is False
    assert r["narrative_authenticity_verdict"] == "excluded_from_scoring"
    assert r["scores"]["signal_gain"] == 0
    diag = r["gameplay_validation"].get("diagnostic_scores") or {}
    assert isinstance(diag, dict)
    assert sum(int(v) for v in diag.values() if isinstance(v, (int, float))) > 0


def test_narrative_authenticity_eval_does_not_infer_dead_turn_from_api_error_shape() -> None:
    fem = {
        "narrative_authenticity_checked": True,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_status": "pass",
        "narrative_authenticity_reason_codes": [],
        "narrative_authenticity_metrics": {"generic_filler_score": 0.12, "signal_markers_detected": 2},
    }
    payload = {
        "ok": False,
        "error": "upstream_api_error: retry_terminal_fallback",
        "gm_output": {
            "player_facing_text": "Captain Halvar points to the east gate roster.",
            "_final_emission_meta": fem,
            "metadata": {"upstream_api_error": {"failure_class": "transport"}},
            "retry_exhausted": True,
            "targeted_retry_terminal": True,
        },
    }
    r = evaluate_narrative_authenticity({}, payload, fem)
    assert r["gameplay_validation"]["excluded_from_scoring"] is False
    assert r["gameplay_validation"]["run_valid"] is True
    assert r["narrative_authenticity_verdict"] != "excluded_from_scoring"


def test_playability_eval_excludes_only_from_fem_dead_turn_source() -> None:
    live_out = evaluate_playability(
        {
            "player_prompt": "Who commands the watch here?",
            "gm_text": "Captain Halvar commands the watch; sergeants rotate shifts.",
            "ok": False,
            "api_error": "upstream_api_error retry_terminal_fallback",
            "gm_output": {
                "metadata": {"upstream_api_error": {"failure_class": "transport"}},
                "retry_exhausted": True,
                "targeted_retry_terminal": True,
            },
        }
    )
    assert live_out["gameplay_validation"]["excluded_from_scoring"] is False
    assert live_out["gameplay_validation"]["run_valid"] is True
    assert live_out["overall"]["score"] > 0

    dead_out = evaluate_playability(
        {
            "player_prompt": "Who commands the watch here?",
            "gm_text": "Captain Halvar commands the watch; sergeants rotate shifts.",
            "gm_output": {
                "_final_emission_meta": {
                    "dead_turn": {
                        "is_dead_turn": True,
                        "dead_turn_class": "upstream_api_failure",
                        "dead_turn_reason_codes": ["upstream_api_error"],
                        "validation_playable": False,
                        "manual_test_valid": False,
                    }
                }
            },
        }
    )
    assert dead_out["gameplay_validation"]["excluded_from_scoring"] is True
    assert dead_out["gameplay_validation"]["run_valid"] is False
    assert dead_out["overall"] == {"score": 0, "rating": "weak", "passed": False}


def test_behavioral_gauntlet_does_not_infer_dead_turn_from_api_error_shape_without_fem() -> None:
    turns = [
        {
            "player_text": "What do I see?",
            "gm_text": "Mist and a posted notice; guards watch quietly.",
            "ok": False,
            "api_error": "upstream_api_error retry_terminal_fallback",
            "gm_output": {
                "metadata": {"upstream_api_error": {"failure_class": "transport"}},
                "retry_exhausted": True,
                "targeted_retry_terminal": True,
            },
        }
    ]
    out = evaluate_behavioral_gauntlet(turns, expected_axis={"neutrality"})
    gv = out["gameplay_validation"]
    assert gv["excluded_from_scoring"] is False
    assert gv["run_valid"] is True
    assert gv["dead_turn_count"] == 0
    assert out["dead_turn_run_report"]["chat_error_count"] == 1
    assert out["dead_turn_run_report"]["invalid_for_gameplay_conclusions"] is False


def test_playability_all_live_turn_still_scores_normally() -> None:
    out = evaluate_playability(
        {
            "player_prompt": "Who commands the watch here?",
            "gm_text": "Captain Halvar commands the watch; sergeants rotate shifts.",
        }
    )
    assert out["gameplay_validation"]["run_valid"] is True
    assert out["overall"]["passed"] is True


def test_playability_rollup_shape_via_tool_helper() -> None:
    from game.playability_eval import rollup_playability_gameplay_validation

    turns_out = [
        {
            "playability_eval": {
                "gameplay_validation": {
                    "run_valid": True,
                    "dead_turn_count": 0,
                    "infra_failure_count": 0,
                    "excluded_from_scoring": False,
                    "invalidation_reason": None,
                }
            }
        },
        {
            "playability_eval": {
                "gameplay_validation": {
                    "run_valid": False,
                    "dead_turn_count": 1,
                    "infra_failure_count": 1,
                    "excluded_from_scoring": True,
                    "invalidation_reason": "excluded_from_score:dead_turn:upstream_api_failure",
                }
            }
        },
    ]
    roll = rollup_playability_gameplay_validation(turns_out)
    assert roll["run_valid"] is False
    assert roll["dead_turn_count"] == 1
    assert roll["excluded_from_scoring"] is True
