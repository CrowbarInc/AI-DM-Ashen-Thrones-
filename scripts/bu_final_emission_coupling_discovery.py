"""Generate BU final-emission coupling discovery CSVs.

This script is intentionally read-only with respect to runtime code. It parses project
Python files with ``ast`` and writes audit data under ``docs/audits``.
"""
from __future__ import annotations

import ast
import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "audits"
PYTHON_ROOTS = ("game", "tests", "scripts")

ADJACENT_GAME_MODULES = {
    "game.dialogue_social_plan",
    "game.diegetic_fallback_narration",
    "game.emitted_speaker_signature",
    "game.fallback_behavior",
    "game.fallback_provenance_debug",
    "game.opening_deterministic_fallback",
    "game.opening_scene_realization",
    "game.output_sanitizer",
    "game.post_emission_speaker_adoption",
    "game.realization_authority",
    "game.realization_provenance",
    "game.runtime_lineage_telemetry",
    "game.social_exchange_emission",
    "game.speaker_contract_enforcement",
}

CORE_TEST_MODULES = {
    "tests.failure_classification_contract",
    "tests.replay_governance_contract",
    "tests.replay_governance_registry",
    "tests.replay_governance_traceability_contract",
    "tests.helpers.attribution_completeness_metric",
    "tests.helpers.attribution_contract",
    "tests.helpers.emission_smoke_assertions",
    "tests.helpers.gate_integration_smoke",
    "tests.helpers.gate_orchestration_smoke",
    "tests.helpers.replay_smoke_assertions",
    "tests.helpers.replay_fem_read_smoke",
    "tests.helpers.fallback_bridge_smoke",
    "tests.helpers.failure_classifier",
    "tests.helpers.gate_equivalence_monkeypatch",
    "tests.helpers.gate_delegator_governance",
    "tests.helpers.gate_thin_boundary_locks",
    "tests.helpers.golden_replay",
    "tests.helpers.golden_replay_projection",
    "tests.helpers.opening_fallback_evidence",
    "tests.helpers.opening_fallback_gate_harness",
    "tests.helpers.post_speaker_finalize_probe",
    "tests.helpers.replacement_attribution_inventory",
    "tests.helpers.replay_drift_taxonomy",
    "tests.helpers.strict_social_harness",
}

BJ_ADDED_MODULES = {
    "game.final_emission_acceptance_quality",
    "game.final_emission_answer_shape_primacy",
    "game.final_emission_anti_railroading",
    "game.final_emission_context_separation",
    "game.final_emission_fast_fallback_composition",
    "game.final_emission_fem_assembly",
    "game.final_emission_finalize",
    "game.final_emission_first_mention_composition",
    "game.final_emission_gate_context",
    "game.final_emission_generic_exit",
    "game.final_emission_narrative_authority",
    "game.final_emission_narrative_mode_output",
    "game.final_emission_non_strict_stack",
    "game.final_emission_opening_mode",
    "game.final_emission_passive_scene_pressure",
    "game.final_emission_player_facing_narration_purity",
    "game.final_emission_referential_clarity",
    "game.final_emission_response_type",
    "game.final_emission_scene_emit_integrity",
    "game.final_emission_scene_facts",
    "game.final_emission_scene_state_anchor",
    "game.final_emission_strict_social_stack",
    "game.final_emission_terminal_pipeline",
    "game.final_emission_tone_escalation",
}

