#!/usr/bin/env python3
"""BV15 — final_emission_gate authority discovery (read-only AST scan)."""

from __future__ import annotations

import ast
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv15_final_emission_gate_analysis.json"
BU_CSV = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"
CALLER_CSV = ROOT / "docs" / "audits" / "BU_caller_fan_in.csv"
TARGET = "game.final_emission_gate"
TARGET_PATH = ROOT / "game" / "final_emission_gate.py"
TERMINAL_TARGET = "game.final_emission_terminal_pipeline"
TERMINAL_PATH = ROOT / "game" / "final_emission_terminal_pipeline.py"
SCAN_ROOTS = ("game", "tests", "tools", "scripts")

ORCHESTRATION = {"apply_final_emission_gate"}
GATE_AUTHORITY = {
    "initialize_gate_execution_context",
    "run_strict_social_composition_trunk",
    "run_non_strict_layer_stack",
    "run_generic_accept_exit",
    "run_generic_replace_exit",
}
COMPAT = {
    "get_speaker_selection_contract",
    "validate_emitted_speaker_against_contract",
    "SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES",
    "detect_emitted_speaker_signature",
    "apply_interaction_continuity_emission_step",
    "attach_interaction_continuity_validation",
}
HELPER = {
    "resolve_gate_preflight_pregate_text",
    "apply_observe_passive_scene_concrete_beat_upstream_satisfier",
}


def subsystem(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    if rel.startswith("tools/") or rel.startswith("scripts/"):
        return "tools/analysis"
    if rel.startswith("tests/helpers/"):
        if "gate" in name:
            return "gate helpers"
        if "replay" in name or "golden" in name:
            return "replay helpers"
        return "test helpers"
    if rel.startswith("tests/"):
        if "ownership" in name:
            return "ownership governance"
        if "gate" in name or "final_emission" in name or "boundary" in name:
            return "final emission gate"
        if "replay" in name or "golden" in name or "transcript" in name:
            return "replay"
        if any(token in name for token in ("architecture", "validation_layer", "test_audit", "realization_layer")):
            return "diagnostics"
        return "integration/regression"
    if rel.startswith("game/"):
        if "final_emission_gate" in name:
            return "final emission gate"
        if "final_emission" in name:
            return "final emission pipeline"
        if name in ("api.py", "api_turn_support.py", "gm.py", "gm_retry.py"):
            return "production runtime"
        return "production runtime"
    return "other"


def ownership_bucket(rel: str, symbols: list[str]) -> str:
    sym = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}
    if any(token in rel for token in ("ownership", "gate_thin_boundary", "gate_delegator")):
        return "ownership-governance"
    if sym <= {"apply_final_emission_gate"}:
        return "gate-orchestration"
    if sym <= {"apply_final_emission_gate", "get_speaker_selection_contract"}:
        return "gate-orchestration"
    if any("(module)" in s for s in symbols):
        return "module-introspection"
    return "mixed-gate-utility"


def usage_classes(rel: str, symbols: list[str]) -> list[str]:
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    classes: set[str] = set()
    sym = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}

    if rel.startswith("tests/"):
        classes.add("tests")
    if any(token in name for token in ("ownership", "gate_delegator", "gate_thin")):
        classes.add("governance")
    if any(token in name for token in ("architecture", "validation_layer", "test_audit", "realization_layer")):
        classes.add("diagnostics")
    if any(token in name for token in ("replay", "golden", "transcript")):
        classes.add("replay")
    if "apply_final_emission_gate" in sym:
        classes.add("gate orchestration")
    if any("(module)" in s for s in symbols):
        classes.add("gate orchestration")
    if rel == "game/final_emission_runtime.py":
        classes.add("terminal pipeline")
    if "fallback" in name:
        classes.add("fallback")
    if "validator" in name or "validation" in name:
        classes.add("validators")
    if "gate" in name or "final_emission" in name or "boundary" in name:
        classes.add("gate orchestration")
    if "terminal" in name or "finalize" in name:
        classes.add("terminal pipeline")

    return sorted(classes or ["other"])


def symbol_category(sym: str) -> str:
    if sym.endswith("(module)"):
        return "module-import"
    clean = sym.split(" as ")[0].strip()
    if clean in ORCHESTRATION:
        return "orchestration"
    if clean in GATE_AUTHORITY:
        return "gate-authority"
    if clean in COMPAT:
        return "compatibility"
    if clean in HELPER:
        return "helper"
    return "other"


def authority_class(sym: str) -> str:
    clean = sym.split(" as ")[0].strip()
    if clean.endswith("(module)"):
        return "module-introspection"
    if clean in ORCHESTRATION:
        return "canonical-gate-authority"
    if clean in COMPAT:
        return "compatibility-bridge"
    if clean in GATE_AUTHORITY:
        return "orchestration-delegate"
    return "accidental-coupling"


