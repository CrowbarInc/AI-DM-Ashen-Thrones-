#!/usr/bin/env python3
"""BV13 — final_emission_text decomposition discovery (read-only AST scan)."""

from __future__ import annotations

import ast
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv13_final_emission_text_analysis.json"
BU_CSV = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"
TARGET = "game.final_emission_text"
TARGET_PATH = ROOT / "game" / "final_emission_text.py"
SCAN_ROOTS = ("game", "tests", "tools", "scripts")


def subsystem(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    if rel.startswith("tools/"):
        return "tools/analysis"
    if rel.startswith("scripts/"):
        return "scripts/analysis"
    if rel.startswith("tests/helpers/"):
        if "replay" in name or "transcript" in name or "golden" in name:
            return "replay helpers"
        if "fallback" in name or "opening" in name:
            return "fallback helpers"
        if "strict_social" in name or "speaker" in name:
            return "speaker helpers"
        if "gate" in name:
            return "gate helpers"
        return "test helpers"
    if rel.startswith("tests/"):
        if "fallback" in name or "opening" in name or "diegetic" in name:
            return "fallback"
        if "replay" in name or "golden" in name:
            return "replay"
        if "speaker" in name:
            return "speaker/social"
        if "ownership" in name:
            return "ownership governance"
        if "observational" in name or "telemetry" in name or "dead_turn" in name:
            return "observability/diagnostics"
        if "boundary" in name or "gate" in name or "final_emission" in name:
            return "final emission gate"
        if "pipeline" in name or "turn_packet" in name or "api_" in name:
            return "HTTP/pipeline integration"
        if name.startswith("bv"):
            return "BV audit suites"
        return "integration/regression"
    if rel.startswith("game/"):
        if "final_emission_gate" in name:
            return "final emission gate"
        if "final_emission" in name:
            return "final emission pipeline"
        if "fallback" in name:
            return "fallback"
        if any(token in name for token in ("narrative", "dialogue", "speaker", "interaction")):
            return "narrative/social"
        return "production runtime"
    return "other"


def ownership_bucket(rel: str, symbols: list[str]) -> str:
    sym = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}
    if any(token in rel for token in ("ownership", "gate_thin_boundary", "gate_delegator")):
        return "ownership-governance"
    if sym <= {"_normalize_text"}:
        return "normalize-primitive"
    if sym <= {"_normalize_text", "_normalize_text_preserve_paragraphs"}:
        return "normalize-primitive"
    if "_RESPONSE_TYPE_VALUES" in sym and len(sym) <= 2:
        return "policy-constant"
    if any(s.startswith("_ANSWER_") or s.startswith("_ACTION_") or s.startswith("_AGENCY_") for s in sym):
        return "validator-pattern"
    if "_global_narrative_fallback_stock_line" in sym:
        return "fallback-content-bridge"
    if any(
        s in sym
        for s in ("_decompress_overpacked_sentences", "_repair_fragmentary_participial_splits")
    ):
        return "legacy-semantic-repair"
    if "_sanitize_output_text" in sym:
        return "formatting-sanitize"
    if "_normalize_terminal_punctuation" in sym or "_capitalize_sentence_fragment" in sym:
        return "formatting-punctuation"
    return "mixed-text-utility"


def usage_classes(rel: str, symbols: list[str]) -> list[str]:
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    classes: set[str] = set()
    if rel.startswith("tests/"):
        classes.add("tests")
        if "replay" in name or "golden" in name:
            classes.add("replay")
        if "gate" in name or "final_emission" in name or "boundary" in name:
            classes.add("gate")
        if "ownership" in name:
            classes.add("ownership")
        if any(token in name for token in ("observational", "telemetry", "dead_turn")):
            classes.add("observability")
        if "diagnostic" in name:
            classes.add("diagnostics")
    if rel.startswith("game/"):
        if "finalize" in name:
            classes.add("finalization")
        if "gate" in name:
            classes.add("gate")
        if "fallback" in name or "provenance" in name:
            classes.add("diagnostics")
        if "replay" in name:
            classes.add("replay")
        if not classes:
            classes.add("gate" if "final_emission" in name else "finalization")
    return sorted(classes or ["other"])


