# Cycle U - Sustained Session Validation Closure

Date: 2026-05-30

## Closure Determination

**Cycle U met its success criteria for the deterministic replay lane.**

The sustained-session evidence now proves that the protected social-inquiry path remains stable across a full 25-turn branch, that replay drift remains bounded under metrics-first assertions, and that fallback behavior does not spiral into escalating fallback chaos. The broader direct-intrusion and 50-turn aggregate paths are intentionally supporting/advisory rather than protected release gates.

## What Cycle U Set Out To Prove

Cycle U targeted deterministic sustained-play validation beyond short replay cases. The intended proof areas were:

- **20-50 turn replay suites:** Move from the prior 20-turn social-inquiry baseline toward full 25-turn branch evidence and advisory 50-turn long-branch aggregate evidence.
- **Continuity persistence:** Verify long-session continuity does not reset, lose late anchors, or degrade progressively across the branch, including a replay split/resume boundary.
- **Speaker persistence:** Track selected speaker / continuity target stability over long social inquiry, including unavailable-speaker classification for scene/action fallbacks.
- **Fallback escalation behavior:** Ensure fallback recurrence, fallback ownership, fallback streaks, response-type repair, sanitizer fallback, and late-window fallback behavior stay bounded and explainable.
- **Route stability over time:** Keep route drift bounded without exact-prose or exact-route overfitting.
- **Mutation accumulation checks:** Ensure final-emission mutation lineage and runtime-lineage mutation recurrence accumulate in known, bounded families rather than unknown or runaway patterns.

## Implemented Work

| Cycle | Result |
|---|---|
| U1 | Promoted the canonical social-inquiry replay from the old 20-turn baseline to the full 25-turn `branch_social_inquiry` path and declared it protected in the protected replay manifest. |
| U2 | Added a supporting 25-turn `branch_direct_intrusion` diagnostic replay to stress risky action/visibility paths without promoting it to protected. |
| U3 | Triaged fallback recurrence so sustained-session assertions distinguish bounded fallback evidence from fallback escalation. |
| U4 | Cleaned replay fallback-family projection, including read-side projection for neutral speaker-grounding replacement evidence. |
| U5 | Classified scene/action fallback speaker absence as optional rather than treating every missing `selected_speaker_id` as blocking dialogue drift. |
| U6 | Refined fallback streak classification so nonblocking scene/action fallback streaks do not masquerade as protected social-reply chaos. |
| U7 | Tightened direct-intrusion diagnostic assertions around fallback counts, owner stability, nonblocking fallback families, lineage recurrence, and mutation kinds. |
| U8 | Added a real snapshot/resume persistence probe: turns 1-12, `storage.create_snapshot()`, `storage.load_snapshot()`, then turns 13-25 of `branch_social_inquiry`. |
| U9 | Added advisory 50-turn aggregate validation for the two long branches and documented the scenario-spine `--all-branches` artifact path. |

No production runtime behavior was changed as part of the closure report.

## Final Evidence Set

### Protected

- `tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability`
- Scenario id: `frontier_gate_social_inquiry_25_turn`
- Fixture source: `data/validation/scenario_spines/frontier_gate_long_session.json`
- Branch: `branch_social_inquiry`
- Turn coverage: `inv_01` through `inv_25`
- Protected manifest status: `PROTECTED`

This is the acceptance-blocking sustained-session replay for Cycle U.

### Supporting

- `tests/test_golden_replay.py::test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability`
- `tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting`
- Golden replay helper/projection contracts around fallback family, fallback escalation, speaker-unavailable classification, runtime lineage, and mutation summaries.

These are useful replay signals, but they are not acceptance blockers by manifest status.

### Advisory

- `tests/test_run_scenario_spine_validation.py::test_frontier_gate_long_branch_50_turn_advisory_aggregate_artifacts`
- `tools/run_scenario_spine_validation.py --all-branches`
- Scenario-spine aggregate artifacts:
  - `aggregate_session_health_summary.json`
  - `runtime_lineage_summary.json`
  - `aggregate_operator_summary.md`

The advisory 50-turn aggregate path covers the two long scripted branches:

- `branch_social_inquiry`: 25 turns
- `branch_direct_intrusion`: 25 turns
- Long-branch aggregate total: 50 turns via `aggregate_meta.coverage_turn_total_long_scripted_branches`

`branch_cautious_observe` remains a 10-turn contrast branch for divergence and harness health, not part of the long-scripted 50-turn total.

## Final Observed Outcomes

### Continuity Behavior

The protected social-inquiry replay completes all 25 turns with the scenario-spine continuity bridge reporting a long-session band, `overall_passed: true`, no progressive degradation, and no late reset/amnesia, referent loss, or continuity-anchor late loss reason codes.

