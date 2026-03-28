#!/usr/bin/env python3
"""Static + pytest inventory for tests/. Writes tests/test_inventory.json.

Run from repo root: python tools/test_audit.py
Requires: same interpreter used for pytest (py -3 tools/test_audit.py).
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
OUT_JSON = TESTS / "test_inventory.json"

# Feature-area keywords (first match wins for primary label; all matches kept in feature_areas)
FEATURE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("transcript regression", ("transcript", "gauntlet", "runner_smoke", "session_log")),
    ("mixed-state recovery", ("mixed_state", "recovery_regressions")),
    ("retry", ("retry", "terminal", "prioritize", "force_terminal")),
    ("fallback", ("fallback", "uncertainty", "minimal", "repair")),
    ("social continuity", ("continuity", "interlocutor", "engagement", "social_target", "dialogue_interaction")),
    ("routing", ("route", "routing", "dialogue_lock", "directed_social", "intent", "parser")),
    ("clue system", ("clue", "discover", "inference")),
    ("lead extraction", ("lead", "contextual_lead", "remember_recent")),
    ("resolution/emission", ("resolution", "emission", "exploration_resolution", "engine_updates")),
    ("legality/sanitizer", ("sanitizer", "legality", "guard", "spoiler", "validator_voice")),
    ("world/state", ("world_state", "campaign", "save_load", "storage", "scene_graph")),
    ("combat/skill", ("combat", "skill_check", "adjudication")),
]

FILE_BUCKET_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("transcript_gauntlet", ("test_transcript_gauntlet_",)),
    ("regression", ("_regressions.py", "test_transcript_regression.py", "test_gauntlet_regressions.py")),
]


def _file_primary_bucket(rel: str) -> str:
    name = Path(rel).name
    for bucket, subs in FILE_BUCKET_RULES:
        if any(s in name for s in subs):
            return bucket
    return "mixed/unclear"


def _refine_bucket_for_test(file_bucket: str, nodeid: str, body: str) -> str:
    """Narrow mixed/unclear using nodeid and body heuristics."""
    if file_bucket != "mixed/unclear":
        return file_bucket
    low = nodeid.lower()
    if "tmp_path" in body or "TestClient" in body or "client.post" in body or "client.get" in body:
        return "integration"
    if "monkeypatch" in body and ("api" in low or "call_gpt" in body):
        return "integration"
    # Default small helpers / pure asserts → unit
    if len(body) < 800 and "TestClient" not in body and "tmp_path" not in body:
        return "unit"
    return "integration"


FEATURE_LINE_RE = re.compile(r"^\s*#\s*feature:\s*(.+?)\s*$", re.IGNORECASE)
MARK_OWNERSHIP_RE = re.compile(r"^\s*@pytest\.mark\.(\w+)\s*")

# Optional ownership tags (pytest markers or "# feature: a, b" comments); map to inventory feature labels.
OWNERSHIP_TAGS = frozenset(
    {"routing", "retry", "fallback", "social", "continuity", "clues", "leads", "emission", "legality"}
)
TAG_TO_AREA: dict[str, str] = {
    "routing": "routing",
    "retry": "retry",
    "fallback": "fallback",
    "social": "social continuity",
    "continuity": "social continuity",
    "clues": "clue system",
    "leads": "lead extraction",
    "emission": "resolution/emission",
    "legality": "legality/sanitizer",
}


def _parse_feature_line(line: str) -> list[str]:
    m = FEATURE_LINE_RE.match(line)
    if not m:
        return []
    return [p.strip().lower() for p in m.group(1).split(",") if p.strip().lower() in OWNERSHIP_TAGS]


def _parse_module_default_feature(src: str) -> list[str]:
    """First `# feature:` before any top-level `def test_` applies to tests without a per-test tag."""
    for line in src.splitlines():
        if re.match(r"^def test_", line):
            return []
        if FEATURE_LINE_RE.match(line):
            return _parse_feature_line(line)
    return []


def _parse_explicit_ownership(src: str, base_name: str) -> list[str]:
    lines = src.splitlines()
    def_idx = None
    for i, line in enumerate(lines):
        if re.match(rf"^def {re.escape(base_name)}\s*\(", line):
            def_idx = i
            break
    if def_idx is None:
        return []

    feature_tags: list[str] = []
    mark_tags: list[str] = []
    i = def_idx - 1
    while i >= 0:
        line = lines[i]
        s = line.strip()
        if s == "":
            i -= 1
            continue
        if FEATURE_LINE_RE.match(line):
            feature_tags = _parse_feature_line(line)
            break
        if s.startswith("@pytest.mark."):
            m = MARK_OWNERSHIP_RE.match(line)
            if m and m.group(1) in OWNERSHIP_TAGS:
                mark_tags.insert(0, m.group(1))
            i -= 1
            continue
        if s.startswith("#"):
            i -= 1
            continue
        if s.startswith("@"):
            i -= 1
            continue
        break

    ordered: list[str] = []
    for t in feature_tags + mark_tags:
        if t not in ordered:
            ordered.append(t)
    return ordered


def _heuristic_feature_areas(nodeid: str) -> list[str]:
    low = nodeid.lower().replace("\\", "/")
    found: list[str] = []
    for label, kws in FEATURE_RULES:
        if any(k in low for k in kws):
            found.append(label)
    if not found:
        found.append("general")
    return found


def _feature_areas(nodeid: str, src: str, base_name: str) -> list[str]:
    explicit = _parse_explicit_ownership(src, base_name)
    if not explicit:
        explicit = _parse_module_default_feature(src)
    if not explicit:
        return _heuristic_feature_areas(nodeid)

    mapped: list[str] = []
    for t in explicit:
        a = TAG_TO_AREA.get(t)
        if a and a not in mapped:
            mapped.append(a)
    if not mapped:
        return _heuristic_feature_areas(nodeid)
    for a in _heuristic_feature_areas(nodeid):
        if a == "general":
            continue
        if a not in mapped:
            mapped.append(a)
    return mapped


def _historical(nodeid: str, file_bucket: str) -> bool:
    low = nodeid.lower()
    if file_bucket == "regression" or file_bucket == "transcript_gauntlet":
        return True
    return any(
        x in low
        for x in (
            "regression",
            "gauntlet",
            "runner_followup",
            "historical",
            "repro",
        )
    )


def _assertion_style(body: str) -> str:
    # Heuristic: long string equality / substring on narrative fields → prose-sensitive
    long_str_eq = len(re.findall(r'==\s*["\'][^"\']{25,}["\']', body))
    in_literal = len(re.findall(r'\bin\s+["\'][^"\']+["\']', body))
    structural = len(re.findall(r"\.get\(|isinstance\(|in response|status_code|keys?\(", body))
    if long_str_eq >= 2 or ("player_facing_text" in body and in_literal >= 1):
        return "prose-sensitive"
    if long_str_eq >= 1 or in_literal >= 2:
        return "mixed"
    if structural >= 3 and long_str_eq == 0:
        return "structural"
    return "behavioral"


def _brittleness(file_bucket: str, body: str, assertion_style: str) -> str:
    if file_bucket == "transcript_gauntlet":
        return "high"
    if file_bucket == "regression" and ("transcript" in body.lower() or "run_" in body or "turn" in body):
        return "high"
    if assertion_style == "prose-sensitive":
        return "high"
    if file_bucket == "regression" or "mock_gpt" in body or "call_gpt" in body:
        return "medium"
    if assertion_style == "mixed":
        return "medium"
    return "low"


def _ast_test_defs(path: Path) -> tuple[list[str], list[str]]:
    """Return (all def names in order, list of names that appear more than once)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            names.append(node.name)
    c = Counter(names)
    dups = [n for n, k in c.items() if k > 1]
    return names, dups


