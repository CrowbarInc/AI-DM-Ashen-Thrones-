from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import build_validation_portfolio as portfolio


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "validation" / "validation_family_registry.json"
FAILURES_PATH = ROOT / "artifacts" / "validation_portfolio" / "current_failure_classification.json"
REPORT_PATH = ROOT / "docs" / "validation_portfolio_rationalization.md"


@pytest.fixture(scope="module")
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def failures() -> dict:
    return json.loads(FAILURES_PATH.read_text(encoding="utf-8"))


def test_registry_and_failure_map_validate(registry: dict, failures: dict) -> None:
    portfolio.validate(registry, failures)


def test_every_family_has_disposition_claim_authority_and_rationale(registry: dict) -> None:
    for family in registry["families"]:
        assert family["disposition"] in portfolio.DISPOSITIONS
        assert family["claim_classes"]
        assert family["current_authority"] in portfolio.AUTHORITIES
        assert family["recommended_authority"] in portfolio.AUTHORITIES
        assert family["rationale"].strip()


def test_uncertainty_is_explicit(registry: dict, failures: dict) -> None:
    uncertain_families = [family for family in registry["families"] if family["confidence"] != "HIGH"]
    uncertain_failures = [row for row in failures["failures"] if row["confidence"] != "HIGH"]
    assert uncertain_families
    assert uncertain_failures
    assert all(family["rationale"] for family in uncertain_families)
    assert all(row["reason"] for row in uncertain_failures)


def test_observed_failures_reconcile_and_map_to_family(registry: dict, failures: dict) -> None:
    family_ids = {family["family_id"] for family in registry["families"]}
    assert failures["observed_failure_count"] == 36
    assert len(failures["failures"]) == 36
    assert all(row["family_id"] in family_ids for row in failures["failures"])
    assert len({row["test"] for row in failures["failures"]}) == 36


def test_disposition_safeguards_are_complete(registry: dict) -> None:
    for family in registry["families"]:
        disposition = family["disposition"]
        if disposition == "RETIRE":
            assert family["evidence_loss_risk"]
        elif disposition == "CONSOLIDATE":
            assert family["surviving_authority"]
            assert family["evidence_loss_risk"]
        elif disposition == "MODERNIZE":
            assert family["preserved_purpose"]
        elif disposition == "QUARANTINE":
            assert family["unresolved_question"]


def test_target_architecture_references_known_authorities(registry: dict) -> None:
    family_ids = {family["family_id"] for family in registry["families"]}
    referenced = {family_id for layer in registry["target_architecture"] for family_id in layer["authorities"]}
    assert referenced <= family_ids
    assert any(layer["layer"] == "Rendered player experience" and not layer["authorities"] for layer in registry["target_architecture"])


def test_generated_views_are_current(registry: dict, failures: dict) -> None:
    assert (ROOT / "docs" / "validation_family_registry.md").read_text(encoding="utf-8") == portfolio.render_registry(registry)
    assert (ROOT / "artifacts" / "validation_portfolio" / "current_failure_summary.md").read_text(encoding="utf-8") == portfolio.render_failure_summary(failures)


def test_primary_report_contains_required_decisions_and_limits() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "## Target validation architecture",
        "## Staged rationalization plan",
        "## Risk analysis",
        "## Human decision surface",
        "## Validation gaps",
        "## Mock and stub authority",
        "No test, gate, evaluator, fixture, gameplay path, prompt, threshold",
    ]
    assert all(text in report for text in required)


def test_audit_inputs_are_not_mutated_by_renderer(registry: dict, failures: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    before_registry = REGISTRY_PATH.read_bytes()
    before_failures = FAILURES_PATH.read_bytes()
    monkeypatch.setattr(portfolio, "REGISTRY_VIEW_PATH", tmp_path / "registry.md")
    monkeypatch.setattr(portfolio, "SUMMARY_PATH", tmp_path / "summary.md")
    portfolio.build()
    assert REGISTRY_PATH.read_bytes() == before_registry
    assert FAILURES_PATH.read_bytes() == before_failures


def test_registry_counts_match_generated_view(registry: dict) -> None:
    view = portfolio.render_registry(registry)
    assert f"Families: **{len(registry['families'])}**" in view
    for disposition in portfolio.DISPOSITIONS:
        expected = sum(family["disposition"] == disposition for family in registry["families"])
        assert f"| {disposition} | {expected} |" in view


def test_review_handoff_config_names_required_outputs() -> None:
    config = json.loads(
        (ROOT / "data" / "validation" / "review_handoffs" / "validation_portfolio_rationalization.json").read_text(encoding="utf-8")
    )
    paths = {item["path"] for item in config["supporting_files"]}
    assert {
        "docs/validation_portfolio_rationalization.md",
        "data/validation/validation_family_registry.json",
        "docs/validation_family_registry.md",
        "artifacts/validation_portfolio/current_failure_classification.json",
        "artifacts/validation_portfolio/current_failure_summary.md",
    } <= paths
