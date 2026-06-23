# Cycle N - Long-Session Stability Closure

## Summary
Cycle N now has a protected/default 20-turn golden replay lane for sustained-play structural stability:

- scenario source: `data/validation/scenario_spines/frontier_gate_long_session.json`
- branch: `branch_social_inquiry`
- protected scenario id: `frontier_gate_social_inquiry_20_turn`
- execution: existing `run_golden_replay(...)`
- model dependency: deterministic mocked GPT only
- assertion style: aggregate structural metrics, continuity/degradation evaluator output, fallback escalation metrics, and compact artifact review

N5 refined the operator artifact so the protected replay failure context clearly surfaces route stability, speaker persistence, continuity/degradation classification, fallback escalation, mutation/unavailable counts, and lineage recurrence without duplicating noisy legacy fallback fields.

## What Cycle N Now Proves
The protected 20-turn lane now proves:

- all 20 deterministic turns complete without a hard replay failure
- route changes remain bounded across sustained play
- speaker persistence remains bounded and visible
- scaffold/internal text does not leak
- scenario-spine continuity bridge classifies the replay as clean/warning with no progressive degradation
- no late-session reset/amnesia, debug leak, referent loss, or continuity-anchor loss reason code appears
- fallback recurrence remains bounded to the fixture baseline
- fallback streaks do not grow
- no late-session fallback spike appears
- fallback owner/lineage owner does not oscillate
- no fallback behavior repair loop appears
- unavailable-to-fallback coupling stays bounded
- runtime lineage recurrence remains visible in the artifact

## What Remains Unproven
Cycle N does not prove:

- 50-turn or longer stress behavior
- nightly/manual stress stability
- live model behavior
- semantic quality of generated prose
- final-emission semantic repair correctness
- model routing escalation frequency inside long-session golden replay observations
- scenario-spine CLI health as a hard-fail gate

50-turn/nightly testing should remain future work. The recommended future shape is a separate nightly/manual stress lane, not an immediate expansion of the protected/default 20-turn gate.

## Files Changed
| File | Closure Role |
|---|---|
| `tests/helpers/golden_replay.py` | Long-session summary, continuity bridge, fallback escalation metrics, and compact artifact rendering. |
| `tests/test_golden_replay.py` | Protected 20-turn replay, continuity/fallback assertions, and renderer contract test. |
| `docs/testing/protected_replay_manifest.md` | Declares `frontier_gate_social_inquiry_20_turn` as a protected end-to-end replay scenario. |
| `tests/README_TESTS.md` | Notes that golden replay now includes the protected 20-turn Frontier Gate stability lane. |
| `docs/cycles/cycle_n_block_n1_canonical_20_turn_replay_2026-05-27.md` | N1 implementation report. |
| `docs/cycles/cycle_n_block_n3_continuity_drift_bridge_2026-05-27.md` | N3 implementation report. |
| `docs/cycles/cycle_n_block_n4_fallback_escalation_guard_2026-05-27.md` | N4 implementation report. |
| `docs/cycles/cycle_n_long_session_stability_closure_2026-05-27.md` | Cycle N closure report. |

## Artifact Review
The long-session artifact now reports:

- route frequency and route changes
- speaker frequency and speaker changes/missing count
- fallback total count
- fallback family/owner summaries
- fallback lineage kinds
- max fallback streak
- late-window fallback count
- fallback escalation warnings
- mutation turn count
- unavailable counts
- lineage event frequency
- lineage recurrence
- continuity warnings/violations
- continuity classification
- degradation status/reasons
- late-window continuity signals
- compact per-turn route/speaker/fallback/mutation/unavailable/lineage table

Removed/tightened noisy fields:

- removed duplicate top-level legacy fallback frequency/owner lines from the long-session markdown summary
- replaced full mutation turn list with mutation turn count in the artifact header

## Tests Run
| Command | Result | Runtime |
|---|---:|---:|
| `python -m pytest tests/test_golden_replay.py::test_long_session_replay_summary_renderer_surfaces_operator_metrics tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability -q --tb=short --basetemp=codex_pytest_tmp_cycle_n5_smoke` | PASS | 7.7s |
| `python -m pytest tests/test_golden_replay.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n5_golden_file` | PASS | 6.35s |
| `python -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_cycle_n5_marker` | PASS | 7.19s |
| `python -m pytest tests/test_golden_replay.py tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_fallback_behavior_gate.py tests/test_fallback_behavior_validator.py tests/test_model_routing_escalation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n5_broader` | PASS | 7.79s |

## CI Safety Status
Cycle N remains protected/default CI safe:

- deterministic fixture
- mocked GPT only
- no live model calls
- no exact prose matching
- no final-emission behavior changes
- no semantic repair logic
- no architecture rewrite
- runtime remains small
- no `slow` marker recommended for the 20-turn protected replay

## Closure Decision
Cycle N can be considered complete for the protected 20-turn sustained-play stability objective.

Future work should target a separate 50-turn/nightly stress lane after operator artifact ergonomics and failure triage expectations are stable.
