#!/usr/bin/env python3
"""BV14 — social_exchange_emission decomposition discovery (read-only AST scan)."""

from __future__ import annotations

import ast
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv14_social_exchange_emission_analysis.json"
BU_CSV = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"
CALLER_CSV = ROOT / "docs" / "audits" / "BU_caller_fan_in.csv"
TARGET = "game.social_exchange_emission"
TARGET_PATH = ROOT / "game" / "social_exchange_emission.py"
SCAN_ROOTS = ("game", "tests", "tools", "scripts")

# --- symbol taxonomy (BV14) ---

COMPOSITION = {
    "build_final_strict_social_response",
    "apply_strict_social_sentence_ownership_filter",
    "apply_strict_social_ownership_enforcement",
    "normalize_social_exchange_candidate",
    "select_best_grounded_social_answer_text",
    "hard_reject_social_exchange_text",
    "coerce_resolution_for_strict_social_emission",
    "reconcile_strict_social_resolution_speaker",
    "effective_strict_social_resolution_for_emission",
    "synthetic_social_exchange_resolution_for_emission",
    "resolve_strict_social_npc_target_id",
    "build_open_social_solicitation_recovery",
    "apply_social_exchange_retry_fallback_gm",
}

PROJECTION = {
    "project_strict_social_replace_realization_family",
    "stamp_strict_social_deterministic_fallback_family",
    "strict_social_deterministic_fallback_family_token",
    "merged_player_prompt_for_gate",
    "log_final_emission_decision",
    "log_final_emission_trace",
}

VALIDATOR = {
    "is_route_illegal_global_or_sanitizer_fallback_text",
    "replacement_is_route_legal_social",
    "strict_social_terminal_dialogue_fallback_valid",
    "social_final_emission_malformed_player_echo",
    "is_conversational_npc_dialogue_line",
    "is_social_exchange_resolution",
}

FALLBACK = {
    "minimal_social_emergency_fallback_line",
    "select_strict_social_emergency_fallback_line",
    "strict_social_ownership_terminal_fallback",
    "deterministic_social_fallback_line",
    "lawful_strict_social_dialogue_emergency_fallback_line",
    "social_fallback_line_for_sanitizer",
    "apply_strict_social_terminal_dialogue_fallback_if_needed",
    "repair_strict_social_terminal_dialogue_fallback_if_needed",
}

POLICY = {
    "strict_social_emission_will_apply",
    "should_apply_strict_social_exchange_emission",
    "player_line_triggers_strict_social_emission",
    "strict_social_suppress_non_native_coercion_for_narration_beat",
    "coerced_strict_social_allowed_by_merged_prompt",
    "minimal_social_resolution_for_directed_question_guard",
    "is_scene_directed_watch_question",
    "looks_like_npc_directed_question",
    "interruption_cue_present_in_text",
    "emission_gate_uncertainty_source",
    "emission_gate_pressure_active",
    "emission_gate_interruption_active",
}


def subsystem(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    if rel.startswith("tools/"):
        return "tools/analysis"
    if rel.startswith("scripts/"):
        return "scripts/analysis"
    if rel.startswith("tests/helpers/"):
        if "replay" in name or "transcript" in name or "golden" in name:
            return "replay helpers"
        if "strict_social" in name or "speaker" in name:
            return "speaker helpers"
        if "gate" in name:
            return "gate helpers"
        return "test helpers"
    if rel.startswith("tests/"):
        if "replay" in name or "golden" in name or "transcript" in name:
            return "replay"
        if "ownership" in name:
            return "ownership governance"
        if "gate" in name or "final_emission" in name or "boundary" in name:
            return "final emission gate"
        if "social" in name or "speaker" in name or "dialogue" in name:
            return "speaker/social"
        if "gm_retry" in name or "api_" in name:
            return "HTTP/pipeline integration"
        return "integration/regression"
    if rel.startswith("game/"):
        if "final_emission_gate" in name:
            return "final emission gate"
        if "final_emission" in name:
            return "final emission pipeline"
        if name in ("api.py", "api_turn_support.py", "gm.py", "gm_retry.py"):
            return "production runtime"
        if name in ("output_sanitizer.py", "response_policy_enforcement.py", "anti_reset_emission_guard.py"):
            return "sanitizer/policy boundary"
        if any(token in name for token in ("dialogue", "speaker", "interaction", "social")):
            return "narrative/social"
        return "production runtime"
    return "other"


def ownership_bucket(rel: str, symbols: list[str]) -> str:
    sym = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}
    if any(token in rel for token in ("ownership", "gate_thin_boundary", "gate_delegator")):
        return "ownership-governance"
    if sym <= {"merged_player_prompt_for_gate"} or sym <= {"strict_social_emission_will_apply"}:
        return "gate-preflight-policy"
    if sym & FALLBACK:
        return "fallback-emission"
    if sym <= {"log_final_emission_decision", "log_final_emission_trace"} or sym <= {
        "log_final_emission_decision"
    } or sym <= {"log_final_emission_trace"}:
        return "telemetry-projection"
    if sym & PROJECTION:
        return "realization-projection"
    if sym & VALIDATOR:
        return "route-legality-validator"
    if sym & COMPOSITION:
        return "strict-social-composition"
    if sym & POLICY:
        return "eligibility-policy"
    if any("(module)" in s for s in symbols):
        return "module-monkeypatch"
    return "mixed-social-utility"