def module_exports(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    exports: dict[str, str] = {}
    skip_modules = {"__future__", "typing", "collections.abc"}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            exports[node.name] = "defined"
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports[target.id] = "defined"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in skip_modules:
                continue
            for alias in node.names:
                name = alias.asname or alias.name
                exports[name] = f"re-export from {mod}"
    return exports


def parse_imports(path: Path, target: str) -> list[str]:
    short = target.rsplit(".", 1)[-1]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except SyntaxError:
        return []
    syms: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "game":
            for alias in node.names:
                if alias.name == "final_emission_gate":
                    syms.append(f"{alias.asname or short} (module)")
        elif isinstance(node, ast.ImportFrom) and node.module == target:
            for alias in node.names:
                if alias.name != "*":
                    syms.append(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == target:
                    syms.append(f"{alias.asname or short} (module)")
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
                rows[qname[len(prefix) :]] = int(row["caller_file_count"])
    return rows


def gate_terminal_boundary() -> dict[str, Any]:
    gate_exports = set(module_exports(TARGET_PATH))
    terminal_exports = set(module_exports(TERMINAL_PATH))
    gate_fan_out = fan_out_modules(TARGET_PATH)
    terminal_fan_out = fan_out_modules(TERMINAL_PATH)
    shared_deps = sorted(gate_fan_out & terminal_fan_out)
    gate_only_deps = sorted(gate_fan_out - terminal_fan_out)
    terminal_only_deps = sorted(terminal_fan_out - gate_fan_out)

    # Who imports both modules
    dual_importers: list[str] = []
    gate_importers = set()
    terminal_importers = set()
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/__pycache__/" in rel:
            continue
        if parse_imports(path, TARGET):
            gate_importers.add(rel)
        if parse_imports(path, TERMINAL_TARGET):
            terminal_importers.add(rel)
    dual_importers = sorted(gate_importers & terminal_importers)

    return {
        "gate_fan_out_count": len(gate_fan_out),
        "terminal_fan_out_count": len(terminal_fan_out),
        "shared_dependency_count": len(shared_deps),
        "shared_dependencies": shared_deps,
        "gate_only_dependencies": gate_only_deps,
        "terminal_only_dependencies": terminal_only_deps,
        "dual_importers": dual_importers,
        "dual_importer_count": len(dual_importers),
        "gate_imports_terminal": TERMINAL_TARGET.replace(".", "/") + ".py" in gate_fan_out,
        "terminal_imports_gate": TARGET.replace(".", "/") + ".py" in terminal_fan_out,
    }


def build_analysis() -> dict[str, Any]:
    bu_fi = load_bu_fi()
    caller_fi = load_caller_fi()
    export_map = module_exports(TARGET_PATH)
    exports = sorted(export_map)
    public_exports = [e for e in exports if not e.startswith("_")]
    importers: list[dict[str, Any]] = []
    symbol_fi: dict[str, set[str]] = defaultdict(set)

    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/__pycache__/" in rel or rel == "game/final_emission_gate.py":
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
        bu_sym_fi = caller_fi.get(sym, ast_fi if sym.endswith("(module)") else caller_fi.get(sym, 0) or ast_fi)
        if not sym.endswith("(module)"):
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
        "cycle": "BV15",
        "target": TARGET,
        "bu_fan_in": bu_fi.get(TARGET, 0),
        "terminal_bu_fan_in": bu_fi.get(TERMINAL_TARGET, 0),
        "ast_direct_importers": len(importers),
        "production_importers": len(prod),
        "test_importers": len(test_only),
        "loc": len(TARGET_PATH.read_text(encoding="utf-8-sig").splitlines()),
        "export_count": len(exports),
        "public_export_count": len(public_exports),
        "defined_export_count": sum(1 for v in export_map.values() if v == "defined"),
        "reexport_count": sum(1 for v in export_map.values() if v.startswith("re-export")),
        "exports": exports,
        "export_map": export_map,
        "public_exports": public_exports,
        "fan_out": sorted(fan_out_modules(TARGET_PATH)),
        "fan_out_count": len(fan_out_modules(TARGET_PATH)),
        "importers": importers,
        "symbol_fi_counts": sorted(
            [(sym, len(files), symbol_meta[sym]["fan_in_bu"]) for sym, files in symbol_fi.items()],
            key=lambda x: (-x[2], -x[1], x[0]),
        ),
        "symbol_meta": symbol_meta,
        "usage_class_totals": dict(sorted(usage_totals.items(), key=lambda x: -x[1])),
        "ownership_bucket_totals": dict(sorted(bucket_totals.items(), key=lambda x: -x[1])),
        "category_totals": dict(sorted(category_totals.items(), key=lambda x: -x[1])),
        "subsystem_totals": dict(sorted(subsystem_totals.items(), key=lambda x: -x[1])),
        "gate_terminal_boundary": gate_terminal_boundary(),
    }


def main() -> int:
    analysis = build_analysis()
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(analysis, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(
        f"{TARGET}: BU FI={analysis['bu_fan_in']} "
        f"AST={analysis['ast_direct_importers']} "
        f"prod={analysis['production_importers']} test={analysis['test_importers']} "
        f"LOC={analysis['loc']} defined={analysis['defined_export_count']} reexport={analysis['reexport_count']}"
    )
    for sym, ast_fi, bu_fi in analysis["symbol_fi_counts"][:10]:
        print(f"  {sym}: AST={ast_fi} BU={bu_fi}")
    print(f"Terminal pipeline BU FI={analysis['terminal_bu_fan_in']}")
    print(f"Dual importers gate+terminal={analysis['gate_terminal_boundary']['dual_importer_count']}")
    print(f"Wrote {ARTIFACT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
