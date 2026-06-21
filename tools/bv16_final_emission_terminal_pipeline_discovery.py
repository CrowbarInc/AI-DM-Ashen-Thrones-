#!/usr/bin/env python3
"""BV16 — final_emission_terminal_pipeline authority discovery (read-only AST scan)."""

from __future__ import annotations

import ast
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv16_final_emission_terminal_pipeline_analysis.json"
BU_CSV = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"
CALLER_CSV = ROOT / "docs" / "audits" / "BU_caller_fan_in.csv"
TARGET = "game.final_emission_terminal_pipeline"
TARGET_PATH = ROOT / "game" / "final_emission_terminal_pipeline.py"
GATE_TARGET = "game.final_emission_gate"
GATE_PATH = ROOT / "game" / "final_emission_gate.py"
VISIBILITY_PATH = ROOT / "game" / "final_emission_visibility_fallback.py"
OPENING_PATH = ROOT / "game" / "final_emission_opening_fallback.py"
IC_PATH = ROOT / "game" / "interaction_continuity.py"
SCAN_ROOTS = ("game", "tests", "tools", "scripts")

FINALIZE_DEFINED = {
    "run_gate_terminal_enforcement_pipeline",
    "apply_strict_social_emergency_fallback_patch",
    "GateTerminalEnforcementProfile",
    "_patch_fem_text_fingerprint",
    "_apply_referent_clarity_pre_finalize",
}
VISIBILITY_SYMBOLS = {"apply_visibility_enforcement"}
N4_SYMBOLS = {"apply_acceptance_quality_n4_floor_seam"}
OPENING_SYMBOLS = {"opening_fallback", "reassert_scene_opening_accepted_candidate"}
IC_SYMBOLS = {
    "apply_interaction_continuity_emission_step",
    "attach_interaction_continuity_validation",
}
REALIZATION_SYMBOLS = {
    "minimal_social_emergency_fallback_line",
    "stamp_strict_social_deterministic_fallback_family",
    "stamp_sealed_fallback_realization_family",
    "stamp_producer_repair_kind",
}
COMPAT_SYMBOLS = {
    "_apply_fallback_behavior_layer",
    "_merge_fallback_behavior_meta",
    "merge_fallback_behavior_into_emission_debug",
    "_apply_referent_clarity_emission_layer",
    "_merge_referent_clarity_meta",
    "_normalize_text",
    "assert_final_emission_mutation_allowed",
    "ensure_final_emission_meta_dict",
    "merge_narration_constraint_debug_into_outputs",
    "_merge_narrative_mode_output_trace_into_gate_fem",
    "_narrative_mode_output_legality_assessment",
    "apply_observe_referential_clarity_upstream_repair",
    "apply_observe_passive_scene_concrete_beat_upstream_satisfier",
    "_strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id",
    "FINAL_EMISSION_META_KEY",
    "PRODUCER_REPAIR_KIND_STRICT_SOCIAL_REPAIR",
}


def subsystem(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    if rel.startswith("tools/") or rel.startswith("scripts/"):
        return "tools/analysis"
    if rel.startswith("tests/helpers/"):
        if "gate" in name or "finalize" in name:
            return "gate helpers"
        if "replay" in name or "golden" in name:
            return "replay helpers"
        return "test helpers"
    if rel.startswith("tests/"):
        if "ownership" in name or "gate_delegator" in name:
            return "ownership governance"
        if "gate" in name or "final_emission" in name or "boundary" in name:
            return "final emission terminal"
        if "replay" in name or "golden" in name or "transcript" in name:
            return "replay"
        if any(token in name for token in ("architecture", "validation_layer", "test_audit", "realization_layer")):
            return "diagnostics"
        return "integration/regression"
    if rel.startswith("game/"):
        if "terminal_pipeline" in name:
            return "final emission terminal"
        if "final_emission" in name:
            return "final emission pipeline"
        return "production runtime"
    return "other"


def ownership_bucket(rel: str, symbols: list[str], attr_uses: list[str]) -> str:
    sym = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}
    attrs = set(attr_uses)
    if any(token in rel for token in ("ownership", "gate_thin_boundary", "gate_delegator")):
        return "ownership-governance"
    if sym <= {"run_gate_terminal_enforcement_pipeline"} and not attrs:
        return "terminal-orchestration"
    if sym <= {"apply_strict_social_emergency_fallback_patch"}:
        return "finalize-realization"
    if attrs <= {"run_gate_terminal_enforcement_pipeline"} or (
        sym <= {f"terminal_pipeline (module)", "tp (module)"} and attrs <= {"run_gate_terminal_enforcement_pipeline"}
    ):
        return "terminal-orchestration"
    if "apply_visibility_enforcement" in attrs:
        return "visibility-monkeypatch"
    if attrs & N4_SYMBOLS or attrs & IC_SYMBOLS:
        return "terminal-tail-monkeypatch"
    if any("(module)" in s for s in symbols):
        return "module-introspection"
    return "mixed-terminal-utility"


