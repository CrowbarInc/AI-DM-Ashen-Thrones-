# Cycle N - Long-Session Stability Recon

## Executive Summary

The repo already has three relevant stability lanes:

- Protected golden replay: compact, deterministic, hard-failing, CI-wired, and strong for route/speaker/fallback/final-emission invariants, but current protected scenarios are short-turn only (mostly 1 turn, two 2-turn cases).
- Scenario spine: committed long-session fixture coverage exists in `data/validation/scenario_spines/frontier_gate_long_session.json` with 10/25/25-turn branches and evaluator support for continuity, referent persistence, progression, branch coherence, metadata completeness, and degradation over time. This lane is currently advisory at the CLI health boundary.
- N1 synthetic longitudinal validation: deterministic fake-GM analyzer coverage exists for continuity/progression/branching, but it is explicitly a tooling/synthetic lane rather than production-facing replay acceptance.

The main missing piece for Cycle N is not raw infrastructure. It is a small protected 20-turn replay/audit shape that bridges golden replay's strong structural signals with scenario spine's longitudinal evaluator signals without introducing live model dependencies or brittle text matching.

Safest first block: create one deterministic 20-turn canonical golden replay fixture or golden-replay-backed audit using mocked `call_gpt`, projected per-turn observations, and metrics-first assertions. Start with route/speaker/fallback/lineage/continuity metrics and a readable artifact before promoting strict behavioral thresholds. Do not begin with a generated 50-turn run or live scenario-spine CLI gate.

## Relevant Files