def usage_classes(rel: str, symbols: list[str]) -> list[str]:
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    classes: set[str] = set()
    sym = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}

    if rel.startswith("tests/"):
        classes.add("tests")
        if "replay" in name or "golden" in name or "transcript" in name:
            classes.add("replay")
        if "ownership" in name or "gate_delegator" in name or "gate_thin" in name:
            classes.add("diagnostics")
        if "gate" in name or "final_emission" in name or "boundary" in name:
            classes.add("gate")
        if "social_exchange_emission" in name:
            classes.add("validators")

    if rel.startswith("game/"):
        if "strict_social_stack" in name or "terminal_pipeline" in name:
            classes.add("strict-social pipeline")
            classes.add("terminal emission")
        elif "final_emission" in name:
            if "gate" in name or "preflight" in name:
                classes.add("gate")
            elif "validator" in name:
                classes.add("validators")
            elif "fallback" in name or "visibility" in name:
                classes.add("terminal emission")
            else:
                classes.add("strict-social pipeline")
        elif name in ("output_sanitizer.py", "response_policy_enforcement.py", "anti_reset_emission_guard.py"):
            classes.add("gate")
        elif name in ("api.py", "api_turn_support.py", "gm.py", "gm_retry.py"):
            classes.add("gate")
        elif "speaker" in name or "dialogue" in name or "interaction" in name:
            classes.add("strict-social pipeline")
        else:
            classes.add("strict-social pipeline")

    if sym & VALIDATOR or sym & {"is_route_illegal_global_or_sanitizer_fallback_text", "replacement_is_route_legal_social"}:
        classes.add("validators")
    if sym & FALLBACK:
        classes.add("terminal emission")

    return sorted(classes or ["other"])


def symbol_category(sym: str) -> str:
    if sym.endswith("(module)"):
        return "module-import"
    clean = sym.split(" as ")[0].strip()
    if clean in COMPOSITION:
        return "composition"
    if clean in PROJECTION:
        return "projection"
    if clean in VALIDATOR:
        return "validator"
    if clean in FALLBACK:
        return "fallback"
    if clean in POLICY:
        return "policy"
    return "other"


def authority_class(sym: str) -> str:
    clean = sym.split(" as ")[0].strip()
    if clean.endswith("(module)"):
        return "convenience-wrapper"
    if clean in COMPOSITION:
        if clean == "build_final_strict_social_response":
            return "canonical-composition-authority"
        return "composition-helper"
    if clean in POLICY:
        if clean in ("strict_social_emission_will_apply", "should_apply_strict_social_exchange_emission"):
            return "policy-vocabulary"
        return "eligibility-projection"
    if clean in FALLBACK:
        if clean == "minimal_social_emergency_fallback_line":
            return "fallback-authority"
        return "fallback-projection"
    if clean in VALIDATOR:
        return "validator-projection"
    if clean in PROJECTION:
        if clean in ("log_final_emission_decision", "log_final_emission_trace"):
            return "telemetry-projection"
        return "realization-projection"
    return "accidental-bridge"


def module_exports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    exports: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            exports.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.append(target.id)
    return exports


