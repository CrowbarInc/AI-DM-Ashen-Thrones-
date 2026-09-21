"""Accounting locks for Validation Cleanup & Governance Repair."""

from tools.build_validation_cleanup import FROZEN, actionable_inventory


def test_cleanup_inventory_accounts_for_seventeen_actionable_failures_once() -> None:
    tests = [test for row in actionable_inventory() for test in row["affected_tests"]]
    assert len(tests) == 17
    assert len(set(tests)) == 17


def test_cleanup_inventory_excludes_frozen_policy_and_unresolved_cases() -> None:
    actionable = {test for row in actionable_inventory() for test in row["affected_tests"]}
    frozen = {test for tests in FROZEN.values() for test in tests}
    assert len(frozen) == 6
    assert not (actionable & frozen)


def test_cleanup_inventory_uses_only_authorized_classifications_and_cites_authority() -> None:
    allowed = {
        "VALIDATION_DEFECT",
        "STALE_EXPECTATION",
        "STALE_FIXTURE",
        "GOVERNANCE_DRIFT",
        "TEST_ONLY_ARCHITECTURE_RESIDUE",
    }
    for row in actionable_inventory():
        assert row["classification"] in allowed
        assert str(row["current_authority"]).startswith("docs/")
        assert row["production_behavior_impact"] == "NONE"