| File | Current Role | Cycle N Relevance | Risk / Notes |
|---|---|---|---|
| `tests/test_golden_replay.py` | Protected and supporting golden replay tests; inline scenario setup and assertions. | Best first home for a canonical deterministic 20-turn protected replay or adjacent golden-replay audit. | Existing protected scenarios are short; adding 20 turns here increases runtime but keeps deterministic mock-GPT behavior. |
| `tests/helpers/golden_replay.py` | Runs replay turns, projects stable observations, classifies drift, renders compact replay markdown. | Primary seam for long-session observation rows and failure report input. | `_observed_turn(...)` already extracts route, speaker, FEM, fallback, sanitizer, mutation, and lineage fields. |
| `tests/helpers/transcript_runner.py` | Clean campaign setup, storage patching, chat snapshot projection. | Supports deterministic replay setup without new storage infrastructure. | Existing helper is reused by golden replay; avoid a parallel runner. |
| `docs/testing/protected_replay_manifest.md` | Declares protected, supporting, advisory, and deprecated replay lanes. | Governance home if a 20-turn replay becomes protected. | Current manifest classifies scenario spine long-session as advisory, not protected. |
| `.github/workflows/convergence-checks.yml` | Current hard-fail CI workflow. | Already runs `python -m pytest -m golden_replay -q` and uploads `artifacts/golden_replay/replay_failure_report.md` on protected replay failure. | Adding 20-turn replay under `golden_replay` will affect CI immediately unless marked or isolated. |
| `data/validation/scenario_spines/frontier_gate_long_session.json` | Canonical game-level scenario-spine long-session fixture. | Existing 20+ turn source material: `branch_direct_intrusion` and `branch_social_inquiry` are 25 turns each. | Not consumed by golden replay; CLI runner health is advisory. |
| `data/validation/scenario_spines/c1a_opening_convergence_paths.json` | Opening convergence fixture with a multi-transition branch around 14 turns. | Useful medium-turn opening/continuation evidence. | Does not approach 20 turns. |
| `game/scenario_spine.py` | Scenario spine dataclasses, JSON conversion, validation. | Owns fixture schema and long-branch minimum validation. | No expected route/speaker/fallback assertions in schema. |
| `game/scenario_spine_eval.py` | Offline evaluator for scenario-spine transcript rows. | Existing non-brittle continuity drift detector: windows, anchors, referents, progression, degradation. | Text heuristic based, but anchored and aggregate rather than exact transcript matching. |
| `tools/run_scenario_spine_validation.py` | Runs spine branches through `/api/chat`, writes transcript/session-health/operator artifacts. | Best artifact model for long-session failure review and runtime-lineage aggregation. | Writes artifacts but current health failures do not make the command fail. |
| `tests/test_scenario_spine_contracts.py` | Schema and fixture validation tests. | Proves the long-session fixture validates and long branch minimum is enforced. | Unit-level; does not execute a 20-turn replay. |
| `tests/test_scenario_spine_eval.py` | Deterministic evaluator tests over 25-turn fixture-shaped rows. | Proves long-session continuity/progression/degradation signals over 25 turns. | Uses synthetic GM rows, not the chat pipeline. |
| `tests/test_scenario_spine_continuation_convergence.py` | Continuation convergence evaluator tests. | Existing plan-driven continuation stability signal. | Evaluator-only. |
| `tests/test_run_scenario_spine_validation.py` | CLI/artifact/transcript/runtime-lineage contract tests. | Best source for artifact shape and runtime-lineage summary seams. | Mocked runner tests, not live model calls. |
| `tests/helpers/failure_classifier.py` | Replay-side deterministic failure classification. | Existing owner/severity/investigate-first vocabulary for long-session artifact rows. | Signal names are centralized here plus `tests/failure_classification_contract.py`. |
| `tests/helpers/failure_dashboard_report.py` | Dashboard and protected replay failure report renderer. | Candidate renderer or pattern for long-session failure artifact. | Current artifact path is protected replay oriented. |
| `tests/failure_classification_contract.py` | Central taxonomy for replay failure rows. | Centralized allowed categories/owners/severities/tags/source fields. | Long-session tags may need additive taxonomy entries if promoted. |
| `game/runtime_lineage_telemetry.py` | Runtime-lineage event normalization/summarization. | Existing recurrence/frequency signal for fallback/gate/mutation stability over turns. | Observational today; not pass/fail thresholded. |
| `game/final_emission_meta.py` | FEM normalization, owner buckets, runtime-lineage event construction. | Emits final source, fallback owner, mutation, repair, speaker/gate lineage signals. | High fanout; avoid semantic changes in Cycle N first block. |
| `game/final_emission_gate.py` | Final emission gate orchestration and fallback selection. | Source of route/fallback/gate outcomes tested by replay. | Hotspot; recon recommends assertions first, not edits. |
| `game/interaction_continuity.py` | Interaction continuity contracts/validation. | Speaker/thread persistence signal source for social continuity. | Existing runtime may disable continuity strength on non-social turns. |
| `game/speaker_contract_enforcement.py` | Speaker contract enforcement and reason fields. | Speaker persistence/failure owner surface. | Good future assertion source; do not add brittle text checks. |
| `tests/helpers/n1_scenarios.py` | Registered synthetic N1 fixtures. | Separate deterministic longitudinal ideas and fake-GM patterns. | Useful as reference only; not production-facing. |
| `tests/helpers/n1_scenario_spine_harness.py` | N1 continuity observations, stable run IDs, JSON artifacts. | Useful deterministic fingerprint/artifact patterns. | N1-specific contracts; avoid mixing into golden replay. |
| `tools/run_n1_scenario_spine_validation.py` | N1 CLI with hard-fail synthetic verdict behavior. | Reference for CI-friendly hard-fail semantics. | Synthetic fake-GM, not recommended as first Cycle N acceptance lane. |
| `tests/test_transcript_regression.py` and transcript gauntlet tests | Broad multi-turn transcript regressions. | Evidence of replay-adjacent stability cases. | Heavier/advisory; not declared protected golden. |

## Existing Replay Coverage

Protected golden replay currently proves compact acceptance surfaces:

- End-to-end protected scenarios: `directed_npc_question` (1 turn), `vocative_override_after_prior_continuity` (2 turns), `wrong_speaker_strict_social_emission` (1 turn), `thin_answer_action_outcome_final_emission` (1 turn), `sanitizer_scaffold_leakage` (1 turn), and `lead_followup_with_dialogue_lock` (2 turns).
- Direct-seam protected scenarios: `declared_alias_dialogue_plan` and `opening_fallback_path`.
- Supporting branch smoke: `scenario_spine_three_branch`, but it is one turn per branch and does not execute the committed long-session JSON fixture.

