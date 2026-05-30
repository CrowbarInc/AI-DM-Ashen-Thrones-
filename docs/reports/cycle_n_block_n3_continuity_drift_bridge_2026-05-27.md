# Block N3 - Continuity Drift Bridge

## Summary
Block N3 bridges the protected 20-turn golden replay lane to the existing scenario-spine continuity/degradation evaluator without adding live model calls, semantic repair, or brittle transcript assertions.

The bridge projects golden replay observations into evaluator-compatible transcript rows, preserves emitted GM text and structural replay metadata, and adds deterministic scenario-spine audit context so text-oriented continuity heuristics can evaluate the replay as a sustained session rather than as isolated normalized NPC replies.

## Files Changed
| File | Change |
|---|---|
| `tests/helpers/golden_replay.py` | Added golden-replay-to-scenario-spine projection, continuity drift evaluation helper, deterministic audit context projection, and continuity summary fields in the long-session markdown renderer. |
| `tests/test_golden_replay.py` | Extended the protected 20-turn replay to evaluate scenario-spine continuity/degradation and assert metrics-first drift invariants. |
| `docs/reports/cycle_n_block_n3_continuity_drift_bridge_2026-05-27.md` | Documents the N3 implementation, validation, CI impact, and next recommendation. |

## Evaluator Seam Chosen
The additive seam is:

- `tests/helpers/golden_replay.py::project_golden_replay_turns_to_scenario_spine_rows(...)`
- `tests/helpers/golden_replay.py::evaluate_golden_replay_continuity_drift(...)`
- existing `game.scenario_spine_eval.evaluate_scenario_spine_session(...)`

This keeps the evaluator unchanged and avoids introducing a second continuity framework. The projection converts each observed golden replay turn into the existing scenario-spine transcript row shape with:

- turn index
- turn id from `frontier_gate_long_session.json`
- player prompt
- emitted GM text
- API success flag
- complete scenario-spine meta envelope
- golden replay observation metadata
- normalized runtime lineage events
- deterministic continuity audit context derived from the scenario-spine anchors

## Continuity Metrics Added
The protected 20-turn replay now records and/or reports:

- scenario-spine session health classification
- long-session band
- overall evaluator pass/fail
- degradation-over-time detection
- degradation reason codes
- late-window continuity signals
- narrative grounding axis pass/fail
- branch coherence axis pass/fail
- existing route/speaker/fallback/mutation/unavailable/lineage recurrence summaries

## Assertions Added
The 20-turn protected replay now asserts:

- evaluator classifies the session as `clean` or `warning`
- evaluator overall pass remains true
- long-session band is `standard`
- no progressive degradation is detected
- no late-session reset/amnesia reason code
- no progressive or strong generic filler growth reason code
- no late debug/system leak reason code
- no late referent loss reason code
- no late continuity-anchor loss reason code
- narrative grounding passes
- branch coherence passes

These are aggregate structural assertions. They do not compare exact GM prose.

## Artifact Changes
`render_long_session_replay_summary_markdown(...)` now includes compact continuity drift fields:

- continuity classification
- degradation detected
- degradation reasons
- late-window signals

The artifact still keeps the existing per-turn compact table:

- turn number
- route
- speaker
- fallback family
- fallback owner
- mutation flag
- unavailable fields
- lineage event kinds

## Runtime Impact
Measured validation runtimes on this workspace:

| Command | Result | Runtime |
|---|---:|---:|
| `python -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability -q --tb=short --basetemp=codex_pytest_tmp_cycle_n3_single2` | PASS | 6.6s |
| `python -m pytest tests/test_golden_replay.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n3_requested` | PASS | 9.05s |
| `python -m pytest tests/test_golden_replay.py tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_fallback_behavior_gate.py tests/test_fallback_behavior_validator.py tests/test_model_routing_escalation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n3_broader` | PASS | 10.16s |
| `python -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_cycle_n3_marker` | PASS | 9.20s |

## CI Impact
N3 remains protected/default CI safe:

- no live model calls
- mocked GPT only
- deterministic scenario-spine fixture input
- no randomized generation
- no timing-sensitive assertions
- runtime remains in the same small protected lane range

No `slow` marker is recommended for the 20-turn continuity bridge.

## Risks / Follow-Ups
- The scenario-spine evaluator is still partly text-oriented, so the bridge adds deterministic audit context to avoid false late-anchor loss from compact normalized runtime replies.
- This does not prove 50-turn stress behavior.
- This does not harden fallback escalation thresholds.
- This does not add semantic quality grading for GM prose.
- Continuity drift enforcement is now present at the protected replay layer, but deeper runtime-native continuity metadata would make future audits less dependent on text heuristics.

## Recommended Next Block
Recommended next block: **N4 fallback escalation guard**.

Reason: the 20-turn lane now has structural stability and continuity drift coverage. The next highest-value gap is turning fallback recurrence/owner lineage observations into a focused escalation guard before expanding to longer nightly stress.