OWNERSHIP_PATTERNS = {
    "ownership_registry": re.compile(r"ownership[_ ]registry", re.I),
    "owner_bucket": re.compile(r"owner[_ ]bucket", re.I),
    "final_emission_ownership": re.compile(r"final[_ -]emission.{0,40}owner|owner.{0,40}final[_ -]emission", re.I),
    "gate_ownership": re.compile(r"gate.{0,40}owner|owner.{0,40}gate", re.I),
    "replay_ownership": re.compile(r"replay.{0,40}owner|owner.{0,40}replay", re.I),
    "fallback_ownership": re.compile(r"fallback.{0,40}owner|owner.{0,40}fallback", re.I),
    "speaker_ownership": re.compile(r"speaker.{0,40}owner|owner.{0,40}speaker", re.I),
    "semantic_replacement_attribution": re.compile(r"semantic[_ -]replacement|replacement[_ -]attribution", re.I),
}


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def file_kind(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("tests/helpers/"):
        return "helper"
    if rel.startswith("tests/"):
        return "test"
    if rel.startswith("scripts/"):
        return "script"
    return "production"


def responsibility(module: str) -> str:
    name = module.rsplit(".", 1)[-1]
    if "ownership" in name or "governance" in name:
        return "ownership enforcement"
    if "golden_replay" in name or "replay_projection" in name or "replay_drift" in name:
        return "replay projection/governance"
    if "speaker" in name:
        return "speaker finalization"
    if "fallback" in name:
        return "fallback selection/projection"
    if "attribution" in name or "lineage" in name or "realization" in name:
        return "semantic replacement attribution"
    if name == "final_emission_gate" or "gate_" in name:
        return "gate orchestration/preflight"
    if "finalize" in name or "terminal_pipeline" in name or "generic_exit" in name:
        return "finalization/exit"
    if name.startswith("final_emission_"):
        return "final-emission policy/metadata"
    if name == "output_sanitizer":
        return "sanitizer boundary"
    if name in {"social_exchange_emission", "dialogue_social_plan"}:
        return "strict-social composition"
    return "supporting contract/test"


def imported_modules(tree: ast.AST, known: set[str]) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for imported in names:
            candidate = imported
            while candidate:
                if candidate in known:
                    found.add(candidate)
                    break
                candidate = candidate.rpartition(".")[0]
    return found


def import_bindings(tree: ast.AST) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bindings[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name != "*":
                    bindings[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return bindings


def call_target(node: ast.Call, bindings: dict[str, str]) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return bindings.get(func.id)
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        base = bindings.get(func.value.id)
        if base:
            return f"{base}.{func.attr}"
    return None


def is_ecosystem_module(module: str, imports: set[str]) -> bool:
    leaf = module.rsplit(".", 1)[-1]
    if module.startswith("game.final_emission_") or module in ADJACENT_GAME_MODULES:
        return True
    if module in CORE_TEST_MODULES:
        return True
    if module.startswith("tests.") and (
        leaf.startswith("test_final_emission_")
        or "golden_replay" in leaf
        or "fallback" in leaf
        or "speaker" in leaf
        or "ownership" in leaf
        or "attribution" in leaf
    ):
        return True
    return bool(module.startswith(("tests.", "scripts.")) and imports & (ADJACENT_GAME_MODULES | {"game.final_emission_gate"}))


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    paths = sorted(path for root in PYTHON_ROOTS for path in (ROOT / root).rglob("*.py"))
    modules = {module_name(path): path for path in paths}
    trees: dict[str, ast.AST] = {}
    texts: dict[str, str] = {}
    for module, path in modules.items():
        text = path.read_text(encoding="utf-8-sig")
        texts[module] = text
        trees[module] = ast.parse(text, filename=str(path))

    imports = {module: imported_modules(tree, set(modules)) for module, tree in trees.items()}
    ecosystem = {
        module for module in modules if is_ecosystem_module(module, imports[module])
    }

    importer_map: dict[str, set[str]] = defaultdict(set)
    for importer, targets in imports.items():
        for target in targets:
            importer_map[target].add(importer)

    import_rows: list[dict[str, object]] = []
    for module in sorted(ecosystem):
        inbound = importer_map[module]
        outbound = imports[module]
        by_kind = {kind: sum(file_kind(modules[item]) == kind for item in inbound) for kind in ("production", "test", "helper", "script")}
        out_by_kind = {kind: sum(file_kind(modules[item]) == kind for item in outbound) for kind in ("production", "test", "helper", "script")}
        import_rows.append(
            {
                "module": module,
                "file": modules[module].relative_to(ROOT).as_posix(),
                "kind": file_kind(modules[module]),
                "responsibility": responsibility(module),
                "bj_added": module in BJ_ADDED_MODULES,
                "fan_in_total": len(inbound),
                "fan_in_production": by_kind["production"],
                "fan_in_tests": by_kind["test"],
                "fan_in_helpers": by_kind["helper"],
                "fan_in_scripts": by_kind["script"],
                "fan_out_total": len(outbound),
                "fan_out_production": out_by_kind["production"],
                "fan_out_tests": out_by_kind["test"],
                "fan_out_helpers": out_by_kind["helper"],
                "fan_out_scripts": out_by_kind["script"],
                "importer_files": ";".join(sorted(modules[item].relative_to(ROOT).as_posix() for item in inbound)),
                "imported_modules": ";".join(sorted(outbound)),
            }
        )
    write_csv("BU_import_fan_in_fan_out.csv", list(import_rows[0]), import_rows)

    definitions: dict[str, tuple[str, str]] = {}
    for module in ecosystem:
        for node in getattr(trees[module], "body", []):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                definitions[f"{module}.{node.name}"] = (module, type(node).__name__)

    callers: dict[str, set[str]] = defaultdict(set)
    for caller, tree in trees.items():
        bindings = import_bindings(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                target = call_target(node, bindings)
                if target in definitions:
                    callers[target].add(caller)

    caller_rows: list[dict[str, object]] = []
    for target, caller_modules in sorted(callers.items(), key=lambda item: (-len(item[1]), item[0])):
        owner, definition_kind = definitions[target]
        counts = {kind: sum(file_kind(modules[item]) == kind for item in caller_modules) for kind in ("production", "test", "helper", "script")}
        caller_rows.append(
            {
                "api": target,
                "definition_file": modules[owner].relative_to(ROOT).as_posix(),
                "definition_kind": definition_kind,
                "responsibility": responsibility(owner),
                "bj_added_owner": owner in BJ_ADDED_MODULES,
                "caller_file_count": len(caller_modules),
                "production_callers": counts["production"],
                "test_callers": counts["test"],
                "helper_callers": counts["helper"],
                "script_callers": counts["script"],
                "caller_files": ";".join(sorted(modules[item].relative_to(ROOT).as_posix() for item in caller_modules)),
            }
        )
    write_csv("BU_caller_fan_in.csv", list(caller_rows[0]), caller_rows)

    ownership_rows: list[dict[str, object]] = []
    for module, text in texts.items():
        matches = {name: len(pattern.findall(text)) for name, pattern in OWNERSHIP_PATTERNS.items()}
        total = sum(matches.values())
        if not total:
            continue
        ownership_rows.append(
            {
                "module": module,
                "file": modules[module].relative_to(ROOT).as_posix(),
                "kind": file_kind(modules[module]),
                "ecosystem_module": module in ecosystem,
                "responsibility": responsibility(module),
                "ownership_reference_count": total,
                **matches,
            }
        )
    ownership_rows.sort(key=lambda row: (-int(row["ownership_reference_count"]), str(row["module"])))
    write_csv("BU_ownership_dependency_map.csv", list(ownership_rows[0]), ownership_rows)

    print(f"Parsed {len(paths)} Python files; ecosystem={len(ecosystem)} modules")
    print(f"Import rows={len(import_rows)}; caller APIs={len(caller_rows)}; ownership rows={len(ownership_rows)}")


if __name__ == "__main__":
    main()