Existing replay tests are therefore short-turn. The only current committed fixture that approaches or exceeds 20 turns is `frontier_gate_long_session.json`, with:

- `branch_cautious_observe`: 10 turns.
- `branch_direct_intrusion`: 25 turns.
- `branch_social_inquiry`: 25 turns.

`c1a_opening_convergence_paths.json` includes a multi-transition branch of roughly 14 turns, so it is medium-turn rather than long-turn.

Scenario-spine evaluator tests already use 25 deterministic rows from `frontier_gate_long_session.json` and prove the evaluator can detect progressive degradation, late amnesia/reset language, generic filler growth, referent loss, missing progression, debug leaks, and foreign branch prompt echoes. That proves evaluator capability, not sustained play through the protected replay harness.

## Stability Signal Inventory

| Signal | Exists? | Emitted Where | Tested Where | Gap |
|---|---|---|---|---|
| speaker persistence | Partial | `tests/helpers/golden_replay.py::_observed_turn` via `selected_speaker_id`, `selected_speaker_source`, `trace.social_contract_trace`; runtime contracts in `game/interaction_continuity.py` and `game/speaker_contract_enforcement.py`. | `tests/test_golden_replay.py`, speaker/interaction continuity suites. | No 20-turn persistence aggregate that checks stable speaker across a long social chain. |
| route stability | Partial | `route_kind`, `resolution_kind`, `trace.social_contract_trace.route_selected`; runtime route fields from API/debug trace. | `tests/test_golden_replay.py`, model routing and dialogue routing tests. | No per-session route-path sequence or drift threshold over 20+ turns. |
| gate path stability | Partial | FEM fields in `game/final_emission_meta.py`; runtime lineage events; stage diff telemetry. | `tests/test_golden_replay.py`, `tests/test_run_scenario_spine_validation.py`, final emission gate tests. | Gate path is observable, but no long-session count/frequency threshold. |
| fallback kind | Yes | FEM fields: `fallback_family_used`, `realization_fallback_family`, `fallback_temporal_frame`, visibility/opening/sealed owner buckets; sanitizer trace. | `tests/test_golden_replay.py`, fallback behavior/gate tests, failure classifier tests. | Long-session fallback recurrence is summarized but not hard-fail thresholded. |
| fallback escalation | Partial | `response_type_repair_used`, `response_type_repair_kind`, `upstream_prepared_emission_*`, `fallback_behavior_*`, model escalation fields in routing tests. | `tests/test_golden_replay.py`, `tests/test_model_routing_escalation.py`, fallback behavior tests. | No 20-turn escalation ladder assertion such as bounded fallback recurrence or no unexpected owner change. |
| continuity/state drift | Yes in scenario-spine lane | `game/scenario_spine_eval.py` axes and `degradation_over_time`; runtime `interaction_continuity_validation`; `conversational_memory_window` fields in payloads. | `tests/test_scenario_spine_eval.py`, `tests/test_scenario_spine_continuation_convergence.py`, interaction continuity tests. | Golden replay does not yet consume scenario-spine degradation signals for protected sustained play. |
| scenario-spine continuity | Yes | `minimal_complete_transcript_turn_meta`, transcript `meta.scenario_spine`, evaluator session health. | Scenario-spine contract/eval/runner tests. | CLI health is advisory; protected replay does not use committed long fixture. |
| mutation kind | Partial | `final_emission_mutation_lineage`, `post_gate_mutation_detected`, sanitizer lineage, stage diff transitions. | `tests/test_golden_replay.py`, `tests/test_run_scenario_spine_validation.py`, stage diff tests. | No centralized "mutation kind" threshold for sustained play; names appear across FEM, sanitizer, stage diff. |
| failure owner/locality | Yes | Replay classifier rows: category, primary/secondary owner, investigate-first target. | `tests/test_failure_classifier.py`, `tests/test_failure_classification_contract.py`, `tests/test_failure_dashboard_controlled_failures.py`. | Strong for individual replay failures; long-session aggregate owner attribution not yet wired. |
| replay drift thresholds | Partial | `classify_golden_drift` supports exact/structural/semantic drift; scenario-spine scoring/classification supports clean/warning/degraded/failed. | `tests/test_golden_replay.py`, `tests/test_scenario_spine_eval.py`. | No aggregate allowed-drift policy for route changes, fallback frequency, speaker switches, or mutation count over 20-50 turns. |

