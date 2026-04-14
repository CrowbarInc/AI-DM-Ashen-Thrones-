"""Runtime ownership and overlap heuristics for ``architecture_audit.py``.

Pure static analysis only:
- stdlib only
- no runtime imports from ``game/``
- deterministic, inspectable heuristics
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROLE_PRIORITY = (
    "orchestration_owner",
    "validator_owner",
    "repair_owner",
    "text_utility_owner",
    "contract_owner",
    "telemetry_owner",
)
ROLE_LABELS = ROLE_PRIORITY + ("mixed_owner", "unclear_owner")
ROLE_PREFIXES = (
    "validate_",
    "inspect_",
    "candidate_satisfies_",
    "repair_",
    "_repair_",
    "apply_",
    "_apply_",
    "merge_",
    "_merge_",
    "build_",
    "resolve_",
    "peek_",
    "snapshot_",
    "diff_",
)
OWNER_LINE_RE = re.compile(
    r"\b(owner|canonical owner|orchestration owner|orchestration home|single source of truth|not the ownership home)\b",
    re.IGNORECASE,
)
ROLE_DECLARATION_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "orchestration_owner": (
        re.compile(r"\borchestration owner\b", re.IGNORECASE),
        re.compile(r"\borchestration home\b", re.IGNORECASE),
        re.compile(r"\bapply_final_emission_gate\b.*\borchestration\b", re.IGNORECASE),
        re.compile(r"\blayer order\b", re.IGNORECASE),
    ),
    "validator_owner": (
        re.compile(r"\bdeterministic validators?\b", re.IGNORECASE),
        re.compile(r"\bpure checks only\b", re.IGNORECASE),
        re.compile(r"\bwhether text satisfies a contract\b", re.IGNORECASE),
        re.compile(r"\bvalidator\b", re.IGNORECASE),
    ),
    "repair_owner": (
        re.compile(r"\brepair and layer wiring\b", re.IGNORECASE),
        re.compile(r"\bdeterministic repair\b", re.IGNORECASE),
        re.compile(r"\bhow to repair\b", re.IGNORECASE),
        re.compile(r"\brepair\b", re.IGNORECASE),
    ),
    "text_utility_owner": (
        re.compile(r"\bshared text utilities\b", re.IGNORECASE),
        re.compile(r"\bnormalization\b", re.IGNORECASE),
        re.compile(r"\bshared patterns\b", re.IGNORECASE),
        re.compile(r"\bno policy orchestration\b", re.IGNORECASE),
        re.compile(r"\btext utilities\b", re.IGNORECASE),
    ),
    "contract_owner": (
        re.compile(r"\bcontract resolution\b", re.IGNORECASE),
        re.compile(r"\bresponse shape the writer owed\b", re.IGNORECASE),
        re.compile(r"\bprompt layer\b", re.IGNORECASE),
        re.compile(r"\bresponse_policy\b", re.IGNORECASE),
        re.compile(r"\bcontract\b", re.IGNORECASE),
    ),
    "telemetry_owner": (
        re.compile(r"\bstage[- ]diff telemetry\b", re.IGNORECASE),
        re.compile(r"\bobservability only\b", re.IGNORECASE),
        re.compile(r"\btelemetry\b", re.IGNORECASE),
        re.compile(r"\bsnapshot\b", re.IGNORECASE),
    ),
}
ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "orchestration_owner": (
        "orchestration",
        "layer order",
        "strict-social",
        "sequences",
        "orders layers",
        "integration",
        "gate",
    ),
    "validator_owner": (
        "validator",
        "validators",
        "pure checks",
        "validate_",
        "inspect_",
        "candidate_satisfies_",
    ),
    "repair_owner": (
        "repair",
        "repairs",
        "repair_",
        "apply_",
        "merge_",
        "skip",
        "extracted from",
    ),
    "text_utility_owner": (
        "normalize",
        "normalization",
        "sanitize",
        "shared text",
        "patterns",
        "text utilities",
    ),
    "contract_owner": (
        "contract",
        "contracts",
        "response_policy",
        "build_",
        "resolve_",
        "prompt layer",
    ),
    "telemetry_owner": (
        "telemetry",
        "observability",
        "snapshot",
        "diff",
        "trace",
    ),
}
ROLE_FILE_HINTS: dict[str, tuple[str, ...]] = {
    "orchestration_owner": ("gate",),
    "validator_owner": ("validator", "validators"),
    "repair_owner": ("repair", "repairs"),
    "text_utility_owner": ("text",),
    "contract_owner": ("contract", "prompt_context"),
    "telemetry_owner": ("telemetry",),
}
ARCHAEOLOGY_TERMS: dict[str, tuple[str, ...]] = {
    "compatibility": ("compatibility", "remain importable", "re-expose", "re-export"),
    "historical": ("historical", "historically", "historical tests"),
    "extracted_from": ("extracted from",),
    "deferred": ("deferred",),
    "not_owner": ("not the owner", "not the ownership home"),
}
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1, "unclear": 0}
SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}


def _rel_path_list(paths: list[str]) -> list[str]:
    return list(dict.fromkeys(sorted(paths)))


def _record_text_lines(record: Any) -> list[str]:
    return [line.strip() for line in str(getattr(record, "text", "") or "").splitlines() if line.strip()]


def _docstring_lines(record: Any) -> list[str]:
    return [line.strip() for line in str(getattr(record, "docstring", "") or "").splitlines() if line.strip()]


def _contains_any(line: str, phrases: tuple[str, ...]) -> bool:
    lower = line.lower()
    return any(phrase in lower for phrase in phrases)


def _extract_references(records: dict[str, Any], focus_paths: list[str]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    doc_refs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    test_refs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rel_path, record in sorted(records.items()):
        is_doc = rel_path.startswith("docs/") and rel_path.endswith(".md")
        is_test = rel_path.startswith("tests/")
        if not (is_doc or is_test):
            continue
        lines = _record_text_lines(record)
        lowered_lines = [line.lower() for line in lines]
        for target in focus_paths:
            target_lower = target.lower()
            basename_lower = Path(target).name.lower()
            matches = [
                lines[idx]
                for idx, lowered in enumerate(lowered_lines)
                if target_lower in lowered or basename_lower in lowered
            ]
            if not matches:
                continue
            payload = {"source": rel_path, "matches": matches[:5]}
            if is_doc:
                doc_refs[target].append(payload)
            else:
                test_refs[target].append(payload)
    return dict(doc_refs), dict(test_refs)


def _count_keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    lower = text.lower()
    return sum(lower.count(keyword.lower()) for keyword in keywords)


def _owner_declaration(record: Any, doc_refs: list[dict[str, Any]]) -> tuple[str, str | None]:
    for line in _docstring_lines(record):
        if OWNER_LINE_RE.search(line):
            return f"module docstring: {line}", getattr(record, "rel_path", None)
    for ref in doc_refs:
        for line in ref["matches"]:
            if OWNER_LINE_RE.search(line):
                return f"{ref['source']}: {line}", getattr(record, "rel_path", None)
    return "unknown", None


def _role_signal_evidence(record: Any, doc_refs: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, list[str]], dict[str, int]]:
    rel_path = str(getattr(record, "rel_path", ""))
    stem = Path(rel_path).stem.lower()
    text = str(getattr(record, "text", "") or "")
    docstring = str(getattr(record, "docstring", "") or "")
    function_names = list(getattr(record, "function_names", []) or [])
    scores: Counter[str] = Counter()
    evidence: dict[str, list[str]] = defaultdict(list)
    concern_counts: dict[str, int] = {}

    def add(role: str, points: int, reason: str) -> None:
        scores[role] += points
        if reason not in evidence[role] and len(evidence[role]) < 5:
            evidence[role].append(reason)

    for role, hints in ROLE_FILE_HINTS.items():
        if any(hint in stem for hint in hints):
            add(role, 3, f"filename hint: `{Path(rel_path).name}`")

    for role, patterns in ROLE_DECLARATION_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(docstring):
                add(role, 5, f"docstring declaration: {pattern.pattern}")
                break

    for role, patterns in ROLE_DECLARATION_PATTERNS.items():
        for ref in doc_refs:
            for line in ref["matches"]:
                if pattern := next((item for item in patterns if item.search(line)), None):
                    add(role, 4, f"{ref['source']}: {line}")
                    break

    for fn_name in function_names:
        if fn_name.startswith(("validate_", "inspect_", "candidate_satisfies_")):
            add("validator_owner", 1, f"function prefix: `{fn_name}`")
        if fn_name.startswith(("repair_", "_repair_")):
            add("repair_owner", 1, f"function prefix: `{fn_name}`")
        if fn_name.startswith(("build_", "resolve_", "peek_")):
            add("contract_owner", 1, f"function prefix: `{fn_name}`")
        if fn_name.startswith(("snapshot_", "diff_")) or "telemetry" in fn_name:
            add("telemetry_owner", 1, f"function prefix: `{fn_name}`")
        if fn_name.startswith(("apply_", "_apply_")):
            if "repair" in stem:
                add("repair_owner", 1, f"layer wiring prefix: `{fn_name}`")
            elif "gate" in stem:
                add("orchestration_owner", 1, f"gate apply prefix: `{fn_name}`")
        if fn_name.startswith(("_normalize", "_sanitize", "compact_", "render_")) and ("text" in stem or "telemetry" in stem):
            add("text_utility_owner", 1, f"utility prefix: `{fn_name}`")

    for role, keywords in ROLE_KEYWORDS.items():
        count = _count_keyword_hits(text, keywords)
        concern_counts[role] = count
        if count >= 6:
            add(role, 3, f"concern language density: {count}")
        elif count >= 3:
            add(role, 2, f"concern language density: {count}")
        elif count >= 1:
            add(role, 1, f"concern language density: {count}")

    return dict(scores), dict(evidence), concern_counts


def _role_labels_and_confidence(role_scores: dict[str, int]) -> tuple[list[str], str]:
    if not role_scores:
        return ["unclear_owner"], "unclear"
    ordered = sorted(((score, role) for role, score in role_scores.items()), reverse=True)
    top_score = ordered[0][0]
    second_score = ordered[1][0] if len(ordered) > 1 else 0
    substantive = [role for role in ROLE_PRIORITY if role_scores.get(role, 0) >= max(4, top_score - 2)]
    if not substantive:
        return ["unclear_owner"], "unclear"
    labels = list(substantive)
    if len(substantive) > 1:
        labels.append("mixed_owner")
    if len(substantive) == 1 and top_score >= 10 and second_score <= top_score - 4:
        confidence = "high"
    elif len(substantive) == 1 and top_score >= 7 and second_score <= top_score - 2:
        confidence = "medium"
    elif top_score >= 4:
        confidence = "low"
    else:
        confidence = "unclear"
    return labels, confidence


def _archaeology_markers(record: Any) -> list[dict[str, str]]:
    markers: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line in _record_text_lines(record):
        for kind, phrases in ARCHAEOLOGY_TERMS.items():
            if _contains_any(line, phrases):
                item = (kind, line)
                if item in seen:
                    continue
                seen.add(item)
                markers.append({"kind": kind, "excerpt": line[:220]})
                break
    return markers[:8]


def _coupling_indicators(
    record: Any,
    fan_in: dict[str, int],
    fan_out: dict[str, int],
    concern_counts: dict[str, int],
    archaeology_markers: list[dict[str, str]],
) -> dict[str, Any]:
    rel_path = str(getattr(record, "rel_path", ""))
    line_count = max(int(getattr(record, "line_count", 0) or 0), 1)
    concern_density = round(sum(concern_counts.values()) / line_count, 4)
    hot_spot_reasons: list[str] = []
    if fan_in.get(rel_path, 0) >= 5:
        hot_spot_reasons.append(f"fan-in {fan_in[rel_path]}")
    if fan_out.get(rel_path, 0) >= 5:
        hot_spot_reasons.append(f"fan-out {fan_out[rel_path]}")
    if int(getattr(record, "private_helper_count", 0) or 0) >= 12:
        hot_spot_reasons.append(f"private helpers {getattr(record, 'private_helper_count', 0)}")
    if concern_density >= 0.07:
        hot_spot_reasons.append(f"concern density {concern_density}")
    compatibility_marker_count = sum(1 for item in archaeology_markers if item["kind"] in {"compatibility", "extracted_from"})
    historical_marker_count = sum(1 for item in archaeology_markers if item["kind"] in {"historical", "deferred"})
    return {
        "fan_in": fan_in.get(rel_path, 0),
        "fan_out": fan_out.get(rel_path, 0),
        "private_helper_count": int(getattr(record, "private_helper_count", 0) or 0),
        "concern_keyword_density": concern_density,
        "concern_keyword_counts": concern_counts,
        "compatibility_marker_count": compatibility_marker_count,
        "historical_marker_count": historical_marker_count,
        "possible_centrality_hotspot": bool(hot_spot_reasons),
        "centrality_reasons": hot_spot_reasons,
        "likely_archaeology_markers": archaeology_markers[:5],
    }


def _build_file_findings(
    records: dict[str, Any],
    focus_paths: list[str],
    fan_in: dict[str, int],
    fan_out: dict[str, int],
    doc_refs: dict[str, list[dict[str, Any]]],
    test_refs: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    findings: dict[str, dict[str, Any]] = {}
    for path in focus_paths:
        record = records[path]
        path_doc_refs = list(doc_refs.get(path, []))
        path_test_refs = list(test_refs.get(path, []))
        declared_owner, declared_owner_path = _owner_declaration(record, path_doc_refs)
        role_scores, evidence_by_role, concern_counts = _role_signal_evidence(record, path_doc_refs)
        role_labels, confidence = _role_labels_and_confidence(role_scores)
        archaeology = _archaeology_markers(record)
        coupling = _coupling_indicators(record, fan_in, fan_out, concern_counts, archaeology)
        owner_evidence: list[str] = []
        for role in role_labels:
            if role in evidence_by_role:
                owner_evidence.extend(evidence_by_role[role])
        if path_doc_refs:
            owner_evidence.append(f"documentation references: {len(path_doc_refs)}")
        if path_test_refs:
            owner_evidence.append(f"test references (metadata only): {len(path_test_refs)}")
        findings[path] = {
            "path": path,
            "declared_owner": declared_owner,
            "declared_owner_path": declared_owner_path,
            "ownership_confidence": confidence,
            "owner_evidence": list(dict.fromkeys(owner_evidence))[:8],
            "role_labels": role_labels,
            "role_scores": {role: role_scores.get(role, 0) for role in ROLE_PRIORITY if role_scores.get(role, 0)},
            "doc_references": path_doc_refs,
            "test_references": [{"source": item["source"]} for item in path_test_refs[:8]],
            "coupling_indicators": coupling,
            "archaeology_markers": archaeology,
        }
    return findings


def _normalized_function_stem(name: str) -> tuple[str | None, str | None]:
    for prefix in ROLE_PREFIXES:
        if name.startswith(prefix):
            stem = name[len(prefix) :].strip("_")
            return prefix.rstrip("_"), stem or None
    return None, None


def _function_stem_overlap(records: dict[str, Any], focus_paths: list[str]) -> list[dict[str, Any]]:
    by_stem: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for path in focus_paths:
        function_names = list(getattr(records[path], "function_names", []) or [])
        for fn_name in function_names:
            prefix, stem = _normalized_function_stem(fn_name)
            if not prefix or not stem:
                continue
            by_stem[stem].append((path, prefix, fn_name))
    findings: list[dict[str, Any]] = []
    for stem, entries in sorted(by_stem.items()):
        files = sorted({path for path, _prefix, _name in entries})
        prefixes = sorted({prefix for _path, prefix, _name in entries})
        if len(files) < 2 or len(prefixes) < 2:
            continue
        severity = "high" if len(files) >= 3 else "medium"
        evidence = [f"{path}: {name}" for path, _prefix, name in sorted(entries)[:6]]
        findings.append(
            {
                "concern_name": stem.replace("_", " "),
                "involved_files": files,
                "overlap_type": "similar_function_stems_across_siblings",
                "severity": severity,
                "evidence": evidence,
            }
        )
    return findings


def _role_spread_overlap(
    primary_by_subsystem: dict[str, list[str]],
    file_findings: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for subsystem_name, primary_files in sorted(primary_by_subsystem.items()):
        by_role: dict[str, list[str]] = defaultdict(list)
        for path in primary_files:
            info = file_findings.get(path)
            if not info:
                continue
            for role in info["role_labels"]:
                if role in {"mixed_owner", "unclear_owner"}:
                    continue
                by_role[role].append(path)
        for role, paths in sorted(by_role.items()):
            unique_paths = _rel_path_list(paths)
            if len(unique_paths) < 2:
                continue
            severity = "high" if len(unique_paths) >= 3 else "medium"
            evidence = [
                f"{path}: {', '.join(file_findings[path]['role_labels'])} ({file_findings[path]['ownership_confidence']})"
                for path in unique_paths
            ]
            findings.append(
                {
                    "concern_name": f"{subsystem_name}: {role}",
                    "involved_files": unique_paths,
                    "overlap_type": "shared_concern_language",
                    "severity": severity,
                    "evidence": evidence[:6],
                }
            )
    return findings


def _compatibility_overlap(records: dict[str, Any], file_findings: dict[str, dict[str, Any]], focus_paths: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    focus_set = set(focus_paths)
    for path in focus_paths:
        info = file_findings[path]
        marker_kinds = {item["kind"] for item in info["archaeology_markers"]}
        if not marker_kinds.intersection({"compatibility", "historical", "extracted_from"}):
            continue
        internal_imports = [item for item in getattr(records[path], "internal_imports", []) if item in focus_set and item != path]
        if not internal_imports:
            continue
        evidence = [item["excerpt"] for item in info["archaeology_markers"][:3]]
        findings.append(
            {
                "concern_name": Path(path).stem.replace("_", " "),
                "involved_files": _rel_path_list([path] + internal_imports[:4]),
                "overlap_type": "compatibility_exports_after_extraction",
                "severity": "medium",
                "evidence": evidence,
            }
        )
    return findings


def _mixed_owner_overlap(file_findings: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path, info in sorted(file_findings.items()):
        substantive = [role for role in info["role_labels"] if role not in {"mixed_owner", "unclear_owner"}]
        if "mixed_owner" not in info["role_labels"] or len(substantive) < 2:
            continue
        severity = "high" if {"orchestration_owner", "validator_owner", "repair_owner"} & set(substantive) else "medium"
        findings.append(
            {
                "concern_name": Path(path).stem.replace("_", " "),
                "involved_files": [path],
                "overlap_type": "mixed_concern_language_in_single_module",
                "severity": severity,
                "evidence": info["owner_evidence"][:5],
            }
        )
    return findings


def _preferred_roles_for_subsystem(subsystem_name: str) -> tuple[str, ...]:
    name = subsystem_name.lower()
    if "telemetry" in name:
        return ("telemetry_owner",)
    if "validator" in name:
        return ("validator_owner",)
    if "repair" in name:
        return ("repair_owner",)
    if "gate" in name or "orchestration" in name:
        return ("orchestration_owner",)
    if "contract" in name or "prompt" in name:
        return ("contract_owner",)
    return ()


def _pick_inferred_owner(
    subsystem_name: str,
    primary_files: list[str],
    file_findings: dict[str, dict[str, Any]],
) -> tuple[str, str, list[str], list[str], str | None]:
    preferred_roles = _preferred_roles_for_subsystem(subsystem_name)
    candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    for path in primary_files:
        info = file_findings.get(path)
        if not info:
            continue
        top_role_score = max(info["role_scores"].values(), default=0)
        preferred_role_score = max((info["role_scores"].get(role, 0) for role in preferred_roles), default=0)
        candidates.append(
            (
                preferred_role_score,
                top_role_score,
                CONFIDENCE_RANK[info["ownership_confidence"]],
                path,
                info,
            )
        )
    if not candidates:
        return "unknown", "unclear", [], [], None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    top_preferred_score, top_score, _top_conf_rank, top_path, top_info = candidates[0]
    second_preferred_score = candidates[1][0] if len(candidates) > 1 else -1
    second_score = candidates[1][1] if len(candidates) > 1 else -1
    substantive_roles = [role for role in top_info["role_labels"] if role not in {"mixed_owner", "unclear_owner"}]
    declared_owner_path = top_info.get("declared_owner_path")
    should_mix = "mixed_owner" in top_info["role_labels"]
    if not should_mix and len(candidates) > 1 and top_score > 0:
        if preferred_roles and top_preferred_score != second_preferred_score:
            should_mix = False
        else:
            should_mix = second_score >= top_score - 1
    if should_mix:
        mixed_paths = _rel_path_list([top_path] + ([candidates[1][3]] if len(candidates) > 1 else []))
        role_labels = sorted(
            {
                role
                for path in mixed_paths
                for role in file_findings[path]["role_labels"]
                if role not in {"mixed_owner", "unclear_owner"}
            }
        )
        if len(role_labels) > 1:
            role_labels.append("mixed_owner")
        return (
            "mixed: " + ", ".join(mixed_paths),
            "low" if top_info["ownership_confidence"] != "unclear" else "unclear",
            role_labels or ["unclear_owner"],
            list(dict.fromkeys(top_info["owner_evidence"] + (file_findings[mixed_paths[-1]]["owner_evidence"] if len(mixed_paths) > 1 else [])))[:8],
            declared_owner_path,
        )
    if not substantive_roles:
        substantive_roles = ["unclear_owner"]
    return top_path, top_info["ownership_confidence"], substantive_roles, top_info["owner_evidence"], declared_owner_path


def _aggregate_coupling(primary_files: list[str], file_findings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    findings = [file_findings[path] for path in primary_files if path in file_findings]
    if not findings:
        return {
            "total_private_helpers": 0,
            "max_fan_in": 0,
            "max_fan_out": 0,
            "average_concern_keyword_density": 0.0,
            "possible_centrality_hotspots": [],
            "compatibility_marker_count": 0,
            "historical_marker_count": 0,
        }
    hotspot_paths = [
        {
            "path": item["path"],
            "fan_in": item["coupling_indicators"]["fan_in"],
            "fan_out": item["coupling_indicators"]["fan_out"],
            "reasons": item["coupling_indicators"]["centrality_reasons"],
        }
        for item in findings
        if item["coupling_indicators"]["possible_centrality_hotspot"]
    ]
    avg_density = round(
        sum(item["coupling_indicators"]["concern_keyword_density"] for item in findings) / len(findings),
        4,
    )
    return {
        "total_private_helpers": sum(item["coupling_indicators"]["private_helper_count"] for item in findings),
        "max_fan_in": max(item["coupling_indicators"]["fan_in"] for item in findings),
        "max_fan_out": max(item["coupling_indicators"]["fan_out"] for item in findings),
        "average_concern_keyword_density": avg_density,
        "possible_centrality_hotspots": hotspot_paths[:5],
        "compatibility_marker_count": sum(item["coupling_indicators"]["compatibility_marker_count"] for item in findings),
        "historical_marker_count": sum(item["coupling_indicators"]["historical_marker_count"] for item in findings),
    }


def _subsystem_archaeology(primary_files: list[str], file_findings: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    markers: list[dict[str, str]] = []
    for path in primary_files:
        info = file_findings.get(path)
        if not info:
            continue
        for item in info["archaeology_markers"]:
            markers.append({"path": path, "kind": item["kind"], "excerpt": item["excerpt"]})
    return markers[:10]


def _attach_docs_vs_code_overlap(
    subsystem_name: str,
    inferred_owner: str,
    declared_owner_path: str | None,
) -> dict[str, Any] | None:
    if not declared_owner_path or not inferred_owner or inferred_owner == "unknown" or inferred_owner.startswith("mixed:"):
        return None
    if declared_owner_path == inferred_owner:
        return None
    return {
        "concern_name": subsystem_name,
        "involved_files": _rel_path_list([declared_owner_path, inferred_owner]),
        "overlap_type": "docs_claim_owner_but_code_shape_differs",
        "severity": "medium",
        "evidence": [
            f"declared owner path: {declared_owner_path}",
            f"inferred owner path: {inferred_owner}",
            "Heuristic only: documentation and code shape disagree.",
        ],
    }


def analyze_runtime_findings(
    *,
    records: dict[str, Any],
    subsystem_seeds: list[dict[str, Any]],
    fan_in: dict[str, int],
    fan_out: dict[str, int],
) -> dict[str, Any]:
    primary_by_subsystem: dict[str, list[str]] = {}
    focus_paths: list[str] = []
    for seed in subsystem_seeds:
        primary_files = [path for path in seed["primary_hints"] if path in records and path.startswith("game/") and path.endswith(".py")]
        primary_by_subsystem[seed["subsystem_name"]] = primary_files
        focus_paths.extend(primary_files)
    focus_paths = _rel_path_list(focus_paths)
    doc_refs, test_refs = _extract_references(records, focus_paths)
    file_findings = _build_file_findings(records, focus_paths, fan_in, fan_out, doc_refs, test_refs)

    overlap_findings = []
    overlap_findings.extend(_role_spread_overlap(primary_by_subsystem, file_findings))
    overlap_findings.extend(_function_stem_overlap(records, focus_paths))
    overlap_findings.extend(_compatibility_overlap(records, file_findings, focus_paths))
    overlap_findings.extend(_mixed_owner_overlap(file_findings))

    subsystem_findings: dict[str, dict[str, Any]] = {}
    for subsystem_name, primary_files in sorted(primary_by_subsystem.items()):
        ownership_findings = [file_findings[path] for path in primary_files if path in file_findings]
        inferred_owner, confidence, role_labels, owner_evidence, declared_owner_path = _pick_inferred_owner(
            subsystem_name,
            primary_files,
            file_findings,
        )
        subsystem_overlap = [
            item
            for item in overlap_findings
            if set(item["involved_files"]) & set(primary_files)
        ]
        docs_vs_code = _attach_docs_vs_code_overlap(subsystem_name, inferred_owner, declared_owner_path)
        if docs_vs_code:
            subsystem_overlap.append(docs_vs_code)
            overlap_findings.append(docs_vs_code)
        subsystem_findings[subsystem_name] = {
            "ownership_findings": ownership_findings,
            "inferred_owner": inferred_owner,
            "ownership_confidence": confidence,
            "owner_evidence": owner_evidence[:8],
            "role_labels": role_labels or ["unclear_owner"],
            "overlap_findings": sorted(
                subsystem_overlap,
                key=lambda item: (-SEVERITY_RANK[item["severity"]], item["concern_name"], tuple(item["involved_files"])),
            )[:8],
            "coupling_indicators": _aggregate_coupling(primary_files, file_findings),
            "archaeology_markers": _subsystem_archaeology(primary_files, file_findings),
        }

    ambiguous = []
    for subsystem_name, info in subsystem_findings.items():
        if info["ownership_confidence"] in {"low", "unclear"} or "mixed_owner" in info["role_labels"]:
            ambiguous.append(
                {
                    "subsystem_name": subsystem_name,
                    "inferred_owner": info["inferred_owner"],
                    "ownership_confidence": info["ownership_confidence"],
                    "role_labels": info["role_labels"],
                    "overlap_count": len(info["overlap_findings"]),
                }
            )
    ambiguous.sort(
        key=lambda item: (
            CONFIDENCE_RANK[item["ownership_confidence"]],
            -item["overlap_count"],
            item["subsystem_name"],
        )
    )

    hotspot_files = []
    for path, info in sorted(file_findings.items()):
        coupling = info["coupling_indicators"]
        if not coupling["possible_centrality_hotspot"]:
            continue
        hotspot_files.append(
            {
                "path": path,
                "fan_in": coupling["fan_in"],
                "fan_out": coupling["fan_out"],
                "private_helper_count": coupling["private_helper_count"],
                "concern_keyword_density": coupling["concern_keyword_density"],
                "reasons": coupling["centrality_reasons"],
            }
        )
    hotspot_files.sort(
        key=lambda item: (
            -(item["fan_in"] + item["fan_out"]),
            -item["private_helper_count"],
            -item["concern_keyword_density"],
            item["path"],
        )
    )

    archaeology_summary = []
    for path, info in sorted(file_findings.items()):
        if not info["archaeology_markers"]:
            continue
        archaeology_summary.append(
            {
                "path": path,
                "markers": [item["kind"] for item in info["archaeology_markers"]],
            }
        )
    archaeology_summary = archaeology_summary[:10]

    overlap_findings = sorted(
        overlap_findings,
        key=lambda item: (-SEVERITY_RANK[item["severity"]], item["concern_name"], tuple(item["involved_files"])),
    )

    return {
        "focus_paths": focus_paths,
        "file_findings": file_findings,
        "subsystem_findings": subsystem_findings,
        "global_overlap_findings": overlap_findings,
        "summary": {
            "top_ownership_ambiguities": ambiguous[:5],
            "top_overlap_findings": overlap_findings[:8],
            "top_coupling_hotspots": hotspot_files[:8],
            "top_archaeology_flags": archaeology_summary,
            "schema_notes": [
                "subsystem_reports now include inferred_owner, ownership_confidence, owner_evidence, role_labels, ownership_findings, overlap_findings, coupling_indicators, and archaeology_markers.",
                "modules_analyzed.files now surface ownership role_labels and ownership_confidence for runtime focus modules.",
                "Overlap findings are heuristic triage signals, not proof of semantic duplication or the true canonical owner.",
            ],
        },
    }
