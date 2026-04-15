"""Test ownership reconciliation helpers for ``architecture_audit.py``.

Pure static analysis only:
- stdlib only
- no runtime imports from ``game/``
- deterministic, inspectable heuristics
"""

from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TEST_CATEGORY_PRIORITY = (
    "transcript / scenario lock",
    "regression / bug class",
    "smoke / overlap",
    "integration / layer interaction",
    "unit / pure-rule",
    "unclear",
)
TEST_CATEGORY_WEIGHT = {
    "unit / pure-rule": 1.15,
    "integration / layer interaction": 1.0,
    "regression / bug class": 0.95,
    "transcript / scenario lock": 0.65,
    "smoke / overlap": 0.55,
    "unclear": 0.35,
}
SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}
HOTSPOT_SUBSYSTEMS = {
    "test ownership / inventory docs",
    "response policy contracts",
    "prompt contracts",
    "stage diff telemetry",
    "final emission gate orchestration",
}
OWNER_TERMS_RE = re.compile(
    r"\b(canonical owner|orchestration owner|owner|owns|home for|lives in|smoke overlap|integration smoke)\b",
    re.IGNORECASE,
)
REPO_PATH_RE = re.compile(r"\b(?:docs|game|tests|tools)/[A-Za-z0-9_.\-/]+\b")
BACKTICK_PATH_RE = re.compile(r"`([^`]+(?:\.py|\.md))`")
TRANSCRIPT_STRING_RE = re.compile(
    r"(turn\s+\d+|session\s+continuity|player asks|npc answers|speaker\s*[:=]|run_transcript)",
    re.IGNORECASE,
)
API_USAGE_RE = re.compile(r"(/api/(?:chat|action)|status_code|json\(\)|testclient|client\.post\()", re.IGNORECASE)
BROAD_OUTCOME_RE = re.compile(
    r"(player_facing_text|resolution|metadata|debug_notes|discovered_clues|_final_emission_meta)",
    re.IGNORECASE,
)


def _safe_parse(text: str) -> ast.AST | None:
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def _stem_tokens(path_or_name: str) -> list[str]:
    stem = Path(path_or_name).stem.lower()
    if stem.startswith("test_"):
        stem = stem[5:]
    for suffix in (
        "_regressions",
        "_regression",
        "_smoke",
        "_tests",
        "_test",
        "_shared",
        "_runner",
        "_contract",
        "_contracts",
        "_accessors",
    ):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return [token for token in re.split(r"[^a-z0-9]+", stem) if token]


def _common_token_score(left: str, right: str) -> int:
    left_tokens = set(_stem_tokens(left))
    right_tokens = set(_stem_tokens(right))
    overlap = left_tokens & right_tokens
    if not overlap:
        return 0
    if left_tokens == right_tokens:
        return 6
    return min(5, len(overlap) * 2)


def _extract_import_names(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)
    return sorted(set(imports))


def _extract_mark_names(node: ast.AST) -> list[str]:
    marks: list[str] = []

    def visit(expr: ast.AST) -> None:
        if isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
            for item in expr.elts:
                visit(item)
            return
        if isinstance(expr, ast.Call):
            visit(expr.func)
            return
        if isinstance(expr, ast.Attribute):
            chain: list[str] = []
            current: ast.AST | None = expr
            while isinstance(current, ast.Attribute):
                chain.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                chain.append(current.id)
            full = ".".join(reversed(chain))
            if full.startswith("pytest.mark.") and len(chain) >= 3:
                marks.append(chain[0])
            return

    visit(node)
    return list(dict.fromkeys(marks))


def _module_markers(tree: ast.AST) -> list[str]:
    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets):
            continue
        return _extract_mark_names(node.value)
    return []


def _node_text(text: str, node: ast.AST) -> str:
    if not getattr(node, "lineno", None) or not getattr(node, "end_lineno", None):
        return ""
    lines = text.splitlines()
    start = max(int(node.lineno) - 1, 0)
    end = min(int(node.end_lineno), len(lines))
    return "\n".join(lines[start:end])


def _iter_test_nodes(tree: ast.AST) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    out: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            out.append((node.name, node))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                    out.append((f"{node.name}.{child.name}", child))
    return out


def _case_strings(node: ast.AST) -> list[str]:
    out: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            out.append(child.value)
    return out