Signal names are partly centralized and partly duplicated:

- Centralized: replay taxonomy in `tests/failure_classification_contract.py`; runtime-lineage normalization in `game/runtime_lineage_telemetry.py`; FEM normalization in `game/final_emission_meta.py`.
- Duplicated/projection-local: expected field names in `tests/helpers/golden_replay.py`, scenario-spine metadata keys in `game/scenario_spine_eval.py` and `tools/run_scenario_spine_validation.py`, CLI summary fields in runner tests.

## Existing Replay Failure Artifacts

| Artifact Path | What It Currently Proves | What It Fails To Prove For 20-50 Turn Stability | CI Review Suitability |
|---|---|---|---|
| `artifacts/golden_replay/replay_failure_report.md` | Canonical protected replay failure report path; rendered by `tests/helpers/failure_dashboard_report.py` when protected failures are recorded. | Only appears on failure; current protected scenarios are short-turn. | Suitable; CI uploads it on protected replay failure. |
| `audits/failure_dashboard_latest.md` | Opt-in latest replay failure dashboard with classifier rows and lineage summary. | Not automatically produced for normal passing runs; not specific to long sessions. | Suitable as diagnostic, not canonical CI artifact. |
| `audits/replay_failure_corpus.md` and `audits/failure_dashboard_*.md` | Historical/probe evidence for classifier and dashboard behavior. | Historical docs, not executable current stability evidence. | Good review context; not CI output. |
| `artifacts/scenario_spine_validation/<timestamp>/<spine>/<branch>/transcript.json` | Per-turn transcript rows, API status, player/GM text, metadata envelope. | Only generated when CLI is run; CLI health failure is advisory. | Suitable if uploaded, but not currently a required CI artifact. |
| `artifacts/scenario_spine_validation/<timestamp>/<spine>/<branch>/session_health_summary.json` | Evaluator result with axes, detected failures, warnings, degradation, metadata completeness. | Not generated by protected replay; not hard-fail by CLI health. | Very suitable for CI review after a hard-fail policy exists. |
| `artifacts/scenario_spine_validation/<timestamp>/<spine>/<branch>/compact_operator_summary.md` | Human-readable per-branch summary. | Same advisory/optional limitation. | Good for CI review. |
| `artifacts/scenario_spine_validation/<timestamp>/<spine>/aggregate_session_health_summary.json` | All-branch aggregate: classifications, long-branch counts, coverage band, branch divergence, runtime-lineage summary. | Optional/advisory; all-branch run is heavier than a 20-turn default gate. | Strong candidate for nightly/manual review. |
| `artifacts/scenario_spine_validation/<timestamp>/<spine>/aggregate_operator_summary.md` | Human-readable aggregate branch summary. | Same optional/advisory limitation. | Strong review artifact. |
| `artifacts/scenario_spine_validation/<timestamp>/<spine>/runtime_lineage_summary.json` | Runtime-lineage event frequency/recurrence summary across branch transcripts. | Not converted into replay drift thresholds. | Suitable for CI review if run exists. |
| `artifacts/architecture_audit/*`, `artifacts/realization_layer_audit/*`, `artifacts/realization_provenance_audit/*` | Static/advisory ownership and provenance scans. | Not replay/session artifacts. | Useful supporting context only. |

## Long-Session Fixture Options

| Option | Upside | Risk | Recommendation |
|---|---|---|---|
| Extend existing golden replay | Reuses protected CI lane and deterministic mock-GPT harness. | Could slow every golden replay run and blur short protected scenarios with longitudinal evidence. | Good if scoped as one new explicit 20-turn scenario and measured. |
| Create new 20-turn canonical replay | Lowest-risk bridge: deterministic, protected or markable, clear purpose. | Needs fixture design and metrics artifact work. | Recommended first block. |
| Generate synthetic 50-turn replay | Useful stress test after instrumentation exists. | Higher fixture noise and likely overfits synthetic patterns before thresholds are known. | Defer. |
| Scenario-spine continuation test | Reuses committed long-session fixture and existing evaluator. | Current CLI is advisory; production chat path may involve live/model variability unless mocked. | Use as source material/artifact model, not first protected gate. |
| Metrics-only audit first | Avoids brittle behavioral assertions and exposes current signal coverage. | Does not prove stability by itself. | Pair with the 20-turn canonical replay as the initial assertion style. |

