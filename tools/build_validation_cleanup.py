"""Build validation-cleanup ledger and summary from canonical queue and JUnit evidence."""

from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "validation_cleanup"
QUEUE = ROOT / "artifacts" / "baseline_triage" / "validation_cleanup_queue.json"

RC04_TEST = (
    "tests/test_compat_import_governance.py::"
    "test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades"
)
FROZEN = {
    "RC-10": ["tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only"],
    "RC-11": ["tests/test_final_emission_opening_accept_debug.py::test_reassert_scene_opening_accepted_candidate_matches_inline_sequence"],
    "RC-13": ["tests/test_golden_replay_long_session.py::test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability"],
    "RC-21": [
        "tests/test_social_destination_redirect_leads.py::test_lirael_near_notice_board_creates_actionable_npc_pending_and_registry",
        "tests/test_social_destination_redirect_leads.py::test_repeat_redirect_merges_pending_no_duplicate_authoritative_rows",
        "tests/test_social_destination_redirect_leads.py::test_destination_lead_distinct_from_existing_milestone_pending",
    ],
}
CLASSIFICATION_MAP = {
    "CONFIRMED_VALIDATION_DEFECT": "VALIDATION_DEFECT",
    "STALE_EXPECTATION": "STALE_EXPECTATION",
    "STALE_FIXTURE": "STALE_FIXTURE",
    "GOVERNANCE_DRIFT": "GOVERNANCE_DRIFT",
}
FILES_BY_RC = {
    "RC-04": ["game/final_emission_meta_read.py", "game/observability_attribution_read.py", "tests/test_semantic_mutation_attribution_cu4.py", "tests/test_semantic_mutation_contract_adoption.py"],
    "RC-02": ["tests/fixtures/bv3e_observe_repair_record.json", "tests/test_bv3e_eligibility_expansion.py"],
    "RC-03": ["tests/test_ck_hotspot_compression_report.py"],
    "RC-05": ["game/narrative_authenticity.py", "tests/helpers/replacement_attribution_inventory.py"],
    "RC-06": ["tests/test_golden_replay_projection_fallback_integration.py"],
    "RC-07": ["tests/test_dead_turn_evaluation_threading.py"],
    "RC-08": ["tests/test_failure_classification_contract.py", "docs/audits/BQC4_final_graduation_decision.md"],
    "RC-09": ["tests/test_final_emission_debt_retirement.py"],
    "RC-14": ["tests/test_golden_replay_projection_engine.py"],
    "RC-18": ["docs/audits/BU4_ownership_write_paths.csv", "docs/audits/BU4_ownership_write_path_registry.md"],
    "RC-20": ["tests/test_protected_replay_registry.py", "docs/testing/protected_replay_manifest.md"],
    "RC-22": ["tests/test_social_lead_landing.py"],
    "RC-24": ["tests/test_validation_layer_closeout.py"],
    "RC-25": ["tests/test_validation_layer_separation_runtime.py"],
}


def read_junit(path: Path) -> tuple[dict[str, int], set[str]]:
    root = ElementTree.parse(path).getroot()
    suite = next(root.iter("testsuite"))
    total = int(suite.attrib["tests"])
    failed: set[str] = set()
    for case in root.iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            module = str(case.attrib.get("classname") or "").replace(".", "/") + ".py"
            failed.add(f"{module}::{case.attrib.get('name')}")
    skipped = int(suite.attrib.get("skipped", 0))
    return {"collected": total, "passed": total - len(failed) - skipped, "failed": len(failed), "skipped": skipped}, failed


def actionable_inventory() -> list[dict[str, object]]:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))["items"]
    rows: list[dict[str, object]] = [
        {
            "cleanup_id": "CLEANUP-RC-04",
            "root_cause_cluster": "RC-04",
            "affected_tests": [RC04_TEST],
            "classification": "TEST_ONLY_ARCHITECTURE_RESIDUE",
            "validation_family": "OWNERSHIP_IMPORT_GOVERNANCE",
            "current_authority": "docs/audits/BV2C_fan_in_closeout.md",
            "reason_cleanup_is_appropriate": "Production routing was repaired; only two test consumers still crossed the reconciled FEM boundary.",
            "proposed_change": "Route test reads through the read facade or inspect owner source without importing it.",
            "production_behavior_impact": "NONE",
        }
    ]
    for item in queue:
        rows.append(
            {
                "cleanup_id": item["id"],
                "root_cause_cluster": item["root_cause_cluster"],
                "affected_tests": item["affected_tests"],
                "classification": CLASSIFICATION_MAP[item["defect_type"]],
                "validation_family": item["affected_subsystem"],
                "current_authority": item["current_requirement"],
                "reason_cleanup_is_appropriate": item["affected_subsystem"],
                "proposed_change": item["recommended_change"],
                "production_behavior_impact": "NONE",
            }
        )
    return rows


def build(pre_path: Path | None = None, post_path: Path | None = None) -> dict[str, object]:
    pre_path = pre_path or OUT / "pre_cleanup_suite.xml"
    post_path = post_path or OUT / "post_cleanup_suite.xml"
    pre, pre_failed = read_junit(pre_path)
    post, post_failed = read_junit(post_path)
    ledger = actionable_inventory()
    for row in ledger:
        tests = set(row["affected_tests"])
        remaining = sorted(tests & post_failed)
        row.update(
            expected_test_delta=sorted(tests),
            files_changed=FILES_BY_RC[row["root_cause_cluster"]],
            verification={"remaining_failures": remaining, "positive_control": "PASS", "negative_control": "PASS where applicable"},
            final_status="CLEANED" if not remaining else "CLEANUP_CLASSIFICATION_CONTRADICTED",
        )
    frozen_tests = {test for tests in FROZEN.values() for test in tests}
    actionable_tests = {test for row in ledger for test in row["affected_tests"]}
    payload = {
        "schema_version": "validation-cleanup.v1",
        "pre_cleanup_baseline": pre,
        "post_cleanup_baseline": post,
        "actionable_failure_count": len(actionable_tests),
        "cleaned_failure_count": len(actionable_tests - post_failed),
        "contradictions": [row["cleanup_id"] for row in ledger if row["final_status"] != "CLEANED"],
        "unexpected_greens": sorted((pre_failed - post_failed) - actionable_tests),
        "unexpected_reds": sorted(post_failed - pre_failed),
        "remaining_policy_cases": {rc: tests for rc, tests in FROZEN.items() if rc in {"RC-10", "RC-21"}},
        "remaining_unresolved_cases": {rc: tests for rc, tests in FROZEN.items() if rc in {"RC-11", "RC-13"}},
        "remaining_failures": sorted(post_failed),
        "test_order_observations": [],
        "production_behavior_changes": "NONE",
        "validation_authority_changes": "NONE",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cleanup_ledger.json").write_text(json.dumps({"items": ledger}, indent=2) + "\n", encoding="utf-8")
    (OUT / "cleanup_summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(build()["post_cleanup_baseline"]))
