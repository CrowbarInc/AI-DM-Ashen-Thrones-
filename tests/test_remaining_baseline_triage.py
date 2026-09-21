import json
from pathlib import Path

from tools.build_baseline_triage import CLUSTERS, build, junit_counts


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "baseline_triage"


def _registry():
    return json.loads((OUT / "failure_investigation_registry.json").read_text(encoding="utf-8"))


def test_registry_accounts_for_every_failure_exactly_once():
    build()
    rows = _registry()["failures"]
    tests = [row["test"] for row in rows]
    assert len(rows) == len(set(tests)) == 36
    assert all(row["validation_family"] for row in rows)
    assert all(row["confirmed_classification"] for row in rows)


def test_clusters_and_queues_reconcile_to_registry():
    build()
    registry = _registry()
    clustered = [test for cluster in registry["root_cause_clusters"] for test in cluster["affected_tests"]]
    assert sorted(clustered) == sorted(row["test"] for row in registry["failures"])
    assert len(registry["root_cause_clusters"]) == len(CLUSTERS)
    repair = json.loads((OUT / "confirmed_repair_queue.json").read_text(encoding="utf-8"))["items"]
    cleanup = json.loads((OUT / "validation_cleanup_queue.json").read_text(encoding="utf-8"))["items"]
    known = {row["test"] for row in registry["failures"]}
    assert repair and cleanup
    assert all(set(item["affected_tests"]) <= known for item in repair + cleanup)


def test_high_confidence_current_defects_cite_authority():
    build()
    for row in _registry()["failures"]:
        if row["confidence"] == "HIGH" and row["confirmed_classification"] in {
            "CONFIRMED_PRODUCT_DEFECT", "CONFIRMED_ARCHITECTURE_DEFECT"
        }:
            assert row["requirement_source"].startswith("docs/")
            assert (ROOT / row["requirement_source"]).is_file()


def test_pre_baseline_is_junit_backed_and_consistent():
    build()
    counts = junit_counts(OUT / "pre_triage_suite.xml")
    assert counts == _registry()["baseline"]
    assert counts["failed"] == 36
    post = junit_counts(OUT / "post_triage_suite.xml")
    assert post == _registry()["post_baseline"]
    assert post["failed"] == counts["failed"]
    assert post["skipped"] == counts["skipped"]


def test_policy_rows_map_to_policy_document():
    build()
    text = (OUT / "policy_decisions.md").read_text(encoding="utf-8")
    rows = [r for r in _registry()["failures"] if r["human_judgment_required"]]
    assert rows
    assert all(r["root_cause_cluster"] in text for r in rows)
