"""Regression tests for manual gauntlet report helpers (loads ``tools/run_manual_gauntlet.py``)."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from game.dead_turn_report_visibility import build_dead_turn_run_report

from tests.helpers.behavioral_gauntlet_eval import SCHEMA_VERSION as BEHAVIORAL_SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[1]

# Documented snippet cap / truncation (keep in sync with run_manual_gauntlet defaults).
_SNIPPET_MAX_ITEMS = 5
_SNIPPET_MAX_CHARS = 400
_RAW_TRACE_MAX_STR = 12000


@pytest.fixture(scope="module")
def rmg_mod():
    path = ROOT / "tools" / "run_manual_gauntlet.py"
    name = "_run_manual_gauntlet_test_load"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _spec(rmg_mod, gid: str = "g1"):
    return rmg_mod.GAUNTLETS[gid]


def _artifact_paths(rmg_mod, base: str) -> dict[str, Path]:
    d = rmg_mod.ARTIFACTS_DIR
    return {
        "transcript": d / f"{base}_transcript.md",
        "summary": d / f"{base}_summary.json",
        "key_events": d / f"{base}_key_events.json",
        "snippets": d / f"{base}_snippets.json",
        "raw_trace": d / f"{base}_raw_trace.json",
    }


def _basename_from_paths(paths: dict[str, Path]) -> str:
    tname = paths["transcript"].name
    assert tname.endswith("_transcript.md"), tname
    return tname[: -len("_transcript.md")]


# --- 1) Basename + artifact naming ---


def test_artifact_base_name_default_utc_pattern_and_gauntlet_id(rmg_mod):
    # Python 3.14+: datetime.datetime is immutable; assert documented contract, not wall clock.
    base = rmg_mod._artifact_base_name(_spec(rmg_mod, "g5"), None)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_g5", base), base


def test_artifact_base_name_custom_prefix_overrides_timestamp(rmg_mod):
    base = rmg_mod._artifact_base_name(_spec(rmg_mod), "my_smoke_run")
    assert base == "my_smoke_run"


def test_artifact_base_name_prefix_sanitizes_slashes_and_dots(rmg_mod):
    assert rmg_mod._artifact_base_name(_spec(rmg_mod), r"a/b\c") == "a_b_c"
    assert rmg_mod._artifact_base_name(_spec(rmg_mod), ".trim_me.") == "trim_me"


def test_artifact_base_name_empty_after_sanitization_falls_back_to_timestamp(rmg_mod):
    base = rmg_mod._artifact_base_name(_spec(rmg_mod, "g2"), "...")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_g2", base), base


def test_artifact_paths_share_identical_basename(rmg_mod):
    base = "unit_prefix_g3"
    paths = _artifact_paths(rmg_mod, base)
    assert _basename_from_paths(paths) == base
    assert paths["transcript"].name == f"{base}_transcript.md"
    assert paths["summary"].name == f"{base}_summary.json"
    assert paths["key_events"].name == f"{base}_key_events.json"
    assert paths["snippets"].name == f"{base}_snippets.json"
    assert paths["raw_trace"].name == f"{base}_raw_trace.json"


# --- 2) JSON writing helper ---


def test_json_dump_writes_utf8_json_readable_and_creates_parents(tmp_path, rmg_mod):
    path = tmp_path / "nested" / "dir" / "out.json"
    rmg_mod._json_dump(path, {"emoji": "αβγ", "n": 1, "nested": {"a": [None, True]}})
    assert path.is_file()
    raw = path.read_bytes()
    assert raw.startswith(b"{")
    loaded = json.loads(raw.decode("utf-8"))
    assert loaded["emoji"] == "αβγ"
    assert loaded["nested"]["a"] == [None, True]


def test_json_dump_empty_and_nested_payloads(tmp_path, rmg_mod):
    rmg_mod._json_dump(tmp_path / "empty.json", {})
    assert json.loads((tmp_path / "empty.json").read_text(encoding="utf-8")) == {}
    deep = {"a": {"b": {"c": [1, 2, {"d": "x"}]}}}
    rmg_mod._json_dump(tmp_path / "deep.json", deep)
    assert json.loads((tmp_path / "deep.json").read_text(encoding="utf-8")) == deep


# --- 3) Key event extraction + collapse ---


def _record_with_emission_debug(turn_index: int, emission_debug: dict, ok: bool = True) -> dict:
    return {
        "turn_index": turn_index,
        "ok": ok,
        "debug": {
            "last_debug_trace": {
                "resolution": {"metadata": {"emission_debug": emission_debug}},
            }
        },
    }


def test_extract_candidate_events_validator_bridge_repair_fallback_emission(rmg_mod):
    em = {
        "interaction_continuity_validation": {"ok": False, "violations": ["v1"]},
        "interaction_continuity_speaker_binding_bridge": {"applied": True, "extra": "x" * 5000},
        "interaction_continuity_repair": {
            "applied": True,
            "repair_type": "test_repair",
            "violations": ["huge_" + "x" * 10000],
        },
        "social_emission_integrity_fallback_kind": "test_fallback",
        "some_gate_failed": True,
    }
    rec = _record_with_emission_debug(0, em)
    events = rmg_mod._extract_candidate_events([rec])
    by_name = {e["name"]: e for e in events}
    assert "interaction_continuity_validation" in by_name
    assert by_name["interaction_continuity_validation"]["stage"] == "validator"
    assert "interaction_continuity_speaker_binding_bridge" in by_name
    assert by_name["interaction_continuity_speaker_binding_bridge"]["stage"] == "bridge"
    assert "interaction_continuity_repair" in by_name
    assert by_name["interaction_continuity_repair"]["stage"] == "repair"
    # String emission_debug keys → repair / emission_debug stage
    assert any(e["name"] == "social_emission_integrity_fallback_kind" for e in events)
    assert any(e["name"] == "some_gate_failed" and e["stage"] == "emission_debug" for e in events)
    # Large nested payload must not appear verbatim in details (slim/truncate)
    det = by_name["interaction_continuity_speaker_binding_bridge"]["details"]
    assert len(json.dumps(det)) < 800


def test_extract_candidate_events_chat_error_and_missing_keys_safe(rmg_mod):
    assert rmg_mod._extract_candidate_events([]) == []
    assert rmg_mod._extract_candidate_events([{"turn_index": 0, "ok": False}])  # no crash
    err_events = [e for e in rmg_mod._extract_candidate_events([{"turn_index": 1, "ok": False, "error": "boom"}]) if e["name"] == "chat_error"]
    assert len(err_events) == 1
    assert err_events[0]["turn"] == 2  # one-based
    # Malformed / partial debug
    rmg_mod._extract_candidate_events(
        [{"turn_index": 0, "ok": True, "debug": "not-a-dict"}]
    )
    rmg_mod._extract_candidate_events([{"turn_index": 0, "ok": True, "debug": {}}])


def test_collapse_key_events_preserves_first_seen_order(rmg_mod):
    records = [
        {"turn_index": 0, "ok": False, "error": "alpha"},
        {"turn_index": 1, "ok": False, "error": "beta"},
    ]
    collapsed = rmg_mod._collapse_key_events(records)
    errs = [e for e in collapsed if e["name"] == "chat_error"]
    assert len(errs) == 2
    assert errs[0]["turn"] == 1 and errs[1]["turn"] == 2
    assert errs[0]["details"] != errs[1]["details"]


def test_event_fingerprint_distinguishes_details(rmg_mod):
    a = {"turn": 1, "stage": "x", "name": "n", "status": "s", "details": {"k": 1}}
    b = {**a, "details": {"k": 2}}
    assert rmg_mod._event_fingerprint(a) != rmg_mod._event_fingerprint(b)


def test_collapse_key_events_dedupes_identical(rmg_mod):
    records = [{"turn_index": 0, "ok": False, "error": "x"}]
    candidates = rmg_mod._extract_candidate_events(records)
    assert sum(1 for c in candidates if c["name"] == "chat_error") == 1
    collapsed = rmg_mod._collapse_key_events(records + records)
    assert sum(1 for c in collapsed if c["name"] == "chat_error") == 1


# --- 4) Summary builder ---


def test_build_summary_stable_fields_and_defaults(rmg_mod, tmp_path):
    spec = _spec(rmg_mod, "g4")
    transcript = tmp_path / "dummy_transcript.md"
    records = [{"turn_index": 0, "ok": True}, {"turn_index": 1, "ok": True}]
    dtr = build_dead_turn_run_report(records)
    with patch.object(rmg_mod, "_git_meta", return_value=("fixture-branch", "fixture-commit")):
        summary = rmg_mod._build_summary(
            spec,
            freeform=False,
            reset_applied=True,
            records=records,
            started_utc="2026-04-09T12:00:00Z",
            transcript_path=transcript,
            raw_trace_written=True,
            event_count=7,
            dead_turn_report=dtr,
        )
    assert summary["report_version"] == rmg_mod.REPORT_VERSION
    assert summary["dead_turn_report"] == dtr
    assert summary["dead_turn_report"]["schema_version"] == "dead_turn_report_visibility.v1"
    assert summary["gauntlet_id"] == "g4"
    assert summary["label"] == spec.label
    assert summary["description"] == spec.description
    assert summary["turn_count"] == 2
    assert summary["transcript_path"] == str(transcript.resolve())
    assert summary["event_count"] == 7
    assert summary["raw_trace_written"] is True
    assert summary["operator_verdict"] is None
    assert summary["operator_notes"] is None
    assert summary["git_branch"] == "fixture-branch"
    assert summary["git_commit"] == "fixture-commit"


def test_build_summary_partial_records_safe(rmg_mod, tmp_path):
    spec = _spec(rmg_mod, "g1")
    with patch.object(rmg_mod, "_git_meta", return_value=("u", "c")):
        s = rmg_mod._build_summary(
            spec,
            True,
            False,
            [],
            started_utc="2026-01-01T00:00:00Z",
            transcript_path=tmp_path / "t.md",
            raw_trace_written=False,
            event_count=0,
        )
    assert s["turn_count"] == 0
    assert s["mode"] == "freeform"


def test_build_summary_operator_verdict_and_notes_injected(rmg_mod, tmp_path):
    spec = _spec(rmg_mod, "g1")
    transcript = tmp_path / "t.md"
    with patch.object(rmg_mod, "_git_meta", return_value=("b", "c")):
        s = rmg_mod._build_summary(
            spec,
            False,
            False,
            [{"turn_index": 0, "ok": True}],
            started_utc="2026-04-09T12:00:00Z",
            transcript_path=transcript,
            raw_trace_written=False,
            event_count=1,
            operator_verdict="PASS",
            operator_notes="test",
        )
    assert s["operator_verdict"] == "PASS"
    assert s["operator_notes"] == "test"


def test_summary_json_serializes_operator_fields(tmp_path, rmg_mod):
    spec = _spec(rmg_mod, "g2")
    transcript = tmp_path / "tr.md"
    with patch.object(rmg_mod, "_git_meta", return_value=("main", "abc")):
        payload = rmg_mod._build_summary(
            spec,
            True,
            True,
            [{"turn_index": 0, "ok": True}],
            started_utc="2026-04-09T00:00:00Z",
            transcript_path=transcript,
            raw_trace_written=True,
            event_count=3,
            operator_verdict="PARTIAL",
            operator_notes='Line with "quotes" and unicode α',
        )
    path = tmp_path / "summary.json"
    rmg_mod._json_dump(path, payload)
    raw = path.read_text(encoding="utf-8")
    loaded = json.loads(raw)
    assert loaded["operator_verdict"] == "PARTIAL"
    assert loaded["operator_notes"] == 'Line with "quotes" and unicode α'
    assert loaded["operator_verdict"] is not None
    assert json.dumps(loaded)  # round-trip valid JSON


def test_build_parser_verdict_and_notes_flags(rmg_mod):
    p = rmg_mod._build_parser()
    a = p.parse_args(["--gauntlet", "g1", "--verdict", "FAIL", "--notes", "Speaker broke"])
    assert a.gauntlet == "g1"
    assert a.verdict == "FAIL"
    assert a.notes == "Speaker broke"
    b = p.parse_args(["--gauntlet", "g3"])
    assert b.verdict is None
    assert b.notes is None


# --- 5) Snippet extraction ---


def test_extract_snippets_repair_before_after_truncated(rmg_mod):
    long_before = "B" * 800
    long_after = "A" * 800
    rec = _record_with_emission_debug(
        0,
        {
            "interaction_continuity_repair": {
                "applied": True,
                "repair_type": "continuity",
                "input_text": long_before,
                "repaired_text": long_after,
            }
        },
    )
    snips = rmg_mod._extract_snippets([rec], max_items=_SNIPPET_MAX_ITEMS, max_chars=_SNIPPET_MAX_CHARS)
    assert len(snips) == 1
    assert snips[0]["kind"] == "repair_before_after"
    assert len(snips[0]["before"] or "") <= _SNIPPET_MAX_CHARS
    assert len(snips[0]["after"] or "") <= _SNIPPET_MAX_CHARS
    assert snips[0]["before"].endswith("...")


def test_extract_snippets_engine_error(rmg_mod):
    rec = {"turn_index": 0, "ok": False, "error": "E" * 600}
    snips = rmg_mod._extract_snippets([rec])
    assert len(snips) == 1
    assert snips[0]["kind"] == "engine_error"
    assert len(snips[0]["reason"] or "") <= _SNIPPET_MAX_CHARS


def test_extract_snippets_social_fallback(rmg_mod):
    rec = {
        "turn_index": 0,
        "ok": True,
        "gm_text": "G" * 600,
        "debug": {
            "last_debug_trace": {
                "resolution": {
                    "metadata": {
                        "emission_debug": {
                            "social_emission_integrity_replaced": True,
                            "social_emission_integrity_fallback_kind": "integrity_swap",
                        }
                    }
                }
            }
        },
    }
    snips = rmg_mod._extract_snippets([rec])
    assert len(snips) == 1
    assert snips[0]["kind"] == "fallback_response"
    assert len(snips[0]["after"] or "") <= _SNIPPET_MAX_CHARS


def test_extract_snippets_suspicious_speaker_heuristic(rmg_mod):
    gm = (
        'The guard says, "Halt!" and the merchant says, "Come in!" '
        "while the crowd watches."
    )
    rec = {"turn_index": 2, "ok": True, "gm_text": gm, "debug": {}}
    snips = rmg_mod._extract_snippets([rec])
    assert len(snips) == 1
    assert snips[0]["kind"] == "suspicious_speaker_fragment"
    assert len(snips[0]["after"] or "") <= _SNIPPET_MAX_CHARS


def test_extract_snippets_max_five_and_empty_input(rmg_mod):
    rows = []
    for i in range(10):
        rows.append(
            {
                "turn_index": i,
                "ok": True,
                "gm_text": f'NPC says, "Line{i}a" and Other says, "Line{i}b" x',
                "debug": {},
            }
        )
    snips = rmg_mod._extract_snippets(rows)
    assert len(snips) == _SNIPPET_MAX_ITEMS
    assert all(len(s.get("after") or "") <= _SNIPPET_MAX_CHARS for s in snips)

    assert rmg_mod._extract_snippets([]) == []
    assert rmg_mod._extract_snippets([{"turn_index": 0, "ok": True, "gm_text": "short"}]) == []


# --- 6) Raw trace sanitization ---


def test_sanitize_raw_trace_truncates_long_strings_and_preserves_shape(rmg_mod):
    long = "z" * (_RAW_TRACE_MAX_STR + 500)
    src = {"a": [{"b": long}], "ok": True}
    out = rmg_mod._sanitize_raw_trace_payload(src, max_str=_RAW_TRACE_MAX_STR)
    assert isinstance(out["a"][0]["b"], str)
    assert len(out["a"][0]["b"]) < len(long)
    assert "truncated" in out["a"][0]["b"]
    assert src["a"][0]["b"] == long  # input not mutated
    json.dumps(out)  # serializable


def test_sanitize_raw_trace_deep_copy_no_mutation_list(rmg_mod):
    inner = ["x" * 100]
    src = {"k": inner}
    out = rmg_mod._sanitize_raw_trace_payload(src, max_str=50)
    assert out["k"][0] != inner[0] or len(out["k"][0]) <= 53
    assert inner[0] == "x" * 100


# --- 7) Shared basename consistency (simulated, no CLI run) ---


def test_simulated_run_uses_single_basename_for_all_artifacts(rmg_mod):
    base = rmg_mod._artifact_base_name(_spec(rmg_mod, "g8"), "sim_g8")
    paths = _artifact_paths(rmg_mod, base)
    assert _basename_from_paths(paths) == base
    for key, p in paths.items():
        assert p.name.startswith(f"{base}_"), key
        assert p.name.endswith(
            {
                "transcript": "_transcript.md",
                "summary": "_summary.json",
                "key_events": "_key_events.json",
                "snippets": "_snippets.json",
                "raw_trace": "_raw_trace.json",
            }[key]
        ), key


# --- Existing small helpers ---


def test_write_transcript_inserts_dead_turn_markdown_block(rmg_mod, tmp_path):
    spec = _spec(rmg_mod, "g1")
    dead_md = "## Dead turn / run validity (test report)\n\n> **DEAD TURN DETECTED — x**\n"
    path = tmp_path / "t.md"
    rmg_mod._write_transcript(
        path,
        spec=spec,
        freeform=False,
        reset_applied=False,
        records=[{"turn_index": 0, "ok": True, "player_text": "Hi", "gm_text": "Hello.", "debug": {}}],
        dead_turn_markdown_block=dead_md,
    )
    text = path.read_text(encoding="utf-8")
    assert "DEAD TURN DETECTED" in text
    assert "## Turns" in text


def test_safe_get(rmg_mod):
    assert rmg_mod._safe_get({"a": {"b": 1}}, "a", "b") == 1
    assert rmg_mod._safe_get({"a": {}}, "a", "b", default=0) == 0


def test_normalize_bool(rmg_mod):
    assert rmg_mod._normalize_bool(True) is True
    assert rmg_mod._normalize_bool("yes") is True
    assert rmg_mod._normalize_bool("OFF") is False
    assert rmg_mod._normalize_bool(None) is None
    assert rmg_mod._normalize_bool(7) is None


# --- G9–G12 registry + advisory behavioral_eval ---


def test_gauntlet_registry_includes_g1_through_g12(rmg_mod):
    assert set(rmg_mod.GAUNTLETS.keys()) == {f"g{i}" for i in range(1, 13)}


def test_g9_through_g12_axis_tags_match_spec(rmg_mod):
    assert rmg_mod.GAUNTLETS["g9"].axis_tags == ("neutrality",)
    assert rmg_mod.GAUNTLETS["g10"].axis_tags == ("escalation_correctness",)
    assert rmg_mod.GAUNTLETS["g11"].axis_tags == ("reengagement_quality",)
    assert rmg_mod.GAUNTLETS["g12"].axis_tags == ("dialogue_coherence",)
    assert rmg_mod.GAUNTLETS["g1"].axis_tags == ()


def test_build_summary_axis_tags_serialized_when_present(rmg_mod, tmp_path):
    spec = rmg_mod.GAUNTLETS["g10"]
    transcript = tmp_path / "t.md"
    with patch.object(rmg_mod, "_git_meta", return_value=("b", "c")):
        s = rmg_mod._build_summary(
            spec,
            False,
            True,
            [{"turn_index": 0, "ok": True}],
            started_utc="2026-04-09T12:00:00Z",
            transcript_path=transcript,
            raw_trace_written=False,
            event_count=0,
        )
    assert s["axis_tags"] == ["escalation_correctness"]
    assert "behavioral_eval" not in s


def test_build_summary_g1_has_no_axis_tags_key_without_tags(rmg_mod, tmp_path):
    spec = rmg_mod.GAUNTLETS["g1"]
    with patch.object(rmg_mod, "_git_meta", return_value=("b", "c")):
        s = rmg_mod._build_summary(
            spec,
            False,
            True,
            [],
            started_utc="2026-04-09T12:00:00Z",
            transcript_path=tmp_path / "t.md",
            raw_trace_written=False,
            event_count=0,
        )
    assert "axis_tags" not in s


def test_build_summary_behavioral_eval_preserved_evaluator_shape(rmg_mod, tmp_path):
    spec = rmg_mod.GAUNTLETS["g1"]
    be = {
        "schema_version": BEHAVIORAL_SCHEMA_VERSION,
        "overall_passed": True,
        "axes": {
            "neutrality": {
                "axis": "neutrality",
                "passed": True,
                "score": 2,
                "reason_codes": ["neutral_ok"],
                "summary": "ok",
                "evidence_turn_indexes": [],
            }
        },
    }
    with patch.object(rmg_mod, "_git_meta", return_value=("b", "c")):
        s = rmg_mod._build_summary(
            spec,
            False,
            True,
            [{"turn_index": 0, "ok": True, "player_text": "Hi", "gm_text": "Hello."}],
            started_utc="2026-04-09T12:00:00Z",
            transcript_path=tmp_path / "t.md",
            raw_trace_written=False,
            event_count=0,
            behavioral_eval=be,
        )
    assert s["behavioral_eval"] == be
    assert s["behavioral_eval"]["schema_version"] == BEHAVIORAL_SCHEMA_VERSION
    assert "axes" in s["behavioral_eval"] and "overall_passed" in s["behavioral_eval"]


def test_try_behavioral_eval_expected_axis_filter_single_axis(rmg_mod):
    spec = rmg_mod.GAUNTLETS["g9"]
    records = [
        {"turn_index": 0, "ok": True, "player_text": "What do I see?", "gm_text": "Quiet mist; no insults."},
    ]
    be, warn = rmg_mod.try_behavioral_eval_for_run(spec, records)
    assert warn is None
    assert be is not None
    assert be["schema_version"] == BEHAVIORAL_SCHEMA_VERSION
    assert set(be["axes"]) == {"neutrality"}


def test_try_behavioral_eval_g1_runs_all_axes(rmg_mod):
    spec = rmg_mod.GAUNTLETS["g1"]
    records = [
        {"turn_index": 0, "ok": True, "player_text": "Hi", "gm_text": "Hello traveler.", "metadata": {}},
    ]
    be, warn = rmg_mod.try_behavioral_eval_for_run(spec, records)
    assert warn is None
    assert be is not None
    assert set(be["axes"]) == {"dialogue_coherence", "escalation_correctness", "neutrality", "reengagement_quality"}


def test_try_behavioral_eval_accepts_gauntlet_style_snapshot_rows(rmg_mod):
    from tests.helpers.transcript_runner import snapshot_from_chat_payload

    spec = rmg_mod.GAUNTLETS["g12"]

    def _payload(gm: str, scene_id: str | None = "gate") -> dict:
        scene_block: dict = {}
        if scene_id:
            scene_block = {"scene": {"id": scene_id}}
        return {
            "gm_output": {"player_facing_text": gm},
            "scene": {"scene": scene_block.get("scene", {})},
            "session": {"scene_state": {}},
            "resolution": None,
            "journal": None,
            "world": None,
        }

    rows = [
        snapshot_from_chat_payload(0, "What is posted?", _payload("Orders are posted; curfew is strict.")),
        snapshot_from_chat_payload(1, "And fines?", _payload("Coin or labor; clerk records both.")),
    ]
    be, warn = rmg_mod.try_behavioral_eval_for_run(spec, rows)
    assert warn is None
    assert be is not None
    assert set(be["axes"]) == {"dialogue_coherence"}


def test_try_behavioral_eval_warning_non_fatal_on_evaluator_error(rmg_mod, monkeypatch):
    spec = rmg_mod.GAUNTLETS["g1"]

    def _boom(*_a, **_k):
        raise RuntimeError("simulated")

    monkeypatch.setattr(rmg_mod, "evaluate_behavioral_gauntlet", _boom)
    be, warn = rmg_mod.try_behavioral_eval_for_run(spec, [{"turn_index": 0, "ok": True}])
    assert be is None
    assert warn is not None
    assert "behavioral_eval skipped" in warn
    assert "RuntimeError" in warn


def test_try_behavioral_eval_valueerror_axis_tags_compact_warning(rmg_mod):
    spec = rmg_mod.GauntletSpec(
        "gx",
        "x",
        "d",
        ("one",),
        axis_tags=("not_a_real_axis",),
    )
    be, warn = rmg_mod.try_behavioral_eval_for_run(spec, [{"turn_index": 0, "ok": True, "player_text": "a", "gm_text": "b"}])
    assert be is None
    assert warn is not None
    assert "behavioral_eval axis_tags" in warn


def test_parser_accepts_g12(rmg_mod):
    p = rmg_mod._build_parser()
    a = p.parse_args(["--gauntlet", "g12"])
    assert a.gauntlet == "g12"