The U8 resume probe verifies continuity across a real persistence boundary. It checkpointed after turn 12, restored the snapshot, and continued at turn 13. The restored state preserved `turn_counter == 12` and log count `12`, then completed to turn counter/log count `25`.

### Fallback Behavior

The protected social-inquiry replay keeps fallback bounded:

- `fallback_total_count <= 1`
- `max_fallback_streak <= 1`
- `late_window_fallback_count == 0`
- no fallback owner or lineage-owner oscillation
- no fallback behavior repair loop
- sanitizer fallback count remains `0`
- fallback escalation warnings remain empty

The direct-intrusion branch intentionally has more fallback evidence because it stresses forced-access and scene/action paths. Its diagnostic baseline is currently bounded at 7 fallback turns, with accepted families limited to `neutral_reply_speaker_grounding_bridge` and `gate_terminal_repair`, no blocking fallback streak, no fallback owner changes, no behavior repair loop, and no escalation warnings.

### Speaker Persistence Behavior

The protected social-inquiry replay keeps speaker drift bounded:

- `speaker_change_count <= 2`
- `speaker_missing_count <= 2`

The resume probe confirms the first post-resume turn has a selected speaker and source, and the post-resume segment has no unexpected speaker reset. U5/U6 also ensure that scene/action fallback turns are classified correctly when speaker absence is optional rather than social-dialogue drift.

### Route Stability Behavior

The protected social-inquiry replay keeps route changes bounded:

- `route_change_count <= 2`
- at least 12 resolved routes are observed across the full 25-turn run

The direct-intrusion diagnostic permits wider route movement because the branch exercises risky action, cordon, and forced-access beats. It remains supporting until its stress profile is stable enough for protected thresholds.

### Mutation Accumulation Behavior

The protected replay accepts known final-emission mutation accumulation while bounding recurrence:

- mutation events remain within expected turn-count scale
- recurring runtime-lineage keys are limited to expected strict-social accept and final-emission mutation paths
- fallback mutation recurrence remains bounded

The direct-intrusion diagnostic tightens mutation-family expectations separately, allowing known fallback, final-emission, response-type repair, and speaker-repair mutation families within bounded counts.

### Replay Drift Observations

Cycle U stayed metrics-first. It did not add exact prose validation. Drift is tracked through structural and predicate-level signals:

- route, speaker, fallback, final source, unavailable-field, lineage, and degradation summaries
- no scaffold leakage in protected/supporting long replays
- branch and turn ids retained for fixture-backed replay rows
- aggregate branch divergence and runtime-lineage reporting available in advisory scenario-spine artifacts

## Intentionally Advisory / Not Protected

The following remain intentionally advisory or supporting:

- **Direct-intrusion replay:** Supporting diagnostic only. It is valuable stress evidence but intentionally not protected because its forced-access path has a higher fallback profile and broader route movement.
- **50-turn aggregate validation:** Advisory. The mocked aggregate test verifies artifact/report structure and the 50-turn long-branch accounting, but it is not a hard-fail CI gate for live scenario-spine health.
- **Scenario-spine CLI review path:** Advisory/manual. `tools/run_scenario_spine_validation.py --all-branches` may exercise the app/model path depending on configuration and writes review artifacts; it is not promoted to protected replay acceptance.
- **Short contrast branch:** `branch_cautious_observe` remains a short contrast/harness branch, not a long-session protected path.

## Success Criteria Assessment

### Sustained play remains stable

**Yes.** The protected 25-turn social-inquiry replay completes with bounded route/speaker drift, clean/warning accepted continuity health, no progressive degradation, and no late reset/referent/anchor loss. The resume probe adds supporting evidence that continuity survives a real snapshot restore boundary.

### Replay drift remains bounded

**Yes.** Cycle U asserts structural drift rather than exact prose. The protected path bounds route changes, speaker missing/change counts, fallback count, lineage recurrence, mutation count scale, and scaffold leakage. Supporting paths broaden coverage without weakening the protected gate.

### No escalating fallback chaos

**Yes.** The protected social-inquiry replay allows at most one fallback and rejects late fallback spikes, fallback owner oscillation, repair loops, sanitizer fallback recurrence, and fallback escalation warnings. The direct-intrusion branch has more fallback events by design, but they are classified as bounded, nonblocking diagnostic behavior.

## Final Determination

**Cycle U is ready for closure.**

The deterministic protected lane now proves stable sustained play over the full 25-turn social-inquiry branch. Supporting evidence covers a stress branch and real snapshot/resume persistence. Advisory evidence documents and tests the 50-turn long-branch aggregate reporting path. Further promotion should be deliberate: direct-intrusion and 50-turn aggregate validation should remain advisory/supporting until real full `--all-branches` artifacts are reviewed and accepted as a stable release bar.
