# Cycle K - Block K5: Longitudinal Replay Decision

## Decision Summary

Recommendation: `PROMOTE NEITHER`.

Protected golden replay is the appropriate required acceptance lane today. Scenario Spine adds meaningful long-session, branch, and convergence evidence, but its runner records evaluator failure without failing the command. N1 has deterministic fixtures, stable artifacts, and hard-fail exit behavior, but it is explicitly a tooling-only synthetic lane driven by scripted fake-GM outputs. Neither lane is presently both production-representative and ready to become a required acceptance gate.

This decision does not devalue either lane. Scenario Spine is the stronger future promotion candidate; N1 remains useful deterministic analyzer and longitudinal contract coverage.

## Lane Inventory

| Lane | Files Inspected | Purpose | Inputs and Runtime Behavior | Outputs | Failure Behavior |
| --- | --- | --- | --- | --- | --- |
| Scenario Spine - long-session validation | `data/validation/scenario_spines/frontier_gate_long_session.json`; `tools/run_scenario_spine_validation.py`; `tests/test_scenario_spine_eval.py`; `tests/test_run_scenario_spine_validation.py`; `tests/test_scenario_spine_contracts.py`; `tests/test_scenario_spine_continuation_convergence.py` | Validate continuity, progression, branch health, runtime-lineage signals, and long-session session health around the Frontier Gate scenario. | Fixed JSON fixture. Branches are `branch_cautious_observe` (10 turns), `branch_direct_intrusion` (25 turns), and `branch_social_inquiry` (25 turns). The tool posts each scripted turn through `/api/chat`, using in-process `TestClient` by default or `--base-url` for a running service. | Per branch: `transcript.json`, `session_health_summary.json`, `compact_operator_summary.md`, and debug data. With `--all-branches`: `aggregate_session_health_summary.json`, `aggregate_operator_summary.md`, and runtime-lineage aggregate output. | Fixture/argument problems return nonzero. After executing branches, `_execute()` returns `0` regardless of evaluator `overall_passed` or `classification`; health failure is reported in artifacts and console paths, not made an acceptance failure. |
| Scenario Spine - opening convergence fixture | `data/validation/scenario_spines/c1a_opening_convergence_paths.json`; `tests/test_scenario_spine_opening_convergence.py` | Probe fresh-start, entry, resume, and multi-transition opening convergence paths. | Fixed JSON smoke fixture. Four one-turn probe branches and `branch_multi_transition_smoke` (14 turns). Evaluated through Scenario Spine evaluation tests. | Evaluator result/session-health structures in tests; available to the Scenario Spine runner when selected as its fixture. | Unit assertions enforce evaluator expectations in tests, but there is no separately established required longitudinal runner lane for this fixture. |
| N1 longitudinal scenario spine | `tests/helpers/n1_scenarios.py`; `tests/helpers/n1_scenario_spine_harness.py`; `tools/run_n1_scenario_spine_validation.py`; `tests/test_n1_scenario_spine_validation.py`; `tests/test_n1_scenario_spine_cli.py`; `tests/test_n1_analyzer_regression.py`; `tests/test_n1_continuity_analysis.py` | Exercise deterministic continuity/analyzer behavior for anchor persistence, revisits, progression, and branch divergence. | Four code-defined fixtures: `n1_anchor_persistence`, `n1_investigation_revisit`, `n1_progression_chain`, and `n1_branch_divergence`. The harness runs `run_synthetic_session` with a fixed seed/configuration and scripted fake-GM responder. Stable hashes create run ids; no wall-clock entropy is used for output identity. | Per executed branch: `session_health.json` and `continuity_report.json`. Branch comparison adds `branch_comparison.json`. CLI writes stable parseable summary lines. | The CLI documents and implements exit `1` if any executed branch has `final_session_verdict == "fail"`, exit `2` for operator/config errors, and exit `0` otherwise. |

### Commands Present in the Lanes

| Purpose | Command |
| --- | --- |
| Scenario Spine default branch | `python tools/run_scenario_spine_validation.py` |
| Scenario Spine full long-session fixture | `python tools/run_scenario_spine_validation.py --spine data/validation/scenario_spines/frontier_gate_long_session.json --all-branches` |
| Scenario Spine opening convergence fixture | `python tools/run_scenario_spine_validation.py --spine data/validation/scenario_spines/c1a_opening_convergence_paths.json --all-branches` |
| N1 all registered fixtures | `python tools/run_n1_scenario_spine_validation.py run --all` |
| N1 branch comparison fixture | `python tools/run_n1_scenario_spine_validation.py run --scenario n1_branch_divergence --compare-branches` |
| Required protected replay already promoted in Cycle K | `python -m pytest -m golden_replay -q` |

## Readiness Assessment

Classification meanings in this memo:

