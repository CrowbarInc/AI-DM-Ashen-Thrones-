#!/usr/bin/env python3
"""BV12 — Smoke bridge domain decomposition discovery (read-only AST scan)."""

from __future__ import annotations

import ast
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv12_smoke_bridge_analysis.json"
BU_CSV = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"

TARGETS = {
    "tests.helpers.replay_smoke_assertions": ROOT / "tests/helpers/replay_smoke_assertions.py",
    "tests.helpers.gate_integration_smoke": ROOT / "tests/helpers/gate_integration_smoke.py",
}

BARREL = "tests.helpers.emission_smoke_assertions"
SCAN_ROOTS = ("game", "tests", "tools", "scripts")

REPLAY_SYMBOLS = frozenset({"final_emission_meta_from_output", "read_turn_debug_notes"})
GATE_SYMBOLS = frozenset({"apply_final_emission_gate_consumer", "gm_response_stub"})


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
        return "production runtime"
    return "other"


def ownership_bucket(rel: str, symbols: list[str], source_module: str) -> str:
    sym_set = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}
    if "ownership" in rel:
        return "ownership-governance"
    if sym_set <= REPLAY_SYMBOLS and sym_set:
        if "read_turn_debug_notes" in sym_set and "final_emission_meta_from_output" not in sym_set:
            return "debug-notes-bridge"
        return "FEM-read-bridge"
    if sym_set <= GATE_SYMBOLS and sym_set:
        if sym_set == {"gm_response_stub"}:
            return "test-fixture-helper"
        return "gate-integration-bridge"
    if sym_set & GATE_SYMBOLS and sym_set & REPLAY_SYMBOLS:
        return "dual-bridge-consumer"
    if source_module == BARREL:
        return "barrel-reexport-consumer"
    return "mixed/downstream-smoke"


def usage_domains(rel: str, symbols: list[str]) -> list[str]:
    """BV12 usage classification buckets."""
    sym_set = {s.split(" as ")[0].split(" (")[0].strip() for s in symbols}
    name = rel.rsplit("/", 1)[-1].replace(".py", "")
    domains: set[str] = set()

    if sym_set & {"final_emission_meta_from_output", "read_turn_debug_notes"}:
        if "golden_replay" in name or "replay" in rel and "projection" in name:
            domains.add("replay projection")
        elif "transcript" in name or "gauntlet" in name:
            domains.add("replay acceptance")
        elif "dead_turn" in name or "telemetry" in name or "observational" in name:
            domains.add("observability testing")
        elif "ownership" in name:
            domains.add("ownership testing")
        else:
            domains.add("replay acceptance")

    if sym_set & {"apply_final_emission_gate_consumer"}:
        if "fallback" in name or "diegetic" in rel:
            domains.add("fallback testing")
        elif "gate" in name or "final_emission" in name or "boundary" in name:
            domains.add("gate validation")
        else:
            domains.add("gate orchestration")

    if sym_set & {"gm_response_stub"}:
        domains.add("gate orchestration")

    if not domains:
        domains.add("gate orchestration" if "gate" in sym_set else "replay acceptance")
    return sorted(domains)


def public_exports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    public: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            public.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    public.add(target.id)
    return public


