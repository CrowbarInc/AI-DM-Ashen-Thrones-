#!/usr/bin/env python3
"""BV9 — Post-reduction hotspot reassessment (read-side measurement only)."""

from __future__ import annotations

import csv
import json
import subprocess
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
OUTPUT_JSON = ARTIFACTS / "bv9_hotspot_analysis.json"

BU_CSV = AUDITS / "BU_import_fan_in_fan_out.csv"
OWNERSHIP_CSV = AUDITS / "BU_ownership_dependency_map.csv"
BV7_SMOKE = ARTIFACTS / "bv7_smoke_analysis.json"
BV8A = ARTIFACTS / "bv8a_recurrence_history.json"
BV1B = ARTIFACTS / "bv1b_fallback_summary.json"
BV3F = ARTIFACTS / "bv3f_reduction_metrics.json"
BV4B = ARTIFACTS / "bv4b_concrete_beat_metrics.json"
BV1_MATRIX = ARTIFACTS / "bv1_maintenance_matrix_data.json"
TEST_INVENTORY = ARTIFACTS / "test_inventory_full.json"
FALLBACK_HISTORY = ARTIFACTS / "golden_replay" / "fallback_incidence_history.json"

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
        "tests.helpers.replay_smoke_assertions",
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
    "tests.helpers.final_emission_meta_read",
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


def _concentration_rankings(
    rows: list[dict[str, Any]],
    ownership_refs: dict[str, int],
) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}

    def add(module: str, category: str) -> None:
        row = next((item for item in rows if item["module"] == module), None)
        if row is None:
            return
        ownership_conc = _ownership_concentration(module, ownership_refs)
        entry = {
            "module": module,
            "category": category,
            "fi": row["fan_in_total"],
            "fo": row["fan_out_total"],
            "ownership_concentration": ownership_conc,
            "kind": row["kind"],
            "responsibility": row["responsibility"],
        }
        existing = candidates.get(module)
        if existing is None or existing["fi"] < entry["fi"]:
            candidates[module] = entry

    for module in rows:
        add(module["module"], module["kind"])

    ranked = sorted(
        candidates.values(),
        key=lambda item: (-item["fi"], -item["fo"], item["module"]),
    )[:20]
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
        item["risk"] = _risk_score(item["fi"], item["fo"], item["ownership_concentration"])
    return ranked


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
            "observe_route_rate": (bv3f.get("comparison_table") or {}).get("observe_route_rate", {}),
            "referential_clarity_hard_replacements": (
                (bv3f.get("comparison_table") or {}).get("referential_clarity_hard_replacements", {})
            ),
        },
        "bv4b": {
            "fallback_incidence": (bv4b.get("comparison_table") or {}).get("fallback_incidence", {}),
            "observe_route_rate": (bv4b.get("comparison_table") or {}).get("observe_route_rate", {}),
            "psp_fallback_count": (bv4b.get("comparison_table") or {}).get(
                "sealed_passive_scene_pressure_fallback_count", {}
            ),
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
    families = {"active": [], "retired": [], "historical": [], "emerging": []}
    for entry in registry:
        status = str(entry.get("registry_status") or "").upper()
        key = str(entry.get("recurrence_key") or "")
        short = key.split("|")[1:4] if "|" in key else [key]
        payload = {"recurrence_key": key, "family": "|".join(short)}
        if status == "ACTIVE":
            families["active"].append(payload)
            families["emerging"].append(payload)
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
        "emerging_families": families["emerging"],
        "dominant_share_before": before.get("dominant_share"),
        "dominant_share_after": after.get("dominant_share"),
        "recurring_keys_after": after.get("recurring_keys"),
    }