- `READY`: sufficient evidence for the criterion if the lane were otherwise an appropriate acceptance candidate.
- `NEEDS_WORK`: the lane has useful evidence but lacks a required acceptance property.
- `NOT_RECOMMENDED`: the criterion or lane purpose does not support promotion as repository acceptance.

| Criterion | Scenario Spine | N1 | Evidence / Assessment |
| --- | --- | --- | --- |
| Determinism | `NEEDS_WORK` | `READY` | Scenario Spine has fixed scripts but executes `/api/chat` against the application runtime; no required deterministic acceptance execution contract is declared. N1 fixtures and responder are explicitly deterministic and artifact serialization is tested for stability. |
| Runtime cost | `NEEDS_WORK` | `READY` | Scenario Spine's primary fixture includes two 25-turn long branches plus a 10-turn branch, with application/API execution and optional external origin. N1 fixture sessions are short synthetic runs. |
| Fixture stability | `READY` | `READY` | Scenario Spine has committed JSON fixtures and contract/evaluator tests. N1 has registered fixed fixtures, uniqueness validation, and stable serialization tests. |
| Failure clarity | `READY` | `READY` | Scenario Spine produces branch summaries, failures/warnings, classification, and aggregate summaries. N1 outputs verdict, reason codes, continuity artifacts, and branch comparison output. |
| Artifact quality | `READY` | `READY` | Both lanes write structured artifacts. Scenario Spine is richer for runtime-lineage and operator review; N1 is especially stable and machine-readable. |
| Ownership clarity | `NEEDS_WORK` | `READY` for analyzer ownership; `NOT_RECOMMENDED` for acceptance ownership | Scenario Spine identifies evaluator signals but has not declared which health outcomes own acceptance. N1 clearly owns synthetic continuity analyzer contracts, but not production replay acceptance. |
| CI suitability | `NEEDS_WORK` | `NOT_RECOMMENDED` | Scenario Spine needs a deterministic, bounded, required command contract. N1 could run reliably in CI, but requiring a scripted fake-GM tooling lane would not prove production-facing replay acceptance. |
| Hard-fail capability | `NEEDS_WORK` | `READY` | Scenario Spine execution returns `0` after writing artifacts even if evaluated session health fails. N1 returns `1` for any failed executed branch verdict. |
| Overall lane classification | `NEEDS_WORK` | `NOT_RECOMMENDED` | Scenario Spine has additional acceptance value but is not promotion-ready. N1 is strong supporting tooling, not the correct required lane. |

### Current Test Position

Scenario Spine evaluator and runner tests are marked `unit`; the runner tests expressly avoid a live model or OpenAI execution. The current convergence workflow references `tests/test_scenario_spine_eval.py`, which validates evaluator behavior rather than establishing the longitudinal tool run as a required pass/fail acceptance command.

N1 validation is covered through deterministic test files and a CLI that can fail on its own verdict. This is evidence of a sound supporting lane, not evidence that it covers production emission or protected replay ownership.

## Comparative Analysis

| Acceptance Concern | Protected Golden Replay | Scenario Spine Increment | N1 Increment | Promotion Consequence |
| --- | --- | --- | --- | --- |
| Routing, speaker ownership, fallback ownership, sanitizer behavior, final emission | Already protected by declared golden replay scenarios and required marker-based CI gate. | Records related metadata over longer application-driven sessions, but does not replace asserted protected surfaces. | Does not target these production-facing protected replay surfaces. | Do not add a second required lane merely to repeat existing required protections. |
| Long-session continuity and referent persistence | Limited to existing protected replay scopes. | Meaningful additional evidence through committed 25-turn branches and continuity/progression anchors. | Deterministic anchor/revisit checks over scripted synthetic outputs. | Scenario Spine has genuine incremental value once its command and runtime contract are suitable for enforcement. |
| Branch divergence and progression | Not the primary purpose of protected golden replay. | Aggregate branch evaluation and divergence information on committed scenario branches. | Stable branch comparison and progression-chain analyzer coverage. | Useful monitoring evidence today; N1 validates analyzer logic while Scenario Spine is closer to eventual game-facing acceptance. |
| Failure diagnostics and artifact retention | Classification-backed failure reporting and retained CI artifact already exist for protected replay. | Produces strong reports, but they are not tied to hard-fail acceptance behavior. | Produces deterministic files and reason codes, with CLI hard-fail behavior. | Neither lane fills an urgent diagnostics gap in required replay acceptance. |
| Production representativeness | Required protected replay exercises the established golden replay acceptance surfaces. | Runs scripted turns through `/api/chat`; closest longitudinal extension of production-facing evidence. | The module calls itself tooling-only and uses a scripted fake-GM responder. | N1 should not be promoted in place of or alongside production-facing acceptance without a new ownership rationale. |

Protected replay is sufficient for the present Cycle K promise: required work must survive the canonical protected replay suite. A longitudinal lane would be additive policy, not a missing prerequisite for enforcing that promise.

