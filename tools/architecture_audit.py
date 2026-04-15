#!/usr/bin/env python3
"""Static architecture durability audit for the repo.

Pure analysis only:
- no runtime imports from ``game/``
- stdlib only
- reads source/docs/tests/tooling and emits durable artifacts
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
from architecture_audit_runtime import analyze_runtime_findings
from architecture_audit_tests import analyze_test_ownership

DEFAULT_JSON_OUT = ROOT / "artifacts" / "architecture_audit" / "architecture_audit.json"
DEFAULT_MD_OUT = ROOT / "artifacts" / "architecture_audit" / "architecture_audit.md"
TARGET_DIRS = ("game", "tests", "docs", "tools")
DOC_SUFFIXES = {".md"}
PY_SUFFIXES = {".py"}
TOP_LEVEL_KEYS = (
    "generated_at",
    "repo_root",
    "modules_analyzed",
    "docs_analyzed",
    "tests_analyzed",
    "subsystem_reports",
    "summary",
    "warnings",
)
DIMENSIONS = (
    "ownership clarity",
    "overlap / duplicate enforcement",
    "extension ease",
    "removal clarity",
    "cost visibility",
    "test alignment",
    "historical residue / archaeology risk",
)
ALIGNMENT_TEST_SCORE = {
    "aligned": "green",
    "partial": "yellow",
    "conflict": "red",
    "unclear": "red",
}
COLOR_POINTS = {
    "green": 3,
    "yellow": 2,
    "red": 0,
    "unknown": 1,
}
ALIGNMENT_POINTS = {
    "aligned": 3,
    "partial": 2,
    "unclear": 1,
    "conflict": 0,
}
SEVERITY_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
}
HOTSPOT_NAMES = (
    "prompt contracts conflict",
    "response policy contracts localized residue",
    "final emission gate orchestration partial mismatch",
    "stage diff telemetry partial mismatch",
    "test ownership / inventory docs still unclear",
    "prompt_context_leads residue",
    "turn_packet telemetry adjacency residue",
    "social_exchange_emission mixed repair/contract role",
)

OWNERSHIP_PATTERNS: dict[str, re.Pattern[str]] = {
    "owner": re.compile(r"\bowner\b", re.IGNORECASE),
    "canonical": re.compile(r"\bcanonical\b", re.IGNORECASE),
    "orchestration": re.compile(r"\borchestration\b", re.IGNORECASE),
    "validator": re.compile(r"\bvalidator\b", re.IGNORECASE),
    "repair": re.compile(r"\brepair\b", re.IGNORECASE),
    "single source of truth": re.compile(r"\bsingle source of truth\b", re.IGNORECASE),
    "deferred": re.compile(r"\bdeferred\b", re.IGNORECASE),
}

RESIDUE_PATTERNS: dict[str, re.Pattern[str]] = {
    "historical": re.compile(r"\bhistorical\b", re.IGNORECASE),
    "deferred": re.compile(r"\bdeferred\b", re.IGNORECASE),
    "legacy": re.compile(r"\blegacy\b", re.IGNORECASE),
    "compatibility": re.compile(r"\bcompatibility\b", re.IGNORECASE),
    "private symbols remain importable": re.compile(r"\bprivate symbols remain importable\b", re.IGNORECASE),
    "for historical tests": re.compile(r"\bfor historical tests\b", re.IGNORECASE),
}

STRONG_OWNER_RE = re.compile(
    r"\b(?:canonical owner|orchestration owner|single source of truth|remains the .* owner)\b",
    re.IGNORECASE,
)

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REPO_PATH_RE = re.compile(r"\b(?:docs|game|tests|tools)/[A-Za-z0-9_.\-/]+\b")
INTERNAL_IMPORT_PREFIXES = ("game", "tests", "tools")
OWNERSHIP_LEDGER_PATH = "docs/architecture_ownership_ledger.md"
LEDGER_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
OWNER_DECLARATION_RE = re.compile(
    r"\b(canonical owner for|canonical orchestration owner for|canonical metadata-only owner for|canonical telemetry-only owner for|orchestration owner for|orchestration home)\b",
    re.IGNORECASE,
)
NON_OWNER_DECLARATION_RE = re.compile(
    r"\b(support-only|helper-only|metadata-only|telemetry-only|not the canonical owner|not the ownership home|non-owner|transitional residue)\b",
    re.IGNORECASE,
)
OWNER_DECLARATION_PHRASES = (
    "canonical owner for",
    "canonical orchestration owner for",
    "canonical metadata-only owner for",
    "canonical telemetry-only owner for",
    "orchestration owner for",
    "orchestration home",
)
NEGATED_OWNER_PHRASES = (
    "not the canonical owner",
    "not the ownership home",
)


@dataclass
class FileRecord:
    path: Path
    rel_path: str
    kind: str
    text: str
    docstring: str
    line_count: int
    function_count: int
    class_count: int
    import_count: int
    private_helper_count: int
    function_names: list[str]
    class_names: list[str]
    internal_imports: list[str]
    ownership_terms: list[str]
    residue_terms: list[str]


SUBSYSTEM_SEEDS: list[dict[str, Any]] = [
    {
        "subsystem_name": "prompt contracts",
        "primary_hints": [
            "game/prompt_context.py",
            "game/prompt_context_leads.py",
            "game/response_policy_contracts.py",
        ],
        "doc_hints": [
            "docs/ai_gm_contract.md",
            "docs/system_overview.md",
            "docs/narrative_integrity_architecture.md",
        ],
        "test_keywords": ("prompt", "response_type", "contract"),
        "doc_keywords": ("prompt", "contract", "response_type"),
        "role_hint": "Resolves prompt-facing contract obligations before final emission enforcement.",
    },
    {
        "subsystem_name": "response policy contracts",
        "primary_hints": [
            "game/response_policy_contracts.py",
            "game/final_emission_validators.py",
            "game/final_emission_repairs.py",
        ],
        "doc_hints": [
            "docs/narrative_integrity_architecture.md",
            "docs/current_focus.md",
            "docs/system_overview.md",
        ],
        "test_keywords": ("answer_completeness", "response_delta", "fallback_behavior", "response_policy"),
        "doc_keywords": ("response_policy", "contract", "answer completeness", "response delta"),
        "role_hint": "Defines shipped response-policy contracts consumed by validators, repairs, and the gate.",
    },
    {
        "subsystem_name": "final emission validators",
        "primary_hints": ["game/final_emission_validators.py"],
        "doc_hints": ["docs/narrative_integrity_architecture.md"],
        "test_keywords": ("final_emission_validators", "answer_completeness", "response_delta"),
        "doc_keywords": ("validator", "final emission"),
        "role_hint": "Owns pure deterministic legality and contract checks for emitted text.",
    },
    {
        "subsystem_name": "final emission repairs",
        "primary_hints": ["game/final_emission_repairs.py"],
        "doc_hints": ["docs/narrative_integrity_architecture.md"],
        "test_keywords": ("final_emission_repairs", "fallback_behavior_repairs", "contextual_minimal_repair"),
        "doc_keywords": ("repair", "final emission"),
        "role_hint": "Owns deterministic repair passes and skip logic for emission contracts.",
    },
    {
        "subsystem_name": "final emission gate orchestration",
        "primary_hints": [
            "game/final_emission_gate.py",
            "game/final_emission_meta.py",
            "game/final_emission_text.py",
            "game/social_exchange_emission.py",
        ],
        "doc_hints": [
            "docs/narrative_integrity_architecture.md",
            "docs/current_focus.md",
        ],
        "test_keywords": ("final_emission_gate", "final_emission_meta", "strict_social"),
        "doc_keywords": ("orchestration", "final emission gate", "metadata packaging"),
        "role_hint": "Orders layer execution, sanitizer integration, metadata packaging, and compatibility paths.",
    },
    {
        "subsystem_name": "narrative authenticity",
        "primary_hints": [
            "game/narrative_authenticity.py",
            "game/narrative_authenticity_eval.py",
        ],
        "doc_hints": [
            "docs/narrative_authenticity_anti_echo_rumor_realism.md",
            "docs/current_focus.md",
            "docs/testing.md",
        ],
        "test_keywords": ("narrative_authenticity", "aer"),
        "doc_keywords": ("narrative authenticity", "anti-echo", "rumor realism"),
        "role_hint": "Enforces anti-echo, rumor realism, and narrative-signal integrity without live-model checks.",
    },
    {
        "subsystem_name": "stage diff telemetry",
        "primary_hints": [
            "game/stage_diff_telemetry.py",
            "game/turn_packet.py",
        ],
        "doc_hints": [
            "docs/current_focus.md",
            "docs/testing.md",
            "docs/README.md",
        ],
        "test_keywords": ("stage_diff", "turn_packet", "telemetry"),
        "doc_keywords": ("stage diff", "telemetry", "turn packet"),
        "role_hint": "Provides bounded observability for emit-path mutations and stage transitions.",
    },
    {
        "subsystem_name": "test ownership / inventory docs",
        "primary_hints": [
            "tests/TEST_AUDIT.md",
            "tests/TEST_CONSOLIDATION_PLAN.md",
            "tests/README_TESTS.md",
            "tools/test_audit.py",
        ],
        "doc_hints": [
            "tests/TEST_AUDIT.md",
            "tests/TEST_CONSOLIDATION_PLAN.md",
            "tests/README_TESTS.md",
        ],
        "test_keywords": ("test_audit", "inventory", "canonical owner", "transcript"),
        "doc_keywords": ("canonical owner", "smoke overlap", "test inventory", "consolidation"),
        "role_hint": "Documents test-suite ownership, overlap hotspots, and inventory regeneration.",
    },
]


def _repo_rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _module_name_for_rel(rel_path: str) -> str | None:
    path = Path(rel_path)
    if path.suffix != ".py":
        return None
    if path.name == "__init__.py":
        return ".".join(path.with_suffix("").parts[:-1])
    return ".".join(path.with_suffix("").parts)


def _resolve_import_target(
    importer_rel: str,
    module_name: str | None,
    alias_name: str | None = None,
    level: int = 0,
    module_index: dict[str, str] | None = None,
) -> str | None:
    module_index = module_index or {}
    base_parts = _module_name_for_rel(importer_rel)
    base_seq = base_parts.split(".") if base_parts else []
    if level:
        trim = max(0, len(base_seq) - level)
        parent = base_seq[:trim]
        tail = module_name.split(".") if module_name else []
        candidate = ".".join(parent + tail)
    else:
        candidate = module_name or ""
    for probe in (candidate, f"{candidate}.{alias_name}" if candidate and alias_name else alias_name or ""):
        if probe in module_index:
            return module_index[probe]
    return None


def _parse_internal_imports(rel_path: str, text: str, module_index: dict[str, str]) -> tuple[list[str], int]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], 0
    imports: list[str] = []
    import_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_count += 1
            for alias in node.names:
                if alias.name.startswith(INTERNAL_IMPORT_PREFIXES):
                    target = _resolve_import_target(rel_path, alias.name, module_index=module_index)
                    if target:
                        imports.append(target)
        elif isinstance(node, ast.ImportFrom):
            import_count += 1
            mod = node.module or ""
            if mod.startswith(INTERNAL_IMPORT_PREFIXES) or node.level > 0:
                target = _resolve_import_target(
                    rel_path,
                    mod or None,
                    alias_name=None,
                    level=node.level,
                    module_index=module_index,
                )
                if target:
                    imports.append(target)
                    continue
                for alias in node.names:
                    target = _resolve_import_target(
                        rel_path,
                        mod or None,
                        alias_name=alias.name,
                        level=node.level,
                        module_index=module_index,
                    )
                    if target:
                        imports.append(target)
    return sorted(set(imports)), import_count


def _ast_counts(text: str) -> tuple[int, int, int, list[str], list[str], str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0, 0, 0, [], [], ""
    functions = 0
    classes = 0
    private_helpers = 0
    function_names: list[str] = []
    class_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            function_names.append(node.name)
            if node.name.startswith("_"):
                private_helpers += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1
            class_names.append(node.name)
    docstring = ast.get_docstring(tree) or ""
    return functions, classes, private_helpers, sorted(function_names), sorted(class_names), docstring


def _pattern_hits(text: str, patterns: dict[str, re.Pattern[str]]) -> list[str]:
    hits = [name for name, pattern in patterns.items() if pattern.search(text)]
    return sorted(hits)


def _collect_records(repo_root: Path) -> tuple[dict[str, FileRecord], list[str]]:
    warnings: list[str] = []
    records: dict[str, FileRecord] = {}
    module_paths: list[str] = []
    for dirname in TARGET_DIRS:
        dir_path = repo_root / dirname
        if not dir_path.exists():
            warnings.append(f"Missing directory handled gracefully: {dirname}/")
            continue
        if not dir_path.is_dir():
            warnings.append(f"Expected directory but found non-directory path: {dirname}/")
            continue
        for path in sorted(dir_path.rglob("*")):
            if not path.is_file():
                continue
            rel_path = _repo_rel(path, repo_root)
            if path.suffix in PY_SUFFIXES and not path.name.startswith("."):
                module_paths.append(rel_path)
    module_index = {
        module_name: rel
        for rel in module_paths
        if (module_name := _module_name_for_rel(rel))
    }
    for dirname in TARGET_DIRS:
        dir_path = repo_root / dirname
        if not dir_path.is_dir():
            continue
        for path in sorted(dir_path.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in PY_SUFFIXES | DOC_SUFFIXES:
                continue
            rel_path = _repo_rel(path, repo_root)
            text = _safe_read_text(path)
            internal_imports: list[str] = []
            functions = 0
            classes = 0
            private_helpers = 0
            import_count = 0
            function_names: list[str] = []
            class_names: list[str] = []
            docstring = ""
            if path.suffix in PY_SUFFIXES:
                internal_imports, import_count = _parse_internal_imports(rel_path, text, module_index)
                functions, classes, private_helpers, function_names, class_names, docstring = _ast_counts(text)
            records[rel_path] = FileRecord(
                path=path,
                rel_path=rel_path,
                kind=dirname,
                text=text,
                docstring=docstring,
                line_count=len(text.splitlines()),
                function_count=functions,
                class_count=classes,
                import_count=import_count,
                private_helper_count=private_helpers,
                function_names=function_names,
                class_names=class_names,
                internal_imports=internal_imports,
                ownership_terms=_pattern_hits(text, OWNERSHIP_PATTERNS),
                residue_terms=_pattern_hits(text, RESIDUE_PATTERNS),
            )
    return records, warnings


def _build_fan_maps(records: dict[str, FileRecord]) -> tuple[dict[str, int], dict[str, int]]:
    fan_in: Counter[str] = Counter()
    fan_out: dict[str, int] = {}
    for rel_path, record in records.items():
        fan_out[rel_path] = len(set(record.internal_imports))
        for imported in record.internal_imports:
            fan_in[imported] += 1
    return dict(fan_in), fan_out


def _resolve_doc_reference(current_path: Path, raw_target: str, repo_root: Path) -> Path | None:
    target = raw_target.strip()
    if not target or target.startswith(("http://", "https://", "#", "mailto:")):
        return None
    clean = target.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return None
    candidates = [
        (current_path.parent / clean).resolve(),
        (repo_root / clean).resolve(),
    ]
    in_repo: list[Path] = []
    for candidate in candidates:
        try:
            candidate.relative_to(repo_root.resolve())
            in_repo.append(candidate)
        except ValueError:
            continue
    for candidate in in_repo:
        if candidate.exists():
            return candidate
    return in_repo[0] if in_repo else None


def _find_doc_reference_issues(records: dict[str, FileRecord], repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for record in sorted(records.values(), key=lambda item: item.rel_path):
        if not (record.rel_path.startswith("docs/") or record.rel_path.startswith("tests/")):
            continue
        if Path(record.rel_path).suffix not in DOC_SUFFIXES:
            continue
        refs: list[str] = []
        refs.extend(match.group(1) for match in MARKDOWN_LINK_RE.finditer(record.text))
        refs.extend(match.group(0) for match in REPO_PATH_RE.finditer(record.text))
        for raw in refs:
            resolved = _resolve_doc_reference(record.path, raw, repo_root)
            if resolved is None:
                continue
            if resolved.exists():
                continue
            issue = (record.rel_path, raw)
            if issue in seen:
                continue
            seen.add(issue)
            issues.append(
                {
                    "source": record.rel_path,
                    "reference": raw,
                    "resolved_path": _repo_rel(resolved, repo_root),
                }
            )
    return issues


def _path_mentions(text: str) -> list[str]:
    return sorted(set(REPO_PATH_RE.findall(text)))


def _parse_ownership_ledger(records: dict[str, FileRecord]) -> dict[str, Any]:
    record = records.get(OWNERSHIP_LEDGER_PATH)
    if not record:
        return {
            "exists": False,
            "entries": [],
            "owner_paths": [],
            "support_paths": [],
        }
    text = record.text
    sections = list(LEDGER_SECTION_RE.finditer(text))
    entries: list[dict[str, Any]] = []
    for idx, match in enumerate(sections):
        start = match.end()
        end = sections[idx + 1].start() if idx + 1 < len(sections) else len(text)
        body = text[start:end]
        owner_paths = []
        support_paths = []
        current_state = "unknown"
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if line.startswith("- Canonical owner module:"):
                owner_paths = _path_mentions(line)
            elif line.startswith("- Non-owner supporting modules:"):
                support_paths = _path_mentions(line)
            elif line.startswith("- Current state:"):
                current_state = line.split(":", 1)[1].strip().strip("`") or "unknown"
        entries.append(
            {
                "concern_name": match.group(1).strip(),
                "owner_paths": owner_paths,
                "support_paths": support_paths,
                "current_state": current_state,
            }
        )
    owner_paths = sorted({path for entry in entries for path in entry["owner_paths"]})
    support_paths = sorted({path for entry in entries for path in entry["support_paths"]})
    return {
        "exists": True,
        "entries": entries,
        "owner_paths": owner_paths,
        "support_paths": support_paths,
    }


def _ownership_declaration_consistency(records: dict[str, FileRecord]) -> dict[str, Any]:
    ledger = _parse_ownership_ledger(records)
    if not ledger["exists"]:
        return {
            "status": "missing",
            "ledger_path": OWNERSHIP_LEDGER_PATH,
            "issues": [],
            "checked_owner_modules": 0,
            "checked_support_only_modules": 0,
            "summary": "Ownership ledger not present in this repo snapshot.",
        }

    owner_paths = {
        path for path in ledger["owner_paths"] if path.startswith("game/") and path.endswith(".py")
    }
    support_only_paths = {
        path
        for path in (set(ledger["support_paths"]) - owner_paths)
        if path.startswith("game/") and path.endswith(".py")
    }
    issues: list[dict[str, str]] = []

    for path in sorted(owner_paths):
        record = records.get(path)
        if not record:
            issues.append({"path": path, "issue": "ledger_owner_missing_from_repo"})
            continue
        docstring = record.docstring or ""
        if not _has_explicit_owner_declaration(docstring):
            issues.append({"path": path, "issue": "owner_missing_explicit_owner_language"})

    for path in sorted(support_only_paths):
        record = records.get(path)
        if not record:
            issues.append({"path": path, "issue": "ledger_support_module_missing_from_repo"})
            continue
        docstring = record.docstring or ""
        if _has_explicit_owner_declaration(docstring):
            issues.append({"path": path, "issue": "support_only_module_claims_owner_language"})
        if not _has_explicit_non_owner_declaration(docstring):
            issues.append({"path": path, "issue": "support_only_module_missing_non_owner_language"})

    mismatch_count = len(issues)
    if mismatch_count == 0:
        status = "aligned"
        summary = "Ownership ledger and module docstrings agree on owner vs support-only declarations."
    else:
        status = "mismatch"
        summary = f"Ownership ledger and module docstrings disagree in {mismatch_count} place(s)."
    return {
        "status": status,
        "ledger_path": OWNERSHIP_LEDGER_PATH,
        "issues": issues[:20],
        "checked_owner_modules": len(owner_paths),
        "checked_support_only_modules": len(support_only_paths),
        "summary": summary,
    }


def _has_explicit_owner_declaration(docstring: str) -> bool:
    for raw_line in str(docstring or "").splitlines():
        line = re.sub(r"[*`_]", "", raw_line.strip().lower())
        if not line:
            continue
        if any(phrase in line for phrase in NEGATED_OWNER_PHRASES):
            continue
        if any(phrase in line for phrase in OWNER_DECLARATION_PHRASES):
            return True
    return False


def _has_explicit_non_owner_declaration(docstring: str) -> bool:
    normalized = re.sub(r"[*`_]", "", str(docstring or ""))
    return bool(NON_OWNER_DECLARATION_RE.search(normalized))


def _first_owner_line(record: FileRecord) -> str | None:
    for line in record.text.splitlines():
        if STRONG_OWNER_RE.search(line):
            return line.strip()
    return None


def _matching_paths(records: dict[str, FileRecord], hints: list[str]) -> list[str]:
    out = [path for path in hints if path in records]
    return list(dict.fromkeys(out))


def _paths_by_keywords(records: dict[str, FileRecord], prefixes: tuple[str, ...], keywords: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for rel_path, record in sorted(records.items()):
        if not rel_path.startswith(prefixes):
            continue
        haystack = f"{rel_path.lower()}\n{record.text.lower()}"
        if any(keyword.lower() in haystack for keyword in keywords):
            hits.append(rel_path)
    return hits


def _pick_related_tests(
    records: dict[str, FileRecord],
    seed: dict[str, Any],
    primary_files: list[str],
) -> list[str]:
    tests = _matching_paths(records, [path for path in seed["primary_hints"] if path.startswith("tests/")])
    tests.extend(_paths_by_keywords(records, ("tests/",), tuple(seed["test_keywords"])))
    primary_basenames = tuple(Path(path).stem for path in primary_files if path.startswith("game/"))
    if primary_basenames:
        tests.extend(_paths_by_keywords(records, ("tests/",), primary_basenames))
    tests = [path for path in tests if path.endswith(".py") or path.endswith(".md")]
    return list(dict.fromkeys(sorted(tests)))


def _pick_related_docs(
    records: dict[str, FileRecord],
    seed: dict[str, Any],
    primary_files: list[str],
) -> list[str]:
    docs = _matching_paths(records, list(seed["doc_hints"]))
    docs.extend(_paths_by_keywords(records, ("docs/", "tests/"), tuple(seed["doc_keywords"])))
    for primary in primary_files:
        basename = Path(primary).name
        docs.extend(_paths_by_keywords(records, ("docs/", "tests/"), (basename, primary)))
    docs = [path for path in docs if path.endswith(".md")]
    return list(dict.fromkeys(sorted(docs)))


def _pick_likely_dependencies(
    records: dict[str, FileRecord],
    primary_files: list[str],
) -> list[str]:
    dep_counts: Counter[str] = Counter()
    primary_set = set(primary_files)
    for path in primary_files:
        record = records.get(path)
        if not record:
            continue
        for dep in record.internal_imports:
            if dep not in primary_set:
                dep_counts[dep] += 1
    return [path for path, _count in dep_counts.most_common(8)]


def _score_color(green: bool, yellow: bool) -> str:
    if green:
        return "green"
    if yellow:
        return "yellow"
    return "red"


def _verdict_from_audit_scores(audit_scores: dict[str, dict[str, str]], has_primary_files: bool) -> str:
    scores = [payload["score"] for payload in audit_scores.values()]
    red_count = scores.count("red")
    yellow_count = scores.count("yellow")
    green_count = scores.count("green")
    if not has_primary_files:
        return "unknown"
    if red_count >= 2:
        return "red"
    if red_count == 1 or yellow_count >= 3:
        return "yellow"
    if green_count >= 4:
        return "green"
    return "yellow"


def _build_subsystem_reports(
    records: dict[str, FileRecord],
    fan_in: dict[str, int],
    fan_out: dict[str, int],
    doc_issues: list[dict[str, str]],
    runtime_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    primary_by_subsystem: dict[str, list[str]] = {}
    for seed in SUBSYSTEM_SEEDS:
        primary_files = _matching_paths(records, list(seed["primary_hints"]))
        primary_by_subsystem[seed["subsystem_name"]] = primary_files

    overlap_index: dict[str, list[str]] = defaultdict(list)
    for subsystem_name, primary_files in primary_by_subsystem.items():
        for path in primary_files:
            overlap_index[path].append(subsystem_name)

    for seed in SUBSYSTEM_SEEDS:
        subsystem_name = seed["subsystem_name"]
        primary_files = primary_by_subsystem[subsystem_name]
        primary_records = [records[path] for path in primary_files if path in records]
        related_tests = _pick_related_tests(records, seed, primary_files)
        related_docs = _pick_related_docs(records, seed, primary_files)
        likely_dependencies = _pick_likely_dependencies(records, primary_files)
        runtime_details = runtime_analysis.get("subsystem_findings", {}).get(subsystem_name, {})

        overlap_points: list[str] = []
        for path in primary_files:
            shared = [name for name in overlap_index[path] if name != subsystem_name]
            if shared:
                overlap_points.append(f"shared primary file: {path} -> {', '.join(sorted(shared))}")
            if fan_in.get(path, 0) >= 5 or fan_out.get(path, 0) >= 5:
                overlap_points.append(
                    f"cross-cutting import surface: {path} (fan-in {fan_in.get(path, 0)}, fan-out {fan_out.get(path, 0)})"
                )
        overlap_points = sorted(dict.fromkeys(overlap_points))

        declared_owner = "unknown"
        for item in runtime_details.get("ownership_findings", []):
            if item.get("declared_owner") and item["declared_owner"] != "unknown":
                declared_owner = item["declared_owner"]
                break
        if declared_owner == "unknown":
            for record in primary_records + [records[path] for path in related_docs if path in records]:
                owner_line = _first_owner_line(record)
                if owner_line:
                    declared_owner = f"{record.rel_path}: {owner_line}"
                    break

        residue_hits = [
            {
                "path": record.rel_path,
                "markers": record.residue_terms,
            }
            for record in primary_records
            if record.residue_terms
        ]
        ownership_hits = [
            {
                "path": record.rel_path,
                "markers": record.ownership_terms,
            }
            for record in primary_records
            if record.ownership_terms
        ]
        file_metrics = [
            {
                "path": record.rel_path,
                "line_count": record.line_count,
                "function_count": record.function_count,
                "class_count": record.class_count,
                "import_count": record.import_count,
                "private_helper_count": record.private_helper_count,
                "fan_in": fan_in.get(record.rel_path, 0),
                "fan_out": fan_out.get(record.rel_path, 0),
            }
            for record in primary_records
        ]
        related_doc_issues = [
            issue
            for issue in doc_issues
            if issue["source"] in related_docs or issue["source"] in primary_files
        ]

        total_lines = sum(item["line_count"] for item in file_metrics)
        max_fan_in = max((item["fan_in"] for item in file_metrics), default=0)
        max_fan_out = max((item["fan_out"] for item in file_metrics), default=0)
        total_residue = sum(len(item["markers"]) for item in residue_hits)
        has_declared_owner = declared_owner != "unknown"
        ownership_confidence = runtime_details.get("ownership_confidence", "unclear")
        role_labels = runtime_details.get("role_labels", ["unclear_owner"])
        overlap_findings = runtime_details.get("overlap_findings", [])
        has_tests = bool([path for path in related_tests if path.endswith(".py")])
        has_docs = bool(related_docs)

        audit_scores = {
            "ownership clarity": {
                "score": (
                    "unknown"
                    if not primary_files
                    else _score_color(
                        has_declared_owner and ownership_confidence in {"high", "medium"} and "mixed_owner" not in role_labels,
                        has_declared_owner or ownership_confidence != "unclear",
                    )
                ),
                "reason": "Explicit owner language and bounded primary file set improve change safety.",
            },
            "overlap / duplicate enforcement": {
                "score": (
                    "unknown"
                    if not primary_files
                    else _score_color(not overlap_points and not overlap_findings, len(overlap_points) + len(overlap_findings) <= 2)
                ),
                "reason": "Shared owners and cross-cutting files raise duplicate-enforcement risk.",
            },
            "extension ease": {
                "score": (
                    "unknown"
                    if not primary_files
                    else _score_color(total_lines <= 900 and max_fan_out <= 6, total_lines <= 1800 and max_fan_out <= 10)
                ),
                "reason": "Smaller surfaces with lower fan-out are easier to extend deterministically.",
            },
            "removal clarity": {
                "score": (
                    "unknown"
                    if not primary_files
                    else _score_color(max_fan_in <= 4 and has_docs, max_fan_in <= 10 or has_docs)
                ),
                "reason": "High fan-in and sparse docs make safe removal expensive.",
            },
            "cost visibility": {
                "score": (
                    "unknown"
                    if not primary_files
                    else _score_color(has_docs and (has_tests or "telemetry" in subsystem_name), has_docs or has_tests)
                ),
                "reason": "Docs and tests are the deterministic visibility surface for structural cost.",
            },
            "test alignment": {
                "score": (
                    "unknown"
                    if not primary_files
                    else _score_color(has_tests and bool([path for path in related_docs if path.startswith("tests/")]), has_tests)
                ),
                "reason": "Canonical tests should match subsystem ownership, not trail it loosely.",
            },
            "historical residue / archaeology risk": {
                "score": (
                    "unknown"
                    if not primary_files
                    else _score_color(total_residue == 0, total_residue <= 3)
                ),
                "reason": "Deferred and compatibility language signals archaeology cost.",
            },
        }

        warnings: list[str] = []
        if not primary_files:
            warnings.append("Seeded subsystem has no resolved primary files in this repo snapshot.")
        if not has_tests:
            warnings.append("No clearly related test files were found by deterministic heuristics.")
        if not has_docs:
            warnings.append("No clearly related documentation files were found by deterministic heuristics.")
        if related_doc_issues:
            warnings.append(f"Related documentation contains {len(related_doc_issues)} broken reference(s).")
        if total_residue >= 3:
            warnings.append("Historical residue markers are dense enough to raise archaeology risk.")
        if ownership_confidence in {"low", "unclear"}:
            warnings.append("Ownership inference stayed ambiguous; review owner_evidence before moving boundaries.")
        if overlap_findings:
            warnings.append(f"Runtime overlap heuristics flagged {len(overlap_findings)} possible responsibility smear point(s).")

        reports.append(
            {
                "subsystem_name": subsystem_name,
                "primary_files": primary_files,
                "declared_owner": declared_owner,
                "inferred_owner": runtime_details.get("inferred_owner", "unknown"),
                "ownership_confidence": ownership_confidence,
                "owner_evidence": runtime_details.get("owner_evidence", []),
                "role_labels": role_labels,
                "inferred_role": seed["role_hint"],
                "related_tests": related_tests,
                "related_docs": related_docs,
                "likely_dependencies": likely_dependencies,
                "likely_overlap_points": overlap_points,
                "ownership_findings": runtime_details.get("ownership_findings", []),
                "overlap_findings": overlap_findings,
                "coupling_indicators": runtime_details.get("coupling_indicators", {}),
                "archaeology_markers": runtime_details.get("archaeology_markers", []),
                "audit_scores": audit_scores,
                "evidence": {
                    "file_metrics": file_metrics,
                    "ownership_language_hits": ownership_hits,
                    "historical_residue_hits": residue_hits,
                    "related_doc_reference_issues": related_doc_issues,
                },
                "warnings": warnings,
                "verdict": _verdict_from_audit_scores(audit_scores, bool(primary_files)),
            }
        )
    return reports


def _module_summary(
    records: dict[str, FileRecord],
    fan_in: dict[str, int],
    fan_out: dict[str, int],
    runtime_analysis: dict[str, Any],
) -> dict[str, Any]:
    files = []
    runtime_files = runtime_analysis.get("file_findings", {})
    for record in sorted(records.values(), key=lambda item: item.rel_path):
        if not (record.rel_path.startswith("game/") or record.rel_path.startswith("tools/")):
            continue
        if not record.rel_path.endswith(".py"):
            continue
        payload = {
            "path": record.rel_path,
            "line_count": record.line_count,
            "function_count": record.function_count,
            "class_count": record.class_count,
            "import_count": record.import_count,
            "private_helper_count": record.private_helper_count,
            "fan_in": fan_in.get(record.rel_path, 0),
            "fan_out": fan_out.get(record.rel_path, 0),
            "ownership_terms": record.ownership_terms,
            "residue_terms": record.residue_terms,
        }
        runtime_info = runtime_files.get(record.rel_path)
        if runtime_info:
            payload.update(
                {
                    "declared_owner": runtime_info["declared_owner"],
                    "ownership_confidence": runtime_info["ownership_confidence"],
                    "role_labels": runtime_info["role_labels"],
                    "coupling_indicators": runtime_info["coupling_indicators"],
                }
            )
        files.append(payload)
    return {
        "count": len(files),
        "files": files,
    }


def _doc_summary(records: dict[str, FileRecord], doc_issues: list[dict[str, str]]) -> dict[str, Any]:
    files = []
    for record in sorted(records.values(), key=lambda item: item.rel_path):
        if not (
            record.rel_path.startswith("docs/")
            or record.rel_path in {"tests/README_TESTS.md", "tests/TEST_AUDIT.md", "tests/TEST_CONSOLIDATION_PLAN.md"}
        ):
            continue
        if not record.rel_path.endswith(".md"):
            continue
        files.append(
            {
                "path": record.rel_path,
                "line_count": record.line_count,
                "ownership_terms": record.ownership_terms,
                "residue_terms": record.residue_terms,
            }
        )
    return {
        "count": len(files),
        "files": files,
        "broken_references": doc_issues,
    }


def _test_summary(records: dict[str, FileRecord], test_analysis: dict[str, Any]) -> dict[str, Any]:
    test_files = test_analysis.get("test_files", {})
    files = []
    for record in sorted(records.values(), key=lambda item: item.rel_path):
        if not record.rel_path.startswith("tests/"):
            continue
        if not record.rel_path.endswith(".py"):
            continue
        inferred = test_files.get(record.rel_path, {})
        files.append(
            {
                "path": record.rel_path,
                "line_count": record.line_count,
                "test_function_count": record.function_count,
                "import_count": record.import_count,
                "ownership_terms": record.ownership_terms,
                "residue_terms": record.residue_terms,
                "inferred_category": inferred.get("file_category", "unclear"),
                "module_markers": inferred.get("module_markers", []),
                "direct_runtime_imports": inferred.get("direct_runtime_imports", []),
                "transcript_like_case_count": inferred.get("transcript_like_case_count", 0),
            }
        )
    return {
        "count": len(files),
        "files": files,
        "category_counts": test_analysis.get("summary", {}).get("test_category_counts", {}),
        "file_category_counts": test_analysis.get("summary", {}).get("test_file_category_counts", {}),
    }


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _count_scores(subsystem_reports: list[dict[str, Any]], dimension: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for report in subsystem_reports:
        score = report.get("audit_scores", {}).get(dimension, {}).get("score", "unknown")
        counts[score] += 1
    return dict(counts)


def _dimension_entry(
    *,
    dimension: str,
    status: str,
    points: int,
    evidence: list[str],
    counts: dict[str, Any] | None = None,
    confidence_effect: str | None = None,
) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "status": status,
        "points": points,
        "evidence": evidence[:4],
        "counts": counts or {},
        "confidence_effect": confidence_effect or "neutral",
    }


def _classify_hotspot(
    report: dict[str, Any],
    *,
    label: str,
    module_path: str | None = None,
) -> dict[str, Any]:
    alignment = report.get("test_ownership_alignment", {})
    overlap_findings = report.get("overlap_findings", [])
    overlap_types = {item.get("overlap_type", "") for item in overlap_findings}
    archaeology_markers = report.get("archaeology_markers", [])
    coupling = report.get("coupling_indicators", {})
    module_archaeology = [
        marker
        for marker in archaeology_markers
        if not module_path or marker.get("path") == module_path
    ]
    overlap_for_module = [
        item
        for item in overlap_findings
        if not module_path or module_path in item.get("involved_files", [])
    ]
    coverage_spread = alignment.get("coverage_spread", 0)
    role_labels = set(report.get("role_labels", []))
    alignment_status = alignment.get("alignment_status", "unclear")
    runtime_owner = report.get("inferred_owner", "unknown")

    if label == "test ownership / inventory docs still unclear":
        if alignment_status == "partial":
            classification = "localized under-consolidation"
            why = "Governance docs are materially clearer, but this docs-led concern still relies on heuristic practical-affinity mapping."
        else:
            classification = "unclear / needs human review"
            why = "Inventory docs still read authoritatively while practical ownership remains unresolved."
    elif (
        label == "prompt contracts conflict"
        and alignment_status == "aligned"
        and alignment.get("healthy_overlap")
        and alignment.get("severity") == "low"
    ):
        classification = "localized under-consolidation"
        why = "A dominant prompt owner and direct-owner suite are visible; remaining spread reads as governed downstream adjacency rather than owner smear."
    elif label == "prompt contracts conflict" and alignment_status == "partial":
        classification = "localized under-consolidation"
        why = "The runtime owner and practical direct-owner suite are visible again, but prompt-adjacent coverage remains broader than ideal."
    elif label == "prompt_context_leads residue":
        classification = "transitional residue"
        why = "This hotspot is anchored in extraction residue rather than a fresh owner split."
    elif label == "social_exchange_emission mixed repair/contract role":
        if (
            "mixed_owner" not in role_labels
            and alignment_status in {"aligned", "partial"}
            and (
                "compatibility_exports_after_extraction" in overlap_types
                or any(
                    marker.get("kind") in {"compatibility", "historical", "extracted_from", "not_owner"}
                    for marker in module_archaeology
                )
            )
        ):
            classification = "transitional residue"
            why = "The seam now has a visible downstream owner story; remaining spread reads like compatibility residue and gate/retry adjacency."
        else:
            classification = "possible ownership smear"
            why = "The named module still carries mixed role signals that should be split before growth."
    elif label == "turn_packet telemetry adjacency residue":
        if alignment_status == "conflict" or coverage_spread >= 8:
            classification = "possible ownership smear"
            why = "Packet-boundary and telemetry signals still spread widely enough to blur the owner."
        elif (
            "compatibility_exports_after_extraction" in overlap_types
            or any(marker.get("kind") in {"compatibility", "historical", "extracted_from"} for marker in module_archaeology)
            or any(marker.get("kind") in {"compatibility", "historical", "extracted_from"} for marker in archaeology_markers)
        ):
            classification = "transitional residue"
            why = "The packet owner remains visible; residual overlap reads like compatibility preservation rather than active co-ownership."
        else:
            classification = "localized under-consolidation"
            why = "The packet owner is visible, but tests/docs still have not fully re-converged around the boundary."
    elif alignment_status == "unclear" or runtime_owner == "unknown":
        classification = "unclear / needs human review"
        why = "The audit still cannot reconcile a stable owner path with practical tests/docs."
    elif label in {
        "response policy contracts localized residue",
        "response policy contracts partial drift toward repairs",
    } and alignment_status == "aligned":
        classification = "transitional residue"
        why = "The runtime owner and practical direct-owner suite now align; remaining spread reads like compatibility or adjacency residue."
    elif label in {
        "response policy contracts localized residue",
        "response policy contracts partial drift toward repairs",
        "final emission gate orchestration partial mismatch",
    } and alignment_status == "partial":
        classification = "localized under-consolidation"
        why = "The owner is still visible, but practical tests and docs still drift around the boundary."
    elif label == "stage diff telemetry partial mismatch" and alignment_status == "partial":
        if coverage_spread >= 6:
            classification = "possible ownership smear"
            why = "Telemetry and packet-boundary evidence still spread widely enough to blur ownership."
        else:
            classification = "localized under-consolidation"
            why = "Telemetry ownership is visible, but practical coverage still leaks into adjacent packet seams."
    elif (
        "mixed_owner" in role_labels
        or alignment_status == "conflict"
        or "shared_concern_language" in overlap_types
        or "mixed_concern_language_in_single_module" in overlap_types
        or coverage_spread >= 8
    ):
        classification = "possible ownership smear"
        why = "Ownership signals still spread across adjacent modules or suites instead of staying anchored in one home."
    elif (
        "compatibility_exports_after_extraction" in overlap_types
        or any(marker.get("kind") in {"compatibility", "historical", "extracted_from"} for marker in module_archaeology)
        or any(marker.get("kind") in {"compatibility", "historical", "extracted_from"} for marker in archaeology_markers)
    ):
        classification = "transitional residue"
        why = "The seam still looks shaped by extraction residue or compatibility preservation more than fresh ownership blur."
    else:
        classification = "localized under-consolidation"
        why = "The owner is still visible, but tests/docs or adjacent files have not fully re-converged around it."

    evidence: list[str] = []
    if alignment.get("evidence"):
        evidence.extend(alignment["evidence"][:2])
    for item in overlap_for_module[:1] or overlap_findings[:1]:
        if item.get("evidence"):
            evidence.append(item["evidence"][0])
    for marker in module_archaeology[:1]:
        excerpt = marker.get("excerpt", "").strip()
        if excerpt:
            evidence.append(f"{marker.get('path', module_path or 'module')}: {excerpt}")
    if report.get("likely_overlap_points"):
        evidence.append(report["likely_overlap_points"][0])

    return {
        "hotspot_name": label,
        "source_subsystem": report["subsystem_name"],
        "classification": classification,
        "why": why,
        "runtime_owner": alignment.get("runtime_owner", runtime_owner),
        "test_alignment_status": alignment.get("alignment_status", "unclear"),
        "severity": alignment.get("severity", "medium"),
        "evidence": list(dict.fromkeys(evidence))[:4],
    }


def _build_hotspot_reviews(subsystem_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {item["subsystem_name"]: item for item in subsystem_reports}
    hotspot_specs = [
        ("prompt contracts conflict", "prompt contracts", None),
        ("response policy contracts localized residue", "response policy contracts", None),
        ("final emission gate orchestration partial mismatch", "final emission gate orchestration", None),
        ("stage diff telemetry partial mismatch", "stage diff telemetry", None),
        ("test ownership / inventory docs still unclear", "test ownership / inventory docs", None),
        ("prompt_context_leads residue", "prompt contracts", "game/prompt_context_leads.py"),
        ("turn_packet telemetry adjacency residue", "stage diff telemetry", "game/turn_packet.py"),
        ("social_exchange_emission mixed repair/contract role", "final emission gate orchestration", "game/social_exchange_emission.py"),
    ]
    items = []
    for label, subsystem_name, module_path in hotspot_specs:
        report = by_name.get(subsystem_name)
        if not report:
            continue
        items.append(_classify_hotspot(report, label=label, module_path=module_path))
    return items


def _build_repo_level_scorecard(
    subsystem_reports: list[dict[str, Any]],
    *,
    broken_doc_reference_count: int,
    top_coupling_hotspots: list[dict[str, Any]],
    top_overlap_findings: list[dict[str, Any]],
    top_archaeology_flags: list[dict[str, Any]],
    test_alignment_overview: dict[str, int],
    top_test_runtime_doc_mismatches: list[dict[str, Any]],
    inventory_docs_authority_status: dict[str, Any],
) -> list[dict[str, Any]]:
    ownership_counts = _count_scores(subsystem_reports, "ownership clarity")
    ownership_points = _average(
        [COLOR_POINTS[report["audit_scores"]["ownership clarity"]["score"]] for report in subsystem_reports]
    )
    unclear_owners = sum(
        1 for report in subsystem_reports if report.get("ownership_confidence") == "unclear" or report.get("inferred_owner") == "unknown"
    )
    ownership_status = (
        "clear"
        if ownership_points >= 1.9 and unclear_owners <= 1
        else "mixed"
        if ownership_points >= 1.5 and unclear_owners < len(subsystem_reports)
        else "weak"
    )

    overlap_counts = Counter(item.get("severity", "medium") for item in top_overlap_findings)
    overlap_status = (
        "system-wide smear risk"
        if overlap_counts.get("high", 0) >= 4
        else "localized hotspots"
        if len(top_overlap_findings) >= 3
        else "bounded"
    )

    archaeology_counts = _count_scores(subsystem_reports, "historical residue / archaeology risk")
    archaeology_status = (
        "heavy" if len(top_archaeology_flags) >= 8 else "moderate" if len(top_archaeology_flags) >= 3 else "light"
    )

    central_subsystems = sum(
        1
        for report in subsystem_reports
        if report.get("coupling_indicators", {}).get("possible_centrality_hotspots")
        or report.get("coupling_indicators", {}).get("max_fan_in", 0) >= 20
        or report.get("coupling_indicators", {}).get("max_fan_out", 0) >= 10
    )
    coupling_status = "highly central" if central_subsystems >= 4 else "concentrated" if central_subsystems >= 2 else "bounded"

    alignment_points = _average(
        [ALIGNMENT_POINTS[report.get("test_ownership_alignment", {}).get("alignment_status", "unclear")] for report in subsystem_reports]
    )
    conflict_count = test_alignment_overview.get("conflict", 0)
    partial_count = test_alignment_overview.get("partial", 0)
    unclear_count = test_alignment_overview.get("unclear", 0)
    test_alignment_status = (
        "aligned"
        if alignment_points >= 2.3 and conflict_count == 0 and unclear_count == 0
        else "drifting"
        if alignment_points >= 1.2 and conflict_count <= 1
        else "weak"
    )

    docs_status = (
        "coherent"
        if broken_doc_reference_count == 0 and inventory_docs_authority_status.get("status") == "clearer"
        else "patchy"
        if broken_doc_reference_count <= 5 and inventory_docs_authority_status.get("status") in {"clearer", "partially clearer"}
        else "weak"
    )

    return [
        _dimension_entry(
            dimension="ownership clarity",
            status=ownership_status,
            points={"clear": 3, "mixed": 2, "weak": 0}[ownership_status],
            counts={**ownership_counts, "unclear_owner_count": unclear_owners},
            confidence_effect="lower" if unclear_owners else "neutral",
            evidence=[
                f"{ownership_counts.get('green', 0)} green / {ownership_counts.get('yellow', 0)} yellow / {ownership_counts.get('red', 0)} red subsystem ownership scores.",
                f"{unclear_owners} subsystem(s) still rely on unclear owner inference.",
            ],
        ),
        _dimension_entry(
            dimension="overlap severity",
            status=overlap_status,
            points={"bounded": 3, "localized hotspots": 2, "system-wide smear risk": 0}[overlap_status],
            counts=dict(overlap_counts),
            evidence=[
                f"{len(top_overlap_findings)} top overlap finding(s) remain inspectable in the current pass.",
                *(item["concern_name"] for item in top_overlap_findings[:2]),
            ],
        ),
        _dimension_entry(
            dimension="archaeology burden",
            status=archaeology_status,
            points={"light": 3, "moderate": 2, "heavy": 0}[archaeology_status],
            counts=archaeology_counts,
            evidence=[
                f"{len(top_archaeology_flags)} top archaeology flag(s) remain in the report.",
                *(f"{item['path']}: {', '.join(item['markers'][:3])}" for item in top_archaeology_flags[:2]),
            ],
        ),
        _dimension_entry(
            dimension="coupling centrality",
            status=coupling_status,
            points={"bounded": 3, "concentrated": 2, "highly central": 0}[coupling_status],
            counts={"central_subsystem_count": central_subsystems, "top_coupling_hotspots": len(top_coupling_hotspots)},
            evidence=[
                f"{central_subsystems} subsystem(s) include centrality hotspots by existing runtime indicators.",
                *(f"{item['path']} ({', '.join(item['reasons'][:2])})" for item in top_coupling_hotspots[:2]),
            ],
        ),
        _dimension_entry(
            dimension="test alignment",
            status=test_alignment_status,
            points={"aligned": 3, "drifting": 2, "weak": 0}[test_alignment_status],
            counts=test_alignment_overview,
            confidence_effect="lower" if unclear_count else "neutral",
            evidence=[
                f"Alignment states: aligned {test_alignment_overview.get('aligned', 0)}, partial {partial_count}, conflict {conflict_count}, unclear {unclear_count}.",
                *(f"{item['concern_name']} -> {item['alignment_status']}" for item in top_test_runtime_doc_mismatches[:2]),
            ],
        ),
        _dimension_entry(
            dimension="documentation coherence",
            status=docs_status,
            points={"coherent": 3, "patchy": 2, "weak": 0}[docs_status],
            counts={
                "broken_doc_reference_count": broken_doc_reference_count,
                "inventory_docs_authority_status": inventory_docs_authority_status.get("status", "unknown"),
            },
            confidence_effect="lower" if docs_status != "coherent" else "neutral",
            evidence=[
                f"{broken_doc_reference_count} broken documentation reference(s) were found.",
                inventory_docs_authority_status.get("summary", "No inventory-doc summary recorded."),
            ],
        ),
    ]


def _pick_architecture_real_evidence(subsystem_reports: list[dict[str, Any]]) -> list[str]:
    candidates = []
    for report in subsystem_reports:
        alignment = report.get("test_ownership_alignment", {})
        if report.get("inferred_owner") in {"unknown", ""}:
            continue
        if "mixed_owner" in report.get("role_labels", []):
            continue
        score = (
            (2 if report.get("ownership_confidence") in {"high", "medium"} else 0)
            + (2 if alignment.get("alignment_status") == "aligned" else 1 if alignment.get("alignment_status") == "partial" else 0)
            + (1 if report.get("verdict") == "green" else 0)
        )
        candidates.append((score, report))
    candidates.sort(key=lambda item: (-item[0], item[1]["subsystem_name"]))
    out = []
    for _score, report in candidates[:3]:
        alignment = report.get("test_ownership_alignment", {})
        out.append(
            f"`{report['subsystem_name']}` still resolves to `{report['inferred_owner']}` "
            f"({report['ownership_confidence']} ownership confidence; test alignment `{alignment.get('alignment_status', 'unclear')}`)."
        )
    return out


def _pick_patch_accumulation_evidence(
    *,
    top_test_runtime_doc_mismatches: list[dict[str, Any]],
    hotspot_reviews: list[dict[str, Any]],
    broken_doc_reference_count: int,
) -> list[str]:
    out = []
    for item in top_test_runtime_doc_mismatches[:2]:
        evidence = item.get("evidence", ["runtime/test/doc mismatch"])
        out.append(
            f"`{item['concern_name']}` is `{item['alignment_status']}` with practical tests centered in `{item['practical_test_owner']}`; "
            f"evidence: {evidence[0]}"
        )
    smearish = [item for item in hotspot_reviews if item["classification"] in {"possible ownership smear", "unclear / needs human review"}]
    if smearish:
        out.append(
            f"{len(smearish)} hotspot(s) still look like ownership-smear or unclear-review candidates, led by `{smearish[0]['hotspot_name']}`."
        )
    if broken_doc_reference_count:
        out.append(
            f"Documentation coherence is still weak enough to add uncertainty: {broken_doc_reference_count} broken reference(s)."
        )
    return out[:4]


def _cleanup_recommendation_for_hotspot(hotspot_name: str) -> str | None:
    mapping = {
        "response policy contracts localized residue": "Keep `game/response_policy_contracts.py` as the runtime owner and `tests/test_response_policy_contracts.py` as the direct-owner suite; treat remaining downstream usage as compatibility/adjacency residue only.",
        "final emission gate orchestration partial mismatch": "Thin the `final_emission_gate` vs `final_emission_meta` overlap so orchestration remains primary and metadata packaging stays secondary.",
        "prompt_context_leads residue": "Convert `game/prompt_context_leads.py` from residue wording into a clearly subordinate helper or document it as retired sediment only.",
        "stage diff telemetry partial mismatch": "Tighten tests/docs so `game/stage_diff_telemetry.py` stays the telemetry owner while `game.turn_packet.py` remains the packet-boundary owner.",
        "turn_packet telemetry adjacency residue": "Continue trimming compatibility wrappers/import paths so telemetry derives from `game.turn_packet.py` without implying a second packet owner.",
    }
    return mapping.get(hotspot_name)


def _stop_warning_for_hotspot(hotspot_name: str) -> str | None:
    mapping = {
        "prompt contracts conflict": "Stop before adding new prompt-contract obligations until `game/prompt_context.py`, `game/prompt_context_leads.py`, and `game/response_policy_contracts.py` stop co-presenting as owners.",
        "social_exchange_emission mixed repair/contract role": "Stop before adding more social-emission repair behavior until `game/social_exchange_emission.py` is either a contract owner or a repair consumer, not both.",
        "test ownership / inventory docs still unclear": "Stop before treating inventory docs as canonical governance while practical test ownership remains unclear.",
    }
    return mapping.get(hotspot_name)


def _synthesize_repo_verdict(
    subsystem_reports: list[dict[str, Any]],
    *,
    broken_doc_reference_count: int,
    top_overlap_findings: list[dict[str, Any]],
    top_coupling_hotspots: list[dict[str, Any]],
    top_archaeology_flags: list[dict[str, Any]],
    test_alignment_overview: dict[str, int],
    top_test_runtime_doc_mismatches: list[dict[str, Any]],
    concerns_with_widest_test_ownership_spread: list[dict[str, Any]],
    likely_transcript_lock_seams: list[dict[str, Any]],
    likely_contract_owned_seams_with_weak_direct_tests: list[dict[str, Any]],
    inventory_docs_authority_status: dict[str, Any],
    manual_review_shortlist: list[dict[str, Any]],
) -> dict[str, Any]:
    scorecard = _build_repo_level_scorecard(
        subsystem_reports,
        broken_doc_reference_count=broken_doc_reference_count,
        top_coupling_hotspots=top_coupling_hotspots,
        top_overlap_findings=top_overlap_findings,
        top_archaeology_flags=top_archaeology_flags,
        test_alignment_overview=test_alignment_overview,
        top_test_runtime_doc_mismatches=top_test_runtime_doc_mismatches,
        inventory_docs_authority_status=inventory_docs_authority_status,
    )
    hotspot_reviews = _build_hotspot_reviews(subsystem_reports)
    hotspot_counts = Counter(item["classification"] for item in hotspot_reviews)
    score_total = sum(item["points"] for item in scorecard)
    weak_dimension_count = sum(item["points"] == 0 for item in scorecard)
    spread_heavy_count = sum(1 for item in concerns_with_widest_test_ownership_spread if item.get("coverage_spread", 0) >= 6)
    system_wide_smear = (
        any(item["status"] == "system-wide smear risk" for item in scorecard)
        or (
            hotspot_counts.get("possible ownership smear", 0) >= 4
            and spread_heavy_count >= 3
            and test_alignment_overview.get("conflict", 0) + test_alignment_overview.get("unclear", 0) >= 2
        )
    )
    unclear_signal_count = (
        test_alignment_overview.get("unclear", 0)
        + sum(1 for report in subsystem_reports if report.get("ownership_confidence") == "unclear")
        + (1 if inventory_docs_authority_status.get("status") in {"remains unclear", "missing"} else 0)
    )
    confidence = "high" if unclear_signal_count <= 1 and weak_dimension_count <= 1 else "medium" if unclear_signal_count <= 4 else "low"

    if score_total >= 14 and hotspot_counts.get("possible ownership smear", 0) <= 1 and hotspot_counts.get("unclear / needs human review", 0) == 0:
        repo_verdict = "structurally real, under-consolidated"
    elif score_total >= 11 and not system_wide_smear and weak_dimension_count <= 2:
        repo_verdict = "transitional but coherent"
    elif score_total >= 7 and not system_wide_smear:
        repo_verdict = "mixed / caution"
    else:
        repo_verdict = "high ambiguity / architecture risk"

    if repo_verdict == "structurally real, under-consolidated" and hotspot_counts.get("possible ownership smear", 0) <= 1:
        action_mode = "stable enough for cleanup-only consolidation"
    elif repo_verdict == "high ambiguity / architecture risk" or system_wide_smear or (
        hotspot_counts.get("possible ownership smear", 0) + hotspot_counts.get("unclear / needs human review", 0) >= 4
        and len(likely_contract_owned_seams_with_weak_direct_tests) >= 2
    ):
        action_mode = "high ambiguity / stop and stabilize before growth"
    else:
        action_mode = "needs targeted ownership cleanup before more features"

    strongest_real = _pick_architecture_real_evidence(subsystem_reports)
    strongest_patch = _pick_patch_accumulation_evidence(
        top_test_runtime_doc_mismatches=top_test_runtime_doc_mismatches,
        hotspot_reviews=hotspot_reviews,
        broken_doc_reference_count=broken_doc_reference_count,
    )
    cleanup_only = []
    for item in hotspot_reviews:
        if item["classification"] not in {"localized under-consolidation", "transitional residue"}:
            continue
        recommendation = _cleanup_recommendation_for_hotspot(item["hotspot_name"])
        if recommendation and recommendation not in cleanup_only:
            cleanup_only.append(recommendation)
    stop_warnings = []
    for item in hotspot_reviews:
        if item["classification"] not in {"possible ownership smear", "unclear / needs human review"}:
            continue
        warning = _stop_warning_for_hotspot(item["hotspot_name"])
        if warning and warning not in stop_warnings:
            stop_warnings.append(warning)

    mismatch_review = []
    for item in top_test_runtime_doc_mismatches[:5]:
        mismatch_review.append(
            {
                "concern_name": item["concern_name"],
                "alignment_status": item["alignment_status"],
                "severity": item["severity"],
                "runtime_owner": item["runtime_owner"],
                "practical_test_owner": item["practical_test_owner"],
                "coverage_spread": item.get("coverage_spread", 0),
                "evidence": item.get("evidence", [])[:4],
            }
        )

    transcript_summary = {
        "transcript_lock_seam_count": len(likely_transcript_lock_seams),
        "weak_contract_direct_test_count": len(likely_contract_owned_seams_with_weak_direct_tests),
        "summary": (
            "Transcript-style protection is starting to compete with direct contract-owner tests."
            if likely_transcript_lock_seams or likely_contract_owned_seams_with_weak_direct_tests
            else "Transcript locks look secondary to direct owner tests in this pass."
        ),
        "transcript_lock_seams": likely_transcript_lock_seams[:5],
        "weak_contract_owned_seams": likely_contract_owned_seams_with_weak_direct_tests[:5],
    }

    rationale = [
        f"Repo-level verdict: **{repo_verdict}** with scorecard total {score_total}/18.",
        f"Action mode: **{action_mode}**.",
        f"Hotspot mix: {hotspot_counts.get('localized under-consolidation', 0)} localized, "
        f"{hotspot_counts.get('transitional residue', 0)} transitional, "
        f"{hotspot_counts.get('possible ownership smear', 0)} possible smear, "
        f"{hotspot_counts.get('unclear / needs human review', 0)} unclear.",
    ]

    return {
        "repo_level_verdict": repo_verdict,
        "repo_level_confidence": confidence,
        "recommended_action_mode": action_mode,
        "repo_level_scorecard": scorecard,
        "hotspot_classifications": hotspot_reviews,
        "strongest_evidence_architecture_real": strongest_real[:4],
        "strongest_evidence_patch_accumulating": strongest_patch[:4],
        "runtime_test_doc_mismatch_review": mismatch_review,
        "transcript_contract_lock_risk_summary": transcript_summary,
        "cleanup_only_opportunities": cleanup_only[:5],
        "stop_before_feature_warnings": stop_warnings[:5],
        "manual_spot_check_list": manual_review_shortlist[:8],
        "localized_hotspot_count": hotspot_counts.get("localized under-consolidation", 0),
        "transitional_residue_count": hotspot_counts.get("transitional residue", 0),
        "possible_ownership_smear_count": hotspot_counts.get("possible ownership smear", 0),
        "unclear_hotspot_count": hotspot_counts.get("unclear / needs human review", 0),
        "system_wide_smear": system_wide_smear,
        "score_total": score_total,
        "rationale": rationale,
    }


def _build_summary(
    subsystem_reports: list[dict[str, Any]],
    records: dict[str, FileRecord],
    fan_in: dict[str, int],
    fan_out: dict[str, int],
    doc_issues: list[dict[str, str]],
    runtime_analysis: dict[str, Any],
    test_analysis: dict[str, Any],
) -> dict[str, Any]:
    verdict_counts = Counter(report["verdict"] for report in subsystem_reports)
    scored_files = []
    for rel_path, record in records.items():
        if not rel_path.endswith(".py"):
            continue
        scored_files.append((fan_in.get(rel_path, 0) + fan_out.get(rel_path, 0), rel_path, record))
    scored_files.sort(key=lambda item: (-item[0], item[1]))
    top_cross_cutting = [
        {
            "path": rel_path,
            "fan_in": fan_in.get(rel_path, 0),
            "fan_out": fan_out.get(rel_path, 0),
        }
        for _score, rel_path, _record in scored_files[:8]
        if _score > 0
    ]

    top_strengths = [
        f"{report['subsystem_name']} is {report['verdict']} with {len(report['primary_files'])} primary file(s) and {len(report['related_tests'])} related test/doc links."
        for report in subsystem_reports
        if report["verdict"] == "green"
    ][:3]
    top_risks = [
        f"{report['subsystem_name']} is {report['verdict']} because overlap, owner clarity, or test alignment stayed weak."
        for report in subsystem_reports
        if report["verdict"] in {"red", "yellow"}
    ][:5]

    archaeology_flags = []
    for rel_path, record in sorted(records.items()):
        if record.residue_terms:
            archaeology_flags.append(
                {
                    "path": rel_path,
                    "markers": record.residue_terms,
                }
            )
    archaeology_flags = archaeology_flags[:10]
    runtime_summary = runtime_analysis.get("summary", {})
    test_summary = test_analysis.get("summary", {})

    next_steps: list[str] = []
    if doc_issues:
        next_steps.append("Fix broken documentation references before using docs as ownership authority.")
    if any(report["ownership_confidence"] in {"low", "unclear"} for report in subsystem_reports):
        next_steps.append("Document explicit owners for subsystems that still rely on inference only.")
    if any("mixed_owner" in report["role_labels"] for report in subsystem_reports):
        next_steps.append("Trim mixed-owner modules before extracting additional integrity logic across validator/repair/orchestration boundaries.")
    if any(not [path for path in report["related_tests"] if path.endswith(".py")] for report in subsystem_reports):
        next_steps.append("Add or relink focused tests where subsystem ownership lacks a stable pytest home.")
    if test_summary.get("top_test_runtime_doc_mismatches"):
        next_steps.append("Resolve the highest test/runtime/doc mismatches before adding more cross-cutting regression locks.")
    if not next_steps:
        next_steps.append("Review the highest fan-in/fan-out files first for future consolidation batches.")
        next_steps.append("Use this report as a baseline before changing final-emission orchestration boundaries.")

    overall_verdict = "green"
    if verdict_counts["red"] >= 1:
        overall_verdict = "red"
    elif verdict_counts["yellow"] >= 2:
        overall_verdict = "yellow"

    summary = {
        "overall_verdict": overall_verdict,
        "subsystem_verdict_counts": dict(verdict_counts),
        "top_cross_cutting_files": top_cross_cutting,
        "top_structural_strengths": top_strengths,
        "top_structural_risks": top_risks,
        "top_ownership_ambiguities": runtime_summary.get("top_ownership_ambiguities", []),
        "top_overlap_findings": runtime_summary.get("top_overlap_findings", []),
        "top_coupling_hotspots": runtime_summary.get("top_coupling_hotspots", []),
        "top_archaeology_flags": runtime_summary.get("top_archaeology_flags", archaeology_flags),
        "recommended_next_audit_steps": next_steps[:5],
        "broken_doc_reference_count": len(doc_issues),
        "test_category_counts": test_summary.get("test_category_counts", {}),
        "test_file_category_counts": test_summary.get("test_file_category_counts", {}),
        "test_alignment_overview": test_summary.get("test_alignment_overview", {}),
        "top_test_runtime_doc_mismatches": test_summary.get("top_test_runtime_doc_mismatches", []),
        "concerns_with_widest_test_ownership_spread": test_summary.get(
            "concerns_with_widest_test_ownership_spread", []
        ),
        "likely_transcript_lock_seams": test_summary.get("likely_transcript_lock_seams", []),
        "likely_contract_owned_seams_with_weak_direct_tests": test_summary.get(
            "likely_contract_owned_seams_with_weak_direct_tests", []
        ),
        "inventory_docs_authority_status": test_summary.get("inventory_docs_authority_status", {}),
        "manual_review_shortlist": test_summary.get("manual_review_shortlist", []),
        "schema_notes": runtime_summary.get("schema_notes", []) + test_summary.get("schema_notes", []),
    }
    summary.update(
        _synthesize_repo_verdict(
            subsystem_reports,
            broken_doc_reference_count=summary["broken_doc_reference_count"],
            top_overlap_findings=summary["top_overlap_findings"],
            top_coupling_hotspots=summary["top_coupling_hotspots"],
            top_archaeology_flags=summary["top_archaeology_flags"],
            test_alignment_overview=summary["test_alignment_overview"],
            top_test_runtime_doc_mismatches=summary["top_test_runtime_doc_mismatches"],
            concerns_with_widest_test_ownership_spread=summary["concerns_with_widest_test_ownership_spread"],
            likely_transcript_lock_seams=summary["likely_transcript_lock_seams"],
            likely_contract_owned_seams_with_weak_direct_tests=summary[
                "likely_contract_owned_seams_with_weak_direct_tests"
            ],
            inventory_docs_authority_status=summary["inventory_docs_authority_status"],
            manual_review_shortlist=summary["manual_review_shortlist"],
        )
    )
    return summary


def analyze_repo(repo_root: Path) -> dict[str, Any]:
    records, warnings = _collect_records(repo_root)
    fan_in, fan_out = _build_fan_maps(records)
    doc_issues = _find_doc_reference_issues(records, repo_root)
    ownership_consistency = _ownership_declaration_consistency(records)
    runtime_analysis = analyze_runtime_findings(
        records=records,
        subsystem_seeds=SUBSYSTEM_SEEDS,
        fan_in=fan_in,
        fan_out=fan_out,
    )
    subsystem_reports = _build_subsystem_reports(records, fan_in, fan_out, doc_issues, runtime_analysis)
    test_analysis = analyze_test_ownership(records=records, subsystem_reports=subsystem_reports)
    test_alignment_by_name = test_analysis.get("subsystem_findings", {})
    for report in subsystem_reports:
        alignment = test_alignment_by_name.get(report["subsystem_name"])
        if not alignment:
            continue
        report["test_ownership_alignment"] = alignment
        report["audit_scores"]["test alignment"] = {
            "score": ALIGNMENT_TEST_SCORE.get(alignment["alignment_status"], "red"),
            "reason": "Reconciles runtime owner, documented owner, and practical test home instead of counting test links alone.",
        }
        if alignment["alignment_status"] in {"partial", "conflict", "unclear"}:
            report["warnings"].append(
                f"Test ownership reconciliation is {alignment['alignment_status']}: {alignment['mismatch_type']}."
            )
        if alignment["healthy_overlap"]:
            report["warnings"].append("Healthy overlap detected: focused owner tests remain primary and cross-layer suites look secondary.")
        report["warnings"] = sorted(dict.fromkeys(report["warnings"]))
        report["verdict"] = _verdict_from_audit_scores(report["audit_scores"], bool(report["primary_files"]))
    warnings.extend(
        f"Broken documentation reference: {issue['source']} -> {issue['reference']}"
        for issue in doc_issues
    )
    warnings.extend(
        f"Ownership declaration mismatch: {item['path']} -> {item['issue']}"
        for item in ownership_consistency.get("issues", [])
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root.resolve()),
        "modules_analyzed": _module_summary(records, fan_in, fan_out, runtime_analysis),
        "docs_analyzed": _doc_summary(records, doc_issues),
        "tests_analyzed": _test_summary(records, test_analysis),
        "subsystem_reports": subsystem_reports,
        "summary": _build_summary(subsystem_reports, records, fan_in, fan_out, doc_issues, runtime_analysis, test_analysis),
        "warnings": sorted(dict.fromkeys(warnings)),
    }
    report["summary"]["ownership_declaration_consistency"] = ownership_consistency
    report["summary"]["schema_notes"] = report["summary"].get("schema_notes", []) + [
        "summary now includes ownership_declaration_consistency for ledger-vs-module declaration checks."
    ]
    return report


def _focus_subsystem_text(report: dict[str, Any], subsystem_name: str) -> str:
    subsystem_reports = report["subsystem_reports"]
    target = next((item for item in subsystem_reports if item["subsystem_name"].lower() == subsystem_name.lower()), None)
    if not target:
        available = ", ".join(item["subsystem_name"] for item in subsystem_reports)
        return f"Subsystem `{subsystem_name}` not found. Available subsystems: {available}"

    alignment = target.get("test_ownership_alignment", {})
    coupling = target.get("coupling_indicators", {})
    overlap_lines = []
    if target.get("overlap_findings"):
        overlap_lines.extend(
            f"- {item['overlap_type']} ({item['severity']})"
            for item in target["overlap_findings"][:3]
        )
    if target.get("likely_overlap_points"):
        overlap_lines.extend(f"- {item}" for item in target["likely_overlap_points"][:2])
    archaeology_lines = [
        f"- {item.get('path', 'module')}: {item.get('kind', 'marker')}"
        for item in target.get("archaeology_markers", [])[:3]
    ] or ["- none"]
    evidence_lines = []
    evidence_lines.extend(f"- {item}" for item in target.get("owner_evidence", [])[:2])
    evidence_lines.extend(f"- {item}" for item in alignment.get("evidence", [])[:3])
    if not evidence_lines:
        evidence_lines.append("- no concise evidence lines recorded")

    lines = [
        f"Focus subsystem: {target['subsystem_name']}",
        f"Verdict: {target['verdict']}",
        f"Declared owner: {target.get('declared_owner', 'unknown')}",
        f"Inferred owner: {target.get('inferred_owner', 'unknown')} ({target.get('ownership_confidence', 'unclear')})",
        f"Role labels: {', '.join(target.get('role_labels', [])) or 'none'}",
        f"Overlap: {len(target.get('overlap_findings', []))} runtime finding(s), {len(target.get('likely_overlap_points', []))} likely overlap point(s)",
        f"Coupling: max fan-in {coupling.get('max_fan_in', 0)}, max fan-out {coupling.get('max_fan_out', 0)}, hotspot paths {len(coupling.get('possible_centrality_hotspots', []))}",
        f"Archaeology: {len(target.get('archaeology_markers', []))} marker(s)",
        f"Test ownership alignment: {alignment.get('alignment_status', 'unclear')} / {alignment.get('mismatch_type', 'none')} / {alignment.get('severity', 'n/a')}",
        "Key overlap lines:",
        *(overlap_lines or ["- none"]),
        "Key archaeology lines:",
        *archaeology_lines,
        "Key evidence lines:",
        *evidence_lines,
    ]
    return "\n".join(lines)


def _cli_summary_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"Repo verdict: {summary.get('repo_level_verdict', summary.get('overall_verdict', 'unknown'))}",
        f"Confidence: {summary.get('repo_level_confidence', 'unknown')}",
        f"Action mode: {summary.get('recommended_action_mode', 'unknown')}",
        "Top scorecard signals:",
    ]
    for item in summary.get("repo_level_scorecard", [])[:6]:
        lines.append(f"- {item['dimension']}: {item['status']} ({item['points']}/3)")
    lines.append("Top hotspots:")
    for item in summary.get("hotspot_classifications", [])[:5]:
        lines.append(f"- {item['hotspot_name']}: {item['classification']}")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    subsystem_reports = report["subsystem_reports"]
    lines = [
        "# Architecture Audit",
        "",
        "## Executive verdict",
        "",
        f"- Repo-level verdict: **{summary.get('repo_level_verdict', 'unknown')}**",
        f"- Confidence: **{summary.get('repo_level_confidence', 'unknown')}**",
        f"- Recommended action mode: **{summary.get('recommended_action_mode', 'unknown')}**",
        f"- Legacy subsystem roll-up color: **{summary['overall_verdict']}**",
        f"- Modules analyzed: **{report['modules_analyzed']['count']}**",
        f"- Docs analyzed: **{report['docs_analyzed']['count']}**",
        f"- Test files analyzed: **{report['tests_analyzed']['count']}**",
        "",
    ]
    for item in summary.get("rationale", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Repo-level scorecard", ""])
    lines.append("| Dimension | Status | Points |")
    lines.append("| --- | --- | ---: |")
    for item in summary.get("repo_level_scorecard", []):
        lines.append(f"| {item['dimension']} | {item['status']} | {item['points']}/3 |")

    lines.extend(["", "## Subsystem verdicts", ""])
    lines.append("| Subsystem | Verdict | Owner | Test alignment |")
    lines.append("| --- | --- | --- | --- |")
    for subsystem in subsystem_reports:
        alignment = subsystem.get("test_ownership_alignment", {})
        lines.append(
            f"| {subsystem['subsystem_name']} | {subsystem['verdict']} | "
            f"{subsystem.get('inferred_owner', 'unknown')} | {alignment.get('alignment_status', 'unclear')} |"
        )

    lines.extend(["", "## Strongest evidence that the architecture is real", ""])
    for item in summary.get("strongest_evidence_architecture_real", []) or ["No strong real-architecture signals cleared the current heuristic thresholds."]:
        lines.append(f"- {item}")

    lines.extend(["", "## Strongest evidence that the architecture may be patch-accumulating", ""])
    for item in summary.get("strongest_evidence_patch_accumulating", []) or ["No strong patch-accumulation signals were elevated in the current pass."]:
        lines.append(f"- {item}")

    lines.extend(["", "## Known ambiguity hotspots", ""])
    for item in summary.get("hotspot_classifications", []):
        evidence = item.get("evidence", [])
        note = evidence[0] if evidence else item.get("why", "heuristic hotspot signal")
        lines.append(f"- `{item['hotspot_name']}` -> {item['classification']}; {note}")

    lines.extend(["", "## Runtime/test/doc mismatch review", ""])
    mismatch_items = summary.get("runtime_test_doc_mismatch_review", [])
    if mismatch_items:
        for item in mismatch_items:
            evidence = item["evidence"][0] if item["evidence"] else "heuristic mismatch signal"
            lines.append(
                f"- `{item['concern_name']}` -> runtime `{item['runtime_owner']}` vs practical `{item['practical_test_owner']}` "
                f"({item['alignment_status']}; {item['severity']}; spread {item['coverage_spread']}); evidence: {evidence}"
            )
    else:
        lines.append("- No runtime/test/doc mismatches were promoted into the current shortlist.")

    lines.extend(["", "## Transcript-lock vs contract-lock risk summary", ""])
    transcript_summary = summary.get("transcript_contract_lock_risk_summary", {})
    lines.append(f"- {transcript_summary.get('summary', 'No transcript/contract summary recorded.')}")
    for item in transcript_summary.get("transcript_lock_seams", [])[:3]:
        evidence = item["evidence"][0] if item.get("evidence") else "transcript-heavy seam"
        lines.append(f"- Transcript-heavy seam: `{item['concern_name']}` -> {evidence}")
    for item in transcript_summary.get("weak_contract_owned_seams", [])[:3]:
        evidence = item["evidence"][0] if item.get("evidence") else "weak direct test seam"
        lines.append(f"- Weak direct contract test seam: `{item['concern_name']}` -> {evidence}")

    lines.extend(["", "## Manual spot-check list", ""])
    for item in summary.get("manual_spot_check_list", []) or [{"concern_name": "none", "alignment_status": "n/a", "severity": "n/a", "runtime_owner": "n/a", "practical_test_owner": "n/a"}]:
        if item["concern_name"] == "none":
            lines.append("- No manual spot-check items were shortlisted.")
            break
        lines.append(
            f"- `{item['concern_name']}` -> runtime `{item['runtime_owner']}`, practical `{item['practical_test_owner']}` "
            f"({item['alignment_status']}; {item['severity']})"
        )

    lines.extend(["", "## Cleanup-only opportunities", ""])
    cleanup_items = summary.get("cleanup_only_opportunities", [])
    if cleanup_items:
        for item in cleanup_items:
            lines.append(f"- {item}")
    else:
        lines.append("- No safe cleanup-only opportunities were elevated above current ambiguity risk.")

    lines.extend(["", "## Stop-before-feature warnings", ""])
    stop_items = summary.get("stop_before_feature_warnings", [])
    if stop_items:
        for item in stop_items:
            lines.append(f"- {item}")
    else:
        lines.append("- No stop-before-feature warnings were triggered by the current rubric.")

    lines.extend(["", "## Schema notes", ""])
    for item in summary.get("schema_notes", []) or ["No schema additions were recorded in this pass."]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def _write_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Static architecture durability audit.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root to inspect.")
    parser.add_argument("--json-out", default=str(DEFAULT_JSON_OUT), help="Path for JSON report output.")
    parser.add_argument("--md-out", default=str(DEFAULT_MD_OUT), help="Path for Markdown summary output.")
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print the repo-level verdict summary after writing artifacts.",
    )
    parser.add_argument(
        "--focus-subsystem",
        help="Print a focused subsystem breakdown by seeded subsystem name.",
    )
    parser.add_argument(
        "--strict-doc-check",
        action="store_true",
        help="Exit non-zero when broken documentation references are detected.",
    )
    parser.add_argument(
        "--strict-test-check",
        action="store_true",
        help="Exit non-zero when a seeded subsystem has no related pytest files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    report = analyze_repo(repo_root)

    json_out = Path(args.json_out).resolve()
    md_out = Path(args.md_out).resolve()
    _write_report(json_out, json.dumps(report, indent=2))
    _write_report(md_out, render_markdown(report))

    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    if args.print_summary:
        print(_cli_summary_text(report))
    if args.focus_subsystem:
        print(_focus_subsystem_text(report, args.focus_subsystem))

    exit_code = 0
    if args.strict_doc_check and report["docs_analyzed"]["broken_references"]:
        exit_code = 1
        print("Strict doc check failed: broken documentation references detected.", file=sys.stderr)
    if args.strict_test_check:
        missing = [
            item["subsystem_name"]
            for item in report["subsystem_reports"]
            if not [path for path in item["related_tests"] if path.endswith(".py")]
        ]
        if missing:
            exit_code = 1
            print(
                "Strict test check failed: missing related pytest files for "
                + ", ".join(missing),
                file=sys.stderr,
            )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