def usage_classes(rel: str, symbols: list[str], attr_uses: list[str]) -> list[str]:
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    classes: set[str] = set()
    sym = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}
    attrs = set(attr_uses)

    if rel.startswith("tests/"):
        classes.add("tests")
    if any(token in name for token in ("ownership", "gate_delegator", "gate_thin")):
        classes.add("governance")
    if any(token in name for token in ("replay", "golden", "transcript")):
        classes.add("replay")
    if "validator" in name or "validation" in name:
        classes.add("validators")
    if rel.startswith("game/"):
        classes.add("finalize path")
    if "run_gate_terminal_enforcement_pipeline" in sym or "run_gate_terminal_enforcement_pipeline" in attrs:
        classes.add("finalize path")
    if "apply_visibility_enforcement" in attrs:
        classes.add("visibility")
    if attrs & N4_SYMBOLS or "n4" in name:
        classes.add("N4")
    if attrs & IC_SYMBOLS or "interaction_continuity" in name or "ic" in name:
        classes.add("IC")
    if any("(module)" in s for s in symbols):
        classes.add("finalize path")
    if "opening" in name or "reassert_scene_opening" in attrs:
        classes.add("opening")
    if "sealed_fallback" in name or "apply_strict_social_emergency_fallback_patch" in sym:
        classes.add("realization")

    return sorted(classes or ["other"])


def export_category(sym: str, export_map: dict[str, str]) -> str:
    clean = sym.split(" as ")[0].strip()
    if clean.endswith("(module)"):
        return "module-import"
    if clean in FINALIZE_DEFINED:
        return "finalize"
    if clean in VISIBILITY_SYMBOLS:
        return "visibility"
    if clean in N4_SYMBOLS:
        return "N4"
    if clean in OPENING_SYMBOLS:
        return "opening"
    if clean in IC_SYMBOLS:
        return "IC"
    if clean in REALIZATION_SYMBOLS:
        return "realization"
    if clean in COMPAT_SYMBOLS:
        return "compatibility"
    origin = export_map.get(clean, "")
    if origin.startswith("re-export"):
        return "compatibility"
    return "other"


def authority_class(sym: str, export_map: dict[str, str]) -> str:
    clean = sym.split(" as ")[0].strip()
    if clean.endswith("(module)"):
        return "module-introspection"
    if clean == "run_gate_terminal_enforcement_pipeline":
        return "canonical-finalize-authority"
    if clean == "apply_strict_social_emergency_fallback_patch":
        return "realization-helper"
    if clean in VISIBILITY_SYMBOLS:
        return "visibility-policy-delegate"
    if clean in N4_SYMBOLS:
        return "N4-policy-delegate"
    if clean in IC_SYMBOLS:
        return "IC-projection-delegate"
    if clean in OPENING_SYMBOLS:
        return "opening-projection-delegate"
    if clean in REALIZATION_SYMBOLS:
        return "realization-helper"
    if export_map.get(clean, "").startswith("re-export"):
        return "accidental-bridge"
    if clean.startswith("_"):
        return "internal-helper"
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
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[-1]
                exports[name] = f"import {alias.name}"
    return exports


