"""PR-PLAY-71V regression lanes. Provider calls stay disabled. No source edits."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from artifacts.pr_play_66 import run_regression as runner

runner.OUT = Path(__file__).resolve().parent
HISTORICAL_FOCUSED = {
    "tests.test_pr_play_49_anchored_narration::test_no_gameplay_wiring_or_effects",
    "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
    "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
    "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues",
}
HISTORICAL_BOUNDARY = {
    "tests.test_start_campaign_api::test_start_campaign_emits_opening_and_sets_started",
    "tests.test_start_campaign_api::test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text",
    "tests.test_start_campaign_api::test_start_campaign_promotes_valid_upstream_prepared_scene_opening",
    "tests.test_start_campaign_api::test_failed_start_campaign_does_not_mark_started",
    "tests.test_pr_play_37_opening_recovery::test_http_invalid_declaration_discards_provider_text",
    "tests.test_pr_play_37_opening_recovery::test_http_composer_failure_does_not_commit",
}
FOCUSED = runner.SUITES + [
    "tests/test_pr_play_68_structured_publication.py",
    "tests/test_pr_play_69_target_references.py",
    "tests/test_pr_play_70_branching.py",
    "tests/test_pr_play_71_lifecycle.py",
    "tests/test_pr_play_71_persistence_recovery.py",
    "tests/test_pr_play_71v_verification.py",
]
BOUNDARY = [
    "tests/test_pr_play_67_player_projection.py",
    "tests/test_ui_mode_backend_integration.py",
    "tests/test_ui_mode_regression_matrix_objective15.py",
    "tests/test_frontend_ui_mode_hardening_objective15.py",
    "tests/test_state_channels.py",
    "tests/test_snapshots.py",
    "tests/test_start_campaign_api.py",
    "tests/test_pr_play_37_opening_recovery.py",
]
BROADER = ["tests/test_pr_cx_authority_assurance.py"]


def classify(result, historical):
    failed = set(result["failed_nodeids"])
    result["historical_failures_seen"] = sorted(failed & historical)
    result["new_failures"] = sorted(failed - historical)
    result["historical_not_seen"] = sorted(historical - failed)
    return result


def main():
    saved = runner.snapshot(runner.PROTECT_ROOTS + [ROOT / "data"])
    try:
        focused = classify(runner.run_pytest("focused", FOCUSED), HISTORICAL_FOCUSED)
        boundary = classify(runner.run_pytest("boundary", BOUNDARY), HISTORICAL_BOUNDARY)
        broader = runner.run_pytest("broader", BROADER)
    finally:
        restored = runner.restore(saved)
    summary = {
        "focused": focused,
        "boundary": boundary,
        "broader": broader,
        "restored": restored,
        "historical_focused": sorted(HISTORICAL_FOCUSED),
        "historical_boundary": sorted(HISTORICAL_BOUNDARY),
    }
    (runner.OUT / "regression_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "focused_passed": focused["passed"],
        "focused_failed": focused["failed"],
        "focused_new": focused["new_failures"],
        "boundary_passed": boundary["passed"],
        "boundary_failed": boundary["failed"],
        "boundary_new": boundary["new_failures"],
        "broader_passed": broader["passed"],
        "broader_failed": broader["failed"],
    }, indent=2))


if __name__ == "__main__":
    main()