Recommended first Cycle N block: one canonical deterministic 20-turn golden replay/audit that asserts metrics and structural invariants, not exact prose. Use `frontier_gate_long_session.json` social or direct branch prompts as source material, but execute through `run_golden_replay(...)` with mocked GPT outputs and per-turn projected observations.

## Proposed Implementation Blocks

| Name | Goal | Files Likely Touched | Tests Likely Added/Changed | Risk Level | Parallelizable? |
|---|---|---|---|---|---|
| N1 - Canonical 20-turn replay fixture | Add one deterministic 20-turn sustained-play replay using existing golden harness and fixture prompts. | `tests/test_golden_replay.py`; maybe `tests/helpers/golden_replay.py`; possibly `docs/testing/protected_replay_manifest.md`. | New `test_golden_replay_frontier_gate_20_turn_stability_metrics` or similar. | Medium | Yes, if artifact work avoids same helper sections. |
| N2 - Long-session metrics projection | Add helper to summarize per-turn route, speaker, fallback, mutation, unavailable, and lineage recurrence without exact text matching. | `tests/helpers/golden_replay.py`; possibly `game/runtime_lineage_telemetry.py` if only reusing existing summarizer. | Unit/projection test in `tests/test_golden_replay.py`. | Low-medium | Yes. |
| N3 - Continuity drift bridge | Feed long replay observed rows into scenario-spine-shaped evaluator rows or a minimal metrics audit to detect late resets/referent loss. | `tests/test_golden_replay.py`; `game/scenario_spine_eval.py` only if an additive public helper is needed. | New test asserts no progressive degradation on deterministic 20-turn fixture. | Medium | Partly; coordinate with N1 fixture. |
| N4 - Fallback escalation guard | Assert fallback recurrence/owner stability and no unexpected escalation across the 20-turn fixture. | `tests/helpers/golden_replay.py`; `tests/test_golden_replay.py`; maybe `tests/failure_classification_contract.py` for tags. | Long-session fallback metrics test. | Medium | Yes after N2 metrics helper exists. |
| N5 - Failure artifact for long sessions | Render a compact long-session failure artifact with per-turn summary and owner hints. | `tests/helpers/failure_dashboard_report.py`; `tests/helpers/golden_replay.py`; maybe CI docs. | Renderer contract test; failing probe test with synthetic observed rows. | Low-medium | Yes, but avoid simultaneous edits to dashboard renderer. |

## Likely Implementation Seams

- Adding a 20-turn replay fixture:
  - `tests/test_golden_replay.py`: add setup function or reuse `_seed_spine_three_branch_context`, load `frontier_gate_long_session.json`, select first 20 turns from `branch_social_inquiry` or `branch_direct_intrusion`, and call `run_golden_replay(...)`.
  - `tests/helpers/golden_replay.py::run_golden_replay(...)`: already supports arbitrary turn lists and mocked `chat_fn`; no rewrite needed.

- Asserting route stability across turns:
  - `tests/helpers/golden_replay.py::_observed_turn(...)`: already emits `route_kind`, `resolution_kind`, `trace.social_contract_trace.route_selected`, `final_emitted_source`, `unavailable`.
  - Add a small test helper in `tests/helpers/golden_replay.py` or local to `tests/test_golden_replay.py` to summarize route sequence/frequencies.

- Asserting speaker persistence:
  - Existing fields: `selected_speaker_id`, `selected_speaker_source`, `trace.canonical_entry.target_actor_id`, `trace.social_contract_trace.final_reply_owner`.
  - Runtime supporting files: `game/interaction_continuity.py`, `game/speaker_contract_enforcement.py`.
  - First assertion should compare structural selected speaker/target fields, not speaker labels in prose.