def symbol_category(sym: str) -> str:
    if sym.endswith("(module)"):
        return "module-import"
    if sym in {
        "_normalize_text",
        "_normalize_text_preserve_paragraphs",
        "_sanitize_output_text",
        "_normalize_terminal_punctuation",
        "_capitalize_sentence_fragment",
        "_has_terminal_punctuation",
    }:
        return "formatting"
    if sym == "_RESPONSE_TYPE_VALUES" or sym.startswith("_ANSWER_") or sym.startswith("_ACTION_"):
        return "policy"
    if sym == "_global_narrative_fallback_stock_line":
        return "orchestration"
    if sym in ("_decompress_overpacked_sentences", "_repair_fragmentary_participial_splits"):
        return "legacy-repair"
    return "other"


def authority_class(sym: str) -> str:
    if sym in {
        "_normalize_text",
        "_normalize_text_preserve_paragraphs",
        "_sanitize_output_text",
        "_normalize_terminal_punctuation",
        "_capitalize_sentence_fragment",
        "_has_terminal_punctuation",
    }:
        return "formatting-helper"
    if sym in {
        "_RESPONSE_TYPE_VALUES",
        "_ANSWER_DIRECT_PATTERNS",
        "_ANSWER_FILLER_PATTERNS",
        "_ACTION_RESULT_PATTERNS",
        "_AGENCY_SUBSTITUTE_PATTERNS",
        "_ACTION_STOPWORDS",
    }:
        return "policy-constant"
    if sym == "_global_narrative_fallback_stock_line":
        return "convenience-wrapper"
    if sym in ("_decompress_overpacked_sentences", "_repair_fragmentary_participial_splits"):
        return "accidental-bridge"
    return "projection-helper"


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


def build_analysis() -> dict[str, Any]:
    bu_fi = load_bu_fi()
    exports = module_exports(TARGET_PATH)
    importers: list[dict[str, Any]] = []
    symbol_fi: dict[str, set[str]] = defaultdict(set)

    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/__pycache__/" in rel or rel == "game/final_emission_text.py":
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
    for imp in importers:
        for cls in imp["usage_classes"]:
            usage_totals[cls] += 1
        bucket_totals[imp["ownership_bucket"]] += 1

    symbol_meta = {}
    for sym, files in symbol_fi.items():
        symbol_meta[sym] = {
            "fan_in": len(files),
            "category": symbol_category(sym),
            "authority_class": authority_class(sym),
            "importers": sorted(files),
        }

    prod = [i for i in importers if i["file"].startswith("game/")]
    test_only = [i for i in importers if i["file"].startswith("tests/")]

    return {
        "schema_version": 1,
        "cycle": "BV13",
        "target": TARGET,
        "bu_fan_in": bu_fi.get(TARGET, 0),
        "ast_direct_importers": len(importers),
        "production_importers": len(prod),
        "test_importers": len(test_only),
        "loc": len(TARGET_PATH.read_text(encoding="utf-8-sig").splitlines()),
        "export_count": len(exports),
        "exports": exports,
        "fan_out": sorted(fan_out_modules(TARGET_PATH)),
        "importers": importers,
        "symbol_fi_counts": sorted(
            [(sym, len(files)) for sym, files in symbol_fi.items()],
            key=lambda x: -x[1],
        ),
        "symbol_meta": symbol_meta,
        "usage_class_totals": dict(sorted(usage_totals.items(), key=lambda x: -x[1])),
        "ownership_bucket_totals": dict(sorted(bucket_totals.items(), key=lambda x: -x[1])),
    }


def main() -> int:
    analysis = build_analysis()
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(analysis, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(
        f"{TARGET}: BU FI={analysis['bu_fan_in']} "
        f"AST={analysis['ast_direct_importers']} "
        f"prod={analysis['production_importers']} test={analysis['test_importers']}"
    )
    for sym, count in analysis["symbol_fi_counts"][:12]:
        print(f"  {sym}: {count}")
    print(f"Wrote {ARTIFACT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
