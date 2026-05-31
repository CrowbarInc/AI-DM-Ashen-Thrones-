# Block N1 - Canonical 20-Turn Replay

## Summary

Block N1 adds the first deterministic protected long-session golden replay lane. The new replay executes 20 sustained turns through the existing `run_golden_replay(...)` infrastructure, uses mocked GPT only, and asserts aggregate structural stability rather than exact prose.

The implementation is intentionally additive:

- no runtime behavior changes
- no live model calls
- no replay framework rewrite
- no exact transcript matching
- no semantic repair or final-emission changes

## Fixture Chosen

Source fixture: `data/validation/scenario_spines/frontier_gate_long_session.json`

Chosen branch: `branch_social_inquiry`

The replay uses the first 20 prompts from `branch_social_inquiry`. This branch was chosen because it naturally exercises sustained social routing, speaker persistence, route stability, fallback recurrence, and long-session state pressure without becoming a combat/intrusion stress path. The underlying source branch has 25 turns, so the 20-turn protected fixture is a bounded subset of already-canonical scenario-spine material.

The test seeds a deterministic Frontier Gate context with the branch's expected anchors:

- notice board
- missing patrol
- Captain Thoran
- Ash Compact census pressure
- muddy northwest footprints
- gate guard
- gate serjeant
- tavern runner

GPT is mocked with an unbounded deterministic responder because one player turn can trigger retry-path GPT calls. The mock preserves the same anchor set on every call without using live generation.

## Structural Metrics Added

New helper: `summarize_long_session_replay_observations(...)` in `tests/helpers/golden_replay.py`.

Metrics now summarized:

- turn count
- route sequence
- route frequency
- route change count
- speaker sequence
- speaker frequency
- speaker change count
- speaker missing count
- fallback family sequence/frequency/count
- fallback owner sequence/frequency/change count
- mutation turn indices/count
- unavailable field counts
- runtime lineage aggregate summary via existing `summarize_runtime_lineage_events(...)`
- continuity warning/violation counts when projected `interaction_continuity_validation` reports `ok: false`

Protected assertions added in `tests/test_golden_replay.py`:

- all 20 turns complete
- no scaffold leakage
- bounded speaker changes
- bounded missing speaker observations
- bounded fallback-family recurrence
- bounded fallback owner changes
- bounded route changes
- enough resolved route observations
- no more than one fallback-selected lineage recurrence
- no more than one `fallback_mutation` lineage recurrence

Continuity validator counts are reported but not yet hard-failed in N1. The first run showed that this signal can be noisy for the current social fixture, so hard continuity drift enforcement should be a dedicated bridge block rather than a side effect of the first protected 20-turn fixture.

## Artifact Shape

New helper: `render_long_session_replay_summary_markdown(...)` in `tests/helpers/golden_replay.py`.

The artifact is compact and operator-readable. It includes:

- scenario id
- turn count
- route frequency
- speaker frequency
- fallback frequency
- fallback owner frequency
- mutation turn indices
- unavailable counts
- lineage event frequency
- recurring lineage events
- continuity warning/violation counts
- per-turn table with route, speaker, fallback, owner, mutation flag, unavailable fields, and lineage kinds

The protected test includes this rendered summary in assertion debug context. This reuses golden replay projection and runtime-lineage infrastructure rather than creating a second reporting ecosystem.

## Runtime Impact

Measured locally with the bundled Python runtime:

| Command | Result | Runtime |
|---|---|---:|
| Single new 20-turn replay test | PASS, 1 test | ~6.8s |
| Requested targeted suite | PASS, 97 tests | ~9.3s |
| Broader replay/fallback slice | PASS, 231 tests | ~9.8s |
| Marker-selected protected replay | PASS, 34 tests | ~9.8s |

The targeted suite command was:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_golden_replay.py tests/test_scenario_spine_eval.py tests/test_run_scenario_spine_validation.py tests/test_model_routing_escalation.py tests/test_fallback_behavior_gate.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n1_targeted2
```

Result: PASS.

The marker-selected protected replay command was:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_cycle_n1_marker2
```

Result: PASS.

## CI Impact

The new test inherits the module-level `golden_replay` marker, so it is part of the existing protected/default golden replay lane.

Runtime remains small enough locally to keep protected/default. Do not mark this test `slow` at this stage.

The implementation remains CI-safe:

- mocked GPT only
- deterministic fixture prompts
- deterministic seeded scene/world/session
- no network access
- no random generation
- no timing-sensitive assertions

## Risks / Follow-Ups

Remaining gaps before continuity drift enforcement:

- The replay now records continuity validation counts, but N1 does not hard-fail on them because the current signal is too noisy for this fixture.
- N3 should bridge scenario-spine degradation/continuity analysis into a stable replay assertion instead of relying on raw interaction-continuity violation counts.

Remaining gaps before 50-turn stress testing:

- No 50-turn fixture was added.
- No generated stress run was added.
- Runtime budget and marker policy for 50-turn/nightly work remain undecided.

Remaining gaps before nightly longitudinal replay:

- Scenario-spine CLI health still needs explicit hard-fail policy before it can be a required gate.
- Artifact upload policy for long-session scenario-spine runs is separate from protected golden replay.

Remaining gaps before escalation threshold hardening:

- N1 only bounds fallback-selected and fallback-mutation recurrence.
- It does not yet define richer fallback owner/escalation threshold policy across multiple branches.
- A future guard should distinguish expected deterministic retry/fallback paths from true escalation drift.

## Recommended Next Block

Recommended next block: **N3 continuity drift bridge**.

Reason: N1 now establishes the protected 20-turn replay lane and exposes continuity counts, but continuity enforcement should be stabilized through scenario-spine-style degradation/anchor analysis before it becomes a hard protected assertion.

N2 metrics hardening and N4 fallback escalation guard are both useful, but the highest-value next step is to connect the long-session replay to an existing non-brittle continuity drift evaluator.
