"""Build the remaining-baseline investigation artifacts from one reviewed model."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "baseline_triage"
SOURCE = ROOT / "artifacts" / "validation_portfolio" / "current_failure_classification.json"


def _short(test: str) -> str:
    return test.rsplit("::", 1)[-1]


CLUSTERS = [
    ("RC-01", [0, 1, 24, 25, 26, 27], "attribution corpus completeness regression", "CONFIRMED_ARCHITECTURE_DEFECT", "P1", "Repair the unstamped/misclassified mutation producer and then refresh derived metrics.", "docs/audits/CO96_attribution_program_closeout.md"),
    ("RC-02", [2], "obsolete repair-eligibility session fixture", "STALE_FIXTURE", "P3", "Modernize the canonical fixture without changing eligibility policy.", "docs/audits/BV3D_measurement_validation.md"),
    ("RC-03", [3], "historical hotspot percentage snapshot", "STALE_EXPECTATION", "P3", "Regenerate the diagnostic snapshot from the current BU inventory.", "docs/audits/CI_2_hotspot_compression_measurement_standard_closeout.md"),
    ("RC-04", [4], "final-emission metadata facade bypasses", "CONFIRMED_ARCHITECTURE_DEFECT", "P1", "Route production reads/writes through the reconciled facade; separately clean test-only imports.", "docs/audits/BV2C_fan_in_closeout.md"),
    ("RC-05", [5], "attribution helper imports sealed owner constants", "CONFIRMED_VALIDATION_DEFECT", "P3", "Make the test helper consume attribution_read_views.", "docs/audits/BV10C_fan_in_closeout.md"),
    ("RC-06", [6, 7], "test-only social compatibility barrel fan-in", "CONFIRMED_VALIDATION_DEFECT", "P3", "Import named social authorities in the integration test and recompute the cap.", "docs/audits/BV14_closeout.md"),
    ("RC-07", [8], "playability result schema grew diagnostic fields", "STALE_EXPECTATION", "P3", "Assert the authoritative exclusion fields instead of exact whole-dict equality.", "docs/playability_validation.md"),
    ("RC-08", [9, 10, 11], "failure-evidence governance manifests diverged", "GOVERNANCE_DRIFT", "P3", "Reconcile manifests to the classifier contract and governing-authority document.", "docs/validation_evidence_standard.md"),
    ("RC-09", [12], "final-emission debt snapshot predates later modules", "STALE_EXPECTATION", "P3", "Re-audit and regenerate the debt snapshot against current modules.", "docs/audits/BV_maintenance_economics_validation_closeout.md"),
    ("RC-10", [13], "raw-token compatibility boundary lacks final authority", "POLICY_DECISION_REQUIRED", "P2", "Choose whether opening fallback is the sole permitted local raw-token consumer.", "docs/narrative_integrity_architecture.md"),
    ("RC-11", [14], "opening acceptance debug sequence diverges", "UNRESOLVED", "P2", "Trace candidate mutation ordering with non-semantic instrumentation before repair.", "docs/narrative_integrity_architecture.md"),
    ("RC-12", [15, 28], "resolved destination loses scene grounding in global fallback", "CONFIRMED_PRODUCT_DEFECT", "P1", "Preserve resolved destination context when constructing the global scene fallback.", "docs/narrative_integrity_architecture.md"),
    ("RC-13", [16], "25-turn diagnostic history is not stable", "UNRESOLVED", "P2", "Capture the first divergent turn and determine whether mutable history or runtime logic owns it.", "docs/testing/protected_replay_manifest.md"),
    ("RC-14", [17], "projection backup predates attribution columns", "STALE_EXPECTATION", "P3", "Replace byte identity with a versioned semantic projection assertion.", "docs/audits/CU3_semantic_mutation_evidence_reconciliation.md"),
    ("RC-15", [18], "retired projection alias remains exported", "CONFIRMED_ARCHITECTURE_DEFECT", "P2", "Remove the deprecated alias after verifying named-authority callers.", "docs/audits/closeouts/cycle_ar_replay_drift_classification_closeout.md"),
    ("RC-16", [19], "protected assertion bridge omits recurrence event", "CONFIRMED_PRODUCT_DEFECT", "P2", "Restore canonical recurrence recording on protected assertion failure.", "docs/audits/CR_protected_replay_recurrence_separation_closeout.md"),
    ("RC-17", [20], "social fallback calls an undefined prompt helper", "CONFIRMED_PRODUCT_DEFECT", "P0", "Restore the owned resolution-question helper or route to its current authority.", "docs/narrative_integrity_architecture.md"),
    ("RC-18", [21], "ownership write registry is missing discovered paths", "GOVERNANCE_DRIFT", "P3", "Review and register the 29 current production write paths; do not alter ownership policy.", "docs/architecture_ownership_ledger.md"),
    ("RC-19", [22], "visibility fallback writes bypass producer stamping", "CONFIRMED_ARCHITECTURE_DEFECT", "P1", "Route both direct owner writes through the declared stamping function.", "docs/architecture_ownership_ledger.md"),
    ("RC-20", [23], "protected replay count lock predates CO102 case", "STALE_EXPECTATION", "P3", "Update the count assertion to derive from the authoritative protected manifest.", "docs/testing/protected_replay_manifest.md"),
    ("RC-21", [29, 30, 31], "destination redirect authority between NPC pending and clue state is ambiguous", "POLICY_DECISION_REQUIRED", "P2", "Choose the authoritative lead representation, then align production and component contracts.", "docs/narrative_integrity_architecture.md"),
    ("RC-22", [32], "minimum lead source changed from clue to exit", "STALE_EXPECTATION", "P3", "Assert actionable lead semantics rather than the historical source label.", "docs/narrative_integrity_architecture.md"),
    ("RC-23", [33], "narrative-authenticity module imports gate repair surface", "CONFIRMED_ARCHITECTURE_DEFECT", "P1", "Move the dependency behind the reconciled validation-layer boundary.", "docs/validation_layer_separation.md"),
    ("RC-24", [34], "offline evaluator allowlist predates attribution read facade", "STALE_EXPECTATION", "P3", "Update the allowlist to the reconciled read-only facade.", "docs/validation_layer_separation.md"),
    ("RC-25", [35], "runtime import-shape assertion predates gate composition split", "STALE_EXPECTATION", "P3", "Replace the historical module-presence assertion with the current layer invariant.", "docs/validation_layer_separation.md"),
]


def junit_counts(path: Path) -> dict[str, int]:
    root = ElementTree.parse(path).getroot()
    suite = root if root.tag == "testsuite" else next(root.iter("testsuite"))
    total = int(suite.attrib["tests"])
    failures = int(suite.attrib.get("failures", 0)) + int(suite.attrib.get("errors", 0))
    skipped = int(suite.attrib.get("skipped", 0))
    return {"collected": total, "passed": total - failures - skipped, "failed": failures, "skipped": skipped}


def build() -> dict:
    prior = json.loads(SOURCE.read_text(encoding="utf-8"))["failures"]
    assert len(prior) == 36
    by_index = {}
    cluster_rows = []
    for cid, indexes, cause, classification, priority, repair, authority in CLUSTERS:
        cluster_rows.append({"cluster_id": cid, "affected_tests": [prior[i]["test"] for i in indexes], "affected_validation_families": sorted({prior[i]["family_id"] for i in indexes}), "underlying_subsystem": cause, "confirmed_cause": cause, "recommended_repair": repair, "expected_failures_resolved": len(indexes), "regression_risk": "MEDIUM" if priority in {"P0", "P1"} else "LOW", "dependencies": [], "confidence": "HIGH" if classification not in {"POLICY_DECISION_REQUIRED", "UNRESOLVED"} else "LOW"})
        for i in indexes:
            by_index[i] = (cid, classification, priority, repair, authority, cause)
    assert set(by_index) == set(range(36))
    records = []
    for i, old in enumerate(prior):
        cid, classification, priority, repair, authority, cause = by_index[i]
        high = classification.startswith("CONFIRMED_") and classification != "CONFIRMED_VALIDATION_DEFECT"
        confidence = "LOW" if classification in {"POLICY_DECISION_REQUIRED", "UNRESOLVED"} else ("HIGH" if high or classification in {"STALE_EXPECTATION", "GOVERNANCE_DRIFT", "CONFIRMED_VALIDATION_DEFECT"} else "MEDIUM")
        records.append({
            "investigation_id": f"BT-{i+1:03d}", "test": old["test"], "test_path": old["test"].split("::")[0], "test_name": _short(old["test"]), "validation_family": old["family_id"],
            "previous_classification": old["classification"], "previous_confidence": old["confidence"], "protected_requirement": old["reason"], "requirement_source": authority,
            "current_architecture_relevance": "direct" if "ARCHITECTURE" in classification or old["family_id"] in {"OWNERSHIP_IMPORT_GOVERNANCE", "ARCHITECTURE_GOVERNANCE"} else "supporting",
            "current_product_relevance": "direct" if classification == "CONFIRMED_PRODUCT_DEFECT" else "indirect", "reproduction_status": "REPRODUCED_IN_PRE_TRIAGE_JUNIT",
            "observed_behavior": old["reason"], "expected_behavior": repair, "root_cause_finding": cause, "root_cause_cluster": cid,
            "confirmed_classification": classification, "confidence": confidence, "recommended_action": repair, "repair_priority": priority, "dependencies": [],
            "evidence_references": [authority, "artifacts/baseline_triage/pre_triage_suite.xml", old["test"].split("::")[0]],
            "human_judgment_required": classification == "POLICY_DECISION_REQUIRED", "notes": "No production or validation repair was made during triage."
        })
    pre = junit_counts(OUT / "pre_triage_suite.xml")
    post_path = OUT / "post_triage_suite.xml"
    post = junit_counts(post_path) if post_path.exists() else None
    registry = {"schema_version": "baseline-triage.v1", "observed_at": "2026-09-19", "baseline": pre, "post_baseline": post, "counting_reconciliation": "JUnit reports 6,440 pre-triage test cases. The earlier 6,439 value was a generated summary's collection-count semantic, not a missing test case. Post-triage collection adds only the five new passing tooling tests.", "failures": records, "root_cause_clusters": cluster_rows}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "failure_investigation_registry.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    repairs = []
    cleanup = []
    for cluster in cluster_rows:
        first = next(r for r in records if r["root_cause_cluster"] == cluster["cluster_id"])
        cls = first["confirmed_classification"]
        item = {"id": ("REPAIR-" if cls in {"CONFIRMED_PRODUCT_DEFECT", "CONFIRMED_ARCHITECTURE_DEFECT"} else "CLEANUP-") + cluster["cluster_id"], "root_cause_cluster": cluster["cluster_id"], "affected_tests": cluster["affected_tests"], "defect_type": cls, "affected_subsystem": cluster["underlying_subsystem"], "current_requirement": first["requirement_source"], "recommended_change": cluster["recommended_repair"], "validation_required_after_repair": cluster["affected_tests"], "risk": cluster["regression_risk"], "priority": first["repair_priority"], "confidence": first["confidence"]}
        if cls in {"CONFIRMED_PRODUCT_DEFECT", "CONFIRMED_ARCHITECTURE_DEFECT"}:
            repairs.append(item)
        elif cls not in {"POLICY_DECISION_REQUIRED", "UNRESOLVED"}:
            cleanup.append(item)
    (OUT / "confirmed_repair_queue.json").write_text(json.dumps({"schema_version": "baseline-repair-queue.v1", "items": repairs}, indent=2) + "\n", encoding="utf-8")
    (OUT / "validation_cleanup_queue.json").write_text(json.dumps({"schema_version": "baseline-cleanup-queue.v1", "items": cleanup}, indent=2) + "\n", encoding="utf-8")
    repair_md = ["# Confirmed Repair Queue", "", "Only current product and architecture defects are included.", ""] + [f"## {x['id']} ({x['priority']})\n\n{x['recommended_change']}\n\nAffected tests: {len(x['affected_tests'])}. Authority: `{x['current_requirement']}`. Confidence: {x['confidence']}." for x in repairs]
    (OUT / "confirmed_repair_queue.md").write_text("\n\n".join(repair_md) + "\n", encoding="utf-8")
    policy = [r for r in records if r["confirmed_classification"] == "POLICY_DECISION_REQUIRED"]
    policy_md = ["# Policy Decisions", ""] + [f"## {r['root_cause_cluster']}: {r['root_cause_finding']}\n\n**Question:** Which of the competing current representations is authoritative?\n\n**Affected tests:** `{r['test']}`\n\n**Option A:** Preserve the tested boundary and repair production. **Option B:** Adopt current behavior and revise the contract.\n\n**Recommendation:** Resolve intent before changing either side. Confidence: {r['confidence']}." for r in policy]
    (OUT / "policy_decisions.md").write_text("\n\n".join(policy_md) + "\n", encoding="utf-8")
    return registry


if __name__ == "__main__":
    result = build()
    print(json.dumps({"failures": len(result["failures"]), "clusters": len(result["root_cause_clusters"]), "classifications": Counter(r["confirmed_classification"] for r in result["failures"])}, default=dict))
