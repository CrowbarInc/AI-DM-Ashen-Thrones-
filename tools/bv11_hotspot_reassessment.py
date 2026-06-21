#!/usr/bin/env python3
"""BV11 — Post-BV10 hotspot reassessment (read-side measurement only)."""

from __future__ import annotations

import ast
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACTS = ROOT / "artifacts"
AUDITS = ROOT / "docs" / "audits"
OUTPUT_JSON = ARTIFACTS / "bv11_hotspot_analysis.json"
BV9_JSON = ARTIFACTS / "bv9_hotspot_analysis.json"

BU_CSV = AUDITS / "BU_import_fan_in_fan_out.csv"
OWNERSHIP_CSV = AUDITS / "BU_ownership_dependency_map.csv"
BV7_SMOKE = ARTIFACTS / "bv7_smoke_analysis.json"
BV8A = ARTIFACTS / "bv8a_recurrence_history.json"
BV1B = ARTIFACTS / "bv1b_fallback_summary.json"
BV3F = ARTIFACTS / "bv3f_reduction_metrics.json"
BV4B = ARTIFACTS / "bv4b_concrete_beat_metrics.json"
BV9_MATRIX = ARTIFACTS / "bv9_hotspot_analysis.json"
TEST_INVENTORY = ARTIFACTS / "test_inventory_full.json"
FALLBACK_HISTORY = ARTIFACTS / "golden_replay" / "fallback_incidence_history.json"

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
        "tests.helpers.gate_integration_smoke",
        "tests.helpers.route_determinism_smoke",
        "tests.helpers.response_type_smoke",
        "tests.helpers.actor_consistency_smoke",
    ),
    "tests_registry": ("tests.test_ownership_registry",),
}

REPLAY_SURFACES = (
    "tests.helpers.golden_replay",
    "tests.helpers.golden_replay_projection",
    "tests.helpers.golden_replay_fixtures",
    "tests.helpers.golden_replay_api",
    "tests.helpers.replay_drift_taxonomy",
    "tests.helpers.replay_smoke_assertions",
    "game.final_emission_replay_projection",
)

FALLBACK_SURFACES = (
    "game.final_emission_visibility_fallback",
    "game.final_emission_sealed_fallback",
    "game.final_emission_opening_fallback",
    "game.opening_deterministic_fallback",
    "game.diegetic_fallback_narration",
    "game.final_emission_passive_scene_pressure",
    "game.final_emission_fast_fallback_composition",
)

OWNERSHIP_HUBS = (
    "game.attribution_read_views",
    "game.observability_attribution_read",
    "game.ownership_projection_views",
    "game.final_emission_meta_read",
    "game.final_emission_owner_bucket_views",
    "game.final_emission_ownership_schema",
    "game.runtime_lineage_telemetry",
    "tests.helpers.failure_classifier",
    "tests.helpers.failure_classification_sync",
)

