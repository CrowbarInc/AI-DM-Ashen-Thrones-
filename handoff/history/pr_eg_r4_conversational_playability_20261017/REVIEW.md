# Campaign

Campaign: PR-EG-R4 — Conversational Playability Qualification
Identifier: `pr_eg_r4_conversational_playability_20261017`
Date: 2026-10-17
Generated: 2026-10-17T15:35:24.443410+00:00
Purpose: Evaluate integrated adaptive NPC conversation without changing production behavior; stop after R4.

# Executive Summary

**D — CRITICAL ARCHITECTURAL OR INTEGRITY BLOCKER.**

Observed 69 qualification turns in 5 conversations; 4 reached 15 turns. Dialogue quality ≥2: 2/69 (2.9%). Playability ≥2: 1/69 (1.4%).

The stopped sample does not support ordinary conversational playability. Most exchanges expose command or authorization handling, lose a clear addressee/subject, or repeat an irrelevant authored fact. A critical post-rejection delivery bypass requires a D verdict before the planned personal scene or remaining profiles can run. This is a specific integrity finding, not evidence of a leaked secret or corrupted world fact.

Do not close PR-EG. Recommend a narrowly scoped PR-EG-R4-R1 repair of post-gate authoritative-fact preservation: honor final rejection, keep speaker/target authority aligned, and validate the actual emitted text before history commit. Require a production-path regression for the preserved B_skeptical turn 9 and then rerun the full 180-turn adaptive qualification. Do not implement this in R4; await external review.

Objective status: `D — CRITICAL ARCHITECTURAL OR INTEGRITY BLOCKER`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Unchanged relevant regression baseline; adaptive fresh-provider evaluation.

## Tooling changes

- Evaluation runner and evidence report builder.

## Documentation changes

- 27 required reports and CURRENT_REVIEW.

## Generated artifacts

- Frozen protocol, transcripts, per-turn state, scores, metrics, audits and source provenance.

# What Was Tested

- **Focused tests:** No regression expectations changed.
- **Broader relevant tests:** {'passed': 692, 'failed': 25}
- **Full suite:** Not run; relevant historical family only.
- **Runtime validation:** 69 fresh adaptive production HTTP turns.
- **Model/runtime boundary:** Fresh OpenAI Responses API; separate gpt-4.1 evaluator; exact returned model IDs in logs.
- **New regressions:** []
- **Pre-existing failures:** 25 inherited identities.
- **Self-contained bundle review:** Manifest hashes and all 27 reports verified in bundle_verification.json; inherited backup and credentials excluded.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review R4 evidence and recommended next cycle before proceeding.

# Known Problems / Unresolved Findings

## Campaign-specific

- The stopped sample does not support ordinary conversational playability. Most exchanges expose command or authorization handling, lose a clear addressee/subject, or repeat an irrelevant authored fact. A critical post-rejection delivery bypass requires a D verdict before the planned personal scene or remaining profiles can run. This is a specific integrity finding, not evidence of a leaked secret or corrupted world fact.

## Pre-existing baseline

- 25 predecessor relevant-suite failures.

# Missing Concepts / Future Capabilities

- Any broader architecture review requires separate authorization after external review.

# What This Campaign Does NOT Prove

- Population-wide reliability or statistical certainty.
- Full repository regression success.
- Unrestricted improvisation or full process-restart continuity.

# Recommended Next Step

Do not close PR-EG. Recommend a narrowly scoped PR-EG-R4-R1 repair of post-gate authoritative-fact preservation: honor final rejection, keep speaker/target authority aligned, and validate the actual emitted text before history commit. Require a production-path regression for the preserved B_skeptical turn 9 and then rerun the full 180-turn adaptive qualification. Do not implement this in R4; await external review. Stop after PR-EG-R4 and await external review.

# Review Bundle Contents