## Required Promotion Work

### Scenario Spine

Minimum work required before considering CI promotion:

| Requirement | Why Required |
| --- | --- |
| Declare the exact required fixture and branch set. | The repository contains both long-session and opening-convergence fixtures; acceptance must not depend on an implicit selection. |
| Define an acceptance health policy for evaluator outcomes. | The runner exposes `overall_passed`, classification, failures, and warnings, but the required failing conditions are not yet a gate contract. |
| Make evaluated acceptance failure produce a nonzero process exit. | The current runner writes artifacts and returns success after branch execution regardless of evaluator health. |
| Establish a deterministic or otherwise controlled required execution mode. | A required lane must avoid noisy variation from runtime/model behavior or clearly govern that variation. |
| Measure and budget required runtime. | A 60-turn all-branch long-session pass through `/api/chat` is materially heavier than current protected replay and must have a known CI cost. |
| Carry failure artifacts into any future required CI job. | The existing rich operator and aggregate artifacts must remain available when a future required run fails. |
| Collect longitudinal observation data before enforcing new drift categories. | Cycle K4 identified several lineage and recurrence signals as observation-first rather than current hard-fail policy. |

### N1

Minimum work that would be required if N1 were reconsidered for acceptance:

| Requirement | Why Required |
| --- | --- |
| Establish a production-facing acceptance claim, not only analyzer contract ownership. | Current fixtures are explicitly synthetic, test-only, and run through a scripted fake-GM responder. |
| Define protected N1 scenarios and invariants under that claim. | Existing registered fixtures are useful, but have not been declared part of repository acceptance. |
| Explain how N1 adds required evidence unavailable from golden replay or a promoted Scenario Spine lane. | Without this distinction, it would gate tooling correctness rather than player-facing acceptance. |
| Define artifact retention and CI placement if promoted. | The CLI creates good artifacts and exits correctly, but promotion would still require required-job visibility and ownership. |

N1 already has hard-fail mechanics and stable artifacts. Its blocker is not technical reliability; it is that the evidence it supplies is not the right primary acceptance signal for production replay.

## Final Recommendation

`PROMOTE NEITHER`

Scenario Spine is the only lane that currently offers substantial additional game-facing longitudinal acceptance value. It is not ready to be required because its evaluator failure does not propagate to command failure, its required fixture/branch policy is not declared, and its runtime/determinism budget has not been established.

N1 is mature as deterministic supporting validation: its fixtures are stable, its analyzer output is clear, and its CLI already has hard-fail semantics. Those strengths support keeping it as a reliable advisory or unit-validation lane. They do not overcome the fact that it validates scripted synthetic continuity behavior rather than the production-facing replay contract.

## Implementation Path

Because the recommendation is not to promote a lane, no CI implementation sequence is recommended in this block.

### Monitoring-Only Posture

| Lane | Current Posture | Appropriate Use Now | Evidence That Would Justify Reconsideration |
| --- | --- | --- | --- |
| Scenario Spine | Advisory longitudinal monitoring and future promotion candidate. | Run the committed long-session or opening fixture when work changes continuity, progression, opening convergence, runtime-lineage capture, or scenario-spine evaluation. Preserve and review its generated summaries. | A declared canonical branch set; a stable bounded runtime; controlled deterministic execution or approved variability policy; explicit health-to-exit failure semantics; several representative runs demonstrating actionable, low-noise failures beyond protected replay. |
| N1 | Supporting deterministic analyzer validation; not an acceptance candidate now. | Keep using its tests and CLI to validate longitudinal continuity analysis, stable artifacts, progression checks, and branch comparison behavior. | A new, explicit production-facing ownership claim and evidence that a required N1 lane catches acceptance defects not already covered by protected replay or a future Scenario Spine gate. |

Protected replay remains the required gate:

```powershell
python -m pytest -m golden_replay -q
```

Useful non-gating observation commands remain:

```powershell
python tools/run_scenario_spine_validation.py --spine data/validation/scenario_spines/frontier_gate_long_session.json --all-branches
python tools/run_n1_scenario_spine_validation.py run --all
```

## Acceptance Criteria

| Criterion | Result |
| --- | --- |
| Longitudinal lanes inventoried | Complete: Scenario Spine long-session/opening fixtures and N1 fixture/harness/CLI/test lane mapped. |
| Readiness assessed | Complete: both lanes evaluated for determinism, runtime, fixtures, failures, artifacts, ownership, CI suitability, and hard-fail capability. |
| Comparison to protected replay completed | Complete: incremental value and overlap documented. |
| Minimum pre-promotion work identified | Complete for both candidates. |
| One recommendation made | Complete: `PROMOTE NEITHER`. |
| No replay behavior changed | Met: documentation-only decision memo. |
| No CI changed in Block K5 | Met: documentation-only decision memo. |
| No production behavior changed | Met: documentation-only decision memo. |