- Asserting fallback escalation behavior:
  - Existing fields: `fallback_family`, `fallback_temporal_frame`, `fallback_behavior_repaired`, `fallback_behavior_repair_kind`, `opening_fallback_owner_bucket`, `sealed_fallback_owner_bucket`, `visibility_fallback_owner_bucket`, `upstream_prepared_emission_*`, runtime lineage events.
  - Existing tests: `tests/test_fallback_behavior_gate.py`, `tests/test_fallback_behavior_validator.py`, `tests/test_model_routing_escalation.py`.

- Detecting continuity drift without brittle text matching:
  - `game/scenario_spine_eval.py::_compute_degradation_over_time(...)` and `evaluate_scenario_spine_session(...)` already use windows, anchors, referents, reset/amnesia markers, debug markers, and filler density.
  - Use committed `ScenarioSpine` anchors or minimal evaluator rows rather than exact final text.

- Producing a readable failure artifact:
  - `tests/helpers/failure_dashboard_report.py::render_protected_replay_failure_report(...)` and `write_protected_replay_failure_report_if_present(...)` already define the protected replay artifact path.
  - `tests/helpers/golden_replay.py::render_golden_replay_markdown_report(...)` is a compact report renderer that could be extended or used as a model for long-session per-turn summaries.
  - `tools/run_scenario_spine_validation.py::build_aggregate_operator_summary_md(...)` is the best existing long-session operator-summary model.

## CI / Runtime Feasibility

Current validation discovered:

- `pytest.ini` registers `golden_replay`, `slow`, `transcript`, `integration`, and `unit`.
- `.github/workflows/convergence-checks.yml` currently runs `python -m pytest -m golden_replay -q` as a hard-fail step.
- The same workflow uploads `artifacts/golden_replay/replay_failure_report.md` when the protected replay step fails.
- Existing golden replay scenarios use mocked deterministic GPT responses and local storage patches, so they avoid live model calls.
- Scenario-spine CLI can use in-process `TestClient` or `--base-url`, but the production-facing long-session CLI is artifact/advisory rather than a required hard-fail health gate.

Runtime evidence from this recon:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_golden_replay.py tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_fallback_behavior_gate.py tests/test_fallback_behavior_validator.py tests/test_model_routing_escalation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n
```

Result: PASS, 230 tests passed, approximately 4.7 seconds wall time in this local environment.

Initial `python -m pytest ...` failed because `python` is not on this Windows PATH. The bundled runtime command above is the reproducible local command.

Full suite was not run in this recon because the targeted stability slice already covered 230 replay/scenario/fallback/gate/routing tests quickly, while the repo has a broad test inventory and many transcript/slow suites. A future implementation block should measure a 20-turn golden replay directly before deciding whether to mark it `slow`.

Recommendation:

- Run one deterministic 20-turn golden replay by default if its measured runtime remains small and no live model calls are introduced.
- Keep 50-turn or all-branch scenario-spine runs manual/nightly until health-to-exit policy and runtime budgets are explicit.
- Use deterministic fixtures and mocked GPT responses for CI.
- Consider marking 50-turn generated/synthetic stress tests `slow`; do not mark the first 20-turn canonical fixture slow unless measured runtime warrants it.

## Open Questions / Files Needed From User

- Should the first 20-turn canonical fixture become protected immediately under `golden_replay`, or land first as supporting/advisory under the same file?
- Which branch is the desired canonical first long session: social inquiry, direct intrusion, or a curated 20-turn blend?
- Should fallback recurrence be a hard threshold in Cycle N block 1, or only reported as observation until baseline counts are known?
- Should the future artifact live under `artifacts/golden_replay/` or a separate `artifacts/long_session_replay/` path?
- If ChatGPT will generate implementation blocks, pass this report plus any preferred acceptance policy for 20-turn default versus 50-turn manual/nightly.

## Validation

Commands run:

```powershell
python -m pytest tests/test_golden_replay.py tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_fallback_behavior_gate.py tests/test_fallback_behavior_validator.py tests/test_model_routing_escalation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n
```

Result: FAIL to start. PowerShell reported `python` is not recognized on PATH.

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_golden_replay.py tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_fallback_behavior_gate.py tests/test_fallback_behavior_validator.py tests/test_model_routing_escalation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_n
```

Result: PASS, 230 tests passed.
