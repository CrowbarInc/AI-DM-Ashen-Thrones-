# Block N4 - Fallback Escalation Guard

## Summary
Block N4 adds fallback escalation guardrails to the protected 20-turn golden replay without changing final-emission behavior.

The new guard summarizes fallback recurrence, ownership stability, repair usage, unavailable-field coupling, and late-window fallback behavior from existing golden replay observations and runtime lineage events. Assertions remain aggregate and baseline-aware for the current `frontier_gate_social_inquiry_20_turn` fixture.

## Files Changed
| File | Change |
|---|---|
| `tests/helpers/golden_replay.py` | Added fallback escalation summarization metrics, active telemetry token normalization, fallback window/streak helpers, and fallback escalation fields in the compact long-session markdown artifact. Also projects `fallback_behavior_repair_mode` for read-side audit visibility. |
| `tests/test_golden_replay.py` | Added protected 20-turn fallback escalation assertions to the canonical long-session replay. |
| `docs/cycles/cycle_n_block_n4_fallback_escalation_guard_2026-05-27.md` | Documents N4 metrics, assertions, artifacts, validation, and CI status. |

## Metrics Added
`summarize_fallback_escalation_observations(...)` now reports:

- total fallback count
- fallback turn indices
- fallback family counts
- fallback owner counts
- runtime-lineage fallback kind counts
- runtime-lineage fallback owner counts
- fallback counts by early/middle/late window
- max consecutive fallback streak
- late-window fallback count
- fallback owner change count
- fallback lineage owner change count
- fallback behavior repair turns/count
- response-type repair turns/count
- sanitizer fallback turns/count
- unavailable-with-fallback count
- fallback-family-unavailable-with-fallback count
- fallback-selected-without-family count
- escalation warnings
- model routing escalation observability marker

Model routing escalation is not currently observable from the protected golden replay turn observations, so the metric is explicitly marked as not observable instead of inferred.

## Assertions Added
The protected 20-turn replay now asserts:

- fallback total count stays at or below the current baseline allowance of one selected fallback event
- max fallback streak is at most one
- late-window fallback count is zero
- fallback owner change count is zero
- fallback lineage owner change count is zero
- fallback behavior repair count is zero
- response-type repair count is at most one
- sanitizer fallback count is zero
- unavailable-with-fallback coupling is at most one turn
- fallback-selected-without-family coupling is at most one turn
- escalation warnings are empty
- model routing escalation is not treated as observable in this replay lane

These assertions do not compare exact prose and do not alter runtime fallback behavior.

## Artifact Changes
`render_long_session_replay_summary_markdown(...)` now includes:

- fallback total count
- fallback families
- fallback owners
- fallback lineage kinds
- max fallback streak
- late-window fallback count
- fallback escalation warnings

The per-turn table remains compact and still shows route, speaker, fallback, owner, mutation, unavailable fields, and lineage event kinds.

## Test Commands / Results
| Command | Result | Runtime |
|---|---:|---:|
| `python -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability -q --tb=short --basetemp=codex_pytest_tmp_cycle_n4_single2` | PASS | 5.5s |
| `python -m pytest tests/test_golden_replay.py tests/test_fallback_behavior_gate.py tests/test_fallback_behavior_validator.py tests/test_model_routing_escalation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n4_requested` | PASS | 6.34s |
| `python -m pytest tests/test_golden_replay.py tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_fallback_behavior_gate.py tests/test_fallback_behavior_validator.py tests/test_model_routing_escalation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n4_broader` | PASS | 7.79s |
| `python -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_cycle_n4_marker` | PASS | 7.21s |

## CI Safety Status
N4 remains protected/default CI safe:

- no live model calls
- mocked GPT only
- deterministic fixture
- no exact prose matching
- no final-emission behavior changes
- runtime remains small
- no `slow` marker recommended

## Recommended Next Block
Recommended next block: **N5 long-session artifact refinement**.

Reason: the protected 20-turn lane now covers structural stability, continuity drift, and fallback escalation. The next useful increment is improving operator review ergonomics before introducing longer 50-turn or nightly stress coverage.
