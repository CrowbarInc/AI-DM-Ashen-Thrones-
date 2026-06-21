"""BV7 read-only discovery: emission_smoke_assertions dependency inventory."""
from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = ROOT / "tests/helpers/emission_smoke_assertions.py"
ARTIFACT = ROOT / "artifacts/bv7_smoke_analysis.json"


def subsystem(path: Path) -> str:
    rel = path.as_posix()
    name = path.stem
    if rel.startswith("tools/"):
        return "tools/analysis"
    if rel.startswith("tests/helpers/"):
        if "replay" in name or "transcript" in name or "golden" in name:
            return "replay helpers"
        if "fallback" in name or "opening" in name:
            return "fallback helpers"
        if "strict_social" in name or "speaker" in name:
            return "speaker helpers"
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


def ownership_bucket(path: Path, symbols: list[str]) -> str:
    rel = path.as_posix()
    sym_set = set(symbols)
    if "ownership" in rel:
        return "ownership-governance"
    if any("fallback" in s or "opening" in s for s in sym_set) or "fallback" in rel:
        if sym_set & {"response_type_contract", "final_emission_meta_from_output"}:
            return "fallback-projection"
        return "fallback-assertions"
    if sym_set & {
        "assert_social_grounding_smoke",
        "assert_dialogue_lock_social_route_smoke",
        "assert_dialogue_lock_non_dialogue_route_smoke",
        "assert_open_social_solicitation_route",
        "assert_broadcast_open_call_rejected_smoke",
        "assert_open_call_crowd_reaction_wiring_smoke",
        "assert_open_call_no_unresolved_retry_smoke",
    }:
        return "speaker/social-smoke"
    if any("route" in s for s in sym_set):
        return "route-wiring-smoke"
    if sym_set & {
        "response_type_contract",
        "assert_response_type_meta",
        "assert_response_type_contract_surfaces",
        "validate_answer_completeness",
        "apply_answer_completeness_layer",
        "apply_response_delta_layer",
        "enforce_response_type_contract_layer",
        "assert_response_delta_boundary_validate_only",
        "assert_no_boundary_reorder_repair",
    }:
        return "consumer-layer-bridge"
    if sym_set & {"final_emission_meta_from_output", "read_turn_debug_notes"}:
        return "FEM-read-bridge"
    if any(s.startswith("assert_") and "smoke" in s for s in sym_set):
        return "hygiene-smoke"
    if "apply_final_emission_gate_consumer" in sym_set:
        return "gate-integration-bridge"
    if "gm_response_stub" in sym_set:
        return "test-fixture-helper"
    return "mixed/downstream-smoke"


def usage_class(symbols: list[str]) -> list[str]:
    classes: set[str] = set()
    for raw in symbols:
        s = raw.split(" as ")[0].split(" (")[0].strip()
        if s.startswith("*"):
            classes.add("test helpers")
            continue
        sl = s.lower()
        if s in ("final_emission_meta_from_output", "read_turn_debug_notes"):
            classes.add("replay assertions")
        elif "fallback" in sl or s in (
            "assert_no_uncertainty_fallback_stock_smoke",
            "has_non_accept_final_route_smoke",
        ):
            classes.add("fallback assertions")
        elif "owner" in sl or s == "assert_emission_repair_evidence":
            classes.add("ownership assertions")
        elif "social_grounding" in sl or "dialogue_lock" in sl:
            classes.add("speaker assertions")
        elif any(x in sl for x in ("open_call", "open_social", "broadcast", "broad_address")):
            classes.add("attribution assertions")
        elif any(
            x in sl
            for x in (
                "response_type",
                "answer_completeness",
                "response_delta",
                "boundary",
                "continuity_validation",
            )
        ):
            classes.add("observability assertions")
        elif s in (
            "apply_final_emission_gate_consumer",
            "validate_answer_completeness",
            "apply_answer_completeness_layer",
            "apply_response_delta_layer",
            "enforce_response_type_contract_layer",
            "skip_answer_completeness_layer",
            "skip_response_delta_layer",
            "strict_social_answer_pressure_rd_contract_active",
            "validate_response_delta",
            "inspect_response_delta_failure",
            "response_type_contract",
            "gm_response_stub",
        ):
            classes.add("test helpers")
        elif s.startswith("assert_") or s.startswith("SMOKE_"):
            if "route" in sl or "final_route" in sl:
                classes.add("replay assertions")
            elif any(
                x in sl
                for x in (
                    "procedural",
                    "validator",
                    "scaffold",
                    "advisory",
                    "stock",
                    "coaching",
                    "filler",
                    "player_text",
                    "http_chat",
                    "visibility",
                )
            ):
                classes.add("fallback assertions")
            else:
                classes.add("observability assertions")
        else:
            classes.add("test helpers")
    return sorted(classes)


