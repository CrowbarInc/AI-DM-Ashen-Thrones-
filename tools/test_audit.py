#!/usr/bin/env python3
"""Static + pytest inventory for tests/.

Run from repo root: ``py -3 tools/test_audit.py`` (Windows) or ``python tools/test_audit.py``.
Default write: slim governance artifact ``tests/test_inventory_governance.json`` (CI + ownership registry).
Committed ``files[]`` rows are registry-owned paths only (direct owners, neighbors, cross-file dup files);
whole-suite file coverage is derived during ``--check``.
Full diagnostic payload: ``py -3 tools/test_audit.py --full`` → ``artifacts/test_inventory_full.json``,
or ``py -3 tools/test_audit.py --output PATH``. Full output retains ``tests[]`` with per-test markers;
committed governance omits ``tests[]`` (derived during ``--check``).

Use ``py -3 tools/test_audit.py --check`` to verify committed governance JSON matches a fresh regen
(ignores ``summary.generated_utc``). Use ``--check --full`` to verify an explicit full diagnostic file.
Requires: the same interpreter used for pytest.

Emits per-file ``collected_nodeids`` / ``collected_test_names``, AST duplicate-name
guardrails, parsed ``game.*`` imports, heuristic ``likely_ownership_theme`` and
``likely_architecture_layer`` (engine / planner / gpt / gate / evaluator / smoke /
transcript / gauntlet / general), per-file ``marker_set`` / ``declared_pytest_markers``,
``collected_duplicate_base_names`` (parametrize / name reuse triage), parsed ``game.*`` imports,
overlap hints, optional ``ownership_registry_index`` (direct owner + neighbor suites), and
top-level ``block_b_overlap_clusters`` / ``import_hub_modules`` for consolidation triage
(full diagnostic only; not committed in governance JSON since AQ7).

JSON is written with sorted object keys for stable diffs aside from
``summary.generated_utc`` (see ``summary.inventory_schema_version``).

Also prints whether any module defines the same top-level ``test_*`` name twice
(Python keeps only the last — pytest would under-collect). Details:
``summary.files_with_shadowed_duplicate_test_defs`` in the JSON.
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
GOVERNANCE_JSON = TESTS / "test_inventory_governance.json"
FULL_INVENTORY_DEFAULT = ROOT / "artifacts" / "test_inventory_full.json"
# Committed CI / governance artifact (AQ3 slim inventory).
OUT_JSON = GOVERNANCE_JSON

GOVERNANCE_FILE_FIELDS: tuple[str, ...] = (
    "path",
    "marker_set",
    "collected_duplicate_base_names",
    "likely_architecture_layer",
    "pytest_collected",
)

# Running as ``python tools/test_audit.py`` puts ``tools/`` on ``sys.path[0]``; repo root must precede it
# so ``tests.*`` imports (ownership registry snapshot) resolve.
_ROOT_STR = str(ROOT)
if _ROOT_STR not in sys.path:
    sys.path.insert(0, _ROOT_STR)

# Bump when adding/removing inventory fields or changing semantics (governance / CI may assert).
INVENTORY_SCHEMA_VERSION = 2

GOVERNANCE_SUMMARY_FIELDS: tuple[str, ...] = (
    "inventory_schema_version",
    "inventory_kind",
    "declared_pytest_markers",
)

# Heuristic: architecture scores at or below this ceiling resolve to ``general`` (weak signal).
_ARCH_LAYER_GENERAL_THRESHOLD = 2

INTERNAL_PYTEST_MARKS = frozenset(
    {
        "parametrize",
        "usefixtures",
        "filterwarnings",
        "timeout",
        "skip",
        "skipif",
        "xfail",
        "asyncio",
        "anyio",
    }
)

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

# Single primary label per test file for architecture discussions (engine / planner / gpt / gate / …).
# ``general`` is not scored here; it is chosen when all scores fall at/below ``_ARCH_LAYER_GENERAL_THRESHOLD``.
ARCH_LAYERS: tuple[str, ...] = (
    "transcript",
    "gauntlet",
    "evaluator",
    "gate",
    "gpt",
    "planner",
    "smoke",
    "engine",
)


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


def _parse_game_import_modules(src: str) -> list[str]:
    """Top-level ``import game`` / ``from game...`` module paths (deduped, stable order)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "game" or name.startswith("game."):
                    found.add(name if name.startswith("game.") else "game")
        elif isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            if mod == "game" or mod.startswith("game."):
                if node.names and any(a.name == "*" for a in node.names):
                    found.add(f"{mod}.*")
                elif mod == "game":
                    for alias in node.names:
                        found.add(f"game.{alias.name}")
                else:
                    found.add(mod)
    return sorted(found)


def _game_import_roots(modules: list[str]) -> list[str]:
    """First segment under ``game`` (e.g. ``game.final_emission_gate`` -> ``final_emission_gate``)."""
    roots: list[str] = []
    for m in modules:
        if m == "game" or m == "game.*":
            roots.append("game")
            continue
        if m.startswith("game."):
            rest = m[len("game.") :]
            roots.append(rest.split(".", 1)[0])
    return sorted(set(roots))