def parse_imports(path: Path, target: str) -> list[str]:
    short = target.rsplit(".", 1)[-1]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except SyntaxError:
        return []
    syms: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == target:
            for alias in node.names:
                if alias.name != "*":
                    syms.append(f"{alias.asname or alias.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == target:
                    syms.append(f"{alias.asname or short} (module)")
    return sorted(set(syms))


def module_aliases(path: Path, target: str) -> set[str]:
    aliases: set[str] = set()
    short = target.rsplit(".", 1)[-1]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except SyntaxError:
        return aliases
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == target:
                    aliases.add(alias.asname or short)
        elif isinstance(node, ast.ImportFrom) and node.module == target:
            for alias in node.names:
                if alias.name == "*":
                    continue
                aliases.add(alias.asname or alias.name)
    return aliases


def parse_attr_uses(path: Path, aliases: set[str]) -> list[str]:
    if not aliases:
        return []
    text = path.read_text(encoding="utf-8-sig")
    attrs: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id in aliases:
                    attrs.add(node.attr)
    # monkeypatch.setattr(alias, "symbol", ...) — not visible to Attribute AST walks
    for alias in aliases:
        for match in re.finditer(
            rf"(?:monkeypatch\.setattr|setattr)\(\s*{re.escape(alias)}\s*,\s*['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]",
            text,
        ):
            attrs.add(match.group(1))
        for match in re.finditer(
            rf"{re.escape(alias)}\.([a-zA-Z_][a-zA-Z0-9_]*)(?!\.py\b)",
            text,
        ):
            attrs.add(match.group(1))
    return sorted(a for a in attrs if len(a) >= 3 and a not in {"py"})


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


def finalize_boundary() -> dict[str, Any]:
    gate_fan_out = fan_out_modules(GATE_PATH)
    terminal_fan_out = fan_out_modules(TARGET_PATH)
    visibility_fan_out = fan_out_modules(VISIBILITY_PATH)
    opening_fan_out = fan_out_modules(OPENING_PATH)
    ic_fan_out = fan_out_modules(IC_PATH)

    gate_importers: set[str] = set()
    terminal_importers: set[str] = set()
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/__pycache__/" in rel:
            continue
        if parse_imports(path, GATE_TARGET):
            gate_importers.add(rel)
        if parse_imports(path, TARGET):
            terminal_importers.add(rel)

    dual = sorted(gate_importers & terminal_importers)

    terminal_calls = {
        "visibility": "game.final_emission_visibility_fallback.apply_visibility_enforcement",
        "opening": "game.final_emission_opening_fallback.reassert_scene_opening_accepted_candidate",
        "n4": "game.final_emission_acceptance_quality.apply_acceptance_quality_n4_floor_seam",
        "ic_step": "game.interaction_continuity.apply_interaction_continuity_emission_step",
        "ic_attach": "game.interaction_continuity.attach_interaction_continuity_validation",
    }

    return {
        "gate_fan_out_count": len(gate_fan_out),
        "terminal_fan_out_count": len(terminal_fan_out),
        "visibility_fan_out_count": len(visibility_fan_out),
        "opening_fan_out_count": len(opening_fan_out),
        "ic_fan_out_count": len(ic_fan_out),
        "shared_gate_terminal": sorted(gate_fan_out & terminal_fan_out),
        "shared_gate_terminal_count": len(gate_fan_out & terminal_fan_out),
        "gate_only_dependencies": sorted(gate_fan_out - terminal_fan_out),
        "terminal_only_dependencies": sorted(terminal_fan_out - gate_fan_out),
        "gate_imports_terminal": TARGET.replace(".", "/") + ".py" in gate_fan_out,
        "terminal_imports_gate": GATE_TARGET.replace(".", "/") + ".py" in terminal_fan_out,
        "dual_importers": dual,
        "dual_importer_count": len(dual),
        "terminal_direct_calls": terminal_calls,
        "visibility_imports_terminal": any(
            parse_imports(p, TARGET) for p in ROOT.rglob("game/final_emission_visibility_fallback.py")
        ),
    }


def build_analysis() -> dict[str, Any]:
    bu_fi = load_bu_fi()
    caller_fi = load_caller_fi()
    export_map = module_exports(TARGET_PATH)
    exports = sorted(export_map)
    public_exports = [e for e in exports if not e.startswith("_")]
    importers: list[dict[str, Any]] = []
    symbol_fi: dict[str, set[str]] = defaultdict(set)
    attr_fi: dict[str, set[str]] = defaultdict(set)

    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/__pycache__/" in rel or rel == "game/final_emission_terminal_pipeline.py":
            continue
        if not rel.startswith(SCAN_ROOTS):
            continue
        syms = parse_imports(path, TARGET)
        aliases = module_aliases(path, TARGET)
        attrs = parse_attr_uses(path, aliases)
        if not syms and not attrs:
            continue
        importers.append(
            {
                "file": rel,
                "subsystem": subsystem(rel),
                "symbols": syms,
                "attribute_uses": attrs,
                "ownership_bucket": ownership_bucket(rel, syms, attrs),
                "usage_classes": usage_classes(rel, syms, attrs),
            }
        )
        for sym in syms:
            clean = sym.split(" as ")[0].split(" (")[0].strip()
            if clean:
                symbol_fi[clean].add(rel)
        for attr in attrs:
            attr_fi[attr].add(rel)

    usage_totals: dict[str, int] = defaultdict(int)
    bucket_totals: dict[str, int] = defaultdict(int)
    category_totals: dict[str, int] = defaultdict(int)
    for imp in importers:
        for cls in imp["usage_classes"]:
            usage_totals[cls] += 1
        bucket_totals[imp["ownership_bucket"]] += 1
        for sym in imp["symbols"]:
            category_totals[export_category(sym, export_map)] += 1
        for attr in imp["attribute_uses"]:
            category_totals[export_category(attr, export_map)] += 1

    symbol_meta = {}
    all_symbols = set(symbol_fi) | set(attr_fi)
    for sym in all_symbols:
        files = symbol_fi.get(sym, set()) | attr_fi.get(sym, set())
        ast_fi = len(files)
        bu_sym_fi = caller_fi.get(sym, ast_fi)
        symbol_meta[sym] = {
            "fan_in_ast": ast_fi,
            "fan_in_bu": bu_sym_fi,
            "category": export_category(sym, export_map),
            "authority_class": authority_class(sym, export_map),
            "importers": sorted(files),
            "import_only_fi": len(symbol_fi.get(sym, set())),
            "attribute_only_fi": len(attr_fi.get(sym, set()) - symbol_fi.get(sym, set())),
        }

    prod = [i for i in importers if i["file"].startswith("game/")]
    test_only = [i for i in importers if i["file"].startswith("tests/")]

    subsystem_totals: dict[str, int] = defaultdict(int)
    for imp in importers:
        subsystem_totals[imp["subsystem"]] += 1

    defined = [e for e, v in export_map.items() if v == "defined"]
    reexports = [e for e, v in export_map.items() if v.startswith("re-export")]

    category_bucket_counts: dict[str, int] = defaultdict(int)
    for sym, meta in symbol_meta.items():
        if meta["fan_in_ast"] > 0:
            category_bucket_counts[meta["category"]] += 1

    return {
        "schema_version": 1,
        "cycle": "BV16",
        "target": TARGET,
        "gate_bu_fan_in": bu_fi.get(GATE_TARGET, 0),
        "bu_fan_in": bu_fi.get(TARGET, 0),
        "ast_direct_importers": len(importers),
        "production_importers": len(prod),
        "test_importers": len(test_only),
        "loc": len(TARGET_PATH.read_text(encoding="utf-8-sig").splitlines()),
        "export_count": len(exports),
        "public_export_count": len(public_exports),
        "defined_export_count": len(defined),
        "reexport_count": len(reexports),
        "defined_exports": defined,
        "reexports": reexports,
        "exports": exports,
        "export_map": export_map,
        "public_exports": public_exports,
        "fan_out": sorted(fan_out_modules(TARGET_PATH)),
        "fan_out_count": len(fan_out_modules(TARGET_PATH)),
        "importers": importers,
        "symbol_fi_counts": sorted(
            [(sym, meta["fan_in_ast"], meta["fan_in_bu"], meta["category"], meta["authority_class"]) for sym, meta in symbol_meta.items()],
            key=lambda x: (-x[1], -x[2], x[0]),
        ),
        "symbol_meta": symbol_meta,
        "usage_class_totals": dict(sorted(usage_totals.items(), key=lambda x: -x[1])),
        "ownership_bucket_totals": dict(sorted(bucket_totals.items(), key=lambda x: -x[1])),
        "category_totals": dict(sorted(category_totals.items(), key=lambda x: -x[1])),
        "category_symbol_counts": dict(sorted(category_bucket_counts.items(), key=lambda x: -x[1])),
        "subsystem_totals": dict(sorted(subsystem_totals.items(), key=lambda x: -x[1])),
        "finalize_boundary": finalize_boundary(),
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
    for sym, ast_fi, bu_fi, cat, _auth in analysis["symbol_fi_counts"][:12]:
        print(f"  {sym}: AST={ast_fi} BU={bu_fi} cat={cat}")
    print(f"Gate BU FI={analysis['gate_bu_fan_in']}")
    print(f"Dual importers gate+terminal={analysis['finalize_boundary']['dual_importer_count']}")
    print(f"Wrote {ARTIFACT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
