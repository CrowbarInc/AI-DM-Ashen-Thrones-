"""Regression tests for ``tools/aggregate_manual_gauntlets.py`` (aggregation contract only)."""

from __future__ import annotations

import importlib.util
import io
import json
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def agg_mod():
    path = ROOT / "tools" / "aggregate_manual_gauntlets.py"
    name = "_aggregate_manual_gauntlets_test_load"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_summary(parent: Path, base: str, payload: dict) -> Path:
    p = parent / f"{base}_summary.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _pipeline_after_normalize(
    agg_mod,
    runs_raw: list[dict],
    *,
    gauntlet_id: str | None = None,
    objective: str | None = None,
    verdict: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Mirror main(): filter → sort → limit (internal fields preserved)."""
    runs = agg_mod.filter_runs(
        runs_raw,
        gauntlet_id=gauntlet_id,
        objective=objective,
        verdict=verdict,
    )
    runs = agg_mod.sort_runs_newest_first(runs)
    if limit is not None and limit >= 0:
        runs = runs[:limit]
    return runs


# --- 1) Recursive summary discovery ---


def test_discover_summary_paths_only_summary_suffix_recursive_sorted(agg_mod, tmp_path: Path):
    root = tmp_path / "artifacts"
    (root / "a" / "nested").mkdir(parents=True)
    (root / "noise.txt").write_text("x", encoding="utf-8")
    (root / "foo_summary.json").write_text("{}", encoding="utf-8")
    (root / "a" / "nested" / "bar_summary.json").write_text("{}", encoding="utf-8")
    # Must not end with ``_summary.json`` or rglob("*_summary.json") will match (e.g. ``not_a_summary.json``).
    (root / "a" / "summary.json").write_text("{}", encoding="utf-8")
    (root / "a" / "x_summary.md").write_text("", encoding="utf-8")

    found = agg_mod.discover_summary_paths(root)
    assert [p.name for p in found] == ["bar_summary.json", "foo_summary.json"]
    assert all(p.name.endswith("_summary.json") for p in found)


def test_discover_summary_paths_missing_dir_returns_empty(agg_mod, tmp_path: Path):
    assert agg_mod.discover_summary_paths(tmp_path / "nope") == []


# --- 2) Sibling inference ---


def test_infer_sibling_paths_suffixes_and_shared_basename(agg_mod, tmp_path: Path):
    summary = tmp_path / "run1_g5_summary.json"
    sibs = agg_mod.infer_sibling_paths(summary)
    assert sibs["base"] == "run1_g5"
    assert sibs["summary"] == summary
    assert sibs["key_events"] == tmp_path / "run1_g5_key_events.json"
    assert sibs["snippets"] == tmp_path / "run1_g5_snippets.json"
    assert sibs["transcript"] == tmp_path / "run1_g5_transcript.md"


def test_artifact_base_from_summary_path(agg_mod, tmp_path: Path):
    p = tmp_path / "abc_summary.json"
    assert agg_mod.artifact_base_from_summary_path(p) == "abc"
    with pytest.raises(ValueError):
        agg_mod.artifact_base_from_summary_path(tmp_path / "x.json")


# --- 3) Normalization + legacy notes ---


def test_normalize_run_bundle_modern_operator_notes_and_verdict(agg_mod, tmp_path: Path):
    sp = _write_summary(
        tmp_path,
        "m1",
        {
            "gauntlet_id": "G5",
            "label": "L",
            "operator_verdict": "PASS",
            "operator_notes": "from operator_notes",
            "notes": "legacy should not win",
            "started_utc": "2026-01-02T00:00:00Z",
            "turn_count": 3,
        },
    )
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    assert w == []
    assert r is not None
    assert r["gauntlet_id"] == "G5"
    assert r["operator_verdict"] == "PASS"
    assert r["operator_notes"] == "from operator_notes"
    assert r["turn_count"] == 3
    assert r["started_utc"] == "2026-01-02T00:00:00Z"


def test_normalize_run_bundle_legacy_notes_fallback(agg_mod, tmp_path: Path):
    sp = _write_summary(
        tmp_path,
        "leg",
        {"notes": "only legacy", "operator_verdict": "FAIL"},
    )
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    assert w == []
    assert r is not None
    assert r["operator_notes"] == "only legacy"


def test_normalize_run_bundle_partial_missing_optionals(agg_mod, tmp_path: Path):
    sp = _write_summary(tmp_path, "p1", {})
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    assert w == []
    assert r is not None
    assert r["gauntlet_id"] == ""
    assert r["label"] == ""
    assert r["description"] == ""
    assert r["operator_verdict"] is None
    assert r["operator_notes"] is None
    assert r["turn_count"] is None
    assert r["started_utc"] is None
    assert r["event_count"] == 0


def test_filter_gauntlet_id_case_insensitive_documented_semantics(agg_mod, tmp_path: Path):
    """Docs: compare filter to run gauntlet_id lowercased; normalize preserves stored casing."""
    sp = _write_summary(tmp_path, "g", {"gauntlet_id": "G5"})
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    assert r["gauntlet_id"] == "G5"
    out = agg_mod.filter_runs([r], gauntlet_id="g5", objective=None, verdict=None)
    assert len(out) == 1


def test_normalize_transcript_path_from_sibling_when_summary_empty(agg_mod, tmp_path: Path):
    base = "t1"
    sp = _write_summary(tmp_path, base, {})
    (tmp_path / f"{base}_transcript.md").write_text("ic", encoding="utf-8")
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    assert r["transcript_path"] == str((tmp_path / f"{base}_transcript.md").resolve())


def test_normalize_event_count_from_key_events_array_length(agg_mod, tmp_path: Path):
    base = "e1"
    sp = _write_summary(tmp_path, base, {})
    (tmp_path / f"{base}_key_events.json").write_text(json.dumps([{"name": "a"}, {}]), encoding="utf-8")
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    assert r["event_count"] == 2


# --- 4) Filter semantics + pipeline order (filter → sort → limit) ---


def test_filter_runs_gauntlet_objective_verdict_semantics(agg_mod):
    runs = [
        {"gauntlet_id": "g1", "label": "Alpha", "description": "", "operator_verdict": "PASS"},
        {"gauntlet_id": "g2", "label": "Beta", "description": "Gamma", "operator_verdict": "fail"},
        {"gauntlet_id": "g1", "label": "X", "description": "needle here", "operator_verdict": "FAIL"},
    ]
    out = agg_mod.filter_runs(runs, gauntlet_id="G1", objective="needle", verdict="fail")
    assert [r["label"] for r in out] == ["X"]


def test_filter_runs_matches_manual_gauntlet_then_objective_then_verdict(agg_mod):
    """Lock documented filter stages (conjunctive; order matches ``filter_runs`` implementation)."""

    def manual(runs, *, gauntlet_id, objective, verdict):
        out = runs
        if gauntlet_id is not None:
            gid = gauntlet_id.strip().lower()
            out = [r for r in out if r.get("gauntlet_id", "").lower() == gid]
        if objective is not None:
            sub = objective.casefold()
            out = [
                r
                for r in out
                if sub in (r.get("label") or "").casefold()
                or sub in (r.get("description") or "").casefold()
            ]
        if verdict is not None:
            vwant = verdict.strip().casefold()
            out = [r for r in out if (r.get("operator_verdict") or "").strip().casefold() == vwant]
        return out

    runs = [
        {"gauntlet_id": "G1", "label": "L", "description": "D", "operator_verdict": "pass"},
        {"gauntlet_id": "g2", "label": "L", "description": "x", "operator_verdict": "FAIL"},
    ]
    for gid, obj, ver in [
        ("g1", None, None),
        (None, "d", None),
        (None, None, "Pass"),
        ("g2", "x", "fail"),
    ]:
        assert agg_mod.filter_runs(runs, gauntlet_id=gid, objective=obj, verdict=ver) == manual(
            runs, gauntlet_id=gid, objective=obj, verdict=ver
        )


def test_filter_runs_verdict_trim_and_casefold_exact(agg_mod):
    runs = [{"gauntlet_id": "g", "label": "l", "description": "", "operator_verdict": "  pass "}]
    assert len(agg_mod.filter_runs(runs, gauntlet_id=None, objective=None, verdict="PASS")) == 1
    assert len(agg_mod.filter_runs(runs, gauntlet_id=None, objective=None, verdict="pass")) == 1
    assert len(agg_mod.filter_runs(runs, gauntlet_id=None, objective=None, verdict="PARTIAL")) == 0


def test_pipeline_sort_then_limit_not_limit_before_sort(agg_mod, tmp_path: Path):
    """If limit were applied before sort, the newest-of-two would differ for this fixture."""
    bases = [("old", "2020-01-01T00:00:00Z"), ("new", "2026-01-01T00:00:00Z")]
    raw: list[dict] = []
    for name, su in bases:
        sp = _write_summary(
            tmp_path,
            name,
            {"gauntlet_id": "g", "label": name, "started_utc": su, "operator_verdict": "PASS"},
        )
        w: list[str] = []
        raw.append(agg_mod.normalize_run_bundle(sp, warnings=w))
    raw = [r for r in raw if r]
    final = _pipeline_after_normalize(agg_mod, raw, limit=1)
    assert len(final) == 1
    assert final[0]["label"] == "new"

    wrong_first = raw[:1]
    assert wrong_first[0]["label"] == "old"


# --- 5) Sorting: started_utc vs mtime fallback ---


def test_sort_runs_newest_first_by_started_utc(agg_mod):
    runs = [
        {"started_utc": "2026-01-01T00:00:00Z", "_sort_mtime": 1.0, "gauntlet_id": "g"},
        {"started_utc": "2026-06-01T00:00:00Z", "_sort_mtime": 999.0, "gauntlet_id": "g"},
    ]
    s = agg_mod.sort_runs_newest_first(runs)
    assert [r["started_utc"] for r in s] == ["2026-06-01T00:00:00Z", "2026-01-01T00:00:00Z"]


def test_sort_runs_fallback_mtime_when_started_missing(agg_mod):
    old = {"started_utc": None, "_sort_mtime": 100.0, "k": "old"}
    new = {"started_utc": None, "_sort_mtime": 200.0, "k": "new"}
    s = agg_mod.sort_runs_newest_first([old, new])
    assert [r["k"] for r in s] == ["new", "old"]


def test_sort_runs_invalid_started_utc_falls_back_to_mtime(agg_mod):
    hi = {"started_utc": "not-a-date", "_sort_mtime": 500.0, "k": "hi"}
    lo = {"started_utc": "also-bad", "_sort_mtime": 100.0, "k": "lo"}
    s = agg_mod.sort_runs_newest_first([lo, hi])
    assert [r["k"] for r in s] == ["hi", "lo"]


def test_sort_stable_enough_same_key_preserves_relative_order(agg_mod):
    """sorted() is stable; equal keys keep input order."""
    a = {"started_utc": "2026-01-01T00:00:00Z", "_sort_mtime": 1.0, "id": "a"}
    b = {"started_utc": "2026-01-01T00:00:00Z", "_sort_mtime": 1.0, "id": "b"}
    s = agg_mod.sort_runs_newest_first([a, b])
    assert [r["id"] for r in s] == ["a", "b"]


# --- 6) Metrics ---


def test_compute_metrics_structure_and_values(agg_mod, tmp_path: Path):
    s1 = _write_summary(
        tmp_path,
        "m_a",
        {
            "gauntlet_id": "g1",
            "operator_verdict": "pass",
            "turn_count": 4,
            "started_utc": "2026-01-02T00:00:00Z",
            "event_count": 2,
        },
    )
    sn = tmp_path / "m_a_snippets.json"
    sn.write_text(json.dumps([{"kind": "k"}]), encoding="utf-8")
    w: list[str] = []
    r1 = agg_mod.normalize_run_bundle(s1, warnings=w)
    s2 = _write_summary(
        tmp_path,
        "m_b",
        {
            "gauntlet_id": "g1",
            "operator_verdict": "FAIL",
            "turn_count": 2,
            "started_utc": "2026-01-10T00:00:00Z",
            "event_count": 0,
        },
    )
    r2 = agg_mod.normalize_run_bundle(s2, warnings=w)
    runs = [r1, r2]
    m = agg_mod.compute_metrics(runs)
    assert m["total_runs"] == 2
    assert m["runs_with_verdict"] == 2
    assert m["verdict_counts"] == {"FAIL": 1, "PASS": 1}
    assert m["unique_gauntlet_ids"] == ["g1"]
    assert m["average_turn_count"] == 3.0
    assert m["runs_with_events"] == 1
    assert m["runs_with_snippets"] == 1
    assert m["date_range_covered"]["min"] == "2026-01-02T00:00:00Z"
    assert m["date_range_covered"]["max"] == "2026-01-10T00:00:00Z"


def test_compute_metrics_empty_turns_and_no_verdict(agg_mod, tmp_path: Path):
    sp = _write_summary(tmp_path, "z", {"gauntlet_id": "", "operator_verdict": ""})
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    m = agg_mod.compute_metrics([r])
    assert m["total_runs"] == 1
    assert m["runs_with_verdict"] == 0
    assert m["verdict_counts"] == {}
    assert m["unique_gauntlet_ids"] == []
    assert m["average_turn_count"] is None
    assert m["runs_with_events"] == 0


# --- 7) Event rollup ---


def test_rollup_key_events_counts_and_no_full_payload(agg_mod, tmp_path: Path):
    base = "ke"
    sp = _write_summary(tmp_path, base, {"gauntlet_id": "g"})
    ke = tmp_path / f"{base}_key_events.json"
    ke.write_text(
        json.dumps(
            [
                {"name": "evt_a", "stage": "s1"},
                {"name": "evt_a", "stage": "s2"},
                {"name": "", "stage": "  "},
                "not-a-dict",
            ]
        ),
        encoding="utf-8",
    )
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    roll = agg_mod.rollup_key_events([r], warnings=w)
    assert roll["by_name"] == {"evt_a": 2}
    assert roll["by_stage"] == {"s1": 1, "s2": 1}
    dumped = json.dumps(roll)
    assert '"runs"' not in dumped and "raw_events" not in dumped
    assert list(roll.keys()) == ["by_name", "by_stage"]


def test_rollup_key_events_malformed_json_warns_and_continues(agg_mod, tmp_path: Path):
    b1, b2 = "k1", "k2"
    s1 = _write_summary(tmp_path, b1, {})
    s2 = _write_summary(tmp_path, b2, {})
    (tmp_path / f"{b1}_key_events.json").write_text("{", encoding="utf-8")
    (tmp_path / f"{b2}_key_events.json").write_text(json.dumps([{"name": "ok", "stage": "x"}]), encoding="utf-8")
    w: list[str] = []
    r1 = agg_mod.normalize_run_bundle(s1, warnings=w)
    r2 = agg_mod.normalize_run_bundle(s2, warnings=w)
    roll = agg_mod.rollup_key_events([r1, r2], warnings=w)
    assert any("invalid JSON" in x for x in w)
    assert roll["by_name"]["ok"] == 1


def test_rollup_key_events_wrong_type_root_warns(agg_mod, tmp_path: Path):
    base = "kt"
    sp = _write_summary(tmp_path, base, {})
    (tmp_path / f"{base}_key_events.json").write_text(json.dumps({"not": "array"}), encoding="utf-8")
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    roll = agg_mod.rollup_key_events([r], warnings=w)
    assert any("not an array" in x for x in w)
    assert roll["by_name"] == {}


# --- 8) Markdown structure (broad) ---


def test_render_markdown_groups_verdict_order_and_caps(agg_mod, tmp_path: Path):
    gdir = tmp_path / "g"
    gdir.mkdir()
    bases = [
        ("r_pass", "PASS", "2026-01-03T00:00:00Z", "g1"),
        ("r_fail", "FAIL", "2026-01-02T00:00:00Z", "g1"),
        ("r_part", "PARTIAL", "2026-01-01T00:00:00Z", "g1"),
        ("r_unk", None, "2026-01-04T00:00:00Z", ""),
    ]
    runs: list[dict] = []
    for base, verdict, su, gid in bases:
        sp = _write_summary(
            gdir,
            base,
            {
                "gauntlet_id": gid,
                "label": base,
                "operator_verdict": verdict,
                "started_utc": su,
                "operator_notes": "note" if base == "r_fail" else None,
            },
        )
        w: list[str] = []
        runs.append(agg_mod.normalize_run_bundle(sp, warnings=w))

    agg = {
        "generated_utc": "2026-01-01T00:00:00Z",
        "source_dir": str(gdir),
        "metrics": {"total_runs": len(runs), "verdict_counts": {"FAIL": 1}},
        "filters": {},
        "event_rollup": {
            "by_name": {f"n{i}": 1 for i in range(20)},
            "by_stage": {f"s{i}": 1 for i in range(20)},
        },
    }
    w: list[str] = []
    md = agg_mod.render_markdown(agg, runs=runs, include_snippets=False, warnings=w)
    assert "## Runs by gauntlet" in md
    fail_i = md.index("**FAIL**")
    part_i = md.index("**PARTIAL**")
    pass_i = md.index("**PASS**")
    assert fail_i < part_i < pass_i
    assert "### `(unknown)`" in md
    assert "## Operator notes" in md
    assert "note" in md
    by_name_lines = [ln for ln in md.splitlines() if ln.startswith("- `n")]
    by_stage_lines = [ln for ln in md.splitlines() if ln.startswith("- `s")]
    assert len(by_name_lines) <= 15
    assert len(by_stage_lines) <= 15


def test_render_markdown_snippet_sampling_caps(agg_mod, tmp_path: Path):
    """At most 8 examples, 5 runs, 2 snippets per run — without asserting exact prose."""
    runs: list[dict] = []
    for i in range(6):
        base = f"sn{i}"
        sp = _write_summary(
            tmp_path,
            base,
            {"gauntlet_id": "g", "label": base, "operator_verdict": "PASS", "started_utc": "2026-01-01T00:00:00Z"},
        )
        sn = tmp_path / f"{base}_snippets.json"
        sn.write_text(json.dumps([{"kind": "k", "turn": 1, "reason": "r"}] * 5), encoding="utf-8")
        w: list[str] = []
        runs.append(agg_mod.normalize_run_bundle(sp, warnings=w))

    agg = {
        "generated_utc": "x",
        "source_dir": str(tmp_path),
        "metrics": {"total_runs": len(runs)},
        "filters": {},
        "event_rollup": {},
    }
    w: list[str] = []
    md = agg_mod.render_markdown(agg, runs=runs, include_snippets=True, warnings=w)
    assert "## Notable snippets (sampled)" in md
    bullet_snippets = [ln for ln in md.splitlines() if ln.startswith("- Turn ")]
    assert len(bullet_snippets) <= 8
    h3_snip = [ln for ln in md.splitlines() if ln.startswith("### ") and "_snippets.json" in ln]
    assert len(h3_snip) <= 5


def test_render_markdown_warnings_list_capped_at_50(agg_mod):
    agg = {"generated_utc": "x", "source_dir": "y", "metrics": {"total_runs": 0}, "filters": {}, "event_rollup": {}}
    warnings = [f"warn-{i:03d}" for i in range(55)]
    md = agg_mod.render_markdown(agg, runs=[], include_snippets=False, warnings=warnings)
    assert "## Warnings" in md
    listed = [ln for ln in md.splitlines() if ln.startswith("- warn-")]
    assert len(listed) == 50
    assert "5 more" in md


# --- 9) Warnings / resilience ---


def test_bad_summary_skips_run_with_warning(agg_mod, tmp_path: Path):
    bad = tmp_path / "bad_summary.json"
    bad.write_text("{", encoding="utf-8")
    good = _write_summary(tmp_path, "ok", {"gauntlet_id": "g"})
    w: list[str] = []
    rb = agg_mod.normalize_run_bundle(bad, warnings=w)
    rg = agg_mod.normalize_run_bundle(good, warnings=w)
    assert rb is None
    assert rg is not None
    assert any("invalid JSON" in x for x in w)


def test_bad_optional_json_warns_missing_sibling_silent(agg_mod, tmp_path: Path):
    base = "opt"
    sp = _write_summary(tmp_path, base, {"gauntlet_id": "g"})
    (tmp_path / f"{base}_key_events.json").write_text("not json", encoding="utf-8")
    w: list[str] = []
    r = agg_mod.normalize_run_bundle(sp, warnings=w)
    assert r["snippets_path"] is None
    assert any("invalid JSON" in x or "invalid" in x.lower() for x in w)

    w2: list[str] = []
    agg_mod.rollup_key_events([r], warnings=w2)
    assert any("invalid JSON" in x for x in w2)


def test_load_snippets_list_malformed_warns_not_abort(agg_mod, tmp_path: Path):
    p = tmp_path / "x_snippets.json"
    p.write_text("{", encoding="utf-8")
    w: list[str] = []
    assert agg_mod.load_snippets_list(p, w) == []
    assert any("invalid JSON" in x for x in w)


def test_load_snippets_wrong_type_warns(agg_mod, tmp_path: Path):
    p = tmp_path / "y_snippets.json"
    p.write_text(json.dumps({}), encoding="utf-8")
    w: list[str] = []
    assert agg_mod.load_snippets_list(p, w) == []
    assert any("not an array" in x for x in w)


# --- 10) Output file creation ---


def test_main_writes_json_and_md_filenames_no_colons_json_only_skips_md(agg_mod, tmp_path: Path):
    art = tmp_path / "in"
    out = tmp_path / "out"
    art.mkdir()
    _write_summary(art, "one", {"gauntlet_id": "g", "operator_verdict": "PASS"})

    stamp_re_json = re.compile(r"manual_gauntlet_aggregate_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z)\.json$")
    stamp_re_md = re.compile(r"manual_gauntlet_aggregate_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z)\.md$")

    rc = agg_mod.main(["--artifacts-dir", str(art), "--output-dir", str(out)])
    assert rc == 0
    json_files = list(out.glob("manual_gauntlet_aggregate_*.json"))
    md_files = list(out.glob("manual_gauntlet_aggregate_*.md"))
    assert len(json_files) == 1
    assert len(md_files) == 1
    assert stamp_re_json.search(json_files[0].name)
    assert stamp_re_md.search(md_files[0].name)
    assert ":" not in json_files[0].name
    payload = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", payload["generated_utc"])

    out2 = tmp_path / "out2"
    rc2 = agg_mod.main(["--artifacts-dir", str(art), "--output-dir", str(out2), "--json-only"])
    assert rc2 == 0
    assert list(out2.glob("*.md")) == []


# --- 11) Light CLI wiring ---


def test_main_filters_limit_stdout_include_flags(agg_mod, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    art = tmp_path / "a"
    art.mkdir()
    _write_summary(art, "a1", {"gauntlet_id": "g1", "label": "L1", "operator_verdict": "PASS", "started_utc": "2026-02-01T00:00:00Z"})
    _write_summary(art, "a2", {"gauntlet_id": "g2", "label": "L2", "operator_verdict": "FAIL", "started_utc": "2026-03-01T00:00:00Z"})
    out = tmp_path / "rep"
    buf = io.StringIO()
    fixed = __import__("datetime")
    class _FixedDT(fixed.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.datetime(2026, 4, 10, 12, 0, 0, tzinfo=fixed.timezone.utc)

    monkeypatch.setattr(agg_mod, "datetime", _FixedDT)
    with redirect_stdout(buf):
        rc = agg_mod.main(
            [
                "--artifacts-dir",
                str(art),
                "--output-dir",
                str(out),
                "--gauntlet-id",
                "g2",
                "--verdict",
                "fail",
                "--limit",
                "5",
                "--include-events",
                "--include-snippets",
                "--stdout",
            ]
        )
    assert rc == 0
    text = buf.getvalue()
    assert "Runs analyzed: 1" in text
    assert "Verdicts:" in text
    data = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
    assert data["filters"]["gauntlet_id"] == "g2"
    assert data["filters"]["verdict"] == "fail"
    assert data["filters"]["limit"] == 5
    assert len(data["runs"]) == 1
    assert data["runs"][0]["gauntlet_id"] == "g2"


def test_main_objective_filter(agg_mod, tmp_path: Path):
    art = tmp_path / "a"
    art.mkdir()
    _write_summary(art, "x", {"gauntlet_id": "g", "label": "alpha", "description": "beta", "operator_verdict": "PASS"})
    _write_summary(art, "y", {"gauntlet_id": "g", "label": "gamma", "description": "delta", "operator_verdict": "PASS"})
    out = tmp_path / "o"
    agg_mod.main(["--artifacts-dir", str(art), "--output-dir", str(out), "--objective", "BETA", "--json-only"])
    data = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
    assert data["metrics"]["total_runs"] == 1
    assert data["runs"][0]["label"] == "alpha"