def _declared_markers_from_pytest_ini() -> frozenset[str]:
    """Marker names declared under ``[pytest]`` → ``markers`` in ``pytest.ini`` (best-effort)."""
    ini_path = ROOT / "pytest.ini"
    if not ini_path.is_file():
        return frozenset()
    names: list[str] = []
    in_markers = False
    for raw in ini_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not in_markers:
            if re.match(r"^markers\s*=", line, re.IGNORECASE):
                in_markers = True
                rhs = line.split("=", 1)[1].strip()
                if rhs and ":" in rhs and not rhs.startswith("#"):
                    names.append(rhs.split(":", 1)[0].strip())
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("[") or (re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", stripped) and not stripped.lower().startswith("markers")):
            break
        if ":" in stripped:
            name = stripped.split(":", 1)[0].strip()
            if name and not name.startswith("#"):
                names.append(name)
    return frozenset(n for n in names if n)


def _pytest_mark_name_from_decorator(dec: ast.AST) -> str | None:
    """``pytest.mark.foo`` / ``pytest.mark.foo(...)`` → ``foo``."""
    if isinstance(dec, ast.Call):
        dec = dec.func
    parts: list[str] = []
    cur: ast.AST | None = dec
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if not isinstance(cur, ast.Name) or cur.id != "pytest":
        return None
    if len(parts) >= 2 and parts[-1] == "mark":
        return parts[-2]
    return None


def _marks_from_pytestmark_value(val: ast.AST) -> list[str]:
    out: list[str] = []
    if isinstance(val, (ast.List, ast.Tuple)):
        for elt in val.elts:
            n = _pytest_mark_name_from_decorator(elt)
            if n and n not in INTERNAL_PYTEST_MARKS:
                out.append(n)
    else:
        n = _pytest_mark_name_from_decorator(val)
        if n and n not in INTERNAL_PYTEST_MARKS:
            out.append(n)
    return out


def _parse_module_pytestmarks_and_per_test_marks(
    path: Path,
) -> tuple[list[str], dict[str, list[str]]]:
    """Module-level ``pytestmark`` union (sorted), plus per-``test_*`` decorator marks."""
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except (OSError, SyntaxError, UnicodeError):
        return [], {}
    module_level: set[str] = set()
    per_test: dict[str, set[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "pytestmark":
                    for m in _marks_from_pytestmark_value(node.value):
                        module_level.add(m)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "pytestmark":
            for m in _marks_from_pytestmark_value(node.value):
                module_level.add(m)
        elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            marks: set[str] = set()
            for dec in node.decorator_list:
                n = _pytest_mark_name_from_decorator(dec)
                if n and n not in INTERNAL_PYTEST_MARKS:
                    marks.add(n)
            if marks:
                per_test[node.name] = marks
    per_test_lists = {k: sorted(v) for k, v in sorted(per_test.items())}
    return sorted(module_level), per_test_lists


def _build_ownership_registry_index() -> dict[str, object] | None:
    """Snapshot of ``tests/test_ownership_registry.py`` for full diagnostic inventory only."""
    try:
        from tests.test_ownership_registry import build_ownership_registry_index

        return build_ownership_registry_index()
    except Exception:
        return None


def _architecture_layer_scores(fp: str, src: str, file_bucket: str) -> dict[str, int]:
    """Heuristic scores for ``ARCH_LAYERS``; higher wins (ties broken by ``ARCH_LAYERS`` order)."""
    bn = Path(fp).name.lower()
    sl = src.lower()
    scores = {layer: 0 for layer in ARCH_LAYERS}

    if file_bucket == "transcript_gauntlet" or "transcript_gauntlet" in bn:
        scores["gauntlet"] += 12
    if "gauntlet_regressions" in bn or "manual_gauntlet" in bn:
        scores["gauntlet"] += 12
    if "transcript" in bn and "gauntlet" not in bn and "transcript_gauntlet" not in bn:
        scores["transcript"] += 6
    if "run_transcript" in sl or "transcript_runner" in sl or ("session_log" in sl and "replay" in sl):
        scores["transcript"] += 10
    if "mixed_state_recovery" in bn and ("run_transcript" in sl or "transcript" in sl):
        scores["transcript"] += 5

    if any(
        tok in sl
        for tok in (
            "narrative_authenticity_eval",
            "behavioral_gauntlet_eval",
            "evaluate_narrative_authenticity",
            "evaluate_behavioral_gauntlet",
            "evaluate_scenario_spine",
            "playability_eval",
            "intent_fulfillment_eval",
            "session_cohesion_eval",
        )
    ):
        scores["evaluator"] += 10
    if "authenticity" in bn and ("eval" in bn or "aer" in bn):
        scores["evaluator"] += 6
    if "behavioral_gauntlet_eval" in bn or "playability_eval" in bn or "scenario_spine_eval" in bn:
        scores["evaluator"] += 5

    if "final_emission_gate" in sl or "apply_final_emission_gate" in sl:
        scores["gate"] += 10
    if "final_emission_validators" in sl or "final_emission_repairs" in sl:
        scores["gate"] += 4
    if "social_exchange_emission" in sl:
        scores["gate"] += 3
    if "output_sanitizer" in sl or "prompt_and_guard" in sl:
        scores["gate"] += 2

    if "call_gpt" in sl or "mock_gpt" in sl or "patch(" in sl and "gpt" in sl:
        scores["gpt"] += 10
    if re.search(r"\bgame\.gpt\b", sl) or "openai" in sl:
        scores["gpt"] += 6

    if "planner_convergence" in sl or "narration_plan" in sl or re.search(r"\bgame\.narrative_plan", sl):
        scores["planner"] += 9
    if "plan_structural" in sl or "plan_prompt" in bn:
        scores["planner"] += 4

    if "_smoke" in bn or bn.endswith("smoke.py") or "runner_smoke" in bn:
        scores["smoke"] += 10
    if "synthetic_smoke" in bn:
        scores["smoke"] += 6

    if any(
        root in sl
        for root in (
            "exploration_resolution",
            "world_state",
            "skill_check",
            "combat_resolution",
            "lead_engine",
            "scene_graph",
            "world_engine",
            "storage",
        )
    ):
        scores["engine"] += 3
    # Direct-owner governance expects a non-``general`` inventory layer for these suites.
    if re.search(r"\bgame\.response_policy_contracts\b", sl):
        scores["engine"] += 10
    if re.search(r"\bgame\.clues\b", sl) or re.search(r"\bgame\.leads\b", sl):
        scores["engine"] += 10
    if "clue_lead_registry" in bn or ("clue" in bn and "lead" in bn and "registry" in bn):
        scores["engine"] += 6
    if re.search(r"\bgame\.final_emission_validators\b", sl):
        scores["gate"] += 12
    if (
        "validate_narrative_mode_output" in sl
        or "narrative_mode_output_validator" in bn
        or re.search(r"\bgame\.narrative_mode_contract\b", sl)
    ):
        scores["gpt"] += 10
    if "TestClient" not in src and "tmp_path" not in sl and max(scores.values()) <= 4:
        scores["engine"] += 2

    return scores


def _primary_architecture_layer(scores: dict[str, int]) -> str:
    best = max(scores.values())
    if best <= _ARCH_LAYER_GENERAL_THRESHOLD:
        return "general"
    for layer in ARCH_LAYERS:
        if scores.get(layer, 0) == best:
            return layer
    return "general"


def _likely_ownership_theme(fp: str, primary_feature_breakdown: dict[str, int], game_roots: list[str]) -> str:
    """Readable theme: prefer explicit/heuristic feature majority, else filename + imports."""
    if primary_feature_breakdown:
        top_label, top_n = max(primary_feature_breakdown.items(), key=lambda kv: kv[1])
        second = sorted(((k, v) for k, v in primary_feature_breakdown.items() if k != top_label), key=lambda kv: -kv[1])
        if top_label != "general":
            if second and second[0][1] >= max(3, top_n // 4):
                return f"{top_label} (+mixed: {second[0][0]})"
            return top_label
    low = Path(fp).name.lower()
    for label, kws in FEATURE_RULES:
        if any(k in low for k in kws):
            return f"{label} (filename)"
    if game_roots:
        return "general (" + ", ".join(game_roots[:6]) + ")"
    return "general"


def _overlap_hints_for_file(
    fp: str,
    src: str,
    game_modules: list[str],
    game_roots: list[str],
    has_shadowed_dups: bool,
    colliding_base_names: list[str],
    primary_theme: str,
    layer: str,
) -> list[str]:
    hints: list[str] = []
    low = src.lower()
    if has_shadowed_dups:
        hints.append("module_shadowed_duplicate_test_names")
    if colliding_base_names:
        hints.append("cross_file_same_test_base_name:" + ",".join(sorted(colliding_base_names)[:6]))
    fe_sub = [m for m in game_modules if "final_emission" in m]
    if len(fe_sub) >= 2:
        hints.append("imports_multiple_final_emission_subsystems")
    if "final_emission_gate" in low and "prompt_context" in low:
        hints.append("gate_stack_adjacent_to_prompt_context")
    if "final_emission_gate" in low and ("testclient" in low or "client.post" in low or "client.get" in low):
        hints.append("http_client_plus_final_emission_gate")
    if "social_exchange_emission" in low and "final_emission_gate" in low:
        hints.append("strict_social_emission_plus_gate")
    if primary_theme.startswith("lead extraction") and layer in ("gate", "engine", "gpt"):
        hints.append("lead_theme_non_engine_layer")
    if primary_theme.startswith("clue system") and "turn_pipeline" in fp:
        hints.append("clue_theme_in_pipeline_module")
    if len(game_roots) >= 12:
        hints.append(f"broad_game_import_fanout:{len(game_roots)}_roots")
    return hints[:14]


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


def _test_keyword_overlap_hints(nodeid: str, body: str) -> list[str]:
    """When several feature keywords co-occur, flag as a merge-risk hint (not duplicate proof)."""
    blob = f"{nodeid}\n{body}".lower()
    hints: list[str] = []
    for label, kws in FEATURE_RULES:
        hit_kws = [k for k in kws if k in blob]
        if len(hit_kws) >= 2:
            hints.append(f"multi_keyword:{label}:{','.join(hit_kws[:4])}")
    return hints[:6]


_CHECK_DRIFT_SAMPLE_LIMIT = 25


def _inventory_test_nodeids(inventory: dict) -> set[str]:
    tests = inventory.get("tests")
    if not isinstance(tests, list):
        return set()
    return {str(t["nodeid"]) for t in tests if isinstance(t, dict) and "nodeid" in t}


def governance_committed_file_paths(full_payload: dict) -> set[str]:
    """Paths retained in committed governance ``files[]`` (registry + cross-file dup files)."""
    paths: set[str] = set()
    idx = _build_ownership_registry_index()
    if isinstance(idx, dict):
        files_roles = idx.get("files_roles")
        if isinstance(files_roles, dict):
            paths.update(str(fp).replace("\\", "/") for fp in files_roles)
    dups = full_payload.get("cross_file_duplicate_test_names")
    if isinstance(dups, list):
        for block in dups:
            if not isinstance(block, dict):
                continue
            files = block.get("files")
            if isinstance(files, list):
                paths.update(str(fp).replace("\\", "/") for fp in files)
    return paths


def build_governance_summary(full_payload: dict) -> dict[str, object]:
    """Stable metadata retained in committed governance JSON (counts derived at --check)."""
    full_summary = full_payload.get("summary")
    src = full_summary if isinstance(full_summary, dict) else {}
    markers = src.get("declared_pytest_markers")
    if not isinstance(markers, list):
        markers = sorted(_declared_markers_from_pytest_ini())
    return {
        "inventory_schema_version": src.get("inventory_schema_version", INVENTORY_SCHEMA_VERSION),
        "inventory_kind": "governance",
        "declared_pytest_markers": list(markers),
    }


def collect_cross_file_duplicate_governance_errors(
    cross_file_duplicate_test_names: list | object,
    *,
    cross_file_allowlist: frozenset[str] | set[str] | Mapping[str, str],
) -> list[str]:
    """Allowlist enforcement for derived cross-file duplicate base names."""
    errors: list[str] = []
    if not isinstance(cross_file_duplicate_test_names, list):
        errors.append("derived inventory missing cross_file_duplicate_test_names list")
        return errors
    for block in cross_file_duplicate_test_names:
        if not isinstance(block, dict):
            continue
        base = block.get("base_name")
        if not isinstance(base, str):
            continue
        if base in cross_file_allowlist:
            continue
        files = block.get("files")
        fl = ", ".join(files) if isinstance(files, list) else "?"
        errors.append(
            f"cross-file duplicate test name {base!r} not allowlisted "
            f"(files: {fl}); rename tests or extend allowlist with a reason.",
        )
    return errors


def _validate_derived_cross_file_duplicate_governance(full_payload: dict) -> list[str]:
    try:
        from tests.test_ownership_registry import _CROSS_FILE_DUPLICATE_ALLOWLIST
    except ImportError:
        return ["cannot import cross-file duplicate allowlist from tests.test_ownership_registry"]
    return collect_cross_file_duplicate_governance_errors(
        full_payload.get("cross_file_duplicate_test_names", ()),
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
    )


def _validate_governance_summary_shape(governance: dict) -> list[str]:
    errors: list[str] = []
    summary = governance.get("summary")
    if not isinstance(summary, dict):
        return ["governance summary must be an object"]
    extra = sorted(set(summary) - set(GOVERNANCE_SUMMARY_FIELDS))
    missing = sorted(set(GOVERNANCE_SUMMARY_FIELDS) - set(summary))
    if extra:
        errors.append(f"governance summary includes derivable fields: {extra[:8]!r}")
    if missing:
        errors.append(f"governance summary missing stable fields: {missing!r}")
    if summary.get("inventory_kind") != "governance":
        errors.append(f"governance summary inventory_kind must be 'governance', got {summary.get('inventory_kind')!r}")
    return errors


def _validate_derived_full_suite_counts(full_payload: dict) -> list[str]:
    """Ensure full diagnostic summary counts match live collect output."""
    errors: list[str] = []
    full_summary = full_payload.get("summary")
    if not isinstance(full_summary, dict):
        errors.append("full inventory missing summary for count derivation")
        return errors
    full_files = _inventory_test_files(full_payload)
    tests = full_payload.get("tests")
    test_count = len(tests) if isinstance(tests, list) else 0
    file_count = full_summary.get("test_file_count")
    collected = full_summary.get("pytest_collected_items")
    if file_count != len(full_files):
        errors.append(
            f"full inventory file count mismatch: summary.test_file_count={file_count!r}, "
            f"files[]={len(full_files)}",
        )
    if collected != test_count:
        errors.append(
            f"full inventory collected item mismatch: summary.pytest_collected_items={collected!r}, "
            f"tests[]={test_count}",
        )
    return errors


def derive_per_test_marker_rows(full_payload: dict) -> list[dict[str, object]]:
    """Slim per-test marker coverage derived from a full diagnostic inventory payload."""
    rows: list[dict[str, object]] = []
    for row in full_payload.get("tests", ()):
        if not isinstance(row, dict) or "nodeid" not in row:
            continue
        rows.append(
            {
                "nodeid": row["nodeid"],
                "marker_set": list(row.get("marker_set") or []),
            }
        )
    return rows


def _validate_derived_marker_governance(full_payload: dict) -> list[str]:
    """Ensure fresh per-test marker coverage is complete and matches file-level marker_set unions."""
    errors: list[str] = []
    tests = full_payload.get("tests")
    if not isinstance(tests, list) or not tests:
        errors.append("fresh inventory has no tests[] rows for marker derivation")
        return errors

    missing = [t.get("nodeid") for t in tests if not isinstance(t, dict) or "marker_set" not in t]
    if missing:
        errors.append(
            f"derived marker coverage missing marker_set on {len(missing)} tests "
            f"(first: {missing[:3]!r})",
        )

    by_file: dict[str, set[str]] = defaultdict(set)
    for row in tests:
        if not isinstance(row, dict):
            continue
        fp = row.get("file")
        marker_set = row.get("marker_set")
        if isinstance(fp, str) and isinstance(marker_set, list):
            by_file[fp.replace("\\", "/")].update(str(m) for m in marker_set)

    for frow in full_payload.get("files", ()):
        if not isinstance(frow, dict) or "path" not in frow:
            continue
        fp = str(frow["path"]).replace("\\", "/")
        file_markers = set(frow.get("marker_set") or [])
        derived_union = by_file.get(fp, set())
        if file_markers != derived_union:
            errors.append(
                f"{fp}: files[].marker_set {sorted(file_markers)!r} != "
                f"derived per-test union {sorted(derived_union)!r}",
            )
    return errors


def _validate_governance_committed_file_paths(full_payload: dict, governance: dict) -> list[str]:
    """Ensure committed governance files[] matches registry-owned path set derived from full audit."""
    errors: list[str] = []
    required = governance_committed_file_paths(full_payload)
    full_files = _inventory_test_files(full_payload)
    required_present = required & full_files
    committed = _inventory_test_files(governance)
    missing = sorted(required_present - committed)
    extra = sorted(committed - required)
    if missing:
        errors.append(
            f"governance files[] missing required paths ({len(missing)}): {missing[:8]!r}",
        )
    if extra:
        errors.append(
            f"governance files[] includes non-governance paths ({len(extra)}): {extra[:8]!r}",
        )
    summary = governance.get("summary") if isinstance(governance.get("summary"), dict) else {}
    full_summary = full_payload.get("summary") if isinstance(full_payload.get("summary"), dict) else {}
    expected_total = full_summary.get("test_file_count")
    if isinstance(expected_total, int) and len(full_files) != expected_total:
        errors.append(
            f"full inventory covers {len(full_files)} files but derived summary.test_file_count is {expected_total!r}",
        )
    idx = _build_ownership_registry_index()
    if isinstance(idx, dict):
        files_roles = idx.get("files_roles")
        if isinstance(files_roles, dict):
            registry_present = {str(fp).replace("\\", "/") for fp in files_roles} & full_files
            missing_registry = sorted(registry_present - committed)
            if missing_registry:
                errors.append(
                    f"governance files[] missing registry-owned paths ({len(missing_registry)}): "
                    f"{missing_registry[:8]!r}",
                )
    return errors


def _validate_full_diagnostic_triage_aggregates(full_payload: dict) -> list[str]:
    """Ensure full diagnostic payload retains triage aggregates removed from governance JSON."""
    errors: list[str] = []
    clusters = full_payload.get("block_b_overlap_clusters")
    if not isinstance(clusters, list) or not clusters:
        errors.append("full inventory missing non-empty block_b_overlap_clusters")
    else:
        kinds = {c.get("kind") for c in clusters if isinstance(c, dict)}
        if "dense_ownership_theme_by_architecture_layer" not in kinds:
            errors.append("full inventory block_b_overlap_clusters missing dense_ownership_theme_by_architecture_layer")
    hubs = full_payload.get("import_hub_modules")
    if not isinstance(hubs, list):
        errors.append("full inventory missing import_hub_modules list")
    return errors


def _inventory_test_files(inventory: dict) -> set[str]:
    files = inventory.get("files")
    if not isinstance(files, list):
        return set()
    return {str(f["path"]).replace("\\", "/") for f in files if isinstance(f, dict) and "path" in f}


def normalize_inventory_for_compare(inventory: dict) -> dict:
    """Return a deep copy with ``summary.generated_utc`` removed for drift checks."""
    norm = copy.deepcopy(inventory)
    summary = norm.get("summary")
    if isinstance(summary, dict):
        summary.pop("generated_utc", None)
    return norm


def _canonical_inventory_json(inventory: dict) -> str:
    return json.dumps(inventory, sort_keys=True, separators=(",", ":"))


def inventories_match_excluding_timestamp(fresh: dict, committed: dict) -> bool:
    return _canonical_inventory_json(normalize_inventory_for_compare(fresh)) == _canonical_inventory_json(
        normalize_inventory_for_compare(committed)
    )


def format_inventory_drift_report(
    fresh: dict,
    committed: dict,
    *,
    artifact_path: Path,
    regenerate_hint: str = "py -3 tools/test_audit.py",
) -> list[str]:
    """Human-readable drift lines when normalized inventories differ."""
    lines: list[str] = [
        f"Inventory drift: {artifact_path.as_posix()} does not match a fresh regen.",
        f"Regenerate with: {regenerate_hint}",
        "(comparison ignores summary.generated_utc)",
    ]

    fresh_files = _inventory_test_files(fresh)
    committed_files = _inventory_test_files(committed)
    added_files = sorted(fresh_files - committed_files)
    removed_files = sorted(committed_files - fresh_files)
    lines.append(f"Test files: +{len(added_files)} added, -{len(removed_files)} removed")
    for path in added_files[:_CHECK_DRIFT_SAMPLE_LIMIT]:
        lines.append(f"  + {path}")
    if len(added_files) > _CHECK_DRIFT_SAMPLE_LIMIT:
        lines.append(f"  ... and {len(added_files) - _CHECK_DRIFT_SAMPLE_LIMIT} more added files")
    for path in removed_files[:_CHECK_DRIFT_SAMPLE_LIMIT]:
        lines.append(f"  - {path}")
    if len(removed_files) > _CHECK_DRIFT_SAMPLE_LIMIT:
        lines.append(f"  ... and {len(removed_files) - _CHECK_DRIFT_SAMPLE_LIMIT} more removed files")

    fresh_nodeids = _inventory_test_nodeids(fresh)
    committed_nodeids = _inventory_test_nodeids(committed)
    added_nodeids: list[str] = []
    removed_nodeids: list[str] = []
    if committed_nodeids:
        added_nodeids = sorted(fresh_nodeids - committed_nodeids)
        removed_nodeids = sorted(committed_nodeids - fresh_nodeids)
        lines.append(f"Test nodeids: +{len(added_nodeids)} added, -{len(removed_nodeids)} removed")
        for nodeid in added_nodeids[:_CHECK_DRIFT_SAMPLE_LIMIT]:
            lines.append(f"  + {nodeid}")
        if len(added_nodeids) > _CHECK_DRIFT_SAMPLE_LIMIT:
            lines.append(f"  ... and {len(added_nodeids) - _CHECK_DRIFT_SAMPLE_LIMIT} more added nodeids")
        for nodeid in removed_nodeids[:_CHECK_DRIFT_SAMPLE_LIMIT]:
            lines.append(f"  - {nodeid}")
        if len(removed_nodeids) > _CHECK_DRIFT_SAMPLE_LIMIT:
            lines.append(f"  ... and {len(removed_nodeids) - _CHECK_DRIFT_SAMPLE_LIMIT} more removed nodeids")
    else:
        lines.append(
            f"Test nodeids: fresh has {len(fresh_nodeids)} "
            "(committed governance omits tests[]; per-test markers derived at check time)",
        )

    fresh_summary = fresh.get("summary") if isinstance(fresh.get("summary"), dict) else {}
    committed_summary = committed.get("summary") if isinstance(committed.get("summary"), dict) else {}
    derivable_summary_fields = ("pytest_collected_items", "test_file_count", "generated_utc")
    fresh_derivable = {k: fresh_summary.get(k) for k in derivable_summary_fields if k in fresh_summary}
    committed_derivable = {k: committed_summary.get(k) for k in derivable_summary_fields if k in committed_summary}
    if fresh_derivable != committed_derivable:
        lines.append(
            "Derived summary counts differ "
            f"(fresh={fresh_derivable!r}, committed={committed_derivable!r})",
        )

    if not added_files and not removed_files and not added_nodeids and not removed_nodeids and not fresh_derivable:
        lines.append(
            "Nodeid/file sets match, but other inventory fields differ "
            "(heuristics, markers, registry embed, or aggregates)."
        )

    return lines


def build_governance_payload(full_payload: dict) -> dict:
    """Extract slim governance artifact from a full diagnostic inventory payload."""
    committed_paths = governance_committed_file_paths(full_payload)
    slim_files: list[dict] = []
    for row in full_payload.get("files", ()):
        if not isinstance(row, dict) or "path" not in row:
            continue
        fp = str(row["path"]).replace("\\", "/")
        if fp not in committed_paths:
            continue
        slim_files.append({key: row.get(key) if key != "marker_set" else list(row.get(key) or []) for key in GOVERNANCE_FILE_FIELDS})
    slim_files.sort(key=lambda r: str(r.get("path", "")))

    governance: dict[str, object] = {
        "summary": build_governance_summary(full_payload),
        "files": slim_files,
    }
    return governance


def run_inventory_check(*, artifact_path: Path | None = None) -> int:
    """Regenerate governance inventory in memory and compare to committed JSON."""
    path = artifact_path or GOVERNANCE_JSON
    if not path.is_file():
        print(f"Missing inventory: {path} (run py -3 tools/test_audit.py)", file=sys.stderr)
        return 1

    committed = json.loads(path.read_text(encoding="utf-8"))
    full_payload = build_inventory_payload()
    fresh = build_governance_payload(full_payload)
    if not inventories_match_excluding_timestamp(fresh, committed):
        for line in format_inventory_drift_report(
            fresh,
            committed,
            artifact_path=path,
            regenerate_hint="py -3 tools/test_audit.py",
        ):
            print(line, file=sys.stderr)
        return 1

    marker_errors = _validate_derived_marker_governance(full_payload)
    if marker_errors:
        print(f"Derived marker governance failed for {path.as_posix()}:", file=sys.stderr)
        for err in marker_errors[:_CHECK_DRIFT_SAMPLE_LIMIT]:
            print(f"  {err}", file=sys.stderr)
        if len(marker_errors) > _CHECK_DRIFT_SAMPLE_LIMIT:
            print(f"  ... and {len(marker_errors) - _CHECK_DRIFT_SAMPLE_LIMIT} more marker errors", file=sys.stderr)
        return 1

    triage_errors = _validate_full_diagnostic_triage_aggregates(full_payload)
    if triage_errors:
        print(f"Full diagnostic triage aggregates failed for {path.as_posix()}:", file=sys.stderr)
        for err in triage_errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    path_errors = _validate_governance_committed_file_paths(full_payload, fresh)
    if path_errors:
        print(f"Governance file-path coverage failed for {path.as_posix()}:", file=sys.stderr)
        for err in path_errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    summary_errors = _validate_governance_summary_shape(fresh)
    if summary_errors:
        print(f"Governance summary shape failed for {path.as_posix()}:", file=sys.stderr)
        for err in summary_errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    count_errors = _validate_derived_full_suite_counts(full_payload)
    if count_errors:
        print(f"Derived full-suite counts failed for {path.as_posix()}:", file=sys.stderr)
        for err in count_errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    duplicate_errors = _validate_derived_cross_file_duplicate_governance(full_payload)
    if duplicate_errors:
        print(f"Derived cross-file duplicate governance failed for {path.as_posix()}:", file=sys.stderr)
        for err in duplicate_errors[:_CHECK_DRIFT_SAMPLE_LIMIT]:
            print(f"  {err}", file=sys.stderr)
        if len(duplicate_errors) > _CHECK_DRIFT_SAMPLE_LIMIT:
            print(f"  ... and {len(duplicate_errors) - _CHECK_DRIFT_SAMPLE_LIMIT} more duplicate errors", file=sys.stderr)
        return 1

    node_count = len(derive_per_test_marker_rows(full_payload))
    registry_file_count = len(_inventory_test_files(fresh))
    full_file_count = len(_inventory_test_files(full_payload))
    print(
        f"Inventory check OK: {path.as_posix()} matches fresh regen "
        f"({node_count} tests derived, {registry_file_count} registry-owned files / "
        f"{full_file_count} total; generated_utc ignored)."
    )
    return 0


def run_full_inventory_check(*, artifact_path: Path | None = None) -> int:
    """Regenerate full diagnostic inventory in memory and compare to committed JSON."""
    path = artifact_path or FULL_INVENTORY_DEFAULT
    if not path.is_file():
        print(
            f"Missing full inventory: {path} (run py -3 tools/test_audit.py --full)",
            file=sys.stderr,
        )
        return 1

    committed = json.loads(path.read_text(encoding="utf-8"))
    fresh = build_inventory_payload()
    if inventories_match_excluding_timestamp(fresh, committed):
        node_count = len(_inventory_test_nodeids(fresh))
        file_count = len(_inventory_test_files(fresh))
        print(
            f"Full inventory check OK: {path.as_posix()} matches fresh regen "
            f"({node_count} tests, {file_count} files; generated_utc ignored)."
        )
        return 0

    for line in format_inventory_drift_report(
        fresh,
        committed,
        artifact_path=path,
        regenerate_hint="py -3 tools/test_audit.py --full",
    ):
        print(line, file=sys.stderr)
    return 1


def build_inventory_payload() -> dict:
    nodeids = _collect_pytest_nodeids()
    by_file: dict[str, list[str]] = defaultdict(list)
    for nid in nodeids:
        fp, _, _, _ = _parse_nodeid(nid)
        by_file[fp].append(nid)

    all_fps = sorted(set(by_file.keys()) | {"tests/" + p.name for p in TESTS.glob("test_*.py")})
    declared_pytest_markers = sorted(_declared_markers_from_pytest_ini())
    ownership_registry_index = _build_ownership_registry_index()
    registry_positions: dict[str, list[dict[str, str]]] = {}
    if isinstance(ownership_registry_index, dict) and ownership_registry_index.get("available"):
        frmap = ownership_registry_index.get("files_roles")
        if isinstance(frmap, dict):
            registry_positions = {str(k): list(v) for k, v in frmap.items()}

    src_by_fp: dict[str, str] = {}
    for p in sorted(TESTS.glob("test_*.py")):
        fp = "tests/" + p.name
        src_by_fp[fp] = p.read_text(encoding="utf-8")

    markers_by_fp: dict[str, tuple[list[str], dict[str, list[str]]]] = {}
    for p in sorted(TESTS.glob("test_*.py")):
        fp = "tests/" + p.name
        markers_by_fp[fp] = _parse_module_pytestmarks_and_per_test_marks(p)

    ast_total = 0
    dup_report: list[dict] = []
    ast_by_fp: dict[str, tuple[list[str], list[str]]] = {}
    for p in sorted(TESTS.glob("test_*.py")):
        rel = p.as_posix()
        if not rel.startswith("tests/"):
            rel = "tests/" + p.name
        names, dups = _ast_test_defs(p)
        fp = "tests/" + p.name
        ast_by_fp[fp] = (names, dups)
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
        src = src_by_fp.get(fp) or ""
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
        mod_marks, per_test_marks = markers_by_fp.get(fp, ([], {}))
        marker_set = sorted(set(mod_marks) | set(per_test_marks.get(base, [])))
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
                "keyword_overlap_hints": _test_keyword_overlap_hints(nid, body),
                "marker_set": marker_set,
            }
        )

    file_rows: list[dict] = []
    for fp in all_fps:
        path = TESTS / Path(fp).name
        bucket = _file_primary_bucket(fp)
        collected = len(by_file.get(fp, []))
        names, dups = ast_by_fp.get(fp, ([], []))
        if path.is_file() and not names and collected:
            names, dups = _ast_test_defs(path)
        base_counts = Counter(_parse_nodeid(n)[2] for n in by_file.get(fp, []))
        collected_dup_bases = sorted(b for b, c in base_counts.items() if c > 1)
        mod_marks, per_test_marks = markers_by_fp.get(fp, ([], {}))
        file_marker_union = sorted(set(mod_marks) | {m for ms in per_test_marks.values() for m in ms})
        file_rows.append(
            {
                "path": fp,
                "filename_bucket": bucket,
                "pytest_collected": collected,
                "collected_nodeids": sorted(by_file.get(fp, [])),
                "collected_test_names": [nid.split("::", 1)[1] for nid in sorted(by_file.get(fp, []))],
                "collected_duplicate_base_names": collected_dup_bases,
                "ast_test_def_lines": len(names),
                "ast_unique_test_names": len(set(names)),
                "shadowed_duplicate_test_names": sorted(dups) if dups else [],
                "has_shadowed_duplicate_names": bool(dups),
                "marker_set": file_marker_union,
                "ownership_registry_positions": registry_positions.get(fp.replace("\\", "/"), []),
            }
        )

    bucket_counts: Counter[str] = Counter(t["primary_bucket"] for t in tests_out)
    brittle_by_file: Counter[str] = Counter()
    for t in tests_out:
        if t["brittleness"] == "high":
            brittle_by_file[t["file"]] += 1

    uniq_sum = 0
    for p in TESTS.glob("test_*.py"):
        fp = "tests/" + p.name
        names, _ = ast_by_fp.get(fp, ([], []))
        uniq_sum += len(set(names))

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
        "inventory_kind": "full",
        "declared_pytest_markers": declared_pytest_markers,
        "test_file_count": len(file_rows),
        "pytest_collected_items": len(nodeids),
        "ast_test_function_def_lines_total": ast_total,
        "ast_unique_test_names_module_level": uniq_sum,
        "parametrized_extra_items": len(nodeids) - uniq_sum,
        "files_with_shadowed_duplicate_test_defs": dup_report,
        "counts_by_primary_bucket": dict(bucket_counts),
    }

    overlap_clusters = [k for k, v in base_locations.items() if len(set(v)) > 1]

    cross_file_dup_index: dict[str, list[str]] = defaultdict(list)
    for base, fps in base_locations.items():
        ufs = sorted(set(fps))
        if len(ufs) <= 1:
            continue
        for fp in ufs:
            cross_file_dup_index[fp].append(base)

    file_bucket_majority: dict[str, str] = {}
    file_bucket_distribution: dict[str, dict[str, int]] = {}
    for fp in sorted(set(all_fps) | {t["file"] for t in tests_out}):
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
        src = src_by_fp.get(fp, "")
        gmods = _parse_game_import_modules(src)
        groots = _game_import_roots(gmods)
        fr["game_import_modules"] = gmods
        fr["game_import_roots"] = groots
        fb = fr["filename_bucket"]
        layer_scores = _architecture_layer_scores(fp, src, fb)
        fr["architecture_layer_scores"] = layer_scores
        fr["likely_architecture_layer"] = _primary_architecture_layer(layer_scores)
        fr["likely_ownership_theme"] = _likely_ownership_theme(fp, fr["primary_feature_area_breakdown"], groots)
        colliding = sorted(set(cross_file_dup_index.get(fp, [])))
        fr["overlap_hints"] = _overlap_hints_for_file(
            fp,
            src,
            gmods,
            groots,
            bool(fr["has_shadowed_duplicate_names"]),
            colliding,
            fr["likely_ownership_theme"],
            fr["likely_architecture_layer"],
        )

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

    file_row_map = {fr["path"]: fr for fr in file_rows}
    module_to_files: dict[str, set[str]] = defaultdict(set)
    for fr in file_rows:
        for m in fr.get("game_import_modules", ()):
            module_to_files[m].add(fr["path"])
    import_hub_modules = sorted(
        [{"game_module": m, "file_count": len(fs), "sample_files": sorted(fs)[:18]} for m, fs in module_to_files.items() if len(fs) >= 10],
        key=lambda r: (-r["file_count"], r["game_module"]),
    )[:30]

    cross_file_duplicate_test_names = [
        {"base_name": base, "files": sorted(set(fps))}
        for base, fps in sorted(base_locations.items(), key=lambda kv: kv[0])
        if len(set(fps)) > 1
    ]

    theme_layer_counter = Counter((fr["likely_ownership_theme"], fr["likely_architecture_layer"]) for fr in file_rows)
    dense_theme_layer_cells = [
        {"likely_ownership_theme": a, "likely_architecture_layer": b, "file_count": n}
        for (a, b), n in theme_layer_counter.most_common(25)
        if n >= 6
    ]

    def _mods_hit(fr: dict, needle: str) -> bool:
        return any(needle in m for m in fr.get("game_import_modules", ()))

    prompt_gate_files = sorted(
        fr["path"] for fr in file_rows if _mods_hit(fr, "final_emission_gate") and _mods_hit(fr, "prompt_context")
    )

    block_b_overlap_clusters: list[dict] = []
    if cross_file_duplicate_test_names:
        block_b_overlap_clusters.append(
            {
                "kind": "cross_file_duplicate_test_base_names",
                "collision_count": len(cross_file_duplicate_test_names),
                "items": cross_file_duplicate_test_names,
            }
        )
    if dense_theme_layer_cells:
        block_b_overlap_clusters.append(
            {
                "kind": "dense_ownership_theme_by_architecture_layer",
                "note": "Heuristic theme label × architecture layer; high file_count suggests many modules in the same rough neighborhood.",
                "cells": dense_theme_layer_cells,
            }
        )
    if prompt_gate_files:
        block_b_overlap_clusters.append(
            {
                "kind": "imports_final_emission_gate_and_prompt_context",
                "file_count": len(prompt_gate_files),
                "sample_files": prompt_gate_files[:30],
            }
        )

    for t in tests_out:
        row = file_row_map.get(t["file"], {})
        t["likely_architecture_layer"] = row.get("likely_architecture_layer", "engine")
        t["likely_ownership_theme"] = row.get("likely_ownership_theme", "general")
        t["file_overlap_hints"] = list(row.get("overlap_hints", []))

    summary["cross_file_duplicate_test_name_count"] = len(cross_file_duplicate_test_names)

    payload: dict[str, object] = {
        "summary": summary,
        "counts_by_majority_file_bucket": dict(Counter(file_bucket_majority.values())),
        "top_high_brittleness_files": brittle_by_file.most_common(15),
        "cross_file_same_base_name_count": len(overlap_clusters),
        "cross_file_same_base_names_sample": sorted(overlap_clusters)[:40],
        "cross_file_duplicate_test_names": cross_file_duplicate_test_names,
        "import_hub_modules": import_hub_modules,
        "block_b_overlap_clusters": block_b_overlap_clusters,
        "feature_area_primary_counts": dict(feature_primary_counts.most_common()),
        "feature_areas_by_distinct_files": spread_ranked[:25],
        "files": file_rows,
        "tests": tests_out,
    }
    if ownership_registry_index is not None:
        payload["ownership_registry_index"] = ownership_registry_index

    return payload


def write_governance_inventory(full_payload: dict) -> None:
    governance = build_governance_payload(full_payload)
    GOVERNANCE_JSON.write_text(json.dumps(governance, indent=2, sort_keys=True), encoding="utf-8")
    registry_file_count = len(governance.get("files", []))
    full_file_count = len(full_payload.get("files", [])) if isinstance(full_payload.get("files"), list) else 0
    derived_test_count = len(derive_per_test_marker_rows(full_payload))
    print(
        f"Wrote {GOVERNANCE_JSON} (governance: {registry_file_count} registry-owned files / "
        f"{full_file_count} total; {derived_test_count} per-test markers derived at check/full only)",
    )


def write_full_inventory(full_payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nodeids = full_payload.get("tests")
    file_rows = full_payload.get("files")
    test_count = len(nodeids) if isinstance(nodeids, list) else 0
    file_count = len(file_rows) if isinstance(file_rows, list) else 0
    dup_report = []
    summary = full_payload.get("summary")
    if isinstance(summary, dict):
        dup_report = summary.get("files_with_shadowed_duplicate_test_defs") or []
    spread_ranked = full_payload.get("feature_areas_by_distinct_files")
    if not isinstance(spread_ranked, list):
        spread_ranked = []

    path.write_text(json.dumps(full_payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {path} (full diagnostic: {test_count} tests, {file_count} files)")
    top_spread = spread_ranked[:8]
    if top_spread:
        parts = [f"{row['area']}: {row['distinct_files']} files" for row in top_spread]
        print("Overlap spread (heuristic primary feature tag; not proof of duplicate tests): " + "; ".join(parts))
    if dup_report:
        print("Duplicate top-level test_* names (same function name redefined in one module):")
        for row in sorted(dup_report, key=lambda r: r["file"]):
            names = ", ".join(sorted(row["shadowed_duplicate_names"]))
            print(
                f"  {row['file']}: {names} "
                f"({row['raw_def_count']} def lines, {row['unique_name_count']} unique names)"
            )
    else:
        print("No duplicate top-level test_* names (module-level shadowing) in tests/test_*.py.")


def write_inventory(payload: dict) -> None:
    """Backward-compatible alias: write governance artifact from a full payload."""
    write_governance_inventory(payload)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or verify test inventory artifacts (governance default, full diagnostic optional).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify committed governance inventory matches a fresh in-memory regen (no write).",
    )
    parser.add_argument(
        "--check-full",
        action="store_true",
        help="With --check, compare full diagnostic inventory at --output (or default artifacts path).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also write full diagnostic inventory to --output or artifacts/test_inventory_full.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path for full diagnostic inventory write/check (default: artifacts/test_inventory_full.json).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        if args.check_full:
            return run_full_inventory_check(artifact_path=args.output or FULL_INVENTORY_DEFAULT)
        return run_inventory_check()
    full_payload = build_inventory_payload()
    write_governance_inventory(full_payload)
    if args.full or args.output is not None:
        write_full_inventory(full_payload, args.output or FULL_INVENTORY_DEFAULT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