def _classify_test_case(
    *,
    path: str,
    module_markers: list[str],
    import_names: list[str],
    direct_internal_imports: list[str],
    name: str,
    fixture_names: list[str],
    body_text: str,
    string_literals: list[str],
) -> str:
    path_lower = path.lower()
    name_lower = name.lower()
    body_lower = body_text.lower()
    markers = {item.lower() for item in module_markers}
    fixtures = {item.lower() for item in fixture_names}
    joined_strings = "\n".join(string_literals)
    assert_count = body_lower.count("assert ")

    scores: Counter[str] = Counter()
    if (
        "transcript" in path_lower
        or "gauntlet" in path_lower
        or "transcript" in name_lower
        or "scenario" in name_lower
        or "transcript" in markers
        or "slow" in markers
        or "run_transcript" in body_lower
        or (joined_strings.count("\n") >= 2 and TRANSCRIPT_STRING_RE.search(joined_strings))
    ):
        scores["transcript / scenario lock"] += 8
    if "regression" in path_lower or "regression" in name_lower or "regression" in markers or "bug" in name_lower:
        scores["regression / bug class"] += 7
    if "smoke" in path_lower or "smoke" in name_lower or "smoke" in markers:
        scores["smoke / overlap"] += 7
    if (
        "integration" in markers
        or API_USAGE_RE.search(body_text)
        or "tmp_path" in fixtures
        or "monkeypatch" in fixtures
        or "client" in fixtures
        or any("fastapi.testclient" in item.lower() for item in import_names)
        or any(path.startswith("game/api.py") or path.startswith("game/storage.py") for path in direct_internal_imports)
        or BROAD_OUTCOME_RE.search(body_text)
    ):
        scores["integration / layer interaction"] += 5
    if (
        "unit" in markers
        or (
            assert_count <= 6
            and not API_USAGE_RE.search(body_text)
            and "tmp_path" not in fixtures
            and "monkeypatch" not in fixtures
            and any(path.startswith("game/") for path in direct_internal_imports)
        )
    ):
        scores["unit / pure-rule"] += 4

    if not scores:
        return "unclear"
    best_score = max(scores.values())
    for category in TEST_CATEGORY_PRIORITY:
        if scores.get(category, 0) == best_score:
            return category
    return "unclear"


def _analyze_test_file(record: Any) -> dict[str, Any]:
    tree = _safe_parse(str(getattr(record, "text", "") or ""))
    if tree is None:
        return {
            "path": record.rel_path,
            "file_category": "unclear",
            "module_markers": [],
            "import_names": [],
            "direct_runtime_imports": [path for path in getattr(record, "internal_imports", []) if path.startswith("game/")],
            "direct_tool_imports": [path for path in getattr(record, "internal_imports", []) if path.startswith("tools/")],
            "mentioned_paths": [],
            "test_cases": [],
        }

    module_markers = _module_markers(tree)
    import_names = _extract_import_names(tree)
    text = str(getattr(record, "text", "") or "")
    direct_runtime_imports = [
        path
        for path in getattr(record, "internal_imports", []) or []
        if path.startswith("game/") and path.endswith(".py")
    ]
    direct_tool_imports = [
        path
        for path in getattr(record, "internal_imports", []) or []
        if path.startswith("tools/") and path.endswith(".py")
    ]
    mentioned_paths = sorted(set(REPO_PATH_RE.findall(text)))
    test_cases: list[dict[str, Any]] = []
    case_category_counts: Counter[str] = Counter()

    for name, node in _iter_test_nodes(tree):
        body_text = _node_text(text, node)
        string_literals = _case_strings(node)
        fixture_names = [arg.arg for arg in node.args.args]
        case_markers: list[str] = []
        for decorator in node.decorator_list:
            case_markers.extend(_extract_mark_names(decorator))
        category = _classify_test_case(
            path=record.rel_path,
            module_markers=module_markers + case_markers,
            import_names=import_names,
            direct_internal_imports=direct_runtime_imports,
            name=name,
            fixture_names=fixture_names,
            body_text=body_text,
            string_literals=string_literals,
        )
        case_category_counts[category] += 1
        test_cases.append(
            {
                "name": name,
                "category": category,
                "markers": sorted(set(module_markers + case_markers)),
                "fixture_names": fixture_names,
                "assert_count": body_text.count("assert "),
                "transcript_like_strings": bool(
                    any(item.count("\n") >= 2 and TRANSCRIPT_STRING_RE.search(item) for item in string_literals)
                ),
                "broad_outcome_assertions": bool(BROAD_OUTCOME_RE.search(body_text) and body_text.count("assert ") >= 3),
            }
        )

    if case_category_counts:
        top_count = max(case_category_counts.values())
        file_category = next(
            category
            for category in TEST_CATEGORY_PRIORITY
            if case_category_counts.get(category, 0) == top_count
        )
    elif "transcript" in module_markers:
        file_category = "transcript / scenario lock"
    elif "integration" in module_markers:
        file_category = "integration / layer interaction"
    elif "unit" in module_markers:
        file_category = "unit / pure-rule"
    else:
        file_category = "unclear"

    return {
        "path": record.rel_path,
        "file_category": file_category,
        "module_markers": module_markers,
        "import_names": import_names,
        "direct_runtime_imports": direct_runtime_imports,
        "direct_tool_imports": direct_tool_imports,
        "mentioned_paths": mentioned_paths,
        "test_cases": test_cases,
        "case_category_counts": dict(case_category_counts),
        "transcript_like_case_count": sum(1 for item in test_cases if item["transcript_like_strings"]),
    }


