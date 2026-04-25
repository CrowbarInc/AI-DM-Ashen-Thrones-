#!/usr/bin/env python3
"""Static + pytest inventory for tests/. Writes tests/test_inventory.json.

Run from repo root: ``py -3 tools/test_audit.py`` (Windows) or ``python tools/test_audit.py``.
Requires: the same interpreter used for pytest.

Emits per-file ``collected_nodeids`` / ``collected_test_names``, AST duplicate-name
guardrails, parsed ``game.*`` imports, heuristic ``likely_ownership_theme`` and
``likely_architecture_layer`` (engine / planner / gpt / gate / evaluator / smoke /
transcript / gauntlet / general), per-file ``marker_set`` / ``declared_pytest_markers``,
``collected_duplicate_base_names`` (parametrize / name reuse triage), parsed ``game.*`` imports,
overlap hints, optional ``ownership_registry_index`` (direct owner + neighbor suites), and
top-level ``block_b_overlap_clusters`` / ``import_hub_modules`` for consolidation triage.

JSON is written with sorted object keys for stable diffs aside from
``summary.generated_utc`` (see ``summary.inventory_schema_version``).

Also prints whether any module defines the same top-level ``test_*`` name twice
(Python keeps only the last — pytest would under-collect). Details:
``summary.files_with_shadowed_duplicate_test_defs`` in the JSON.
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

# Running as ``python tools/test_audit.py`` puts ``tools/`` on ``sys.path[0]``; repo root must precede it
# so ``tests.*`` imports (ownership registry snapshot) resolve.
_ROOT_STR = str(ROOT)
if _ROOT_STR not in sys.path:
    sys.path.insert(0, _ROOT_STR)

# Bump when adding/removing inventory fields or changing semantics (governance / CI may assert).
INVENTORY_SCHEMA_VERSION = 2

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
    """Snapshot of ``tests/test_ownership_registry.py`` for machine-readable neighbor maps."""
    try:
        from tests.test_ownership_registry import RESPONSIBILITY_REGISTRY
    except Exception:
        return None
    groups: dict[str, dict[str, object]] = {}
    for gid, rec in sorted(RESPONSIBILITY_REGISTRY.items()):
        groups[gid] = {
            "human_title": rec.human_title,
            "declared_architecture_layer": rec.declared_architecture_layer,
            "direct_owner": rec.direct_owner.replace("\\", "/"),
            "smoke_suites": [p.replace("\\", "/") for p in rec.smoke_suites],
            "transcript_suites": [p.replace("\\", "/") for p in rec.transcript_suites],
            "gauntlet_suites": [p.replace("\\", "/") for p in rec.gauntlet_suites],
            "evaluator_suites": [p.replace("\\", "/") for p in rec.evaluator_suites],
            "downstream_consumer_suites": [p.replace("\\", "/") for p in rec.downstream_consumer_suites],
            "compatibility_residue_suites": [p.replace("\\", "/") for p in rec.compatibility_residue_suites],
        }
    roles_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for gid in sorted(groups):
        row = groups[gid]
        d = str(row["direct_owner"])
        roles_by_path[d].append({"group_id": gid, "role": "direct_owner"})
        for p in row["smoke_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "smoke_suite"})
        for p in row["transcript_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "transcript_suite"})
        for p in row["gauntlet_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "gauntlet_suite"})
        for p in row["evaluator_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "evaluator_suite"})
        for p in row["downstream_consumer_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "downstream_consumer_suite"})
        for p in row["compatibility_residue_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "compatibility_residue_suite"})
    files_roles = {
        path: sorted(entries, key=lambda e: (e["role"], e["group_id"]))
        for path, entries in sorted(roles_by_path.items())
    }
    return {
        "available": True,
        "groups": groups,
        "files_roles": files_roles,
    }


def _architecture_layer_scores(fp: str, src: str, file_bucket: str) -> dict[str, int]:
    """Heuristic scores for ``ARCH_LAYERS``; higher wins (ties broken by ``ARCH_LAYERS`` order)."""
    bn = Path(fp).name.lower()
    sl = src.lower()
    scores = {layer: 0 for layer in ARCH_LAYERS}

    if file_bucket == "transcript_gauntlet" or "transcript_gauntlet" in bn:
        scores["gauntlet"] += 12
    if "gauntlet_regressions" in bn or "manual_gauntlet" in bn:
        scores["gauntlet"] += 8
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


def main() -> None:
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

    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(nodeids)} tests, {len(file_rows)} files)")
    # One-line overlap hint: themes touching the most distinct files (see JSON feature_areas_by_distinct_files).
    top_spread = spread_ranked[:8]
    if top_spread:
        parts = [f"{row['area']}: {row['distinct_files']} files" for row in top_spread]
        print("Overlap spread (heuristic primary feature tag; not proof of duplicate tests): " + "; ".join(parts))
    # Surface module-level duplicate test_* names (Python shadowing); pytest only runs the last def.
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


if __name__ == "__main__":
    main()
