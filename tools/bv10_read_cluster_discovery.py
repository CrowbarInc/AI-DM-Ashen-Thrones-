"""BV10 read-side attribution cluster dependency discovery (analysis only)."""
from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "game.final_emission_meta_read": "final_emission_meta_read",
    "game.final_emission_owner_bucket_views": "owner_bucket_views",
    "game.final_emission_ownership_schema": "ownership_schema",
}

BUCKET_PATTERNS = re.compile(r"(OPENING|SEALED|VISIBILITY)_FALLBACK_OWNER|OWNER_BUCKET")


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def file_kind(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("tests/helpers/"):
        return "helper"
    if rel.startswith("tests/"):
        return "test"
    if rel.startswith(("tools/", "scripts/")):
        return "tool"
    return "production"


def subsystem(module: str, path: Path) -> str:
    rel = path.as_posix()
    name = module.rsplit(".", 1)[-1]
    if "replay" in rel or "golden_replay" in name:
        return "replay"
    if "failure_class" in rel or "attribution" in rel or "failure_classifier" in rel:
        return "attribution"
    if "fallback" in rel or "gm_retry" in rel:
        return "fallback"
    if any(
        token in rel
        for token in (
            "dead_turn",
            "playability",
            "observational",
            "stage_diff",
            "narrative_authenticity_eval",
            "run_scenario_spine",
        )
    ):
        return "diagnostics"
    if "speaker" in rel:
        return "speaker"
    if "smoke" in rel or name.startswith("test_"):
        return "tests"
    if any(token in rel for token in ("telemetry", "lineage", "observability")):
        return "observability"
    if rel.startswith("game/final_emission_replay_projection"):
        return "replay"
    if rel.startswith(("game/final_emission_visibility", "game/final_emission_sealed")):
        return "fallback"
    if rel.startswith("game/post_emission_speaker"):
        return "speaker"
    if rel.startswith("game/"):
        return "final emission"
    if rel.startswith("tests/"):
        return "tests"
    return "other"


def ownership_bucket(symbols: list[str], target_key: str) -> str:
    syms = set(symbols)
    if any("owner_bucket" in symbol for symbol in syms):
        return "owner-bucket-projection"
    if any(BUCKET_PATTERNS.search(symbol) for symbol in syms):
        return "schema-vocabulary"
    if syms & {
        "read_final_emission_meta_dict",
        "read_final_emission_meta_from_turn_payload",
        "FINAL_EMISSION_META_KEY",
    }:
        return "read-side-access"
    if syms & {
        "normalized_observational_telemetry_bundle",
        "assemble_unified_observational_telemetry_bundle",
        "classify_dead_turn",
        "summarize_gameplay_validation_for_turn",
        "stage_diff_narrative_authenticity_projection",
        "normalize_final_emission_meta_for_observability",
        "build_fem_observability_events",
    }:
        return "observability-projection"
    if any(
        token in symbol
        for symbol in syms
        for token in ("PRODUCER", "SANITIZER", "LINEAGE", "AUTHORSHIP")
    ):
        return "attribution-vocabulary"
    if any("default_response_type" in symbol or "NARRATIVE_AUTHENTICITY" in symbol for symbol in syms):
        return "layer-projection"
    if target_key == "ownership_schema":
        return "schema-vocabulary"
    if target_key == "owner_bucket_views":
        return "owner-bucket-projection"
    return "read-side-access"


def read_freq(tree: ast.AST, symbols: set[str]) -> str:
    bindings: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bindings[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name != "*":
                    bindings[alias.asname or alias.name] = alias.name
    counts: dict[str, int] = defaultdict(int)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name: str | None = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            name = func.attr
        if name and name in bindings and bindings[name] in symbols:
            counts[bindings[name]] += 1
        elif isinstance(func, ast.Name) and func.id in symbols:
            counts[func.id] += 1
        elif isinstance(func, ast.Attribute) and func.attr in symbols:
            counts[func.attr] += 1
    total = sum(counts.values())
    if total >= 5:
        return "High"
    if total >= 2:
        return "Medium"
    if total >= 1:
        return "Low"
    return "Import-only"


def main() -> None:
    paths = sorted(
        path
        for root in ("game", "tests", "tools", "scripts")
        for path in (ROOT / root).rglob("*.py")
        if path.is_file()
    )
    modules = {module_name(path): path for path in paths}
    trees: dict[str, ast.AST] = {}
    for module, path in modules.items():
        trees[module] = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

    inventory: dict[str, list[dict[str, object]]] = {target: [] for target in TARGETS}
    for importer, tree in trees.items():
        if importer in TARGETS:
            continue
        path = modules[importer]
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            matched: str | None = None
            candidate = node.module
            while candidate:
                if candidate in TARGETS:
                    matched = candidate
                    break
                candidate = candidate.rpartition(".")[0]
            if not matched:
                continue
            symbols = [alias.name for alias in node.names if alias.name != "*"]
            if not symbols and node.names:
                symbols = ["module"]
            inventory[matched].append(
                {
                    "file": path.as_posix(),
                    "module": importer,
                    "subsystem": subsystem(importer, path),
                    "kind": file_kind(path),
                    "symbols": sorted(set(symbols)),
                    "read_frequency": read_freq(tree, set(symbols)),
                    "ownership_bucket": ownership_bucket(symbols, TARGETS[matched]),
                }
            )

    for target, rows in inventory.items():
        merged: dict[str, dict[str, object]] = {}
        for row in rows:
            key = str(row["file"])
            if key not in merged:
                merged[key] = row
            else:
                merged[key]["symbols"] = sorted(
                    set(merged[key]["symbols"]) | set(row["symbols"])  # type: ignore[arg-type]
                )
        inventory[target] = sorted(merged.values(), key=lambda item: str(item["file"]))

    output = ROOT / "artifacts" / "bv10_dependency_inventory.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    for target, rows in inventory.items():
        print(f"{target}: {len(rows)} importers")


if __name__ == "__main__":
    main()
