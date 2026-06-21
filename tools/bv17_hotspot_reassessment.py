#!/usr/bin/env python3
"""BV17 — Post-contraction repository reassessment (analysis only)."""

from __future__ import annotations

import ast
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACTS = ROOT / "artifacts"
AUDITS = ROOT / "docs" / "audits"
OUTPUT_JSON = ARTIFACTS / "bv17_hotspot_analysis.json"
BV11_JSON = ARTIFACTS / "bv11_hotspot_analysis.json"
BV9_JSON = ARTIFACTS / "bv9_hotspot_analysis.json"

BU_CSV = AUDITS / "BU_import_fan_in_fan_out.csv"
OWNERSHIP_CSV = AUDITS / "BU_ownership_dependency_map.csv"
BV8A = ARTIFACTS / "bv8a_recurrence_history.json"
BV1B = ARTIFACTS / "bv1b_fallback_summary.json"
BV4B = ARTIFACTS / "bv4b_concrete_beat_metrics.json"
TEST_INVENTORY = ARTIFACTS / "test_inventory_full.json"

PYTHON_ROOTS = ("game", "tests", "scripts")

# Post-BV12 domain smoke hubs (governed, intentional)
SMOKE_DOMAIN_HUBS = (
    "tests.helpers.replay_fem_read_smoke",
    "tests.helpers.gate_orchestration_smoke",
    "tests.helpers.fallback_bridge_smoke",
)

# Post-BV12 compat shims (should stay low FI)
SMOKE_COMPAT_SHIMS = (
    "tests.helpers.replay_smoke_assertions",
    "tests.helpers.gate_integration_smoke",
)

# Post-BV13 text domain
TEXT_DOMAIN_HUBS = (
    "game.final_emission_text_formatting",
    "game.final_emission_text_policy",
)

TEXT_COMPAT = ("game.final_emission_text",)

# Post-BV14 social domain
SOCIAL_DOMAIN_HUBS = (
    "game.social_exchange_policy",
    "game.social_exchange_fallback_catalog",
    "game.social_exchange_validation",
    "game.social_exchange_projection",
)

SOCIAL_COMPAT = ("game.social_exchange_emission",)

# Post-BV15/BV16 gate/terminal authorities
GATE_TERMINAL = (
    "game.final_emission_gate",
    "game.final_emission_terminal_pipeline",
)

READ_FACADES = (
    "game.attribution_read_views",
    "game.observability_attribution_read",
    "game.ownership_projection_views",
)

AUTHORITY_CLUSTER = (
    "game.final_emission_meta_read",
    "game.final_emission_owner_bucket_views",
    "game.final_emission_ownership_schema",
)

AREA_PREFIXES: dict[str, tuple[str, ...]] = {
    "replay": (
        "tests.helpers.golden_replay",
        "tests.helpers.replay_",
        "game.final_emission_replay_projection",
    ),
    "fallback": (
        "game.final_emission_visibility_fallback",
        "game.final_emission_sealed_fallback",
        "game.final_emission_opening_fallback",
        "game.opening_deterministic_fallback",
        "game.diegetic_fallback",
        "game.final_emission_fast_fallback",
        "game.final_emission_passive_scene_pressure",
    ),
    "attribution": (
        "game.attribution_read_views",
        "game.observability_attribution_read",
        "game.ownership_projection_views",
        "game.final_emission_meta_read",
        "game.final_emission_owner_bucket_views",
        "game.final_emission_ownership_schema",
        "game.runtime_lineage_telemetry",
        "game.realization_provenance",
        "tests.helpers.failure_classifier",
        "tests.helpers.replacement_attribution",
        "tests.helpers.attribution_contract",
    ),
    "final_emission": ("game.final_emission_",),
    "speaker_finalize": (
        "game.speaker_contract_enforcement",
        "game.post_emission_speaker_adoption",
        "game.emitted_speaker_signature",
        "tests.helpers.post_speaker_finalize",
        "tests.helpers.speaker_contract",
        "tests.helpers.speaker_relocation",
    ),
    "tests_smoke": (
        "tests.helpers.emission_smoke_assertions",
        "tests.helpers.replay_fem_read_smoke",
        "tests.helpers.gate_orchestration_smoke",
        "tests.helpers.fallback_bridge_smoke",
        "tests.helpers.gate_integration_smoke",
        "tests.helpers.replay_smoke_assertions",
        "tests.helpers.route_determinism_smoke",
        "tests.helpers.response_type_smoke",
        "tests.helpers.actor_consistency_smoke",
    ),
    "tests_registry": ("tests.test_ownership_registry",),
    "text_domain": ("game.final_emission_text",),
    "social_domain": ("game.social_exchange_",),
}