def _basename_index(records: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for rel_path in records:
        out[Path(rel_path).name.lower()].append(rel_path)
    return {name: sorted(paths) for name, paths in out.items()}


def _extract_doc_claims(
    *,
    records: dict[str, Any],
    related_docs: list[str],
    candidate_paths: list[str],
) -> list[dict[str, Any]]:
    basename_map = _basename_index(records)
    candidate_set = set(candidate_paths)
    claims: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for doc_path in related_docs:
        record = records.get(doc_path)
        if record is None:
            continue
        for raw_line in str(getattr(record, "text", "") or "").splitlines():
            line = raw_line.strip()
            if not line or not OWNER_TERMS_RE.search(line):
                continue
            mentions = set(REPO_PATH_RE.findall(line))
            mentions.update(item for item in BACKTICK_PATH_RE.findall(line) if "/" in item or item.startswith("test_"))
            resolved_paths: list[str] = []
            for item in mentions:
                clean = item.strip().strip("`")
                if clean in candidate_set:
                    resolved_paths.append(clean)
                    continue
                name = Path(clean).name.lower()
                for path in basename_map.get(name, []):
                    if path in candidate_set:
                        resolved_paths.append(path)
            for ref_path in sorted(set(resolved_paths)):
                owner_type = "runtime" if ref_path.startswith("game/") else "test" if ref_path.startswith("tests/") else "tool"
                strength = "strong" if re.search(r"\b(canonical owner|orchestration owner|owns)\b", line, re.IGNORECASE) else "soft"
                claim_key = (doc_path, ref_path, line)
                if claim_key in seen:
                    continue
                seen.add(claim_key)
                claims.append(
                    {
                        "source": doc_path,
                        "claimed_owner": ref_path,
                        "owner_type": owner_type,
                        "strength": strength,
                        "excerpt": line[:220],
                    }
                )
    claims.sort(key=lambda item: (item["owner_type"] != "runtime", item["strength"] != "strong", item["claimed_owner"]))
    return claims[:12]


def _path_affinity(test_info: dict[str, Any], target_path: str) -> tuple[int, list[str], bool]:
    score = 0
    evidence: list[str] = []
    direct = False
    if target_path in test_info["direct_runtime_imports"]:
        score += 8
        direct = True
        evidence.append(f"direct import `{target_path}`")
    elif _common_token_score(test_info["path"], target_path) >= 5:
        score += 6
        direct = True
        evidence.append(f"filename mirrors `{Path(target_path).name}`")
    else:
        token_score = _common_token_score(test_info["path"], target_path)
        if token_score:
            score += token_score
            evidence.append(f"filename overlap with `{Path(target_path).name}`")
    if target_path in test_info["mentioned_paths"]:
        score += 3
        evidence.append(f"text mentions `{target_path}`")
    elif Path(target_path).name.lower() in {Path(item).name.lower() for item in test_info["mentioned_paths"]}:
        score += 2
        evidence.append(f"text mentions `{Path(target_path).name}`")
    return score, evidence[:3], direct


def _is_prompt_lifecycle_adjacency(
    test_info: dict[str, Any],
    subsystem_report: dict[str, Any],
    target_path: str,
) -> bool:
    if subsystem_report.get("subsystem_name") != "prompt contracts":
        return False
    if target_path != "game/prompt_context.py":
        return False
    path_tokens = set(_stem_tokens(test_info["path"]))
    if {"prompt", "context"} & path_tokens:
        return False
    if not {"lead", "lifecycle", "vertical", "pipeline", "progression", "repeat", "npc"} & path_tokens:
        return False
    imported_symbols = {
        "game.prompt_context.build_authoritative_lead_prompt_context",
        "game.prompt_context.build_narration_context",
    }
    return bool(imported_symbols & set(test_info.get("import_names", [])))


def _is_gate_downstream_adjacency(
    test_info: dict[str, Any],
    subsystem_report: dict[str, Any],
    target_path: str,
) -> bool:
    if subsystem_report.get("subsystem_name") != "final emission gate orchestration":
        return False
    if target_path != "game/final_emission_gate.py":
        return False
    path_tokens = set(_stem_tokens(test_info["path"]))
    if {"final", "emission", "gate"} <= path_tokens:
        return False
    downstream_runtime_imports = {
        "game/anti_railroading.py",
        "game/anti_reset_emission_guard.py",
        "game/final_emission_meta.py",
        "game/final_emission_repairs.py",
        "game/final_emission_validators.py",
        "game/social_exchange_emission.py",
        "game/stage_diff_telemetry.py",
        "game/api_turn_support.py",
    }
    if downstream_runtime_imports & set(test_info.get("direct_runtime_imports", [])):
        return True
    return bool(
        path_tokens
        & {
            "scene",
            "integrity",
            "visibility",
            "response",
            "delta",
            "telemetry",
            "pipeline",
            "dead",
            "social",
            "exchange",
            "quality",
            "transcript",
            "anti",
            "reset",
            "guard",
            "railroading",
            "retry",
            "alignment",
            "validator",
            "repair",
            "meta",
        }
    )


def _subsystem_test_affinity(test_info: dict[str, Any], subsystem_report: dict[str, Any]) -> dict[str, Any]:
    target_paths: list[str] = []
    runtime_owner = subsystem_report.get("inferred_owner")
    if isinstance(runtime_owner, str) and runtime_owner.startswith("game/"):
        target_paths.append(runtime_owner)
    else:
        target_paths.extend(
            path
            for path in subsystem_report.get("primary_files", [])
            if isinstance(path, str) and path.startswith("game/")
        )
    target_paths = list(dict.fromkeys(target_paths))

    score = 0
    evidence: list[str] = []
    direct_runtime_match = False
    for target_path in target_paths:
        path_score, path_evidence, is_direct = _path_affinity(test_info, target_path)
        if _is_prompt_lifecycle_adjacency(test_info, subsystem_report, target_path):
            path_score = max(0, path_score - 3)
            path_evidence.append("downstream lifecycle import of exported prompt-context builder")
        if _is_gate_downstream_adjacency(test_info, subsystem_report, target_path):
            path_score = max(0, path_score - 4)
            path_evidence.append("downstream gate-consumer suite around a layer-specific concern")
        score += path_score
        evidence.extend(path_evidence)
        if target_path == runtime_owner and is_direct:
            direct_runtime_match = True

    subsystem_tokens = [token for token in re.split(r"[^a-z0-9]+", subsystem_report["subsystem_name"].lower()) if len(token) >= 4]
    path_tokens = set(_stem_tokens(test_info["path"]))
    shared_tokens = sorted(path_tokens & set(subsystem_tokens))
    if shared_tokens:
        score += min(4, len(shared_tokens) * 2)
        evidence.append("subsystem token overlap: " + ", ".join(shared_tokens[:3]))

    category = test_info["file_category"]
    weighted_score = round(score * TEST_CATEGORY_WEIGHT[category], 2)
    return {
        "path": test_info["path"],
        "category": category,
        "score": weighted_score,
        "raw_score": score,
        "direct_runtime_match": direct_runtime_match,
        "evidence": list(dict.fromkeys(evidence))[:4],
    }


def _primary_and_secondary_homes(affinities: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not affinities:
        return [], []
    ordered = sorted(affinities, key=lambda item: (-item["score"], item["path"]))
    top_score = ordered[0]["score"]
    if top_score <= 0:
        return [], []
    primary = [item for item in ordered if item["score"] >= max(4.0, round(top_score * 0.7, 2))]
    primary_paths = {item["path"] for item in primary}
    secondary = [item for item in ordered if item["score"] >= 2.0 and item["path"] not in primary_paths]
    return primary[:4], secondary[:6]


def _doc_claim_summary(doc_claims: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for item in doc_claims:
        if item["claimed_owner"] not in out[item["owner_type"]]:
            out[item["owner_type"]].append(item["claimed_owner"])
    return {key: value[:5] for key, value in out.items()}


def _alignment_for_subsystem(
    subsystem_report: dict[str, Any],
    related_test_files: list[dict[str, Any]],
    doc_claims: list[dict[str, Any]],
) -> dict[str, Any]:
    runtime_owner = subsystem_report.get("inferred_owner", "unknown")
    role_labels = subsystem_report.get("role_labels", [])
    affinities = [_subsystem_test_affinity(item, subsystem_report) for item in related_test_files]
    affinities = [item for item in affinities if item["score"] > 0]
    primary_homes, secondary_homes = _primary_and_secondary_homes(affinities)
    practical_owner = (
        primary_homes[0]["path"]
        if len(primary_homes) == 1
        else "mixed: " + ", ".join(item["path"] for item in primary_homes[:3])
        if primary_homes
        else "unknown"
    )
    category_counts = Counter(item["category"] for item in affinities)
    direct_runtime_homes = [item["path"] for item in primary_homes if item["direct_runtime_match"]]
    doc_summary = _doc_claim_summary(doc_claims)
    docs_runtime_claims = doc_summary.get("runtime", [])
    docs_test_claims = doc_summary.get("test", [])
    docs_runtime_agree = not docs_runtime_claims or runtime_owner in docs_runtime_claims
    primary_categories = {item["category"] for item in primary_homes}
    spread = len(primary_homes) + len(secondary_homes)

    alignment_status = "aligned"
    mismatch_type = "healthy_overlap"
    severity = "low"
    evidence: list[str] = []

    if not primary_homes:
        alignment_status = "unclear"
        mismatch_type = "no_practical_test_owner"
        severity = "high"
        evidence.append("No related test file accumulated enough concern-specific affinity.")
    elif runtime_owner == "unknown":
        alignment_status = "unclear"
        mismatch_type = "runtime_owner_unknown"
        severity = "medium"
        evidence.append("Runtime owner stayed ambiguous, so test reconciliation could only be partial.")
    elif not direct_runtime_homes:
        alignment_status = "conflict" if docs_runtime_agree else "partial"
        mismatch_type = "tests_center_adjacent_or_diffuse_owner"
        severity = "high" if "contract_owner" in role_labels or "validator_owner" in role_labels else "medium"
        evidence.append(f"No primary test home directly mirrors runtime owner `{runtime_owner}`.")
    elif primary_categories <= {"smoke / overlap"}:
        alignment_status = "conflict"
        mismatch_type = "smoke_overlap_primary_protection"
        severity = "high"
        evidence.append("Smoke-style suites appear to be the main protection surface.")
    elif "transcript / scenario lock" in primary_categories and {"contract_owner", "validator_owner"} & set(role_labels):
        alignment_status = "conflict"
        mismatch_type = "transcript_primary_for_contract_owner"
        severity = "high"
        evidence.append("Transcript-style tests dominate a concern that looks contract-owned at runtime.")
    elif docs_test_claims and practical_owner != "unknown" and practical_owner not in docs_test_claims:
        alignment_status = "partial"
        mismatch_type = "docs_claim_owner_tests_target_other_home"
        severity = "medium"
        evidence.append("Docs name a canonical test owner, but practical coverage concentrates elsewhere.")
    elif spread >= 6 and len(primary_homes) >= 2:
        alignment_status = "partial"
        mismatch_type = "ownership_spread_wide"
        severity = "medium"
        evidence.append("Coverage is spread across many homes rather than anchored in one direct owner suite.")
    elif not docs_runtime_agree:
        alignment_status = "partial"
        mismatch_type = "docs_runtime_owner_drift"
        severity = "medium"
        evidence.append("Docs still point at a different runtime owner than AR2's inferred owner.")

    if subsystem_report["subsystem_name"] == "test ownership / inventory docs":
        if docs_test_claims and practical_owner == "unknown":
            alignment_status = "partial"
            mismatch_type = "inventory_docs_authority_unclear"
            severity = "medium"
            evidence.append(
                "Inventory docs now describe the governance map more coherently, but practical test affinity remains weak because this concern is docs-led rather than runtime-owned."
            )
        elif not docs_test_claims and spread >= 4:
            alignment_status = "unclear"
            mismatch_type = "inventory_docs_authority_unclear"
            severity = "high"
            evidence.append("Inventory docs talk about ownership, but no clear practical owner emerges.")
        elif docs_test_claims and practical_owner != "unknown" and practical_owner not in docs_test_claims:
            alignment_status = "partial"
            mismatch_type = "inventory_docs_vs_actual_usage"
            severity = "high"
            evidence.append("Inventory docs act canonical in prose, but day-to-day coverage concentrates elsewhere.")

    if subsystem_report["subsystem_name"] in HOTSPOT_SUBSYSTEMS and severity == "medium":
        severity = "high"

    for item in primary_homes[:3]:
        evidence.append(f"primary home `{item['path']}` ({item['category']}; score {item['score']})")
        evidence.extend(item["evidence"][:2])
    if docs_runtime_claims:
        evidence.append("docs runtime claims: " + ", ".join(f"`{item}`" for item in docs_runtime_claims[:3]))
    if docs_test_claims:
        evidence.append("docs test claims: " + ", ".join(f"`{item}`" for item in docs_test_claims[:3]))

    healthy_overlap = (
        alignment_status == "aligned"
        and bool(direct_runtime_homes)
        and any(item["category"] in {"integration / layer interaction", "smoke / overlap"} for item in secondary_homes)
    )

    return {
        "concern_name": subsystem_report["subsystem_name"],
        "runtime_owner": runtime_owner,
        "declared_runtime_owner": subsystem_report.get("declared_owner", "unknown"),
        "doc_canonical_owners": doc_claims,
        "practical_test_owner": practical_owner,
        "primary_test_homes": primary_homes,
        "secondary_test_homes": secondary_homes,
        "direct_runtime_owner_test_homes": direct_runtime_homes,
        "alignment_status": alignment_status,
        "mismatch_type": mismatch_type,
        "severity": severity,
        "healthy_overlap": healthy_overlap,
        "coverage_spread": spread,
        "category_counts": dict(category_counts),
        "evidence": list(dict.fromkeys(evidence))[:10],
    }


def _inventory_docs_authority_status(item: dict[str, Any] | None) -> dict[str, Any]:
    if not item:
        return {
            "status": "missing",
            "summary": "The seeded test ownership / inventory docs subsystem did not resolve.",
            "evidence": [],
        }
    if item["alignment_status"] == "aligned":
        status = "clearer"
        summary = "Inventory docs and practical test homes mostly agree on where ownership lives."
    elif item["alignment_status"] == "partial":
        status = "partially clearer"
        summary = "Inventory docs identify owners more clearly now, but adjacent-home heuristics still over-read some practical coverage."
    else:
        status = "remains unclear"
        summary = "Inventory docs still read as canonical prose while practical ownership stays diffuse or shifted."
    return {"status": status, "summary": summary, "evidence": item.get("evidence", [])[:5]}


def analyze_test_ownership(
    *,
    records: dict[str, Any],
    subsystem_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    test_files: dict[str, dict[str, Any]] = {}
    test_case_category_counts: Counter[str] = Counter()
    test_file_category_counts: Counter[str] = Counter()

    for rel_path, record in sorted(records.items()):
        if not rel_path.startswith("tests/") or not rel_path.endswith(".py"):
            continue
        info = _analyze_test_file(record)
        test_files[rel_path] = info
        test_file_category_counts[info["file_category"]] += 1
        test_case_category_counts.update(info.get("case_category_counts", {}))

    subsystem_findings: dict[str, dict[str, Any]] = {}
    mismatch_items: list[dict[str, Any]] = []
    transcript_risks: list[dict[str, Any]] = []
    weak_contract_seams: list[dict[str, Any]] = []
    ownership_spread: list[dict[str, Any]] = []

    for subsystem_report in subsystem_reports:
        related_tests = [
            test_files[path]
            for path in subsystem_report.get("related_tests", [])
            if path.endswith(".py") and path in test_files
        ]
        candidate_paths = list(
            dict.fromkeys(
                list(subsystem_report.get("primary_files", []))
                + list(subsystem_report.get("related_tests", []))
                + [subsystem_report.get("inferred_owner", "")]
            )
        )
        doc_claims = _extract_doc_claims(
            records=records,
            related_docs=[path for path in subsystem_report.get("related_docs", []) if path in records],
            candidate_paths=[path for path in candidate_paths if path],
        )
        item = _alignment_for_subsystem(subsystem_report, related_tests, doc_claims)
        subsystem_findings[subsystem_report["subsystem_name"]] = item
        ownership_spread.append(
            {
                "concern_name": subsystem_report["subsystem_name"],
                "runtime_owner": item["runtime_owner"],
                "coverage_spread": item["coverage_spread"],
                "primary_test_homes": [entry["path"] for entry in item["primary_test_homes"]],
                "secondary_test_homes": [entry["path"] for entry in item["secondary_test_homes"]],
            }
        )
        if item["alignment_status"] in {"partial", "conflict", "unclear"}:
            mismatch_items.append(item)
        if any(entry["category"] == "transcript / scenario lock" for entry in item["primary_test_homes"]):
            transcript_risks.append(
                {
                    "concern_name": item["concern_name"],
                    "runtime_owner": item["runtime_owner"],
                    "practical_test_owner": item["practical_test_owner"],
                    "severity": item["severity"],
                    "evidence": item["evidence"][:4],
                }
            )
        if {"contract_owner", "validator_owner"} & set(subsystem_report.get("role_labels", [])) and not item[
            "direct_runtime_owner_test_homes"
        ]:
            weak_contract_seams.append(
                {
                    "concern_name": item["concern_name"],
                    "runtime_owner": item["runtime_owner"],
                    "practical_test_owner": item["practical_test_owner"],
                    "severity": item["severity"],
                    "evidence": item["evidence"][:4],
                }
            )

    mismatch_items.sort(
        key=lambda item: (
            -SEVERITY_RANK[item["severity"]],
            item["concern_name"] not in HOTSPOT_SUBSYSTEMS,
            -item["coverage_spread"],
            item["concern_name"],
        )
    )
    transcript_risks.sort(key=lambda item: (-SEVERITY_RANK[item["severity"]], item["concern_name"]))
    weak_contract_seams.sort(key=lambda item: (-SEVERITY_RANK[item["severity"]], item["concern_name"]))
    ownership_spread.sort(key=lambda item: (-item["coverage_spread"], item["concern_name"]))

    alignment_counts = Counter(item["alignment_status"] for item in subsystem_findings.values())
    inventory_status = _inventory_docs_authority_status(subsystem_findings.get("test ownership / inventory docs"))

    manual_review_shortlist = []
    for name in (
        "test ownership / inventory docs",
        "response policy contracts",
        "prompt contracts",
        "stage diff telemetry",
        "final emission gate orchestration",
    ):
        item = subsystem_findings.get(name)
        if not item:
            continue
        manual_review_shortlist.append(
            {
                "concern_name": item["concern_name"],
                "runtime_owner": item["runtime_owner"],
                "practical_test_owner": item["practical_test_owner"],
                "alignment_status": item["alignment_status"],
                "severity": item["severity"],
                "evidence": item["evidence"][:5],
            }
        )

    return {
        "test_files": test_files,
        "subsystem_findings": subsystem_findings,
        "summary": {
            "test_category_counts": {
                category: test_case_category_counts.get(category, 0)
                for category in TEST_CATEGORY_PRIORITY
                if test_case_category_counts.get(category, 0)
            },
            "test_file_category_counts": {
                category: test_file_category_counts.get(category, 0)
                for category in TEST_CATEGORY_PRIORITY
                if test_file_category_counts.get(category, 0)
            },
            "test_alignment_overview": dict(alignment_counts),
            "top_test_runtime_doc_mismatches": mismatch_items[:8],
            "concerns_with_widest_test_ownership_spread": ownership_spread[:8],
            "likely_transcript_lock_seams": transcript_risks[:8],
            "likely_contract_owned_seams_with_weak_direct_tests": weak_contract_seams[:8],
            "inventory_docs_authority_status": inventory_status,
            "manual_review_shortlist": manual_review_shortlist[:8],
            "schema_notes": [
                "subsystem_reports now include test_ownership_alignment with runtime/doc/test reconciliation fields.",
                "tests_analyzed now includes deterministic file/test category counts and per-file inferred categories.",
                "summary now includes top_test_runtime_doc_mismatches, concerns_with_widest_test_ownership_spread, likely_transcript_lock_seams, likely_contract_owned_seams_with_weak_direct_tests, inventory_docs_authority_status, and manual_review_shortlist.",
            ],
        },
    }
