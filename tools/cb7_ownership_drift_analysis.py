#!/usr/bin/env python3
"""CB7 read-only ownership/coupling drift analysis. Writes artifacts/cb7_analysis.json."""
from __future__ import annotations

import ast
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "cb7_analysis.json"

# CB7 domain patterns (game + tests + tools where relevant)
DOMAINS: dict[str, list[str]] = {
    "final_emission": [
        "game.final_emission",
    ],
    "fallback": [
        "game.fallback",
        "game.final_emission_visibility_fallback",
        "game.final_emission_sealed_fallback",
        "game.final_emission_opening_fallback",
        "game.opening_deterministic_fallback",
        "game.upstream_response_repairs",
        "game.output_sanitizer",
        "game.diegetic_fallback_narration",
    ],
    "speaker": [
        "game.speaker",
        "game.emitted_speaker",
        "game.post_emission_speaker",
    ],
    "response_policy": [
        "game.response_policy",
    ],
    "replay_governance": [
        "tests.helpers.golden_replay",
        "tests.helpers.protected_replay",
        "tests.helpers.replay",
        "tests.test_golden_replay",
        "tests.test_replay",
        "tools.refresh_protected_replay",
        "tools.run_protected_replay",
        "game.final_emission_replay_projection",
    ],
    "api_orchestration": [
        "game.api",
        "game.api_turn_support",
        "game.gm",
        "game.gm_retry",
        "run",
    ],
    "prompt_ctir": [
        "game.prompt",
        "game.ctir",
        "game.narrative",
        "game.planner",
        "game.turn_packet",
        "game.narration",
    ],
    "state_storage": [
        "game.storage",
        "game.state",
        "game.campaign",
        "game.session",
        "game.defaults",
        "game.persistence",
    ],
}

# BV1 baselines from artifacts/bv1_maintenance_matrix_data.json + CB discovery
BV1_BASELINES = {
    "final_emission": {"modules": 43, "fan_in": 443, "fan_out": 218, "prod_fi": 174},
    "fallback": {"modules": 43, "fan_in": 103, "fan_out": 193, "prod_fi": 41},
    "speaker": {"modules": 19, "fan_in": 80, "fan_out": 125, "prod_fi": 13},
    "replay_governance": {"modules": 20, "fan_in": 86, "fan_out": 80, "prod_fi": 1},
    "response_policy": {"modules": 3, "fan_in": 29, "fan_out": 18, "prod_fi": 12},
    "api_orchestration": {"modules": 6, "fan_in": 156, "fan_out": 101, "prod_fi": 120},
    "prompt_ctir": {"modules": 16, "fan_in": 184, "fan_out": 73, "prod_fi": 90},
    "state_storage": {"modules": 8, "fan_in": 284, "fan_out": 16, "prod_fi": 250},
}

# CB discovery AST scan (2026-06-23) from CB_feature_boundary_readiness_discovery.md
CB_DISCOVERY = {
    "final_emission": {"modules": 52, "fan_in": 527, "fan_out": 285},
    "fallback": {"modules": 43, "fan_in": 103, "fan_out": 193},
    "speaker": {"modules": 3, "fan_in": 29, "fan_out": 16},
    "replay_governance": {"modules": 44, "fan_in": 200, "fan_out": 150},
    "response_policy": {"modules": 4, "fan_in": 35, "fan_out": 22},
    "api_orchestration": {"modules": 6, "fan_in": 156, "fan_out": 101},
    "prompt_ctir": {"modules": 16, "fan_in": 184, "fan_out": 73},
    "state_storage": {"modules": 8, "fan_in": 284, "fan_out": 16},
}

OWNERSHIP_LEDGER_PATTERNS = {
    "final_emission": re.compile(
        r"final[_ -]emission|final_emission_", re.I
    ),
    "fallback": re.compile(
        r"fallback|sanitizer|upstream_response_repairs|output_sanitizer", re.I
    ),
    "speaker": re.compile(
        r"speaker|emitted_speaker|post_emission_speaker", re.I
    ),
    "response_policy": re.compile(r"response[_ -]policy", re.I),
    "replay_governance": re.compile(
        r"golden_replay|protected_replay|replay_governance|replay_projection", re.I
    ),
    "api_orchestration": re.compile(r"\b(api|gm_retry|gm\.py|turn pipeline)\b", re.I),
    "prompt_ctir": re.compile(r"prompt|ctir|turn_packet|narrative|planner", re.I),
    "state_storage": re.compile(
        r"state_authority|state_channels|storage|campaign_state|session|persistence|defaults", re.I
    ),
}


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def matches_domain(mod: str, prefs: list[str]) -> bool:
    return any(mod.startswith(p) or mod == p for p in prefs)