def parse_imports(path: Path, target: str) -> list[str]:
    src = path.read_text(encoding="utf-8-sig")
    syms: list[str] = []
    short = target.rsplit(".", 1)[-1]
    try:
        tree = ast.parse(src)
    except SyntaxError:
        tree = None
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == target:
                for alias in node.names:
                    if alias.name != "*":
                        syms.append(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == target:
                        syms.append(f"{alias.asname or short} (module)")
    for block in re.findall(rf"from {re.escape(target)} import ([^\n]+)", src):
        for part in block.replace("(", "").replace(")", "").split(","):
            part = part.strip().split("#")[0].strip()
            if part:
                syms.append(part.split(" as ")[0].strip())
    if re.search(rf"import {re.escape(target)}\\b", src):
        if not any("(module)" in s for s in syms):
            syms.append(f"{short} (module)")
    return sorted(set(syms))


def fan_out_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def load_bu_fi() -> dict[str, int]:
    rows: dict[str, int] = {}
    with BU_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[row["module"]] = int(row["fan_in_total"])
    return rows


def load_caller_fi() -> dict[str, int]:
    rows: dict[str, int] = {}
    prefix = TARGET + "."
    with CALLER_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            qname = row["api"]
            if qname.startswith(prefix):
                sym = qname[len(prefix) :]
                rows[sym] = int(row["caller_file_count"])
    return rows


def build_analysis() -> dict[str, Any]:
    bu_fi = load_bu_fi()
    caller_fi = load_caller_fi()
    exports = module_exports(TARGET_PATH)
    public_exports = [e for e in exports if not e.startswith("_")]
    importers: list[dict[str, Any]] = []
    symbol_fi: dict[str, set[str]] = defaultdict(set)

    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/__pycache__/" in rel or rel == "game/social_exchange_emission.py":
            continue
        if not rel.startswith(SCAN_ROOTS):
            continue
        syms = parse_imports(path, TARGET)
        if not syms:
            continue
        importers.append(
            {
                "file": rel,
                "subsystem": subsystem(rel),
                "symbols": syms,
                "ownership_bucket": ownership_bucket(rel, syms),
                "usage_classes": usage_classes(rel, syms),
            }
        )
        for sym in syms:
            clean = sym.split(" as ")[0].split(" (")[0].strip()
            if clean:
                symbol_fi[clean].add(rel)

    usage_totals: dict[str, int] = defaultdict(int)
    bucket_totals: dict[str, int] = defaultdict(int)
    category_totals: dict[str, int] = defaultdict(int)
    for imp in importers:
        for cls in imp["usage_classes"]:
            usage_totals[cls] += 1
        bucket_totals[imp["ownership_bucket"]] += 1
        for sym in imp["symbols"]:
            category_totals[symbol_category(sym)] += 1

    symbol_meta = {}
    for sym, files in symbol_fi.items():
        ast_fi = len(files)
        bu_sym_fi = caller_fi.get(sym, ast_fi)
        symbol_meta[sym] = {
            "fan_in_ast": ast_fi,
            "fan_in_bu": bu_sym_fi,
            "category": symbol_category(sym),
            "authority_class": authority_class(sym),
            "importers": sorted(files),
        }

    prod = [i for i in importers if i["file"].startswith("game/")]
    test_only = [i for i in importers if i["file"].startswith("tests/")]

    subsystem_totals: dict[str, int] = defaultdict(int)
    for imp in importers:
        subsystem_totals[imp["subsystem"]] += 1

    return {
        "schema_version": 1,
        "cycle": "BV14",
        "target": TARGET,
        "bu_fan_in": bu_fi.get(TARGET, 0),
        "ast_direct_importers": len(importers),
        "production_importers": len(prod),
        "test_importers": len(test_only),
        "loc": len(TARGET_PATH.read_text(encoding="utf-8-sig").splitlines()),
        "export_count": len(exports),
        "public_export_count": len(public_exports),
        "exports": exports,
        "public_exports": public_exports,
        "fan_out": sorted(fan_out_modules(TARGET_PATH)),
        "fan_out_count": len(fan_out_modules(TARGET_PATH)),
        "importers": importers,
        "symbol_fi_counts": sorted(
            [(sym, len(files), caller_fi.get(sym, len(files))) for sym, files in symbol_fi.items()],
            key=lambda x: -x[2],
        ),
        "symbol_meta": symbol_meta,
        "usage_class_totals": dict(sorted(usage_totals.items(), key=lambda x: -x[1])),
        "ownership_bucket_totals": dict(sorted(bucket_totals.items(), key=lambda x: -x[1])),
        "category_totals": dict(sorted(category_totals.items(), key=lambda x: -x[1])),
        "subsystem_totals": dict(sorted(subsystem_totals.items(), key=lambda x: -x[1])),
    }


def main() -> int:
    analysis = build_analysis()
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(analysis, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(
        f"{TARGET}: BU FI={analysis['bu_fan_in']} "
        f"AST={analysis['ast_direct_importers']} "
        f"prod={analysis['production_importers']} test={analysis['test_importers']} "
        f"LOC={analysis['loc']} exports={analysis['public_export_count']}"
    )
    for sym, ast_fi, bu_fi in analysis["symbol_fi_counts"][:15]:
        print(f"  {sym}: AST={ast_fi} BU={bu_fi}")
    print(f"Wrote {ARTIFACT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