Bundle file count: `250`
Bundle ZIP size: `000005289542` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_eg_r4/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_eg_r4/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_eg_r4/02_BASELINE_AND_ENVIRONMENT.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/02_BASELINE_AND_ENVIRONMENT.md`.
- `support/artifacts/pr_eg_r4/03_EVALUATION_METHODOLOGY.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/03_EVALUATION_METHODOLOGY.md`.
- `support/artifacts/pr_eg_r4/04_SCENE_DEFINITIONS.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/04_SCENE_DEFINITIONS.md`.
- `support/artifacts/pr_eg_r4/05_SIMULATED_PLAYER_PROFILES.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/05_SIMULATED_PLAYER_PROFILES.md`.
- `support/artifacts/pr_eg_r4/06_PLAYER_GENERATION_METHOD.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/06_PLAYER_GENERATION_METHOD.md`.
- `support/artifacts/pr_eg_r4/07_CONVERSATION_INVENTORY.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/07_CONVERSATION_INVENTORY.md`.
- `support/artifacts/pr_eg_r4/08_COMPLETE_CONVERSATION_TRANSCRIPTS.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/08_COMPLETE_CONVERSATION_TRANSCRIPTS.md`.
- `support/artifacts/pr_eg_r4/09_TURN_LEVEL_SCORING.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/09_TURN_LEVEL_SCORING.md`.
- `support/artifacts/pr_eg_r4/10_PLAYABILITY_SCORING.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/10_PLAYABILITY_SCORING.md`.
- `support/artifacts/pr_eg_r4/11_CONVERSATIONAL_RECOVERY_ANALYSIS.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/11_CONVERSATIONAL_RECOVERY_ANALYSIS.md`.
- `support/artifacts/pr_eg_r4/12_INFORMATION_INTEGRITY_AUDIT.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/12_INFORMATION_INTEGRITY_AUDIT.md`.
- `support/artifacts/pr_eg_r4/13_CONTINUITY_AUDIT.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/13_CONTINUITY_AUDIT.md`.
- `support/artifacts/pr_eg_r4/14_CHARACTERIZATION_ASSESSMENT.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/14_CHARACTERIZATION_ASSESSMENT.md`.
- `support/artifacts/pr_eg_r4/15_PLAYER_FREEDOM_ASSESSMENT.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/15_PLAYER_FREEDOM_ASSESSMENT.md`.
- `support/artifacts/pr_eg_r4/16_PROVIDER_PERFORMANCE.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/16_PROVIDER_PERFORMANCE.md`.
- `support/artifacts/pr_eg_r4/17_REGRESSION_BASELINE.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/17_REGRESSION_BASELINE.md`.
- `support/artifacts/pr_eg_r4/18_INDEPENDENT_EVALUATION_METHOD.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/18_INDEPENDENT_EVALUATION_METHOD.md`.
- `support/artifacts/pr_eg_r4/19_FAILURE_TAXONOMY_RESULTS.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/19_FAILURE_TAXONOMY_RESULTS.md`.
- `support/artifacts/pr_eg_r4/20_FAILURE_CLUSTERING.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/20_FAILURE_CLUSTERING.md`.
- `support/artifacts/pr_eg_r4/21_SEVERITY_AND_PRIORITY_RANKING.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/21_SEVERITY_AND_PRIORITY_RANKING.md`.
- `support/artifacts/pr_eg_r4/22_CONVERSATION_LEVEL_ASSESSMENTS.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/22_CONVERSATION_LEVEL_ASSESSMENTS.md`.
- `support/artifacts/pr_eg_r4/23_ACCEPTANCE_GATE_RESULTS.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/23_ACCEPTANCE_GATE_RESULTS.md`.
- `support/artifacts/pr_eg_r4/24_ROOT_CAUSE_HYPOTHESES.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/24_ROOT_CAUSE_HYPOTHESES.md`.
- `support/artifacts/pr_eg_r4/25_RECOMMENDED_NEXT_ACTION.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/25_RECOMMENDED_NEXT_ACTION.md`.
- `support/artifacts/pr_eg_r4/26_FINAL_VERDICT.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/26_FINAL_VERDICT.md`.
- `support/artifacts/pr_eg_r4/27_SOURCE_AND_EVIDENCE_INVENTORY.md`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/27_SOURCE_AND_EVIDENCE_INVENTORY.md`.
- `support/artifacts/pr_eg_r4/acceptance_gates.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/acceptance_gates.json`.
- `support/artifacts/pr_eg_r4/agent_audit.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/agent_audit.json`.
- `support/artifacts/pr_eg_r4/auxiliary_calls.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/auxiliary_calls.jsonl`.
- `support/artifacts/pr_eg_r4/auxiliary_usage_totals.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/auxiliary_usage_totals.json`.
- `support/artifacts/pr_eg_r4/campaign_usage.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/campaign_usage.json`.
- `support/artifacts/pr_eg_r4/critical_stop_evidence.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/critical_stop_evidence.json`.
- `support/artifacts/pr_eg_r4/dependency_versions.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/dependency_versions.json`.
- `support/artifacts/pr_eg_r4/engine_budget_final.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/engine_budget_final.json`.
- `support/artifacts/pr_eg_r4/engine_usage.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/engine_usage.jsonl`.
- `support/artifacts/pr_eg_r4/environment.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/environment.json`.
- `support/artifacts/pr_eg_r4/evaluation_events.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/evaluation_events.json`.
- `support/artifacts/pr_eg_r4/failure_counts.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/failure_counts.json`.
- `support/artifacts/pr_eg_r4/freeze.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/freeze.json`.
- `support/artifacts/pr_eg_r4/history_gap_monitor_pause.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/history_gap_monitor_pause.json`.
- `support/artifacts/pr_eg_r4/initial_git_status.txt`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/initial_git_status.txt`.
- `support/artifacts/pr_eg_r4/metrics.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/metrics.json`.
- `support/artifacts/pr_eg_r4/playability_metrics.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/playability_metrics.json`.
- `support/artifacts/pr_eg_r4/player_payload_audit.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_payload_audit.json`.
- `support/artifacts/pr_eg_r4/preservation_check.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/preservation_check.json`.
- `support/artifacts/pr_eg_r4/progress.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/progress.json`.
- `support/artifacts/pr_eg_r4/protocol.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/protocol.json`.
- `support/artifacts/pr_eg_r4/regression_comparison.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/regression_comparison.json`.
- `support/artifacts/pr_eg_r4/regression_output.txt`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/regression_output.txt`.
- `support/artifacts/pr_eg_r4/regression_restored_outputs.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/regression_restored_outputs.json`.
- `support/artifacts/pr_eg_r4/regression_run.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/regression_run.json`.
- `support/artifacts/pr_eg_r4/regression_selection.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/regression_selection.json`.
- `support/artifacts/pr_eg_r4/relevant_junit.xml`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/relevant_junit.xml`.
- `support/artifacts/pr_eg_r4/reload_checks.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/reload_checks.jsonl`.
- `support/artifacts/pr_eg_r4/request.txt`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/request.txt`.
- `support/artifacts/pr_eg_r4/review_audit.py`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/review_audit.py`.
- `support/artifacts/pr_eg_r4/root_turn_annotations.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/root_turn_annotations.json`.
- `support/artifacts/pr_eg_r4/sandbox_regression_stall.txt`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/sandbox_regression_stall.txt`.
- `support/artifacts/pr_eg_r4/scorer_comparison.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/scorer_comparison.json`.
- `support/artifacts/pr_eg_r4/scores.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/scores.jsonl`.
- `support/artifacts/pr_eg_r4/stop.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/stop.json`.
- `support/artifacts/pr_eg_r4/stressor_coverage.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/stressor_coverage.json`.
- `support/artifacts/pr_eg_r4/turns.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/turns.jsonl`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/auxiliary_calls.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/auxiliary_calls.jsonl`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/auxiliary_usage_totals.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/auxiliary_usage_totals.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/engine_budget_final.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/engine_budget_final.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/engine_usage.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/engine_usage.jsonl`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/progress.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/progress.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/root_scores.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/root_scores.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/scores.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/scores.jsonl`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/stop.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/stop.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/turns.jsonl`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/turns.jsonl`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_01.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_02.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_03.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_04.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_05.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_06.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_07.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_08.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_09.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_10.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_10.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_11.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_11.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_12.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_12.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_13.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_13.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_14.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_14.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_casual_15.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_casual_15.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_01.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_02.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_03.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_04.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_05.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_06.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_07.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_08.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_09.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_10.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_10.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_11.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_11.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_12.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_12.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_13.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_13.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_14.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_14.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_cooperative_15.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_cooperative_15.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_01.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_02.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_03.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_04.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_05.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_06.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_07.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_08.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_09.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_10.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_10.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_11.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_11.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_12.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_12.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_13.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_13.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_14.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_14.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_curious_15.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_curious_15.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_01.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_02.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_03.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_04.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_05.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_06.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_07.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_08.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_09.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_10.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_10.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_11.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_11.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_12.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_12.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_13.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_13.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_14.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_14.json`.
- `support/artifacts/pr_eg_r4/player_inputs/A_playful_15.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/A_playful_15.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_01.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_02.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_03.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_04.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_05.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_06.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_07.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_08.json`.
- `support/artifacts/pr_eg_r4/player_inputs/B_skeptical_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/player_inputs/B_skeptical_09.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_01.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_02.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_03.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_04.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_05.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_06.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_07.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_08.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_09.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_10.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_10.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_11.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_11.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_12.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_12.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_13.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_13.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_14.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_14.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_15.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_15.json`.
- `support/artifacts/pr_eg_r4/states/A_casual_initial.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_casual_initial.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_01.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_02.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_03.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_04.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_05.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_06.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_07.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_08.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_09.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_10.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_10.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_11.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_11.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_12.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_12.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_13.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_13.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_14.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_14.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_15.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_15.json`.
- `support/artifacts/pr_eg_r4/states/A_cooperative_initial.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_cooperative_initial.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_01.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_02.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_03.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_04.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_05.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_06.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_07.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_08.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_09.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_10.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_10.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_11.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_11.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_12.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_12.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_13.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_13.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_14.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_14.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_15.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_15.json`.
- `support/artifacts/pr_eg_r4/states/A_curious_initial.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_curious_initial.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_01.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_02.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_03.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_04.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_05.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_07.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_08.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_09.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_10.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_10.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_11.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_11.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_12.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_12.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_13.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_13.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_14.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_14.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_15.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_15.json`.
- `support/artifacts/pr_eg_r4/states/A_playful_initial.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/A_playful_initial.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_01.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_02.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_03.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_04.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_04.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_05.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_05.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_06.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_06.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_07.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_07.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_08.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_08.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_09.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_09.json`.
- `support/artifacts/pr_eg_r4/states/B_skeptical_initial.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/states/B_skeptical_initial.json`.
- `support/artifacts/pr_eg_r4/transcripts/A_casual.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/transcripts/A_casual.json`.
- `support/artifacts/pr_eg_r4/transcripts/A_cooperative.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/transcripts/A_cooperative.json`.
- `support/artifacts/pr_eg_r4/transcripts/A_curious.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/transcripts/A_curious.json`.
- `support/artifacts/pr_eg_r4/transcripts/A_playful.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/transcripts/A_playful.json`.
- `support/artifacts/pr_eg_r4/transcripts/B_skeptical.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/transcripts/B_skeptical.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/player_inputs/A_cooperative_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/player_inputs/A_cooperative_02.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/player_inputs/A_cooperative_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/player_inputs/A_cooperative_03.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/states/A_cooperative_01.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/states/A_cooperative_01.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/states/A_cooperative_02.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/states/A_cooperative_02.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/states/A_cooperative_03.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/states/A_cooperative_03.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/states/A_cooperative_initial.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/states/A_cooperative_initial.json`.
- `support/artifacts/pr_eg_r4/interrupted_monitor_run/transcripts/A_cooperative.json`: PR-EG-R4 evaluation, provenance or transcript evidence Canonical source: `artifacts/pr_eg_r4/interrupted_monitor_run/transcripts/A_cooperative.json`.
- `support/game/api.py`: Evaluated production path or evaluation setup source Canonical source: `game/api.py`.
- `support/game/api_turn_support.py`: Evaluated production path or evaluation setup source Canonical source: `game/api_turn_support.py`.
- `support/game/noncombat_resolution.py`: Evaluated production path or evaluation setup source Canonical source: `game/noncombat_resolution.py`.
- `support/game/social.py`: Evaluated production path or evaluation setup source Canonical source: `game/social.py`.
- `support/game/dialogue_authority.py`: Evaluated production path or evaluation setup source Canonical source: `game/dialogue_authority.py`.
- `support/game/conversational_continuity.py`: Evaluated production path or evaluation setup source Canonical source: `game/conversational_continuity.py`.
- `support/game/conversational_orchestration.py`: Evaluated production path or evaluation setup source Canonical source: `game/conversational_orchestration.py`.
- `support/game/expressive_dialogue.py`: Evaluated production path or evaluation setup source Canonical source: `game/expressive_dialogue.py`.
- `support/game/ordinary_semantic_ownership.py`: Evaluated production path or evaluation setup source Canonical source: `game/ordinary_semantic_ownership.py`.
- `support/game/interaction_completion.py`: Evaluated production path or evaluation setup source Canonical source: `game/interaction_completion.py`.
- `support/game/immutable_valid_response.py`: Evaluated production path or evaluation setup source Canonical source: `game/immutable_valid_response.py`.
- `support/game/interpretation_proposal.py`: Evaluated production path or evaluation setup source Canonical source: `game/interpretation_proposal.py`.
- `support/game/live_chat_interpretation.py`: Evaluated production path or evaluation setup source Canonical source: `game/live_chat_interpretation.py`.
- `support/game/storage.py`: Evaluated production path or evaluation setup source Canonical source: `game/storage.py`.
- `support/game/provider_budget.py`: Evaluated production path or evaluation setup source Canonical source: `game/provider_budget.py`.
- `support/tools/qualify_pr_eg_r4.py`: Evaluated production path or evaluation setup source Canonical source: `tools/qualify_pr_eg_r4.py`.
- `support/tools/report_pr_eg_r4.py`: Evaluated production path or evaluation setup source Canonical source: `tools/report_pr_eg_r4.py`.
- `support/tests/test_pr_ef_gm_authority.py`: Evaluated production path or evaluation setup source Canonical source: `tests/test_pr_ef_gm_authority.py`.
- `support/tests/test_pr_du_player_pipeline.py`: Evaluated production path or evaluation setup source Canonical source: `tests/test_pr_du_player_pipeline.py`.
- `support/tests/helpers/turn_pipeline_http_fixtures.py`: Evaluated production path or evaluation setup source Canonical source: `tests/helpers/turn_pipeline_http_fixtures.py`.
- `support/experiments/pr_dq/world.py`: Evaluated production path or evaluation setup source Canonical source: `experiments/pr_dq/world.py`.

## Explicit omissions

- `artifacts/pr_eg_r4/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_eg_r4/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_eg_r4/interrupted_monitor_run/preservation_check.json`: duplicate content of artifacts/pr_eg_r4/preservation_check.json; canonical reference retained
- `artifacts/pr_eg_r4/states/A_playful_06.json`: duplicate content of artifacts/pr_eg_r4/states/A_playful_05.json; canonical reference retained
- `artifacts/pr_eg_r4/interrupted_monitor_run/player_inputs/A_cooperative_01.json`: duplicate content of artifacts/pr_eg_r4/player_inputs/A_cooperative_01.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