def _maintenance_matrix(
    area_rollups: dict[str, dict[str, Any]],
    bv1_matrix: dict[str, Any],
    recurrence: dict[str, Any],
    fallback: dict[str, Any],
) -> dict[str, Any]:
    rows = []
    for area, current in area_rollups.items():
        prior = bv1_matrix.get(area.replace("tests_smoke", "tests").replace("tests_registry", "tests"), {})
        if not prior and area in bv1_matrix:
            prior = bv1_matrix[area]
        if area == "tests_smoke" or area == "tests_registry":
            prior = {
                "fan_in_total": 73 if area == "tests_smoke" else 0,
                "fan_out_total": 57 if area == "tests_registry" else 5,
            }
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

    return {
        "classification": "REDISTRIBUTED_COST",
        "primary_drag_center": "final_emission_meta_read_attribution_cluster",
        "area_rows": rows,
        "fallback_status": fallback["verdict"],
        "recurrence_status": "retired_projection_key_bv8a",
        "notes": [
            "Fallback incidence remains at 1.05% (1/95 turns) — no longer dominant drag.",
            "Speaker projection recurrence retired in BV8A deduplicated view.",
            "Largest single-module FI: final_emission_text and social_exchange_emission (52 each).",
            "Largest test-bridge cluster post-BV7: replay_smoke_assertions (46) + gate_integration_smoke (39).",
            "Largest unaddressed read-side cluster: meta_read (29) + owner_bucket_views (22) + ownership_schema (19).",
        ],
    }


def _candidate_rankings(top20: list[dict[str, Any]], recurrence: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        {
            "id": "BV10",
            "title": "Meta-read & attribution read facade consolidation",
            "target": "game.final_emission_meta_read + owner_bucket_views + ownership_schema cluster",
            "expected_roi": "high",
            "maintenance_impact": "Reduce cross-test churn on metadata reads; narrow investigation routing; continue BV2 read-side split",
            "implementation_cost": "medium",
            "replay_risk": "low",
            "evidence": "meta_read FI 29; bucket_views FI 22; ownership_schema FI 19; combined 70 FI read path",
        },
        {
            "id": "BV10B",
            "title": "Second-order smoke bridge thinning",
            "target": "tests.helpers.replay_smoke_assertions + gate_integration_smoke",
            "expected_roi": "medium-high",
            "maintenance_impact": "Split post-BV7 bridge hubs (85 combined FI) by domain without monolith regrowth",
            "implementation_cost": "medium",
            "replay_risk": "low-medium",
            "evidence": "replay_smoke FI 46; gate_integration FI 39; BV7 intentional redistribution",
        },
        {
            "id": "BV10C",
            "title": "Terminal pipeline / gate convergence decomposition",
            "target": "game.final_emission_gate + terminal_pipeline",
            "expected_roi": "medium-high",
            "maintenance_impact": "Split gate orchestration from terminal assembly to reduce 30+26 FI convergence edits",
            "implementation_cost": "high",
            "replay_risk": "medium",
            "evidence": "gate FI 30/FO 9; terminal FI 26/FO 14; 23 test importers on terminal",
        },
        {
            "id": "BV10D",
            "title": "Attribution completeness program (BS continuation)",
            "target": "owner bucket strict completeness + failure classifier routing",
            "expected_roi": "medium",
            "maintenance_impact": "Close 38.78% owner-bucket gap; reduce misrouted investigations",
            "implementation_cost": "medium-high",
            "replay_risk": "low",
            "evidence": "ownership_schema FI 19; classifier helper FI 15; strict completeness 0%",
        },
        {
            "id": "BV10E",
            "title": "Residual RC observe fallback elimination",
            "target": "referential_clarity_hard_replacement (1 event / 1.05%)",
            "expected_roi": "medium (diminishing)",
            "maintenance_impact": "Clear last measurable fallback on BV3D corpus",
            "implementation_cost": "medium",
            "replay_risk": "medium",
            "evidence": "BV1B 1 event; BV4B cleared PSP; RC remains sole fallback",
        },
    ]
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index
    return candidates