def _find_function_body(src: str, func_name: str) -> str:
    """Return source of test function; empty if not found."""
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            lines = src.splitlines()
            end = getattr(node, "end_lineno", None) or node.lineno
            return "\n".join(lines[node.lineno - 1 : end])
    return ""


def _collect_pytest_nodeids() -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(TESTS), "--collect-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "pytest collect failed")
    out: list[str] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("tests/test_") and "::" in line:
            out.append(line)
    return out


def _parse_nodeid(line: str) -> tuple[str, str, str, bool]:
    """file_part, full_name, base_name, is_parametrized."""
    file_part, rest = line.split("::", 1)
    is_param = "[" in rest and rest.rstrip().endswith("]")
    base = rest.split("[", 1)[0]
    return file_part, rest, base, is_param


def main() -> None:
    nodeids = _collect_pytest_nodeids()
    by_file: dict[str, list[str]] = defaultdict(list)
    for nid in nodeids:
        fp, _, _, _ = _parse_nodeid(nid)
        by_file[fp].append(nid)

    ast_total = 0
    dup_report: list[dict] = []
    for p in sorted(TESTS.glob("test_*.py")):
        rel = p.as_posix()
        if not rel.startswith("tests/"):
            rel = "tests/" + p.name
        names, dups = _ast_test_defs(p)
        ast_total += len(names)
        if dups:
            dup_report.append(
                {
                    "file": rel,
                    "raw_def_count": len(names),
                    "unique_name_count": len(set(names)),
                    "shadowed_duplicate_names": dups,
                }
            )

    # Cross-file base name index for redundancy hints
    base_locations: dict[str, list[str]] = defaultdict(list)
    for nid in nodeids:
        fp, _, base, _ = _parse_nodeid(nid)
        base_locations[base].append(fp)

    tests_out: list[dict] = []
    for nid in nodeids:
        fp, full_name, base, is_param = _parse_nodeid(nid)
        path = TESTS / Path(fp).name
        src = path.read_text(encoding="utf-8")
        body = _find_function_body(src, base)
        file_bucket = _file_primary_bucket(fp)
        bucket = _refine_bucket_for_test(file_bucket, nid, body)
        areas = _feature_areas(nid, src, base)
        assertion = _assertion_style(body)
        brittle = _brittleness(bucket, body, assertion)
        locs = base_locations[base]
        redundancy = "likely_unique"
        if len(set(locs)) > 1:
            redundancy = "possible_overlap"
        # Same name collected from one file multiple times shouldn't happen; parametrized differs in [..]
        hist = _historical(nid, file_bucket)
        tests_out.append(
            {
                "nodeid": nid,
                "file": fp,
                "name": full_name,
                "base_name": base,
                "parametrized": is_param,
                "primary_bucket": bucket,
                "feature_areas": areas,
                "historically_motivated": hist,
                "assertion_style": assertion,
                "brittleness": brittle,
                "redundancy_flag": redundancy,
            }
        )

    file_rows: list[dict] = []
    for p in sorted(TESTS.glob("test_*.py")):
        fp = "tests/" + p.name
        bucket = _file_primary_bucket(fp)
        collected = len(by_file.get(fp, []))
        names, dups = _ast_test_defs(p)
        file_rows.append(
            {
                "path": fp,
                "filename_bucket": bucket,
                "pytest_collected": collected,
                "ast_test_def_lines": len(names),
                "ast_unique_test_names": len(set(names)),
                "has_shadowed_duplicate_names": bool(dups),
            }
        )

    bucket_counts: Counter[str] = Counter(t["primary_bucket"] for t in tests_out)
    brittle_by_file: Counter[str] = Counter()
    for t in tests_out:
        if t["brittleness"] == "high":
            brittle_by_file[t["file"]] += 1

    uniq_sum = 0
    for p in TESTS.glob("test_*.py"):
        names, _ = _ast_test_defs(p)
        uniq_sum += len(set(names))

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "test_file_count": len(file_rows),
        "pytest_collected_items": len(nodeids),
        "ast_test_function_def_lines_total": ast_total,
        "ast_unique_test_names_module_level": uniq_sum,
        "parametrized_extra_items": len(nodeids) - uniq_sum,
        "files_with_shadowed_duplicate_test_defs": dup_report,
        "counts_by_primary_bucket": dict(bucket_counts),
    }

    overlap_clusters = [k for k, v in base_locations.items() if len(set(v)) > 1]

    file_bucket_majority: dict[str, str] = {}
    file_bucket_distribution: dict[str, dict[str, int]] = {}
    for fp in {t["file"] for t in tests_out}:
        bc = Counter(t["primary_bucket"] for t in tests_out if t["file"] == fp)
        file_bucket_distribution[fp] = dict(bc)
        file_bucket_majority[fp] = bc.most_common(1)[0][0] if bc else "mixed/unclear"

    for fr in file_rows:
        fp = fr["path"]
        fr["primary_bucket"] = file_bucket_majority.get(fp, "mixed/unclear")
        fr["bucket_distribution"] = file_bucket_distribution.get(fp, {})
        tas = [t for t in tests_out if t["file"] == fp]
        fr["primary_feature_area_breakdown"] = dict(
            Counter(t["feature_areas"][0] for t in tas).most_common(8)
        )
        fr["high_brittleness_test_count"] = sum(1 for t in tas if t["brittleness"] == "high")
        fr["prose_sensitive_test_count"] = sum(1 for t in tas if t["assertion_style"] == "prose-sensitive")

    primary_feature = [t["feature_areas"][0] for t in tests_out]
    feature_primary_counts = Counter(primary_feature)
    area_to_files: dict[str, set[str]] = defaultdict(set)
    for t in tests_out:
        for a in t["feature_areas"]:
            area_to_files[a].add(t["file"])
    spread_ranked = sorted(
        [{"area": a, "distinct_files": len(files), "files": sorted(files)} for a, files in area_to_files.items()],
        key=lambda x: (-x["distinct_files"], -sum(1 for t in tests_out if x["area"] in t["feature_areas"])),
    )

    payload = {
        "summary": summary,
        "counts_by_majority_file_bucket": Counter(file_bucket_majority.values()),
        "top_high_brittleness_files": brittle_by_file.most_common(15),
        "cross_file_same_base_name_count": len(overlap_clusters),
        "cross_file_same_base_names_sample": sorted(overlap_clusters)[:40],
        "feature_area_primary_counts": dict(feature_primary_counts.most_common()),
        "feature_areas_by_distinct_files": spread_ranked[:25],
        "files": file_rows,
        "tests": tests_out,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(nodeids)} tests, {len(file_rows)} files)")


if __name__ == "__main__":
    main()