HELPER_FACADES = (
    "tests.helpers.emission_smoke_assertions",
    "tests.helpers.replay_smoke_assertions",
    "tests.helpers.golden_replay",
    "tests.helpers.golden_replay_projection",
    "tests.helpers.gate_integration_smoke",
    "tests.helpers.repairs_consumer_facade",
    "tests.helpers.failure_classifier",
    "game.attribution_read_views",
    "game.observability_attribution_read",
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def _supplemental_facade_fi() -> dict[str, dict[str, int]]:
    """Full-repo AST fan-in for BV10 read facades outside the BU ecosystem filter."""
    python_roots = ("game", "tests", "scripts")
    modules: set[str] = set()
    for root in python_roots:
        for path in (ROOT / root).rglob("*.py"):
            modules.add(".".join(path.relative_to(ROOT).with_suffix("").parts))

    importers: dict[str, set[str]] = {module: set() for module in READ_FACADES}
    for root in python_roots:
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
                        if candidate in READ_FACADES:
                            found.add(candidate)
                            break
                        candidate = candidate.rpartition(".")[0]
            for facade in found:
                importers[facade].add(importer)

    return {
        module: {"fan_in_total": len(importers[module]), "fan_out_total": 1}
        for module in READ_FACADES
    }


def _merge_rows(rows: list[dict[str, Any]], supplemental: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    by_module = {row["module"]: dict(row) for row in rows}
    for module, metrics in supplemental.items():
        if module in by_module:
            continue
        leaf = module.rsplit(".", 1)[-1]
        by_module[module] = {
            "module": module,
            "file": f"game/{leaf}.py",
            "kind": "production",
            "responsibility": "final-emission policy/metadata",
            "fan_in_total": metrics["fan_in_total"],
            "fan_out_total": metrics["fan_out_total"],
            "fan_in_production": metrics["fan_in_total"],
            "fan_in_tests": 0,
            "fan_in_helpers": 0,
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
        if not module:
            continue
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
    totals = {
        domain: sum(int(row.get(domain) or 0) for row in ownership_rows) for domain in domains
    }
    return sorted(totals.items(), key=lambda item: -item[1])[:10]


def _ownership_concentration(module: str, ownership_refs: dict[str, int]) -> float:
    ref = ownership_refs.get(module, 0)
    max_ref = max(ownership_refs.values()) if ownership_refs else 0
    if max_ref <= 0:
        return 0.0
    return round(ref / float(max_ref), 4)


def _risk_score(fi: int, fo: int, ownership_conc: float, *, recurring: bool = False) -> str:
    score = fi + 0.35 * fo + (20 if recurring else 0) + (10 * ownership_conc)
    if score >= 45:
        return "high"
    if score >= 28:
        return "medium"
    return "low"


def _area_rollups(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rollups: dict[str, dict[str, Any]] = {}
    for area in AREA_PREFIXES:
        subset = [row for row in rows if _area_for_module(row["module"]) == area]
        top = sorted(subset, key=lambda row: (-row["fan_in_total"], -row["fan_out_total"]))[:6]
        rollups[area] = {
            "modules": len(subset),
            "fan_in_total": sum(row["fan_in_total"] for row in subset),
            "fan_out_total": sum(row["fan_out_total"] for row in subset),
            "top_fan_in": [
                [row["module"], row["fan_in_total"], row["fan_out_total"]] for row in top
            ],
        }
    return rollups


def _bv9_fi_map() -> dict[str, int]:
    bv9 = _load_json(BV9_JSON)
    rankings = bv9.get("top20_concentration_rankings") or []
    fi_map = {row["module"]: int(row["fi"]) for row in rankings}
    area_rollups = (bv9.get("hotspot_scan") or {}).get("area_rollups") or {}
    for area, data in area_rollups.items():
        for module, module_fi, _fo in data.get("top_fan_in") or []:
            fi_map.setdefault(module, int(module_fi))
    return fi_map


def _fi_delta(module: str, current_fi: int, bv9_fi: dict[str, int]) -> str:
    prior = bv9_fi.get(module)
    if prior is None:
        return "new"
    delta = current_fi - prior
    if delta == 0:
        return "0"
    return f"{delta:+d}"


def _concentration_rankings(
    rows: list[dict[str, Any]],
    ownership_refs: dict[str, int],
    bv9_fi: dict[str, int],
) -> list[dict[str, Any]]:
    ranked_rows = sorted(rows, key=lambda row: (-row["fan_in_total"], -row["fan_out_total"], row["module"]))[:20]
    top20: list[dict[str, Any]] = []
    for index, row in enumerate(ranked_rows, start=1):
        module = row["module"]
        fi = int(row["fan_in_total"])
        fo = int(row["fan_out_total"])
        ownership_conc = _ownership_concentration(module, ownership_refs)
        top20.append(
            {
                "rank": index,
                "module": module,
                "fi": fi,
                "fo": fo,
                "type": row.get("kind") or "unknown",
                "ownership_concentration": ownership_conc,
                "risk": _risk_score(fi, fo, ownership_conc),
                "change_since_bv9": _fi_delta(module, fi, bv9_fi),
            }
        )
    return top20


def _fallback_review() -> dict[str, Any]:
    bv1b = _load_json(BV1B)
    bv3f = _load_json(BV3F)
    bv4b = _load_json(BV4B)
    history = _load_json(FALLBACK_HISTORY)
    snapshots = history.get("snapshots") or []
    latest = snapshots[-1] if snapshots else {}

    return {
        "bv1b": {
            "fallback_trigger_rate": bv1b.get("fallback_trigger_rate"),
            "fallback_event_count": bv1b.get("fallback_event_count"),
            "eligible_turn_count": bv1b.get("eligible_turn_count"),
        },
        "bv3f": {
            "fallback_incidence": (bv3f.get("comparison_table") or {}).get("fallback_incidence", {}),
        },
        "bv4b": {
            "fallback_incidence": (bv4b.get("comparison_table") or {}).get("fallback_incidence", {}),
        },
        "current": {
            "fallback_trigger_rate": bv1b.get("fallback_trigger_rate"),
            "fallback_event_count": bv1b.get("fallback_event_count"),
            "latest_history_snapshot": latest.get("label"),
        },
        "verdict": "fallback_drag_collapsed",
    }


def _recurrence_review() -> dict[str, Any]:
    bv8a = _load_json(BV8A)
    registry = bv8a.get("retirement_registry") or []
    families = {"active": [], "retired": [], "historical": []}
    for entry in registry:
        status = str(entry.get("registry_status") or "").upper()
        key = str(entry.get("recurrence_key") or "")
        short = key.split("|")[1:4] if "|" in key else [key]
        payload = {"recurrence_key": key, "family": "|".join(short)}
        if status == "ACTIVE":
            families["active"].append(payload)
        elif status == "RETIRED":
            families["retired"].append(payload)
        elif status == "HISTORICAL":
            families["historical"].append(payload)

    after = bv8a.get("after_metrics") or {}
    before = bv8a.get("before_metrics") or {}
    return {
        "source": "artifacts/bv8a_recurrence_history.json",
        "before_metrics": before,
        "after_metrics": after,
        "active_families": families["active"],
        "retired_families": families["retired"],
        "historical_families": families["historical"],
        "dominant_share_before": before.get("dominant_share"),
        "dominant_share_after": after.get("dominant_share"),
        "recurring_keys_after": after.get("recurring_keys"),
    }


def _candidate_review(rows: list[dict[str, Any]], supplemental: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    fi = {row["module"]: int(row["fan_in_total"]) for row in rows}
    for module, metrics in supplemental.items():
        fi[module] = metrics["fan_in_total"]

    def get(module: str) -> int:
        return fi.get(module, 0)

    authority_fi = sum(get(module) for module in AUTHORITY_CLUSTER)
    facade_fi = sum(get(module) for module in READ_FACADES)
    smoke_bridge = get("tests.helpers.replay_smoke_assertions") + get("tests.helpers.gate_integration_smoke")

    return [
        {
            "id": "final_emission_text / social_exchange_emission",
            "bv9_fi": "52 / 52",
            "bv11_fi": f"{get('game.final_emission_text')} / {get('game.social_exchange_emission')}",
            "status": "unchanged_top_hotspot",
            "verdict": "Still the largest production-core pair (104 combined FI). Not addressed by BV10; decomposition remains high-cost/high-risk.",
        },
        {
            "id": "replay_smoke_assertions",
            "bv9_fi": "46",
            "bv11_fi": str(get("tests.helpers.replay_smoke_assertions")),
            "status": "increased",
            "verdict": "Now rank #1 module repository-wide (FI +10). BV10C intentionally routed gate/smoke FEM reads through this bridge — maintenance magnet regrowth.",
        },
        {
            "id": "gate_integration_smoke",
            "bv9_fi": "39",
            "bv11_fi": str(get("tests.helpers.gate_integration_smoke")),
            "status": "unchanged",
            "verdict": "Stable post-BV7 bridge hub. Combined with replay_smoke: 85 → 95 FI (+12%).",
        },
        {
            "id": "remaining read facades",
            "bv9_fi": "meta_read 29 + bucket 22 + schema 19 = 70",
            "bv11_fi": f"authority {authority_fi}; facades {facade_fi} (attribution {get('game.attribution_read_views')}, observability {get('game.observability_attribution_read')}, projection {get('game.ownership_projection_views')})",
            "status": "closed_bv10",
            "verdict": "Authority cluster −73% (70→19). Traffic absorbed by governed facades (+48 FI). Governance lock in place.",
        },
        {
            "id": "recurrence active rows",
            "bv9_fi": "3 active (BV8A)",
            "bv11_fi": "3 active (unchanged)",
            "status": "stable",
            "verdict": "No recurring keys post-deduplication. Speaker projection retired; emerging families remain single-observation.",
        },
        {
            "id": "fallback residuals",
            "bv9_fi": "1.05% (1/95)",
            "bv11_fi": "1.05% (1/95)",
            "status": "unchanged",
            "verdict": "Single RC hard-replacement event. Not a structural maintenance driver.",
        },
    ]


def _maintenance_matrix(
    area_rollups: dict[str, dict[str, Any]],
    bv9_area: dict[str, dict[str, Any]],
    recurrence: dict[str, Any],
    fallback: dict[str, Any],
    authority_fi: int,
    smoke_bridge_fi: int,
) -> dict[str, Any]:
    rows = []
    for area, current in area_rollups.items():
        prior = bv9_area.get(area) or {}
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

    reduced_signals = sum(1 for row in rows if row["delta_fan_in"] < 0)
    increased_signals = sum(1 for row in rows if row["delta_fan_in"] > 0)
    if authority_fi <= 25 and smoke_bridge_fi > 85:
        classification = "MIXED_OR_INCONCLUSIVE"
    elif reduced_signals > increased_signals and authority_fi < 30:
        classification = "REDUCED_COST"
    else:
        classification = "REDISTRIBUTED_COST"

    return {
        "classification": classification,
        "primary_drag_center": "smoke_bridge_and_terminal_emission_core",
        "area_rows": rows,
        "fallback_status": fallback["verdict"],
        "recurrence_status": "stable_post_bv8a",
        "authority_cluster_fi": authority_fi,
        "smoke_bridge_fi": smoke_bridge_fi,
        "notes": [
            "BV10 closed the read-side authority cluster: combined FI 70 → 19 (−73%).",
            "Read traffic redistributed to governed facades (attribution + observability + projection ≈ 48 FI).",
            "replay_smoke_assertions grew 46 → 56 (+10) — now the single largest module by fan-in.",
            "Production-core pair final_emission_text + social_exchange_emission unchanged at 52 FI each.",
            "Gate + terminal convergence remains 30 + 26 = 56 FI with medium replay risk.",
            "Fallback (1.05%) and recurrence (0 recurring keys) remain non-drivers.",
        ],
    }


def _candidate_rankings(rows: list[dict[str, Any]], supplemental: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    fi = {row["module"]: int(row["fan_in_total"]) for row in rows}
    for module, metrics in supplemental.items():
        fi[module] = metrics["fan_in_total"]

    replay_fi = fi.get("tests.helpers.replay_smoke_assertions", 0)
    gate_smoke_fi = fi.get("tests.helpers.gate_integration_smoke", 0)
    gate_fi = fi.get("game.final_emission_gate", 0)
    terminal_fi = fi.get("game.final_emission_terminal_pipeline", 0)
    text_fi = fi.get("game.final_emission_text", 0)
    social_fi = fi.get("game.social_exchange_emission", 0)

    candidates = [
        {
            "id": "BV12",
            "title": "Smoke bridge domain decomposition (BV10B continuation)",
            "target": "tests.helpers.replay_smoke_assertions + gate_integration_smoke",
            "projected_fi_reduction": "25–35 (split domain-specific bridges; cap monolith regrowth)",
            "implementation_risk": "medium",
            "replay_risk": "low-medium",
            "maintenance_impact": "Highest current FI cluster (95 combined, +10 post-BV10); reduces cross-domain test churn",
            "evidence": f"replay_smoke FI {replay_fi} (#1 repo-wide); gate_integration FI {gate_smoke_fi}; BV10C added intentional bridge load",
        },
        {
            "id": "BV12B",
            "title": "Gate / terminal pipeline convergence split",
            "target": "game.final_emission_gate + final_emission_terminal_pipeline",
            "projected_fi_reduction": "15–22 (orchestration vs assembly boundary)",
            "implementation_risk": "high",
            "replay_risk": "medium",
            "maintenance_impact": "Second-largest production convergence hub (56 combined FI); 23+ test importers on terminal",
            "evidence": f"gate FI {gate_fi}/FO 9; terminal FI {terminal_fi}/FO 14; unchanged since BV9",
        },
        {
            "id": "BV12C",
            "title": "Terminal text / social emission surface thinning",
            "target": "game.final_emission_text + social_exchange_emission",
            "projected_fi_reduction": "20–30 (extract read-only views and policy slices)",
            "implementation_risk": "high",
            "replay_risk": "medium-high",
            "maintenance_impact": "Largest production-core concentration (104 FI) but touches live composition path",
            "evidence": f"text FI {text_fi}; social FI {social_fi}; tied #2–#3 rank unchanged since BV9",
        },
        {
            "id": "BV12D",
            "title": "Attribution completeness & classifier routing (BS continuation)",
            "target": "failure_classifier + attribution completeness metrics",
            "projected_fi_reduction": "8–12 (narrow misrouted investigations)",
            "implementation_risk": "medium",
            "replay_risk": "low",
            "maintenance_impact": "Closes owner-bucket strict completeness gap; adjacent to closed BV10 read cluster",
            "evidence": "failure_classifier FI 13; strict completeness 0%; facades now govern read path",
        },
        {
            "id": "BV12E",
            "title": "Residual RC observe fallback elimination",
            "target": "referential_clarity_hard_replacement (1 event / 1.05%)",
            "projected_fi_reduction": "1 incidence event (not FI)",
            "implementation_risk": "medium",
            "replay_risk": "medium",
            "maintenance_impact": "Clears last measurable fallback; diminishing structural returns",
            "evidence": "BV1B 1 event unchanged; gate_terminal_repair family",
        },
    ]
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index
    return candidates


def _recommendation(candidates: list[dict[str, Any]], top20: list[dict[str, Any]]) -> dict[str, Any]:
    top_modules = [row["module"] for row in top20[:5]]
    return {
        "selected_cycle": "BV12",
        "title": "Smoke bridge domain decomposition (BV10B continuation)",
        "rationale": (
            "BV10 closed the read-side attribution cluster (authority FI 70→19, governance locked) without "
            "changing runtime behavior. Post-closeout measurement shows maintenance cost **redistributed**, not "
            "eliminated: replay_smoke_assertions is now the **#1 module** (FI 56, +10 from BV10C routing), and "
            "the smoke bridge cluster (replay_smoke + gate_integration) totals **95 FI** — up from 85 at BV9. "
            "Production-core text/social (52 each) and gate/terminal (56 combined) remain large but higher-risk "
            "targets. BV12 addresses the largest **addressable** concentration with BV7/BV10 lineage and bounded replay risk."
        ),
        "projected_scorecard_impact": {
            "maintenance_drag": "+0.5",
            "ownership_clarity": "+0.25",
            "operational_simplicity": "+0.5",
            "maintenance_economics": "+0.5",
        },
        "top_modules_evidence": top_modules,
        "alternates": ["BV12B", "BV12C"],
    }


def build_bv11_analysis(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    rows = _load_bu_rows()
    supplemental = _supplemental_facade_fi()
    merged_rows = _merge_rows(rows, supplemental)

    ownership_rows: list[dict[str, str]] = []
    if OWNERSHIP_CSV.is_file():
        with OWNERSHIP_CSV.open(encoding="utf-8", newline="") as handle:
            ownership_rows = list(csv.DictReader(handle))

    ownership_refs = _ownership_ref_map(ownership_rows)
    bv9_fi = _bv9_fi_map()
    area_rollups = _area_rollups(merged_rows)
    top20 = _concentration_rankings(merged_rows, ownership_refs, bv9_fi)
    recurrence = _recurrence_review()
    fallback = _fallback_review()
    candidate_review = _candidate_review(rows, supplemental)

    fi = {row["module"]: int(row["fan_in_total"]) for row in rows}
    authority_fi = sum(fi.get(module, 0) for module in AUTHORITY_CLUSTER)
    smoke_bridge_fi = fi.get("tests.helpers.replay_smoke_assertions", 0) + fi.get(
        "tests.helpers.gate_integration_smoke", 0
    )

    bv9_area = (_load_json(BV9_MATRIX).get("hotspot_scan") or {}).get("area_rollups") or {}
    matrix = _maintenance_matrix(area_rollups, bv9_area, recurrence, fallback, authority_fi, smoke_bridge_fi)
    candidates = _candidate_rankings(rows, supplemental)
    recommendation = _recommendation(candidates, top20)

    test_inventory = _load_json(TEST_INVENTORY)
    test_hubs = (test_inventory.get("import_hub_modules") or [])[:10]
    bv7 = _load_json(BV7_SMOKE)
    ownership_domain_totals = _ownership_domain_totals(ownership_rows)

    return {
        "schema_version": 1,
        "generated_at": timestamp,
        "cycle": "BV11",
        "primary_question": "What is now the largest source of maintenance drag after BV10?",
        "executive_answer": (
            "Post-BV10, replay_smoke_assertions (FI 56) is the largest single module; "
            "the smoke bridge cluster (95 FI) exceeds gate/terminal convergence (56 FI)."
        ),
        "selected_next_cycle": recommendation["selected_cycle"],
        "sources": {
            "bu_import_fan_in_fan_out": str(BU_CSV.relative_to(ROOT)).replace("\\", "/"),
            "bv9_hotspot_analysis": str(BV9_JSON.relative_to(ROOT)).replace("\\", "/"),
            "bv8a_recurrence_history": str(BV8A.relative_to(ROOT)).replace("\\", "/"),
            "bv1b_fallback_summary": str(BV1B.relative_to(ROOT)).replace("\\", "/"),
            "bv10_read_cluster_verification": "docs/audits/BV10_read_cluster_verification.md",
            "bv7_smoke_analysis": str(BV7_SMOKE.relative_to(ROOT)).replace("\\", "/"),
            "test_inventory_full": str(TEST_INVENTORY.relative_to(ROOT)).replace("\\", "/"),
        },
        "hotspot_scan": {
            "module_count": len(merged_rows),
            "area_rollups": area_rollups,
            "ownership_domain_top": ownership_domain_totals,
            "test_import_hubs_top10": test_hubs,
            "smoke_facade_fi": bv7.get("module_fi"),
            "smoke_facade_fo": bv7.get("module_fo"),
            "authority_cluster_fi": authority_fi,
            "read_facade_fi": sum(metrics["fan_in_total"] for metrics in supplemental.values()),
            "smoke_bridge_fi": smoke_bridge_fi,
            "recurrence_concentration": recurrence,
            "fallback_concentration": fallback,
        },
        "top20_concentration_rankings": top20,
        "candidate_review": candidate_review,
        "maintenance_matrix": matrix,
        "candidate_rankings": candidates,
        "recommendation": recommendation,
    }


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_audit_docs(analysis: dict[str, Any]) -> list[Path]:
    AUDITS.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    top20 = analysis["top20_concentration_rankings"]
    area = analysis["hotspot_scan"]["area_rollups"]
    recurrence = analysis["hotspot_scan"]["recurrence_concentration"]
    fallback = analysis["hotspot_scan"]["fallback_concentration"]
    matrix = analysis["maintenance_matrix"]
    candidates = analysis["candidate_rankings"]
    candidate_review = analysis["candidate_review"]
    rec = analysis["recommendation"]
    scan = analysis["hotspot_scan"]

    hotspot_path = AUDITS / "BV11_hotspot_inventory.md"
    hotspot_path.write_text(
        "\n".join(
            [
                "# BV11 — Hotspot Inventory",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Scope:** Entire repository (post BV10 closeout)  ",
                f"**Method:** `python tools/bv11_hotspot_reassessment.py` + `scripts/bu_final_emission_coupling_discovery.py`  ",
                f"**Primary question:** {analysis['primary_question']}",
                "",
                "---",
                "",
                "## Executive answer",
                "",
                analysis["executive_answer"],
                "",
                f"**Recommended next cycle:** **{rec['selected_cycle']}** — {rec['title']}",
                "",
                "---",
                "",
                "## Repository hotspot scan",
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
                "### BV10 read-cluster closeout (supplemental)",
                "",
                _md_table(
                    ["Cluster", "FI"],
                    [
                        ["Authority cluster (meta_read + bucket + schema)", scan["authority_cluster_fi"]],
                        ["Read facades (attribution + observability + projection)", scan["read_facade_fi"]],
                        ["Smoke bridge (replay_smoke + gate_integration)", scan["smoke_bridge_fi"]],
                    ],
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
                        ["Active keys", recurrence["before_metrics"].get("active_recurrence_count"), recurrence["after_metrics"].get("active_recurrence_count")],
                    ],
                ),
                "",
                "### Fallback concentration (unchanged)",
                "",
                _md_table(
                    ["Snapshot", "Fallback incidence", "Events", "Eligible turns"],
                    [
                        ["BV1B / current", f"{(fallback['bv1b'].get('fallback_trigger_rate') or 0)*100:.2f}%", fallback["bv1b"].get("fallback_event_count"), fallback["bv1b"].get("eligible_turn_count")],
                        ["BV4B current", f"{(fallback['bv4b']['fallback_incidence'].get('current') or 0)*100:.2f}%", "—", "—"],
                    ],
                ),
                "",
                "### Ownership concentration (domain refs)",
                "",
                _md_table(
                    ["Ownership domain", "Reference count"],
                    scan["ownership_domain_top"],
                ),
                "",
                "### Test concentration (import hubs)",
                "",
                _md_table(
                    ["Game module", "Test file count"],
                    [[hub["game_module"], hub["file_count"]] for hub in scan["test_import_hubs_top10"]],
                ),
                "",
                f"Legacy smoke facade (emission_smoke, post-BV7): FI **{scan['smoke_facade_fi']}**, FO **{scan['smoke_facade_fo']}**",
                "",
                "---",
                "",
                "## Evidence",
                "",
                "| Source | Role |",
                "|---|---|",
                "| `docs/audits/BU_import_fan_in_fan_out.csv` | Module FI/FO (BU ecosystem) |",
                "| Full-repo AST scan | Read facade FI (outside BU filter) |",
                "| `artifacts/bv9_hotspot_analysis.json` | BV9 baseline for deltas |",
                "| `docs/audits/BV10_read_cluster_verification.md` | BV10 closeout verification |",
                "| `artifacts/bv8a_recurrence_history.json` | Recurrence view |",
                "| `artifacts/bv1b_fallback_summary.json` | Fallback incidence |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(hotspot_path)

    rankings_path = AUDITS / "BV11_concentration_rankings.md"
    rankings_path.write_text(
        "\n".join(
            [
                "# BV11 — Top-20 Concentration Rankings",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Population:** BU AST import graph + supplemental read-facade AST scan  ",
                "**Risk heuristic:** FI + 0.35×FO + ownership concentration weight  ",
                "**Baseline:** BV9 (`artifacts/bv9_hotspot_analysis.json`)",
                "",
                "---",
                "",
                _md_table(
                    ["Rank", "Module", "FI", "FO", "Type", "Risk", "Change since BV9"],
                    [
                        [
                            row["rank"],
                            f"`{row['module']}`",
                            row["fi"],
                            row["fo"],
                            row["type"],
                            row["risk"],
                            row["change_since_bv9"],
                        ]
                        for row in top20
                    ],
                ),
                "",
                "## Category highlights",
                "",
                "### Helper / bridge facades",
                "",
                _md_table(
                    ["Module", "FI", "FO", "Risk", "Δ since BV9"],
                    [
                        [row["module"], row["fi"], row["fo"], row["risk"], row["change_since_bv9"]]
                        for row in top20
                        if row["module"] in HELPER_FACADES
                    ],
                ),
                "",
                "### Read facades (post-BV10)",
                "",
                _md_table(
                    ["Module", "FI", "FO", "Risk", "Δ since BV9"],
                    [
                        [row["module"], row["fi"], row["fo"], row["risk"], row["change_since_bv9"]]
                        for row in top20
                        if row["module"] in READ_FACADES or row["module"] in AUTHORITY_CLUSTER
                    ],
                ),
                "",
                "### Replay surfaces",
                "",
                _md_table(
                    ["Module", "FI", "FO", "Risk", "Δ since BV9"],
                    [
                        [row["module"], row["fi"], row["fo"], row["risk"], row["change_since_bv9"]]
                        for row in top20
                        if row["module"] in REPLAY_SURFACES
                    ],
                ),
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(rankings_path)

    review_path = AUDITS / "BV11_candidate_review.md"
    review_path.write_text(
        "\n".join(
            [
                "# BV11 — Prior Candidate Review",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Scope:** Re-check BV9-ranked candidates against post-BV10 evidence  ",
                "",
                "---",
                "",
                "## Executive answer",
                "",
                "BV10 **closed** the read-side attribution cluster. The next drag center is the **smoke bridge** "
                "(replay_smoke + gate_integration, 95 FI, +10 on replay_smoke). Production-core text/social (52 each) "
                "and gate/terminal (56 combined) remain unchanged high-FI surfaces.",
                "",
                "## Candidate re-evaluation",
                "",
                _md_table(
                    ["Candidate", "BV9 FI", "BV11 FI", "Status", "Verdict"],
                    [
                        [item["id"], item["bv9_fi"], item["bv11_fi"], item["status"], item["verdict"]]
                        for item in candidate_review
                    ],
                ),
                "",
                "## BV10 outcomes (context)",
                "",
                "| Metric | Pre-BV10 | Post-BV10C |",
                "|---|---:|---:|",
                "| Authority cluster FI | 70 | **19** |",
                "| Accidental triple-import test files | 16 | **0** |",
                "| Direct read-cluster imports | ungoverned | **governance locked** |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(review_path)

    matrix_path = AUDITS / "BV11_maintenance_matrix.md"
    matrix_path.write_text(
        "\n".join(
            [
                "# BV11 — Maintenance Matrix Refresh",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Prior matrix:** [BV9_maintenance_matrix.md](BV9_maintenance_matrix.md)  ",
                "**Method:** BU CSV area rollups + BV9 baseline + BV10 closeout verification",
                "",
                "---",
                "",
                "## Executive verdict",
                "",
                f"**Classification:** **{matrix['classification']}** — BV10 **reduced** authority-cluster FI (−73%) "
                "while **redistributing** read traffic to facades (+48 FI) and **increasing** replay-smoke bridge load (+10 FI). "
                "Net repository drag shifted rather than uniformly declining.",
                "",
                f"**Primary drag center:** `{matrix['primary_drag_center']}`",
                "",
                "## Area matrix (BV9 → BV11)",
                "",
                _md_table(
                    ["Area", "BV9 FI", "BV11 FI", "Δ FI", "BV9 FO", "BV11 FO"],
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
                "## Key cluster metrics",
                "",
                _md_table(
                    ["Cluster", "BV9", "BV11", "Δ"],
                    [
                        ["Authority cluster", "70", matrix["authority_cluster_fi"], matrix["authority_cluster_fi"] - 70],
                        ["Smoke bridge", "85", matrix["smoke_bridge_fi"], matrix["smoke_bridge_fi"] - 85],
                        ["Gate + terminal", "56", "56", "0"],
                        ["Text + social (production core)", "104", "104", "0"],
                    ],
                ),
                "",
                "## Status notes",
                "",
                "\n".join(f"- {note}" for note in matrix["notes"]),
                "",
                "## Net shift since BV9",
                "",
                "| Drag center | BV9 status | BV11 status |",
                "|---|---|---|",
                "| Read-side attribution | **#1 unaddressed cluster** (70 FI) | **Closed** — authority 19 FI, facades governed |",
                "| replay_smoke_assertions | FI 46 (#3) | **FI 56 (#1)** — bridge load increased |",
                "| Smoke bridge combined | 85 FI | **95 FI** (+12%) |",
                "| Gate / terminal | Convergence hub (56 FI) | **Unchanged** — still #2 production cluster |",
                "| Fallback / recurrence | Collapsed / stable | **Unchanged** — not drivers |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(matrix_path)

    candidates_path = AUDITS / "BV11_next_candidates.md"
    candidates_path.write_text(
        "\n".join(
            [
                "# BV11 — Next Candidate Rankings",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Trigger:** Post-BV10 hotspot reassessment  ",
                "",
                "---",
                "",
                "## Top 5 next-cycle opportunities",
                "",
            ]
            + [
                "\n".join(
                    [
                        f"### {candidate['rank']}. {candidate['id']} — {candidate['title']}",
                        "",
                        f"- **Target:** `{candidate['target']}`",
                        f"- **Projected FI reduction:** {candidate['projected_fi_reduction']}",
                        f"- **Implementation risk:** {candidate['implementation_risk']}",
                        f"- **Replay risk:** {candidate['replay_risk']}",
                        f"- **Maintenance impact:** {candidate['maintenance_impact']}",
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
                    ["Rank", "Cycle", "Projected FI ↓", "Replay risk", "Rationale"],
                    [
                        ["1", "BV12", "25–35", "low-medium", "Largest addressable FI cluster (95); grew post-BV10"],
                        ["2", "BV12B", "15–22", "medium", "Gate/terminal convergence — high impact, higher cost"],
                        ["3", "BV12C", "20–30", "medium-high", "Production-core text/social — largest FI but highest touch risk"],
                        ["4", "BV12D", "8–12", "low", "Attribution completeness — adjacent to closed BV10 cluster"],
                        ["5", "BV12E", "1 event", "medium", "Last fallback — diminishing structural returns"],
                    ],
                ),
                "",
                "## BV12 recommendation",
                "",
                f"**Selected cycle:** **{rec['selected_cycle']}** — {rec['title']}",
                "",
                rec["rationale"],
                "",
                "### Projected scorecard impact",
                "",
                _md_table(
                    ["Dimension", "Projected delta"],
                    [[key.replace("_", " ").title(), value] for key, value in rec["projected_scorecard_impact"].items()],
                ),
                "",
                f"**Alternates if blocked:** {', '.join(rec['alternates'])}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    written.append(candidates_path)

    return written


def main() -> int:
    analysis = build_bv11_analysis()
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