def parse_imports(path: Path) -> list[str]:
    src = path.read_text(encoding="utf-8")
    syms: list[str] = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        tree = None
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod in ("tests.helpers.emission_smoke_assertions",):
                    for alias in node.names:
                        if alias.name != "*":
                            syms.append(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "tests.helpers.emission_smoke_assertions":
                        syms.append(f"{alias.asname or alias.name} (module)")
    for block in re.findall(
        r"from tests\.helpers\.emission_smoke_assertions import ([^\n]+)", src
    ):
        for part in block.replace("(", "").replace(")", "").split(","):
            part = part.strip().split("#")[0].strip()
            if part:
                syms.append(part.split(" as ")[0].strip())
    if re.search(r"from tests\.helpers import emission_smoke_assertions", src):
        syms.append("emission_smoke_assertions (module)")
    return sorted(set(syms))


def main() -> None:
    facade_src = TARGET_FILE.read_text(encoding="utf-8")
    facade_tree = ast.parse(facade_src)
    public: set[str] = set()
    for node in facade_tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                public.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    public.add(t.id)

    importers: list[dict] = []
    symbol_fi: dict[str, set[str]] = defaultdict(set)

    scan_roots = ("game", "tests", "tools", "scripts")
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "tests/helpers/emission_smoke_assertions.py":
            continue
        if not rel.startswith(scan_roots):
            continue
        syms = parse_imports(path)
        if not syms:
            continue
        for s in syms:
            clean = s.split(" as ")[0].split(" (")[0].strip()
            if clean and not clean.startswith("emission_smoke_assertions"):
                symbol_fi[clean].add(rel)
        importers.append(
            {
                "file": rel,
                "subsystem": subsystem(path),
                "symbols": syms,
                "ownership_bucket": ownership_bucket(path, syms),
                "usage_classes": usage_class(syms),
            }
        )

    fo_modules: set[str] = set()
    for node in ast.walk(facade_tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            fo_modules.add(node.module)
    for node in facade_tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(node):
                if isinstance(n, ast.ImportFrom) and n.module:
                    fo_modules.add(n.module)

    families = {
        "FEM/read bridge": ["final_emission_meta_from_output", "read_turn_debug_notes"],
        "Gate integration bridge": [
            "apply_final_emission_gate_consumer",
            "gm_response_stub",
        ],
        "Consumer layer bridge (AC/RD/RT)": [
            "validate_answer_completeness",
            "apply_answer_completeness_layer",
            "apply_response_delta_layer",
            "enforce_response_type_contract_layer",
            "skip_answer_completeness_layer",
            "skip_response_delta_layer",
            "strict_social_answer_pressure_rd_contract_active",
            "validate_response_delta",
            "inspect_response_delta_failure",
            "assert_response_delta_boundary_validate_only",
            "assert_no_boundary_reorder_repair",
            "response_type_contract",
            "assert_response_type_meta",
            "assert_response_type_contract_surfaces",
        ],
        "Route wiring smoke": [
            "assert_final_route_present_smoke",
            "assert_final_route_accept_candidate_smoke",
            "assert_final_route_not_replaced_smoke",
            "has_non_accept_final_route_smoke",
            "assert_final_route_replaced_or_not_accept",
            "assert_dialogue_lock_social_route_smoke",
            "assert_dialogue_lock_non_dialogue_route_smoke",
        ],
        "Phrase/hygiene smoke": [
            "assert_player_text_present",
            "assert_global_visibility_stock_absent",
            "assert_procedural_adjudication_smoke",
            "assert_no_validator_voice_smoke",
            "assert_no_retry_coaching_leak_smoke",
            "assert_no_social_visible_intro_filler_smoke",
            "assert_no_uncertainty_fallback_stock_smoke",
            "assert_no_internal_scaffold_labels",
            "assert_no_advisory_prose",
            "assert_no_unresolved_stock_phrases",
            "assert_http_chat_response_smoke",
        ],
        "Repair evidence smoke": ["assert_emission_repair_evidence"],
        "Social/open-call smoke": [
            "assert_social_grounding_smoke",
            "assert_continuity_validation_failed_without_repair",
            "assert_open_social_solicitation_route",
            "assert_broadcast_open_call_rejected_smoke",
            "assert_open_call_crowd_reaction_wiring_smoke",
            "assert_open_call_no_unresolved_retry_smoke",
        ],
        "Smoke phrase constants": [
            "SMOKE_PROCEDURAL_ADJUDICATION_PHRASES",
            "SMOKE_VALIDATOR_VOICE_PHRASES",
            "SMOKE_RETRY_COACHING_LEAK_PHRASES",
            "SMOKE_SOCIAL_VISIBLE_INTRO_FILLER_PHRASES",
            "SMOKE_UNCERTAINTY_FALLBACK_STOCK_PHRASES",
            "SMOKE_SYNTHETIC_INTERNAL_LEAK_PATTERNS",
            "SMOKE_SYNTHETIC_SCAFFOLD_LEAK_PATTERNS",
            "SMOKE_SYNTHETIC_VAGUE_FILLER_PATTERNS",
            "STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH",
        ],
    }

    family_stats = {}
    for fam, members in families.items():
        consumers: set[str] = set()
        for m in members:
            consumers |= symbol_fi.get(m, set())
        family_stats[fam] = {
            "assertion_count": len(members),
            "consumer_count": len(consumers),
            "members": members,
            "consumers": sorted(consumers),
        }

    sym_counts = {k: len(v) for k, v in symbol_fi.items()}
    result = {
        "module_fi": len(importers),
        "module_fo": len(fo_modules),
        "fo_modules": sorted(fo_modules),
        "public_export_count": len(public),
        "loc": len(facade_src.splitlines()),
        "importers": importers,
        "symbol_fi": {k: sorted(v) for k, v in sorted(symbol_fi.items(), key=lambda x: -len(x[1]))},
        "top_symbols": sorted(sym_counts.items(), key=lambda x: -x[1])[:25],
        "family_stats": family_stats,
        "usage_class_totals": {},
    }

    class_totals: dict[str, int] = defaultdict(int)
    for imp in importers:
        for c in imp["usage_classes"]:
            class_totals[c] += 1
    result["usage_class_totals"] = dict(sorted(class_totals.items(), key=lambda x: -x[1]))

    ARTIFACT.parent.mkdir(exist_ok=True)
    ARTIFACT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"FI={len(importers)} FO={len(fo_modules)} exports={len(public)} LOC={result['loc']}")
    print(f"Wrote {ARTIFACT}")


if __name__ == "__main__":
    main()