def main() -> None:
    files = (
        list(ROOT.glob("game/**/*.py"))
        + list(ROOT.glob("tests/**/*.py"))
        + list(ROOT.glob("tools/**/*.py"))
        + list(ROOT.glob("scripts/**/*.py"))
        + ([ROOT / "run.py"] if (ROOT / "run.py").exists() else [])
    )
    modules: dict[str, Path] = {}
    for p in files:
        if "__pycache__" in p.parts:
            continue
        modules[module_name(p)] = p

    imports: dict[str, set[str]] = {m: set() for m in modules}
    for m, p in modules.items():
        try:
            tree = ast.parse(p.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.name.startswith(("game", "tests", "tools", "scripts")):
                        imports[m].add(a.name)
            elif isinstance(n, ast.ImportFrom) and n.module:
                if n.module.startswith(("game", "tests", "tools", "scripts")):
                    imports[m].add(n.module)

    fan_in: dict[str, int] = {m: 0 for m in modules}
    for m, outs in imports.items():
        for out in outs:
            for cand in modules:
                if out == cand or out.startswith(cand + "."):
                    fan_in[cand] += 1
                    break

    domain_stats: dict[str, dict] = {}
    for domain, prefs in DOMAINS.items():
        mods = [m for m in modules if matches_domain(m, prefs)]
        prod = [m for m in mods if m.startswith("game.")]
        tests_mod = [m for m in mods if m.startswith("tests.")]
        tools_mod = [m for m in mods if m.startswith(("tools.", "scripts.")) or m == "run"]
        total_fi = sum(fan_in.get(m, 0) for m in mods)
        total_fo = sum(len(imports.get(m, set())) for m in mods)
        prod_fi = sum(fan_in.get(m, 0) for m in prod)
        top = sorted(
            ((fan_in.get(m, 0), len(imports.get(m, set())), m) for m in mods),
            reverse=True,
        )[:8]
        domain_stats[domain] = {
            "file_count": len(mods),
            "prod_modules": len(prod),
            "test_modules": len(tests_mod),
            "tool_modules": len(tools_mod),
            "fan_in": total_fi,
            "fan_out": total_fo,
            "prod_fan_in": prod_fi,
            "top_hubs": [{"fi": fi, "fo": fo, "module": m} for fi, fo, m in top],
            "delta_vs_bv1_fi": total_fi - BV1_BASELINES[domain]["fan_in"],
            "delta_vs_bv1_fo": total_fo - BV1_BASELINES[domain]["fan_out"],
            "delta_vs_cb_fi": total_fi - CB_DISCOVERY[domain]["fan_in"],
            "delta_vs_cb_fo": total_fo - CB_DISCOVERY[domain]["fan_out"],
        }

    # Ownership lexical refs from BU CSV if present
    ownership_by_domain: dict[str, int] = defaultdict(int)
    ownership_csv = ROOT / "docs" / "audits" / "BU_ownership_dependency_map.csv"
    if ownership_csv.exists():
        with ownership_csv.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                mod = row["module"]
                refs = int(row.get("ownership_reference_count", 0))
                for domain, prefs in DOMAINS.items():
                    if matches_domain(mod, prefs):
                        ownership_by_domain[domain] += refs

    # Ledger domain tagging for game/*.py files
    ledger_path = ROOT / "docs" / "architecture_ownership_ledger.md"
    ledger_text = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    game_files = sorted(ROOT.glob("game/**/*.py"))
    file_domain_tags: dict[str, list[str]] = defaultdict(list)
    for p in game_files:
        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        for domain, rx in OWNERSHIP_LEDGER_PATTERNS.items():
            if rx.search(rel) or rx.search(text[:2000]):
                file_domain_tags[rel].append(domain)
    dual_owned = {k: v for k, v in file_domain_tags.items() if len(v) > 1}
    untagged_game = [
        p.relative_to(ROOT).as_posix()
        for p in game_files
        if p.relative_to(ROOT).as_posix() not in file_domain_tags
        and not p.name.startswith("__")
    ]

    # Parse BU ecosystem CSV for key module deltas
    bu_csv = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"
    key_modules_bv1 = json.loads(
        (ROOT / "artifacts" / "bv1_maintenance_matrix_data.json").read_text(encoding="utf-8")
    )["key_modules"]
    key_deltas = []
    if bu_csv.exists():
        current = {}
        with bu_csv.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                current[row["module"]] = row
        for mod, baseline in key_modules_bv1.items():
            cur = current.get(mod)
            if cur:
                key_deltas.append(
                    {
                        "module": mod,
                        "bv1_fi": baseline["fan_in"],
                        "current_fi": int(cur["fan_in_total"]),
                        "delta_fi": int(cur["fan_in_total"]) - baseline["fan_in"],
                        "bv1_fo": baseline["fan_out"],
                        "current_fo": int(cur["fan_out_total"]),
                        "delta_fo": int(cur["fan_out_total"]) - baseline["fan_out"],
                    }
                )

    payload = {
        "generated_at": "2026-06-23",
        "python_files_parsed": len(modules),
        "ecosystem_modules_bu_script": 236,
        "domain_stats": domain_stats,
        "ownership_refs_by_domain": dict(ownership_by_domain),
        "dual_owned_heuristic_files": dict(sorted(dual_owned.items())),
        "dual_owned_count": len(dual_owned),
        "untagged_game_files_sample": untagged_game[:30],
        "untagged_game_count": len(untagged_game),
        "key_module_deltas": key_deltas,
        "governance_drift": {
            "added_test_files": 19,
            "removed_test_files": 0,
            "root_cause": "BW/BZ closeout + fallback portfolio + golden replay structural suites added without governance JSON regen",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