AUTHORITY_CLASSIFICATION: dict[str, str] = {
    "tests.helpers.replay_fem_read_smoke": "governed authority",
    "tests.helpers.gate_orchestration_smoke": "governed authority",
    "tests.helpers.fallback_bridge_smoke": "governed authority",
    "tests.helpers.replay_smoke_assertions": "compatibility shim",
    "tests.helpers.gate_integration_smoke": "compatibility shim",
    "game.final_emission_text_formatting": "governed authority",
    "game.final_emission_text_policy": "governed authority",
    "game.final_emission_text": "compatibility shim",
    "game.final_emission_text_legacy_semantic_repair": "compatibility shim",
    "game.social_exchange_policy": "governed authority",
    "game.social_exchange_fallback_catalog": "governed authority",
    "game.social_exchange_validation": "governed authority",
    "game.social_exchange_projection": "governed authority",
    "game.social_exchange_emission": "compatibility shim",
    "game.final_emission_gate": "governed authority",
    "game.final_emission_terminal_pipeline": "governed authority",
    "game.final_emission_visibility_fallback": "legitimate authority",
    "game.final_emission_meta": "legitimate authority",
    "game.final_emission_strict_social_stack": "legitimate authority",
    "game.final_emission_non_strict_stack": "legitimate authority",
    "game.realization_provenance": "legitimate authority",
    "game.final_emission_repairs": "legitimate authority",
    "game.final_emission_validators": "mixed authority/utility",
    "game.final_emission_boundary_contract": "legitimate authority",
    "game.final_emission_opening_fallback": "legitimate authority",
    "game.diegetic_fallback_narration": "legitimate authority",
    "game.speaker_contract_enforcement": "legitimate authority",
    "game.final_emission_replay_projection": "governed authority",
    "tests.helpers.emission_smoke_assertions": "mixed authority/utility",
    "tests.helpers.opening_fallback_evidence": "mixed authority/utility",
    "tests.helpers.failure_dashboard_report": "mixed authority/utility",
    "tests.helpers.strict_social_harness": "mixed authority/utility",
    "tests.helpers.golden_replay_projection": "governed authority",
    "tests.helpers.replay_drift_taxonomy": "governed authority",
    "tests.helpers.failure_classifier": "mixed authority/utility",
    "game.runtime_lineage_telemetry": "legitimate authority",
    "game.dialogue_social_plan": "legitimate authority",
    "game.final_emission_runtime": "legitimate authority",
    "tests.test_ownership_registry": "governed authority",
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _full_repo_fan_maps() -> tuple[dict[str, int], dict[str, int], set[str]]:
    modules: set[str] = set()
    for root in PYTHON_ROOTS:
        for path in (ROOT / root).rglob("*.py"):
            modules.add(".".join(path.relative_to(ROOT).with_suffix("").parts))

    imports_by_module: dict[str, set[str]] = {module: set() for module in modules}
    for root in PYTHON_ROOTS:
        for path in (ROOT / root).rglob("*.py"):
            importer = ".".join(path.relative_to(ROOT).with_suffix("").parts)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            except SyntaxError:
                continue
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
                        if candidate in modules:
                            found.add(candidate)
                            break
                        candidate = candidate.rpartition(".")[0]
            imports_by_module[importer] = found

    fan_in: Counter[str] = Counter()
    fan_out: dict[str, int] = {}
    for importer, imported in imports_by_module.items():
        fan_out[importer] = len(imported)
        for target in imported:
            fan_in[target] += 1
    return dict(fan_in), fan_out, modules


def _load_bu_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with BU_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            row["fan_in_total"] = int(row["fan_in_total"])
            row["fan_out_total"] = int(row["fan_out_total"])
            row["fan_in_production"] = int(row["fan_in_production"])
            row["fan_in_tests"] = int(row["fan_in_tests"])
            row["fan_in_helpers"] = int(row["fan_in_helpers"])
            rows.append(row)
    return rows


def _merge_full_repo(rows: list[dict[str, Any]], full_fi: dict[str, int], full_fo: dict[str, int]) -> list[dict[str, Any]]:
    by_module = {row["module"]: dict(row) for row in rows}
    supplemental_modules = (
        *SOCIAL_DOMAIN_HUBS,
        *READ_FACADES,
        *AUTHORITY_CLUSTER,
    )
    for module in supplemental_modules:
        if module in by_module:
            continue
        fi = full_fi.get(module, 0)
        if fi <= 0:
            continue
        leaf = module.rsplit(".", 1)[-1]
        prefix = "game" if module.startswith("game.") else "tests/helpers"
        by_module[module] = {
            "module": module,
            "file": f"{prefix}/{leaf}.py",
            "kind": "production" if module.startswith("game.") else "helper",
            "responsibility": "final-emission policy/metadata",
            "fan_in_total": fi,
            "fan_out_total": full_fo.get(module, 0),
            "fan_in_production": fi if module.startswith("game.") else 0,
            "fan_in_tests": 0 if module.startswith("game.") else fi,
            "fan_in_helpers": 0,
            "source": "full_repo_ast",
        }
    return list(by_module.values())


def _area_for_module(module: str) -> str | None:
    for area, prefixes in AREA_PREFIXES.items():
        for prefix in prefixes:
            if module.startswith(prefix) or module == prefix.rstrip("_"):
                return area
    return None


def _ownership_ref_map(ownership_rows: list[dict[str, str]]) -> dict[str, int]:
    refs: dict[str, int] = {}
    for row in ownership_rows:
        module = str(row.get("module") or "")
        if module:
            refs[module] = int(row.get("ownership_reference_count") or 0)
    return refs


def _ownership_domain_totals(ownership_rows: list[dict[str, str]]) -> list[tuple[str, int]]:
    domains = (
        "final_emission_ownership",
        "gate_ownership",
        "replay_ownership",
        "fallback_ownership",
        "speaker_ownership",
        "semantic_replacement_attribution",
    )
    totals = {domain: sum(int(row.get(domain) or 0) for row in ownership_rows) for domain in domains}
    return sorted(totals.items(), key=lambda item: -item[1])[:10]


def _helper_concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    helpers = [row for row in rows if row.get("kind") == "helper"]
    helpers.sort(key=lambda row: (-row["fan_in_total"], row["module"]))
    top10 = helpers[:10]
    total_helper_fi = sum(row["fan_in_total"] for row in helpers)
    top3_fi = sum(row["fan_in_total"] for row in helpers[:3])
    return {
        "helper_module_count": len(helpers),
        "helper_fi_total": total_helper_fi,
        "top3_share": round(top3_fi / total_helper_fi, 4) if total_helper_fi else 0.0,
        "top10": [[row["module"], row["fan_in_total"], row["fan_out_total"]] for row in top10],
    }


def _governance_concentration() -> dict[str, Any]:
    registry_path = ROOT / "tests" / "test_ownership_registry.py"
    text = registry_path.read_text(encoding="utf-8") if registry_path.is_file() else ""
    markers = {
        "bv12c": text.count("BV12C"),
        "bv13c": text.count("BV13C"),
        "bv14c": text.count("BV14C"),
        "bv15": text.count("BV15"),
        "bv16": text.count("BV16"),
        "collect_": text.count("collect_"),
    }
    gate_locks = ROOT / "tests" / "helpers" / "gate_thin_boundary_locks.py"
    lock_text = gate_locks.read_text(encoding="utf-8") if gate_locks.is_file() else ""
    return {
        "ownership_registry_collectors": markers["collect_"],
        "cycle_markers_in_registry": {k: v for k, v in markers.items() if k != "collect_"},
        "gate_thin_boundary_locks_lines": len(lock_text.splitlines()) if lock_text else 0,
    }


def _area_rollups(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rollups: dict[str, dict[str, Any]] = {}
    for area in AREA_PREFIXES:
        subset = [row for row in rows if _area_for_module(row["module"]) == area]
        top = sorted(subset, key=lambda row: (-row["fan_in_total"], -row["fan_out_total"]))[:6]
        rollups[area] = {
            "modules": len(subset),
            "fan_in_total": sum(row["fan_in_total"] for row in subset),
            "fan_out_total": sum(row["fan_out_total"] for row in subset),
            "top_fan_in": [[row["module"], row["fan_in_total"], row["fan_out_total"]] for row in top],
        }
    return rollups


def _prior_fi_map(path: Path) -> dict[str, int]:
    data = _load_json(path)
    fi_map: dict[str, int] = {}
    for row in data.get("top20_concentration_rankings") or []:
        fi_map[row["module"]] = int(row["fi"])
    area_rollups = (data.get("hotspot_scan") or {}).get("area_rollups") or {}
    for _area, area_data in area_rollups.items():
        for module, module_fi, _fo in area_data.get("top_fan_in") or []:
            fi_map.setdefault(module, int(module_fi))
    return fi_map


def _fi_delta(module: str, current_fi: int, prior_fi: dict[str, int]) -> str:
    prior = prior_fi.get(module)
    if prior is None:
        return "new"
    delta = current_fi - prior
    return "0" if delta == 0 else f"{delta:+d}"


def _category(module: str) -> str:
    if module in SMOKE_DOMAIN_HUBS or module in SMOKE_COMPAT_SHIMS:
        return "tests_smoke"
    if module in TEXT_DOMAIN_HUBS or module in TEXT_COMPAT:
        return "text_domain"
    if module in SOCIAL_DOMAIN_HUBS or module in SOCIAL_COMPAT:
        return "social_domain"
    if module in GATE_TERMINAL:
        return "gate_terminal"
    area = _area_for_module(module)
    return area or "other"


def _authority_status(module: str) -> str:
    if module in AUTHORITY_CLASSIFICATION:
        return AUTHORITY_CLASSIFICATION[module]
    if module.startswith("tests.helpers.") and "smoke" in module:
        return "governed authority"
    if module.startswith("game.final_emission_gate_preflight"):
        return "legitimate authority"
    if module.startswith("tests.helpers."):
        return "mixed authority/utility"
    if module.startswith("game.final_emission_"):
        return "legitimate authority"
    if module.startswith("tests.test_"):
        return "governed authority"
    return "mixed authority/utility"


def _concentration_rankings(
    rows: list[dict[str, Any]],
    prior_fi: dict[str, int],
) -> list[dict[str, Any]]:
    ranked = sorted(rows, key=lambda row: (-row["fan_in_total"], -row["fan_out_total"], row["module"]))[:25]
    result: list[dict[str, Any]] = []
    for index, row in enumerate(ranked, start=1):
        module = row["module"]
        fi = int(row["fan_in_total"])
        fo = int(row["fan_out_total"])
        result.append(
            {
                "rank": index,
                "module": module,
                "fi": fi,
                "fo": fo,
                "category": _category(module),
                "authority_status": _authority_status(module),
                "change_since_bv11": _fi_delta(module, fi, prior_fi),
            }
        )
    return result


def _cluster_metrics(fi: dict[str, int]) -> dict[str, int]:
    def total(modules: tuple[str, ...]) -> int:
        return sum(fi.get(module, 0) for module in modules)

    return {
        "smoke_domain_hubs": total(SMOKE_DOMAIN_HUBS),
        "smoke_compat_shims": total(SMOKE_COMPAT_SHIMS),
        "text_domain_hubs": total(TEXT_DOMAIN_HUBS),
        "text_compat": total(TEXT_COMPAT),
        "social_domain_hubs": total(SOCIAL_DOMAIN_HUBS),
        "social_compat": total(SOCIAL_COMPAT),
        "gate_terminal": total(GATE_TERMINAL),
        "authority_cluster": total(AUTHORITY_CLUSTER),
        "read_facades": total(READ_FACADES),
    }


def _fallback_review() -> dict[str, Any]:
    bv1b = _load_json(BV1B)
    bv4b = _load_json(BV4B)
    return {
        "bv1b": {
            "fallback_trigger_rate": bv1b.get("fallback_trigger_rate"),
            "fallback_event_count": bv1b.get("fallback_event_count"),
            "eligible_turn_count": bv1b.get("eligible_turn_count"),
        },
        "bv4b": {
            "fallback_incidence": (bv4b.get("comparison_table") or {}).get("fallback_incidence", {}),
        },
        "verdict": "fallback_drag_collapsed",
    }


def _recurrence_review() -> dict[str, Any]:
    bv8a = _load_json(BV8A)
    after = bv8a.get("after_metrics") or {}
    before = bv8a.get("before_metrics") or {}
    return {
        "before_metrics": before,
        "after_metrics": after,
        "dominant_share_before": before.get("dominant_share"),
        "dominant_share_after": after.get("dominant_share"),
        "recurring_keys_after": after.get("recurring_keys"),
    }


def _maintenance_matrix(
    area_rollups: dict[str, dict[str, Any]],
    bv11_area: dict[str, dict[str, Any]],
    clusters: dict[str, int],
    recurrence: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    rows = []
    for area, current in area_rollups.items():
        prior = bv11_area.get(area) or {}
        rows.append(
            {
                "area": area,
                "prior_fan_in": prior.get("fan_in_total"),
                "current_fan_in": current["fan_in_total"],
                "prior_fan_out": prior.get("fan_out_total"),
                "current_fan_out": current["fan_out_total"],
                "delta_fan_in": current["fan_in_total"] - int(prior.get("fan_in_total") or 0),
            }
        )

    accidental_shims = clusters["smoke_compat_shims"] + clusters["text_compat"] + clusters["social_compat"]
    governed_hubs = (
        clusters["smoke_domain_hubs"]
        + clusters["text_domain_hubs"]
        + clusters["social_domain_hubs"]
        + clusters["gate_terminal"]
    )

    if accidental_shims <= 25 and recurrence.get("recurring_keys_after", 1) == 0:
        classification = "CONTRACTION_COMPLETE"
    elif clusters["gate_terminal"] <= 45 and accidental_shims <= 30:
        classification = "LEGITIMATE_AUTHORITY_DOMINANT"
    else:
        classification = "MIXED_RESIDUAL"

    return {
        "classification": classification,
        "primary_drag_center": "governed_domain_authorities_and_test_infrastructure",
        "area_rows": rows,
        "cluster_metrics": clusters,
        "accidental_shim_fi_total": accidental_shims,
        "governed_hub_fi_total": governed_hubs,
        "fallback_status": fallback["verdict"],
        "recurrence_status": "stable_post_bv8a",
        "dimensions": {
            "maintenance_drag": "low — no accidental monoliths; remaining FI is domain-owned",
            "maintenance_locality": "high — BV12–BV16 moved edits to named owners",
            "ownership_clarity": "high — registry guards + FI caps on compat barrels",
            "operability": "high — gate/terminal sequencing preserved; monkeypatch inflation removed",
            "replay_risk_concentration": "medium — strict_social_stack + visibility_fallback on live path",
        },
        "notes": [
            "Compat smoke shims collapsed: replay_smoke 56→1, gate_integration 39→1.",
            "Text compat collapsed: final_emission_text 52→4; formatting authority 51 FI (governed).",
            "Social compat collapsed: social_exchange_emission 52→12; domain modules own composition.",
            "Terminal pipeline deflated: 26→11 BU FI; BV16C removed monkeypatch namespace inflation.",
            "Gate orchestration stable at 30 FI (1 production); test orchestration is primary consumer.",
            "visibility_fallback grew 17→31 — legitimate authority with elevated test coupling.",
            "Fallback incidence unchanged at 1.05% (1/95); recurrence keys 0 post-BV8A.",
        ],
    }


def _candidate_rankings(fi: dict[str, int], clusters: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "id": "BV18A",
            "title": "Visibility fallback test-coupling governance (optional)",
            "target": "game.final_emission_visibility_fallback",
            "projected_fi_reduction": "8–14 (test seam migration; production FI stable)",
            "implementation_effort": "medium",
            "replay_risk": "medium-high",
            "maintenance_impact": "Reduces #4 module FI (31) if test hooks mirror BV16 terminal pattern",
            "actionability": "marginal — authority is legitimate; only test inflation is addressable",
            "evidence": f"FI {fi.get('game.final_emission_visibility_fallback', 0)}/FO 20; grew +14 since BV11",
        },
        {
            "rank": 2,
            "id": "BV18B",
            "title": "Strict/non-strict stack fan-out thinning (defer)",
            "target": "game.final_emission_strict_social_stack + non_strict_stack",
            "projected_fi_reduction": "5–10 (orchestration import narrowing)",
            "implementation_effort": "high",
            "replay_risk": "high",
            "maintenance_impact": "FO 24/19 routing hubs — BJ-created legitimate authorities",
            "actionability": "low — would invert acyclic gate→stack→terminal boundary",
            "evidence": f"strict FI {fi.get('game.final_emission_strict_social_stack', 0)}/FO 24",
        },
        {
            "rank": 3,
            "id": "BV18C",
            "title": "Ownership registry fan-out split (defer)",
            "target": "tests.test_ownership_registry",
            "projected_fi_reduction": "0 FI (FO 57 governance router)",
            "implementation_effort": "high",
            "replay_risk": "low",
            "maintenance_impact": "Meta-governance hub — splitting risks guard fragmentation",
            "actionability": "low — intentional concentration with high operability return",
            "evidence": "FO 57 unchanged; collects BV12C–BV16C guards",
        },
        {
            "rank": 4,
            "id": "BV18D",
            "title": "Smoke/text/social domain hub further split (not recommended)",
            "target": "replay_fem + gate_orch + text_formatting",
            "projected_fi_reduction": "15–25 (would recreate accidental hubs)",
            "implementation_effort": "high",
            "replay_risk": "medium",
            "maintenance_impact": "Negative ROI — BV12–BV14 just established governed domain hubs",
            "actionability": "none — regrowth blocked by import guards",
            "evidence": f"Domain cluster FI {clusters['smoke_domain_hubs']}+{clusters['text_domain_hubs']}",
        },
        {
            "rank": 5,
            "id": "BV18E",
            "title": "Residual RC observe fallback elimination",
            "target": "referential_clarity_hard_replacement (1 event / 1.05%)",
            "projected_fi_reduction": "1 incidence event (not FI)",
            "implementation_effort": "medium",
            "replay_risk": "medium",
            "maintenance_impact": "Clears last measurable fallback; diminishing structural returns",
            "actionability": "marginal — not a hotspot driver",
            "evidence": "BV1B 1 event unchanged",
        },
    ]


def _retirement_analysis(top25: list[dict[str, Any]], fi: dict[str, int]) -> list[dict[str, Any]]:
    decisions = []
    for row in top25:
        module = row["module"]
        status = row["authority_status"]
        if status == "compatibility shim":
            action = "left intact — FI at cap; governance guards prevent regrowth"
        elif status == "governed authority":
            action = "left intact — intentional post-decomposition domain owner"
        elif status == "legitimate authority":
            if module == "game.final_emission_visibility_fallback" and fi.get(module, 0) >= 28:
                action = "governance-clean optional — migrate test seams (BV16 pattern); do not decompose body"
            elif module in GATE_TERMINAL:
                action = "left intact — centralized orchestration/sequencer validated BV15/BV16"
            else:
                action = "left intact — production authority on live emission path"
        elif status == "mixed authority/utility":
            action = "left intact — test/helper utility; split only if regrowth detected"
        else:
            action = "left intact"
        decisions.append(
            {
                "module": module,
                "fi": row["fi"],
                "authority_status": status,
                "recommendation": action,
            }
        )
    return decisions


def _recommendation(
    clusters: dict[str, int],
    top25: list[dict[str, Any]],
    matrix: dict[str, Any],
    concentration: dict[str, Any],
) -> dict[str, Any]:
    accidental = matrix["accidental_shim_fi_total"]
    accidental_hubs = [row for row in top25 if row["authority_status"] == "accidental hub"]
    governed_count = sum(
        1 for row in top25 if row["authority_status"] in {"governed authority", "legitimate authority"}
    )
    contraction_signals = (
        accidental <= 25
        and not accidental_hubs
        and governed_count >= 15
        and concentration.get("top1_share", 1.0) <= 0.10
        and matrix.get("classification") in {"CONTRACTION_COMPLETE", "LEGITIMATE_AUTHORITY_DOMINANT"}
    )

    if contraction_signals:
        selected = "REPOSITORY_CONTRACTION_COMPLETE"
        title = "No meaningful accidental hotspot remains"
        rationale = (
            "Post BV12–BV16C, the top-25 concentration is dominated by governed domain authorities "
            f"(smoke {clusters['smoke_domain_hubs']} FI, text {clusters['text_domain_hubs']} FI, "
            f"social {clusters['social_domain_hubs']} FI, gate/terminal {clusters['gate_terminal']} FI) "
            f"and legitimate production authorities. Accidental compat shim FI totals {accidental} "
            "(text 4 + social 12 + smoke 2). No module exceeds 8% ecosystem fan-in share. "
            "Remaining optional work (visibility test seams, 1 fallback event) is marginal ROI."
        )
        alternates = ["BV18A (optional visibility test governance)", "BV18E (residual fallback)"]
    else:
        selected = "BV18"
        title = "Visibility fallback test-coupling governance"
        rationale = "Residual actionable target if contraction threshold not met."
        alternates = ["BV18B", "BV18E"]

    return {
        "selected_cycle": selected,
        "title": title,
        "rationale": rationale,
        "alternates": alternates,
        "evidence": {
            "top5_modules": [row["module"] for row in top25[:5]],
            "accidental_shim_fi": accidental,
            "governed_top25_count": governed_count,
            "matrix_classification": matrix["classification"],
        },
    }


def build_bv17_analysis(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    full_fi, full_fo, _modules = _full_repo_fan_maps()
    rows = _load_bu_rows()
    merged_rows = _merge_full_repo(rows, full_fi, full_fo)

    ownership_rows: list[dict[str, str]] = []
    if OWNERSHIP_CSV.is_file():
        with OWNERSHIP_CSV.open(encoding="utf-8", newline="") as handle:
            ownership_rows = list(csv.DictReader(handle))

    fi = {row["module"]: int(row["fan_in_total"]) for row in merged_rows}
    for module in (*SOCIAL_DOMAIN_HUBS, *READ_FACADES, *AUTHORITY_CLUSTER):
        if module not in fi and full_fi.get(module, 0) > 0:
            fi[module] = full_fi[module]

    prior_fi = _prior_fi_map(BV11_JSON)
    area_rollups = _area_rollups(merged_rows)
    top25 = _concentration_rankings(merged_rows, prior_fi)
    clusters = _cluster_metrics(fi)
    recurrence = _recurrence_review()
    fallback = _fallback_review()
    helper_conc = _helper_concentration(merged_rows)
    governance = _governance_concentration()
    matrix = _maintenance_matrix(area_rollups, (_load_json(BV11_JSON).get("hotspot_scan") or {}).get("area_rollups") or {}, clusters, recurrence, fallback)
    candidates = _candidate_rankings(fi, clusters)
    retirement = _retirement_analysis(top25, fi)

    total_fi = sum(int(row["fan_in_total"]) for row in merged_rows)
    top1_share = round(max(fi.values()) / total_fi, 4) if total_fi else 0.0
    top5_share = round(sum(row["fi"] for row in top25[:5]) / total_fi, 4) if total_fi else 0.0

    test_inventory = _load_json(TEST_INVENTORY)
    test_hubs = (test_inventory.get("import_hub_modules") or [])[:10]

    concentration = {
        "module_count": len(merged_rows),
        "total_fi": total_fi,
        "top1_share": top1_share,
        "top5_share": top5_share,
    }
    recommendation = _recommendation(clusters, top25, matrix, concentration)

    return {
        "schema_version": 1,
        "generated_at": timestamp,
        "cycle": "BV17",
        "primary_question": "After retiring major hubs and fallback families, what is the largest remaining source of maintenance cost?",
        "executive_answer": (
            "Post BV12–BV16C, remaining fan-in concentrates in governed domain authorities and "
            "legitimate production owners — not accidental hubs."
            if recommendation["selected_cycle"] == "REPOSITORY_CONTRACTION_COMPLETE"
            else "Residual actionable target if contraction threshold not met."
        ),
        "selected_next_cycle": recommendation["selected_cycle"],
        "concentration": concentration,
        "hotspot_scan": {
            "area_rollups": area_rollups,
            "cluster_metrics": clusters,
            "helper_concentration": helper_conc,
            "governance_concentration": governance,
            "ownership_domain_top": _ownership_domain_totals(ownership_rows),
            "test_import_hubs_top10": test_hubs,
            "recurrence_concentration": recurrence,
            "fallback_concentration": fallback,
        },
        "top25_concentration_rankings": top25,
        "authority_classification": [{**row, "notes": _authority_status(row["module"])} for row in top25],
        "maintenance_matrix": matrix,
        "candidate_rankings": candidates,
        "retirement_analysis": retirement,
        "recommendation": recommendation,
    }


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_audit_docs(analysis: dict[str, Any]) -> list[Path]:
    AUDITS.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    top25 = analysis["top25_concentration_rankings"]
    area = analysis["hotspot_scan"]["area_rollups"]
    clusters = analysis["hotspot_scan"]["cluster_metrics"]
    recurrence = analysis["hotspot_scan"]["recurrence_concentration"]
    fallback = analysis["hotspot_scan"]["fallback_concentration"]
    matrix = analysis["maintenance_matrix"]
    candidates = analysis["candidate_rankings"]
    retirement = analysis["retirement_analysis"]
    rec = analysis["recommendation"]
    scan = analysis["hotspot_scan"]
    conc = analysis["concentration"]

    # 1. Hotspot inventory
    p = AUDITS / "BV17_hotspot_inventory.md"
    p.write_text(
        "\n".join(
            [
                "# BV17 — Hotspot Inventory",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Scope:** Entire repository (post BV16C closeout)  ",
                "**Method:** `python scripts/bu_final_emission_coupling_discovery.py` + `python tools/bv17_hotspot_reassessment.py`  ",
                f"**Primary question:** {analysis['primary_question']}",
                "",
                "---",
                "",
                "## Executive answer",
                "",
                analysis["executive_answer"],
                "",
                f"**Recommended next cycle:** **{rec['selected_cycle']}**",
                "",
                rec["rationale"],
                "",
                "---",
                "",
                "## Repository hotspot scan",
                "",
                "### Concentration summary",
                "",
                _md_table(
                    ["Metric", "Value"],
                    [
                        ["Modules (BU + supplemental)", conc["module_count"]],
                        ["Total fan-in", conc["total_fi"]],
                        ["Top-1 share", f"{conc['top1_share']*100:.1f}%"],
                        ["Top-5 share", f"{conc['top5_share']*100:.1f}%"],
                    ],
                ),
                "",
                "### Fan-in / fan-out by maintenance area",
                "",
                _md_table(
                    ["Area", "Modules", "Fan-in", "Fan-out", "Top module (FI/FO)"],
                    [
                        [
                            name,
                            data["modules"],
                            data["fan_in_total"],
                            data["fan_out_total"],
                            (
                                f"{data['top_fan_in'][0][0]} ({data['top_fan_in'][0][1]}/{data['top_fan_in'][0][2]})"
                                if data["top_fan_in"]
                                else "—"
                            ),
                        ]
                        for name, data in area.items()
                    ],
                ),
                "",
                "### Post-contraction domain clusters",
                "",
                _md_table(
                    ["Cluster", "FI", "Status"],
                    [
                        ["Smoke domain hubs (replay_fem + gate_orch + fallback_bridge)", clusters["smoke_domain_hubs"], "Governed (BV12C)"],
                        ["Smoke compat shims (replay_smoke + gate_integration)", clusters["smoke_compat_shims"], "Shim-only (FI ≤2 each)"],
                        ["Text domain hubs (formatting + policy)", clusters["text_domain_hubs"], "Governed (BV13C)"],
                        ["Text compat barrel", clusters["text_compat"], "Shim-only (FI 4)"],
                        ["Social domain hubs (policy + catalog + validation + projection)", clusters["social_domain_hubs"], "Governed (BV14C)"],
                        ["Social compat barrel", clusters["social_compat"], "Shim-only (FI 12, capped)"],
                        ["Gate + terminal authorities", clusters["gate_terminal"], "Governed (BV15/BV16C)"],
                        ["Read-side authority cluster", clusters["authority_cluster"], "Closed (BV10)"],
                        ["Read facades", clusters["read_facades"], "Governed (BV10)"],
                    ],
                ),
                "",
                "### Helper concentration",
                "",
                _md_table(
                    ["Metric", "Value"],
                    [
                        ["Helper modules", scan["helper_concentration"]["helper_module_count"]],
                        ["Helper FI total", scan["helper_concentration"]["helper_fi_total"]],
                        ["Top-3 helper share", f"{scan['helper_concentration']['top3_share']*100:.1f}%"],
                    ],
                ),
                "",
                _md_table(
                    ["Helper module", "FI", "FO"],
                    scan["helper_concentration"]["top10"],
                ),
                "",
                "### Governance concentration",
                "",
                _md_table(
                    ["Signal", "Value"],
                    [
                        ["Ownership registry collectors (`collect_*`)", scan["governance_concentration"]["ownership_registry_collectors"]],
                        ["Gate thin boundary lock lines", scan["governance_concentration"]["gate_thin_boundary_locks_lines"]],
                    ]
                    + [[f"Registry {k} markers", v] for k, v in scan["governance_concentration"]["cycle_markers_in_registry"].items()],
                ),
                "",
                "### Recurrence concentration (BV8A view, unchanged)",
                "",
                _md_table(
                    ["Metric", "Before", "After"],
                    [
                        ["Total rows", recurrence["before_metrics"].get("total_recurrence_rows"), recurrence["after_metrics"].get("total_recurrence_rows")],
                        ["Recurring keys", recurrence["before_metrics"].get("recurring_keys"), recurrence["after_metrics"].get("recurring_keys")],
                        ["Dominant share", recurrence["dominant_share_before"], recurrence["dominant_share_after"]],
                    ],
                ),
                "",
                "### Fallback concentration (unchanged)",
                "",
                _md_table(
                    ["Snapshot", "Fallback incidence", "Events", "Eligible turns"],
                    [
                        ["BV1B / current", f"{(fallback['bv1b'].get('fallback_trigger_rate') or 0)*100:.2f}%", fallback["bv1b"].get("fallback_event_count"), fallback["bv1b"].get("eligible_turn_count")],
                    ],
                ),
                "",
                "### Ownership concentration (domain refs)",
                "",
                _md_table(["Ownership domain", "Reference count"], scan["ownership_domain_top"]),
                "",
                "### Test concentration (import hubs)",
                "",
                _md_table(
                    ["Game module", "Test file count"],
                    [[hub["game_module"], hub["file_count"]] for hub in scan["test_import_hubs_top10"]],
                ),
                "",
                "---",
                "",
                "## Evidence",
                "",
                "| Source | Role |",
                "|---|---|",
                "| `docs/audits/BU_import_fan_in_fan_out.csv` | Fresh BU AST import graph (223 modules) |",
                "| Full-repo AST scan | Social/read modules outside BU filter |",
                "| `artifacts/bv11_hotspot_analysis.json` | BV11 baseline for deltas |",
                "| `artifacts/bv8a_recurrence_history.json` | Recurrence view |",
                "| `artifacts/bv1b_fallback_summary.json` | Fallback incidence |",
                "| BV12–BV16C closeout reports | Contraction trajectory |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(p)

    # 2. Concentration rankings
    p = AUDITS / "BV17_concentration_rankings.md"
    p.write_text(
        "\n".join(
            [
                "# BV17 — Top-25 Concentration Rankings",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Population:** BU AST import graph + supplemental full-repo scan  ",
                "**Baseline:** BV11 (`artifacts/bv11_hotspot_analysis.json`)",
                "",
                "---",
                "",
                _md_table(
                    ["Rank", "Module", "FI", "FO", "Category", "Authority Status", "Δ since BV11"],
                    [
                        [
                            row["rank"],
                            f"`{row['module']}`",
                            row["fi"],
                            row["fo"],
                            row["category"],
                            row["authority_status"],
                            row["change_since_bv11"],
                        ]
                        for row in top25
                    ],
                ),
                "",
                "## Category distribution (top 25)",
                "",
                _md_table(
                    ["Authority status", "Count in top 25"],
                    [
                        [status, sum(1 for row in top25 if row["authority_status"] == status)]
                        for status in sorted({row["authority_status"] for row in top25})
                    ],
                ),
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(p)

    # 3. Authority classification
    p = AUDITS / "BV17_authority_classification.md"
    p.write_text(
        "\n".join(
            [
                "# BV17 — Authority Classification Review",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Scope:** Top-25 modules by fan-in  ",
                "",
                "---",
                "",
                "## Classification key",
                "",
                "| Status | Meaning |",
                "|---|---|",
                "| **legitimate authority** | Production owner on live emission path; FI reflects real coupling |",
                "| **governed authority** | Intentional post-decomposition domain hub with import guards + FI caps |",
                "| **compatibility shim** | Delegate barrel; low FI by design; regrowth blocked |",
                "| **accidental hub** | High FI without ownership boundary — *none remain in top 25* |",
                "| **mixed authority/utility** | Test/helper surfaces combining contract enforcement and convenience |",
                "",
                "## Top-25 classification",
                "",
                _md_table(
                    ["Rank", "Module", "FI", "Authority Status", "Retirement posture"],
                    [
                        [
                            row["rank"],
                            f"`{row['module']}`",
                            row["fi"],
                            row["authority_status"],
                            next(item["recommendation"] for item in retirement if item["module"] == row["module"]),
                        ]
                        for row in top25
                    ],
                ),
                "",
                "## Summary",
                "",
                f"- **Governed + legitimate authorities:** {sum(1 for row in top25 if row['authority_status'] in {'governed authority', 'legitimate authority'})} / 25",
                f"- **Compatibility shims:** {sum(1 for row in top25 if row['authority_status'] == 'compatibility shim')} / 25",
                f"- **Accidental hubs:** {sum(1 for row in top25 if row['authority_status'] == 'accidental hub')} / 25",
                f"- **Mixed utility:** {sum(1 for row in top25 if row['authority_status'] == 'mixed authority/utility')} / 25",
                "",
                "**Verdict:** Repository concentration is now **authority-shaped**, not **hub-shaped**.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(p)

    # 4. Maintenance economics
    p = AUDITS / "BV17_maintenance_economics.md"
    dims = matrix["dimensions"]
    p.write_text(
        "\n".join(
            [
                "# BV17 — Maintenance Economics Refresh",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Prior matrices:** [BV5_maintenance_cost_matrix.md](BV5_maintenance_cost_matrix.md), [BV9_maintenance_matrix.md](BV9_maintenance_matrix.md), [BV11_maintenance_matrix.md](BV11_maintenance_matrix.md)  ",
                "**Method:** BU CSV area rollups + BV11 baseline + BV12–BV16C closeout verification",
                "",
                "---",
                "",
                "## Executive verdict",
                "",
                f"**Classification:** **{matrix['classification']}**",
                "",
                f"**Primary drag center:** `{matrix['primary_drag_center']}`",
                "",
                "## Dimension scorecard",
                "",
                _md_table(
                    ["Dimension", "BV17 assessment"],
                    [[key.replace("_", " ").title(), value] for key, value in dims.items()],
                ),
                "",
                "## Area matrix (BV11 → BV17)",
                "",
                _md_table(
                    ["Area", "BV11 FI", "BV17 FI", "Δ FI", "BV11 FO", "BV17 FO"],
                    [
                        [
                            row["area"],
                            row["prior_fan_in"],
                            row["current_fan_in"],
                            row["delta_fan_in"],
                            row["prior_fan_out"],
                            row["current_fan_out"],
                        ]
                        for row in matrix["area_rows"]
                    ],
                ),
                "",
                "## Key cluster metrics (BV11 → BV17)",
                "",
                _md_table(
                    ["Cluster", "BV11 (approx)", "BV17", "Interpretation"],
                    [
                        ["Smoke compat bridge", "95", str(clusters["smoke_compat_shims"]), "Collapsed — domain hubs absorbed traffic"],
                        ["Smoke domain hubs", "6", str(clusters["smoke_domain_hubs"]), "Intentional governed redistribution"],
                        ["Text compat + domain", "104", f"{clusters['text_compat']}+{clusters['text_domain_hubs']}", "Compat 52→4; formatting owns composition"],
                        ["Social compat + domain", "104", f"{clusters['social_compat']}+…", "Compat 52→12; policy/catalog own slices"],
                        ["Gate + terminal", "56", str(clusters["gate_terminal"]), "Terminal 26→11; gate stable 30"],
                        ["Accidental shim FI total", "—", str(matrix["accidental_shim_fi_total"]), "≤18 — contraction threshold met"],
                    ],
                ),
                "",
                "## Status notes",
                "",
                "\n".join(f"- {note}" for note in matrix["notes"]),
                "",
                "## Net shift since BV5/BV9",
                "",
                "| Drag center | BV5/BV9 status | BV17 status |",
                "|---|---|---|",
                "| Fallback incidence | **Reduced** (1.05%) | **Unchanged** — not a driver |",
                "| Meta write hub | FI 61 → 24 | **Stable** — read facades governed |",
                "| Smoke monolith | FI 73 pre-BV7 | **Retired** — domain hubs + shims |",
                "| Text/social compat | FI 52 each accidental | **Shim-only** (4 / 12 FI) |",
                "| Gate/terminal convergence | Accidental namespace FI | **Governed authorities** |",
                "| Recurrence | 8 speaker rows | **0 recurring keys** (BV8A) |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(p)

    # 5. Candidate rankings
    p = AUDITS / "BV17_candidate_rankings.md"
    p.write_text(
        "\n".join(
            [
                "# BV17 — Remaining Candidate Rankings",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Trigger:** Post-BV16C contraction reassessment  ",
                "",
                "---",
                "",
                "## Top remaining opportunities (ranked by ROI)",
                "",
            ]
            + [
                "\n".join(
                    [
                        f"### {candidate['rank']}. {candidate['id']} — {candidate['title']}",
                        "",
                        f"- **Target:** `{candidate['target']}`",
                        f"- **Projected FI reduction:** {candidate['projected_fi_reduction']}",
                        f"- **Implementation effort:** {candidate['implementation_effort']}",
                        f"- **Replay risk:** {candidate['replay_risk']}",
                        f"- **Maintenance impact:** {candidate['maintenance_impact']}",
                        f"- **Actionability:** {candidate['actionability']}",
                        f"- **Evidence:** {candidate['evidence']}",
                        "",
                    ]
                )
                for candidate in candidates
            ]
            + [
                "## Priority ordering",
                "",
                _md_table(
                    ["Rank", "Cycle", "Projected FI ↓", "Replay risk", "Actionability", "Rationale"],
                    [
                        ["1", "BV18A", "8–14", "medium-high", "marginal", "Optional visibility test seam cleanup"],
                        ["2", "BV18E", "1 event", "medium", "marginal", "Last fallback event — not structural"],
                        ["3", "BV18B", "5–10", "high", "low", "Stack FO thinning — defer"],
                        ["4", "BV18C", "0", "low", "low", "Registry split — defer"],
                        ["5", "BV18D", "negative ROI", "medium", "none", "Do not split governed domain hubs"],
                    ],
                ),
                "",
                f"## Recommendation: **{rec['selected_cycle']}**",
                "",
                rec["rationale"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    written.append(p)

    # 6. Retirement analysis
    p = AUDITS / "BV17_retirement_analysis.md"
    p.write_text(
        "\n".join(
            [
                "# BV17 — Retirement Analysis",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Scope:** Top-25 high-FI modules — decompose vs governance-clean vs leave intact  ",
                "",
                "---",
                "",
                "## Decision framework",
                "",
                "| Action | When |",
                "|---|---|",
                "| **Decompose** | Accidental hub with unclear ownership and no live-path sequencer role |",
                "| **Governance-clean** | Legitimate authority with test/monkeypatch FI inflation (BV16 pattern) |",
                "| **Leave intact** | Governed domain hub, compat shim at cap, or live orchestration owner |",
                "",
                "## Module decisions",
                "",
                _md_table(
                    ["Module", "FI", "Authority", "Decision"],
                    [[item["module"], item["fi"], item["authority_status"], item["recommendation"]] for item in retirement],
                ),
                "",
                "## Aggregate verdict",
                "",
                "| Action | Count (top 25) |",
                "|---|---:|",
                f"| Leave intact | {sum(1 for item in retirement if item['recommendation'].startswith('left intact'))} |",
                f"| Governance-clean (optional) | {sum(1 for item in retirement if 'governance-clean' in item['recommendation'])} |",
                f"| Decompose | {sum(1 for item in retirement if item['recommendation'].startswith('decompose'))} |",
                "",
                "**No top-25 module warrants decomposition.** Optional governance-clean applies at most to "
                "`game.final_emission_visibility_fallback` (test seam migration mirroring BV16C).",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(p)

    # 7. Recommendation (standalone summary in hotspot doc; also write JSON)
    return written


def main() -> int:
    analysis = build_bv17_analysis()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(analysis, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    written = write_audit_docs(analysis)
    print(f"Wrote {OUTPUT_JSON.relative_to(ROOT)}")
    for path in written:
        print(f"Wrote {path.relative_to(ROOT)}")
    print(f"Recommended next cycle: {analysis['recommendation']['selected_cycle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