def parse_target_imports(path: Path, target_module: str) -> list[str]:
    src = path.read_text(encoding="utf-8-sig")
    syms: list[str] = []
    short = target_module.rsplit(".", 1)[-1]
    try:
        tree = ast.parse(src)
    except SyntaxError:
        tree = None
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == target_module:
                    for alias in node.names:
                        if alias.name != "*":
                            syms.append(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == target_module:
                        syms.append(f"{alias.asname or short} (module)")
    pattern = rf"from {re.escape(target_module)} import ([^\n]+)"
    for block in re.findall(pattern, src):
        for part in block.replace("(", "").replace(")", "").split(","):
            part = part.strip().split("#")[0].strip()
            if part:
                syms.append(part.split(" as ")[0].strip())
    if re.search(rf"from tests\.helpers import {short}\b", src):
        syms.append(f"{short} (module)")
    return sorted(set(syms))


def parse_barrel_bridge_symbols(path: Path) -> dict[str, list[str]]:
    """Symbols imported from targets via emission_smoke_assertions barrel."""
    src = path.read_text(encoding="utf-8-sig")
    found: dict[str, list[str]] = defaultdict(list)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return found
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != BARREL:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            name = alias.asname or alias.name
            if name in REPLAY_SYMBOLS:
                found["tests.helpers.replay_smoke_assertions"].append(name)
            elif name in GATE_SYMBOLS:
                found["tests.helpers.gate_integration_smoke"].append(name)
    for block in re.findall(rf"from {re.escape(BARREL)} import ([^\n]+)", src):
        for part in block.replace("(", "").replace(")", "").split(","):
            part = part.strip().split("#")[0].strip().split(" as ")[0].strip()
            if part in REPLAY_SYMBOLS:
                found["tests.helpers.replay_smoke_assertions"].append(part)
            elif part in GATE_SYMBOLS:
                found["tests.helpers.gate_integration_smoke"].append(part)
    return {k: sorted(set(v)) for k, v in found.items()}


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
    exports_by_module = {mod: public_exports(path) for mod, path in TARGETS.items()}

    importers_by_module: dict[str, list[dict[str, Any]]] = {mod: [] for mod in TARGETS}
    symbol_fi: dict[str, dict[str, set[str]]] = {
        mod: defaultdict(set) for mod in TARGETS
    }
    barrel_consumers: dict[str, list[dict[str, Any]]] = {mod: [] for mod in TARGETS}

    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(".") or "/__pycache__/" in rel:
            continue
        if not rel.startswith(SCAN_ROOTS):
            continue
        if rel in {p.relative_to(ROOT).as_posix() for p in TARGETS.values()}:
            continue

        for target_mod, target_path in TARGETS.items():
            if path == target_path:
                continue
            direct = parse_target_imports(path, target_mod)
            if direct:
                record = {
                    "file": rel,
                    "subsystem": subsystem(rel),
                    "symbols": direct,
                    "ownership_bucket": ownership_bucket(rel, direct, target_mod),
                    "usage_domains": usage_domains(rel, direct),
                    "import_path": "direct",
                }
                importers_by_module[target_mod].append(record)
                for sym in direct:
                    clean = sym.split(" as ")[0].split(" (")[0].strip()
                    if clean and not clean.endswith("(module)"):
                        symbol_fi[target_mod][clean].add(rel)

        barrel = parse_barrel_bridge_symbols(path)
        for target_mod, syms in barrel.items():
            if not syms:
                continue
            barrel_consumers[target_mod].append(
                {
                    "file": rel,
                    "subsystem": subsystem(rel),
                    "symbols": syms,
                    "ownership_bucket": "barrel-reexport-consumer",
                    "usage_domains": usage_domains(rel, syms),
                    "import_path": "barrel",
                }
            )
            for sym in syms:
                symbol_fi[target_mod][sym].add(f"{rel} (via barrel)")

    combined_symbol_fi: dict[str, int] = {}
    for mod in TARGETS:
        for sym, files in symbol_fi[mod].items():
            combined_symbol_fi[f"{mod}::{sym}"] = len(files)

    usage_totals: dict[str, int] = defaultdict(int)
    for mod in TARGETS:
        for imp in importers_by_module[mod] + barrel_consumers[mod]:
            for domain in imp["usage_domains"]:
                usage_totals[domain] += 1

    gate_to_replay = {
        "gate_integration_smoke imports replay_smoke_assertions": True,
        "coupling_symbol": "final_emission_meta_from_output",
    }

    return {
        "schema_version": 1,
        "cycle": "BV12",
        "targets": list(TARGETS.keys()),
        "bu_fan_in": {mod: bu_fi.get(mod, 0) for mod in TARGETS},
        "combined_fan_in": sum(bu_fi.get(mod, 0) for mod in TARGETS),
        "exports_by_module": {mod: sorted(exports) for mod, exports in exports_by_module.items()},
        "fan_out_by_module": {
            mod: sorted(fan_out_modules(path)) for mod, path in TARGETS.items()
        },
        "loc_by_module": {
            mod: len(path.read_text(encoding="utf-8-sig").splitlines())
            for mod, path in TARGETS.items()
        },
        "direct_importers": importers_by_module,
        "barrel_importers": barrel_consumers,
        "symbol_fi": {
            mod: {sym: sorted(files) for sym, files in sorted(items.items(), key=lambda x: -len(x[1]))}
            for mod, items in symbol_fi.items()
        },
        "symbol_fi_counts": {
            mod: sorted(
                [(sym, len(files)) for sym, files in items.items()],
                key=lambda x: -x[1],
            )
            for mod, items in symbol_fi.items()
        },
        "usage_domain_totals": dict(sorted(usage_totals.items(), key=lambda x: -x[1])),
        "gate_replay_coupling": gate_to_replay,
        "emission_smoke_barrel_fi": bu_fi.get(BARREL, 0),
    }


def main() -> int:
    analysis = build_analysis()
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(analysis, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    for mod, fi in analysis["bu_fan_in"].items():
        direct = len(analysis["direct_importers"][mod])
        barrel = len(analysis["barrel_importers"][mod])
        print(f"{mod}: BU FI={fi} direct={direct} barrel={barrel}")
    print(f"Combined BU FI={analysis['combined_fan_in']}")
    print(f"Wrote {ARTIFACT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
