from __future__ import annotations

import json
from pathlib import Path

from game.playability_eval import evaluate_playability
from tests.helpers.behavioral_gauntlet_eval import evaluate_behavioral_gauntlet


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "validation" / "validation_family_registry.json"
AUTHORITY_LEDGER = ROOT / "artifacts" / "validation_rationalization" / "authority_changes.json"
RETIREMENT_LEDGER = ROOT / "artifacts" / "validation_rationalization" / "retired_tests.json"


def _families() -> dict[str, dict]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {row["family_id"]: row for row in payload["families"]}


def test_historical_closeout_retirement_is_fully_accounted() -> None:
    ledger = json.loads(RETIREMENT_LEDGER.read_text(encoding="utf-8"))
    assert ledger["retired_node_count"] == 16
    assert len(ledger["retired_tests"]) == 16
    assert len(ledger["replacement_tests"]) == 2
    assert ledger["unique_evidence_lost"] is False


def test_historical_closeout_provenance_is_canonical_and_available() -> None:
    ledger = json.loads(RETIREMENT_LEDGER.read_text(encoding="utf-8"))
    for path in ledger["preserved_provenance"][:5]:
        assert (ROOT / path).exists(), path
    manifest = (ROOT / "docs" / "audits" / "audit_manifest.md").read_text(encoding="utf-8")
    assert "BW_protected_replay_trend_window_closeout.md" in manifest
    assert "BZ_protected_replay_trend_window_2_closeout.md" in manifest


def test_authority_change_ledger_distinguishes_claim_from_execution_changes() -> None:
    changes = json.loads(AUTHORITY_LEDGER.read_text(encoding="utf-8"))["changes"]
    by_family = {row["validation_family"]: row for row in changes}
    assert set(by_family) == {
        "GENERATED_CLOSEOUT_ASSERTIONS",
        "PLAYABILITY_RUNTIME",
        "GOLDEN_PROTECTED_REPLAY",
        "BEHAVIORAL_GAUNTLET",
    }
    assert by_family["GENERATED_CLOSEOUT_ASSERTIONS"]["execution_behavior_changed"] is True
    assert all(
        not by_family[family]["execution_behavior_changed"]
        for family in ("PLAYABILITY_RUNTIME", "GOLDEN_PROTECTED_REPLAY", "BEHAVIORAL_GAUNTLET")
    )
    assert all(row["evidence_generation_changed"] is False for row in changes)


def test_registry_reflects_only_implemented_authority_changes() -> None:
    families = _families()
    assert families["GENERATED_CLOSEOUT_ASSERTIONS"]["current_authority"] == "HISTORICAL_ONLY"
    assert families["PLAYABILITY_RUNTIME"]["current_authority"] == "SUPPORTING_EVIDENCE"
    assert families["GOLDEN_PROTECTED_REPLAY"]["current_authority"] == "RELEASE_GATE"
    assert families["BEHAVIORAL_GAUNTLET"]["current_authority"] == "DIAGNOSTIC"
    assert families["OWNERSHIP_IMPORT_GOVERNANCE"]["disposition"] == "QUARANTINE"
    assert families["REPLAY_PROJECTION_DIAGNOSTICS"]["confidence"] == "MEDIUM"


def test_playability_still_executes_and_exposes_semantic_evidence() -> None:
    result = evaluate_playability(
        {
            "player_input": "What does the posted notice say?",
            "gm_output": {"player_facing_text": "The notice lists a dusk curfew and a reward for a missing courier."},
        }
    )
    assert result["semantic_result"] in {"PASS", "FAIL", "UNCHECKED", "NOT_APPLICABLE", "INVALID_RUN"}
    assert set(result["mandatory_gates"]) == {"malformed_output", "player_intent_addressed"}
    assert "diagnostic_quality" in result
    assert set(result["axes"]) == {"direct_answer", "player_intent", "logical_escalation", "immersion"}


def test_playability_docs_state_supporting_authority() -> None:
    text = (ROOT / "docs" / "playability_validation.md").read_text(encoding="utf-8")
    assert "supporting player-facing evidence" in text
    assert "not independent proof that gameplay is acceptable" in text


def test_protected_replay_claim_is_structural_without_weakening_gate() -> None:
    manifest = (ROOT / "docs" / "testing" / "protected_replay_manifest.md").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "convergence-checks.yml").read_text(encoding="utf-8")
    assert "controlled structural replay" in manifest
    assert "does not establish production-model semantics" in manifest
    assert "python -m pytest -m golden_replay -q" in workflow
    assert "controlled structural replay acceptance" in workflow


def test_behavioral_gauntlet_still_detects_enumerated_antipatterns() -> None:
    result = evaluate_behavioral_gauntlet(
        [{"player_text": "I look around calmly.", "gm_text": "How dare you - you're a liar and a traitor, you fool."}],
        expected_axis={"neutrality"},
    )
    assert result["overall_passed"] is False
    assert "ungrounded_hostility" in result["axes"]["neutrality"]["reason_codes"]
    assert _families()["BEHAVIORAL_GAUNTLET"]["current_authority"] == "DIAGNOSTIC"


def test_deferred_families_are_absent_from_implementation_locations() -> None:
    changes = json.loads(AUTHORITY_LEDGER.read_text(encoding="utf-8"))["changes"]
    locations = {path for row in changes for path in row["implementation_locations"]}
    assert not any("compat_import" in path or "ownership_write" in path for path in locations)
    assert not any("golden_replay_projection" in path or "failure_classifier" in path for path in locations)


def test_review_handoff_config_includes_required_implementation_outputs() -> None:
    config = json.loads(
        (
            ROOT
            / "data"
            / "validation"
            / "review_handoffs"
            / "high_confidence_validation_rationalization.json"
        ).read_text(encoding="utf-8")
    )
    paths = {row["path"] for row in config["supporting_files"]}
    assert {
        "docs/high_confidence_validation_rationalization.md",
        "artifacts/validation_rationalization/authority_changes.json",
        "artifacts/validation_rationalization/retired_tests.json",
        "artifacts/validation_rationalization/baseline_comparison.json",
        "data/validation/validation_family_registry.json",
        "artifacts/validation_portfolio/current_failure_classification.json",
    } <= paths