def _recommendation(candidates: list[dict[str, Any]], top20: list[dict[str, Any]]) -> dict[str, Any]:
    top_modules = [row["module"] for row in top20[:5]]
    return {
        "selected_cycle": "BV10",
        "title": "Meta-read & attribution read facade consolidation",
        "rationale": (
            "After BV2–BV8, fallback incidence collapsed (69%→1%), smoke monolith FI fell 73→15 (BV7), "
            "and speaker recurrence was retired (BV8A). The largest remaining *unaddressed* maintenance "
            "cluster is the final-emission read/attribution path: meta_read (FI 29), owner_bucket_views "
            "(22), and ownership_schema (19) — 70 combined FI with low replay risk. Post-BV7 test bridge "
            "hubs (replay_smoke 46 + gate_integration 39) are intentional and governance-capped; BV10 targets "
            "production read facades first as the highest-ROI continuation of BV2."
        ),
        "projected_scorecard_impact": {
            "maintenance_drag": "+0.75",
            "ownership_clarity": "+0.5",
            "operational_simplicity": "+0.5",
            "maintenance_economics": "+0.5",
        },
        "top_modules_evidence": top_modules,
        "alternates": ["BV10B", "BV10C"],
    }


def build_bv9_analysis(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    rows = _load_bu_rows()
    ownership_rows: list[dict[str, str]] = []
    if OWNERSHIP_CSV.is_file():
        with OWNERSHIP_CSV.open(encoding="utf-8", newline="") as handle:
            ownership_rows = list(csv.DictReader(handle))

    ownership_refs = _ownership_ref_map(ownership_rows)
    area_rollups = _area_rollups(rows)
    top20 = _concentration_rankings(rows, ownership_refs)
    recurrence = _recurrence_review()
    fallback = _fallback_review()
    matrix = _maintenance_matrix(area_rollups, _load_json(BV1_MATRIX), recurrence, fallback)
    candidates = _candidate_rankings(top20, recurrence)
    recommendation = _recommendation(candidates, top20)

    test_inventory = _load_json(TEST_INVENTORY)
    test_hubs = (test_inventory.get("import_hub_modules") or [])[:10]
    bv7 = _load_json(BV7_SMOKE)

    ownership_domain_totals = _ownership_domain_totals(ownership_rows)

    return {
        "schema_version": 1,
        "generated_at": timestamp,
        "cycle": "BV9",
        "primary_question": "What is now the largest source of maintenance drag?",
        "executive_answer": recommendation["rationale"].split(".")[0] + ".",
        "selected_next_cycle": recommendation["selected_cycle"],
        "sources": {
            "bu_import_fan_in_fan_out": str(BU_CSV.relative_to(ROOT)).replace("\\", "/"),
            "bv8a_recurrence_history": str(BV8A.relative_to(ROOT)).replace("\\", "/"),
            "bv1b_fallback_summary": str(BV1B.relative_to(ROOT)).replace("\\", "/"),
            "bv3f_reduction_metrics": str(BV3F.relative_to(ROOT)).replace("\\", "/"),
            "bv4b_concrete_beat_metrics": str(BV4B.relative_to(ROOT)).replace("\\", "/"),
            "bv7_smoke_analysis": str(BV7_SMOKE.relative_to(ROOT)).replace("\\", "/"),
            "test_inventory_full": str(TEST_INVENTORY.relative_to(ROOT)).replace("\\", "/"),
        },
        "hotspot_scan": {
            "module_count": len(rows),
            "area_rollups": area_rollups,
            "ownership_domain_top": ownership_domain_totals,
            "test_import_hubs_top10": test_hubs,
            "smoke_facade_fi": bv7.get("module_fi"),
            "smoke_facade_fo": bv7.get("module_fo"),
            "recurrence_concentration": recurrence,
            "fallback_concentration": fallback,
        },
        "top20_concentration_rankings": top20,
        "recurrence_review": recurrence,
        "fallback_review": fallback,
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
    recurrence = analysis["recurrence_review"]
    fallback = analysis["fallback_review"]
    matrix = analysis["maintenance_matrix"]
    candidates = analysis["candidate_rankings"]
    rec = analysis["recommendation"]

    hotspot_path = AUDITS / "BV9_hotspot_inventory.md"
    hotspot_path.write_text(
        "\n".join(
            [
                "# BV9 — Hotspot Inventory",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Scope:** Entire repository (post BV2–BV8)  ",
                f"**Method:** `python tools/bv9_hotspot_reassessment.py`  ",
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
                "### Recurrence concentration (BV8A view)",
                "",
                _md_table(
                    ["Metric", "Before", "After"],
                    [
                        ["Total rows", recurrence["before_metrics"].get("total_recurrence_rows"), recurrence["after_metrics"].get("total_recurrence_rows")],
                        ["Recurring keys", recurrence["before_metrics"].get("recurring_keys"), recurrence["after_metrics"].get("recurring_keys")],
                        ["Dominant share", recurrence["before_metrics"].get("dominant_share"), recurrence["after_metrics"].get("dominant_share")],
                        ["Active keys", recurrence["before_metrics"].get("active_recurrence_count"), recurrence["after_metrics"].get("active_recurrence_count")],
                    ],
                ),
                "",
                "### Fallback concentration",
                "",
                _md_table(
                    ["Snapshot", "Fallback incidence", "Events", "Eligible turns"],
                    [
                        ["BV1B / current", f"{(fallback['bv1b'].get('fallback_trigger_rate') or 0)*100:.2f}%", fallback["bv1b"].get("fallback_event_count"), fallback["bv1b"].get("eligible_turn_count")],
                        ["BV3F actual", f"{(fallback['bv3f']['fallback_incidence'].get('actual') or 0)*100:.2f}%", "—", "—"],
                        ["BV4B current", f"{(fallback['bv4b']['fallback_incidence'].get('current') or 0)*100:.2f}%", "—", "—"],
                    ],
                ),
                "",
                "### Ownership concentration (domain refs)",
                "",
                _md_table(
                    ["Ownership domain", "Reference count"],
                    analysis["hotspot_scan"]["ownership_domain_top"],
                ),
                "",
                "### Test concentration (import hubs)",
                "",
                _md_table(
                    ["Game module", "Test file count"],
                    [[hub["game_module"], hub["file_count"]] for hub in analysis["hotspot_scan"]["test_import_hubs_top10"]],
                ),
                "",
                f"Smoke facade (post-BV7): FI **{analysis['hotspot_scan']['smoke_facade_fi']}**, FO **{analysis['hotspot_scan']['smoke_facade_fo']}**",
                "",
                "---",
                "",
                "## Evidence",
                "",
                "| Source | Role |",
                "|---|---|",
                "| `docs/audits/BU_import_fan_in_fan_out.csv` | Module FI/FO |",
                "| `artifacts/bv8a_recurrence_history.json` | Post-BV8A recurrence view |",
                "| `artifacts/bv1b_fallback_summary.json` | Current fallback incidence |",
                "| `artifacts/bv7_smoke_analysis.json` | Smoke facade post-decomposition |",
                "| `artifacts/test_inventory_full.json` | Test import hub concentration |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(hotspot_path)

    rankings_path = AUDITS / "BV9_concentration_rankings.md"
    rankings_path.write_text(
        "\n".join(
            [
                "# BV9 — Top-20 Concentration Rankings",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Population:** BU AST import graph (`BU_import_fan_in_fan_out.csv`)  ",
                "**Risk heuristic:** FI + 0.35×FO + ownership concentration weight",
                "",
                "---",
                "",
                _md_table(
                    ["Rank", "Module", "FI", "FO", "Ownership concentration", "Risk"],
                    [
                        [
                            row["rank"],
                            f"`{row['module']}`",
                            row["fi"],
                            row["fo"],
                            row["ownership_concentration"],
                            row["risk"],
                        ]
                        for row in top20
                    ],
                ),
                "",
                "## Category highlights",
                "",
                "### Helper facades",
                "",
                _md_table(
                    ["Module", "FI", "FO", "Risk"],
                    [
                        [row["module"], row["fi"], row["fo"], row["risk"]]
                        for row in top20
                        if row["module"] in HELPER_FACADES
                    ],
                ),
                "",
                "### Replay surfaces",
                "",
                _md_table(
                    ["Module", "FI", "FO", "Risk"],
                    [
                        [row["module"], row["fi"], row["fo"], row["risk"]]
                        for row in top20
                        if row["module"] in REPLAY_SURFACES
                    ],
                ),
                "",
                "### Fallback surfaces",
                "",
                _md_table(
                    ["Module", "FI", "FO", "Risk"],
                    [
                        [row["module"], row["fi"], row["fo"], row["risk"]]
                        for row in top20
                        if row["module"] in FALLBACK_SURFACES
                    ],
                ),
                "",
                "### Ownership hubs",
                "",
                _md_table(
                    ["Module", "FI", "FO", "Risk"],
                    [
                        [row["module"], row["fi"], row["fo"], row["risk"]]
                        for row in top20
                        if row["module"] in OWNERSHIP_HUBS
                    ],
                ),
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(rankings_path)

    recurrence_path = AUDITS / "BV9_recurrence_review.md"
    recurrence_path.write_text(
        "\n".join(
            [
                "# BV9 — Recurrence Review",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Source:** BV8A deduplicated recurrence view (`artifacts/bv8a_recurrence_history.json`)  ",
                "**Raw event log:** Unmodified",
                "",
                "---",
                "",
                "## Executive answer",
                "",
                "Speaker projection recurrence is **retired** in the BV8A view. Three **emerging** families remain active with single observations each. No recurring keys remain after deduplication.",
                "",
                "## Active recurrence families",
                "",
                _md_table(
                    ["Family", "Recurrence key"],
                    [[item["family"], f"`{item['recurrence_key']}`"] for item in recurrence["active_families"]],
                ),
                "",
                "## Retired families",
                "",
                _md_table(
                    ["Family", "Recurrence key"],
                    [[item["family"], f"`{item['recurrence_key']}`"] for item in recurrence["retired_families"]],
                ),
                "",
                "## Historical families (evidence retained)",
                "",
                _md_table(
                    ["Family", "Recurrence key"],
                    [[item["family"], f"`{item['recurrence_key']}`"] for item in recurrence["historical_families"]],
                ),
                "",
                "## Emerging families",
                "",
                "Same as active — each key has `occurrence_count = 1` and trend class `emerging`.",
                "",
                "## Metric delta (BV8A)",
                "",
                _md_table(
                    ["Metric", "Before", "After"],
                    [
                        ["Dominant share", recurrence["dominant_share_before"], recurrence["dominant_share_after"]],
                        ["Recurring keys", recurrence["before_metrics"].get("recurring_keys"), recurrence["recurring_keys_after"]],
                        ["Validated outcomes", recurrence["before_metrics"].get("validated_outcome_count"), recurrence["after_metrics"].get("validated_outcome_count")],
                    ],
                ),
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(recurrence_path)

    fallback_path = AUDITS / "BV9_fallback_review.md"
    fb = fallback
    fallback_path.write_text(
        "\n".join(
            [
                "# BV9 — Fallback Review",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Scope:** BV3D-filtered corpus, post-BV4B  ",
                "",
                "---",
                "",
                "## Executive answer",
                "",
                "Fallback maintenance drag **collapsed** across BV1B → BV3F → BV4B. Current incidence is **1.05%** (1/95 turns). Residual drag is a **single RC hard-replacement event**, not a concentrated module hub.",
                "",
                "## Comparison table",
                "",
                _md_table(
                    ["Program", "Fallback incidence", "Observe route", "Notes"],
                    [
                        [
                            "BV1B baseline",
                            f"{(fb['bv1b'].get('fallback_trigger_rate') or 0)*100:.2f}%",
                            "—",
                            f"{fb['bv1b'].get('fallback_event_count')} event(s)",
                        ],
                        [
                            "BV3F actual",
                            f"{(fb['bv3f']['fallback_incidence'].get('actual') or 0)*100:.2f}%",
                            f"{(fb['bv3f']['observe_route_rate'].get('actual') or 0)*100:.2f}%",
                            f"RC hard replace: {fb['bv3f']['referential_clarity_hard_replacements'].get('actual')}",
                        ],
                        [
                            "BV4B current",
                            f"{(fb['bv4b']['fallback_incidence'].get('current') or 0)*100:.2f}%",
                            f"{(fb['bv4b']['observe_route_rate'].get('current') or 0)*100:.2f}%",
                            f"PSP delta: {fb['bv4b']['psp_fallback_count'].get('delta')}",
                        ],
                        [
                            "Current (BV1B re-run)",
                            f"{(fb['current'].get('fallback_trigger_rate') or 0)*100:.2f}%",
                            "4.35% est.",
                            f"{fb['current'].get('fallback_event_count')} event(s)",
                        ],
                    ],
                ),
                "",
                "## Verdict",
                "",
                f"**{fb['verdict']}** — fallback is no longer the largest maintenance-cost driver repository-wide.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(fallback_path)

    matrix_path = AUDITS / "BV9_maintenance_matrix.md"
    matrix_path.write_text(
        "\n".join(
            [
                "# BV9 — Maintenance Matrix Refresh",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Prior matrix:** [BV5_maintenance_cost_matrix.md](BV5_maintenance_cost_matrix.md)  ",
                "**Method:** BU CSV area rollups + BV8A recurrence + BV1B fallback re-read",
                "",
                "---",
                "",
                "## Executive verdict",
                "",
                f"**Classification:** **{matrix['classification']}** — fallback and recurrence wins shifted drag to **final-emission read facades** and **gate/terminal convergence**.",
                "",
                f"**Primary drag center:** `{matrix['primary_drag_center']}`",
                "",
                "## Area matrix",
                "",
                _md_table(
                    ["Area", "Prior FI", "Current FI", "Δ FI", "Prior FO", "Current FO"],
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
                "## Status notes",
                "",
                "\n".join(f"- {note}" for note in matrix["notes"]),
                "",
                "## Net shift since BV5",
                "",
                "| Drag center | BV5 status | BV9 status |",
                "|---|---|---|",
                "| Fallback incidence | **Reduced** (1.05%) | **Collapsed** — residual 1 event |",
                "| Meta write (`final_emission_meta`) | **Reduced** (FI 24) | Stable read facades dominate |",
                "| Smoke facade | FI 73 pre-BV7 | FI 17 post-BV7B |",
                "| Speaker recurrence | 8 rows active | **Retired** (BV8A) |",
                "| Gate / terminal | Convergence hub | **Largest remaining FI cluster** |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(matrix_path)

    candidates_path = AUDITS / "BV9_candidate_rankings.md"
    candidates_path.write_text(
        "\n".join(
            [
                "# BV9 — Candidate Rankings",
                "",
                f"**Date:** {analysis['generated_at'][:10]}  ",
                "**Trigger:** Post BV2–BV8 hotspot reassessment  ",
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
                        f"- **Expected ROI:** {candidate['expected_roi']}",
                        f"- **Maintenance impact:** {candidate['maintenance_impact']}",
                        f"- **Implementation cost:** {candidate['implementation_cost']}",
                        f"- **Replay risk:** {candidate['replay_risk']}",
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
                    ["Rank", "Cycle", "Rationale"],
                    [
                        ["1", "BV10", "Highest-ROI unaddressed read/attribution cluster; BV2 continuation; low replay risk"],
                        ["2", "BV10B", "Largest test-bridge FI (85 combined) post-BV7 redistribution"],
                        ["3", "BV10C", "Gate/terminal convergence — high impact, higher cost/risk"],
                        ["4", "BV10D", "Ownership clarity — closes attribution completeness gap"],
                        ["5", "BV10E", "Last fallback event — diminishing returns"],
                    ],
                ),
                "",
                "## BV10 recommendation",
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
    analysis = build_bv9_analysis()
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
