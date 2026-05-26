# Cycle K — Replay Promotion Recon

## Executive Summary

Replay is **almost ready** to promote as a primary acceptance mechanism, but it is not promoted today.

The repository already has a deterministic golden replay harness, a named `golden_replay` pytest marker, nine scenarios described as a canonical baseline, hard pytest assertions over routing/final-emission behavior, and opt-in failure dashboard reporting. The narrow executable suite is `tests/test_golden_replay.py`, with observation and drift helpers in `tests/helpers/golden_replay.py`.

The material promotion gaps are governance and enforcement gaps:

- Neither GitHub Actions workflow explicitly runs `tests/test_golden_replay.py` or `-m golden_replay`.
- The committed golden baseline is Markdown documentation, not an executable external fixture/snapshot consumed by the tests; expectations are inline in `tests/test_golden_replay.py`.
- The richer game-level scenario-spine runner produces useful artifacts, but `tools/run_scenario_spine_validation.py` returns success after completed runs even when evaluator output reports failures. It is currently an evidence/report lane, not an acceptance gate.
- Golden replay has exact/structural/semantic drift categories and strong per-field assertion failures, but it has no aggregate allowed-drift policy for fallback counts, mutation counts, gate-path frequency, or runtime-lineage recurrence.

Recommended posture for Cycle K: promote the existing deterministic golden replay file as the initial required replay gate, keep scenario-spine and N1 as adjacent longitudinal evidence until their role is explicitly chosen, and add threshold/report governance only after the required golden lane is named and wired.

## Current Replay Inventory

| Area | Files | Purpose | Notes |
|---|---|---|---|
| Golden replay runner / harness | `tests/helpers/golden_replay.py`; `tests/helpers/transcript_runner.py`; `tests/helpers/transcript_snapshots.py` | Runs clean-campaign chat turns; projects final text, route, speaker, FEM/fallback, sanitizer, trace, and runtime-lineage signals into stable observed rows; asserts/classifies drift. | Test-only harness. `run_golden_replay(...)` reuses transcript infrastructure and does not create runtime behavior. |
| Golden replay tests | `tests/test_golden_replay.py` | Executable replay suite and inline expectations for canonical turn/final-emission scenarios plus projection/renderer contract tests. | Module marked `integration` and `golden_replay`; failures are pytest failures. |
| Golden baseline / expected-output records | `audits/golden_replay_baseline_2026-05-11.md`; `audits/golden_replay_readiness_2026-05-11.md`; `audits/replay_failure_corpus.md` | Human-readable canonical scenario baseline, original readiness map, and controlled failure observations. | Baseline Markdown is documentary; it is not loaded as an executable snapshot file by `tests/test_golden_replay.py`. |
| Replay drift / failure diagnostics | `tests/helpers/failure_classifier.py`; `tests/helpers/failure_dashboard_report.py`; `tests/failure_classification_contract.py`; `tests/test_failure_classifier.py`; `tests/test_failure_dashboard_controlled_failures.py`; `tests/test_failure_classification_contract.py`; `tests/conftest.py`; `audits/failure_dashboard_latest.md`; `audits/failure_dashboard_probe_sample.md`; `audits/failure_dashboard_*.md` | Classifies replay drift into owner/category/severity rows; renders opt-in Markdown dashboards; validates controlled known-bad rows and taxonomy. | Dashboard generation is opt-in via CLI flag or environment variable; normal golden replay runs do not write it. |
| Game-level scenario definitions | `data/validation/scenario_spines/frontier_gate_long_session.json`; `data/validation/scenario_spines/c1a_opening_convergence_paths.json`; `game/scenario_spine.py` | JSON-defined long-session/branch fixtures and schema. | Adjacent to golden replay. `frontier_gate_long_session.json` is documented as canonical for the scenario-spine lane, not consumed by the golden three-branch smoke scenario. |
| Game-level scenario evaluation / runner | `game/scenario_spine_eval.py`; `game/scenario_spine_opening_convergence.py`; `game/scenario_spine_transition_convergence.py`; `tools/run_scenario_spine_validation.py` | Deterministic session-health, opening/continuation/transition checks, branch divergence, runtime-lineage summaries, and artifact-producing API runs. | Richest longitudinal artifact lane; CLI is currently advisory with respect to evaluator result. |
| Game-level scenario tests | `tests/test_scenario_spine_contracts.py`; `tests/test_scenario_spine_eval.py`; `tests/test_scenario_spine_opening_convergence.py`; `tests/test_scenario_spine_continuation_convergence.py`; `tests/test_run_scenario_spine_validation.py` | Schema, evaluator, convergence, runner/artifact, and runtime-lineage summary contracts. | `tests/test_scenario_spine_eval.py` is already included in hard-fail convergence CI; it tests the evaluator, not a live replay execution. |
| N1 scenario-spine fixtures / harness | `tests/helpers/n1_scenarios.py`; `tests/helpers/n1_scenario_spine_contract.py`; `tests/helpers/n1_scenario_spine_harness.py`; `tests/helpers/n1_continuity_analysis.py`; `tools/run_n1_scenario_spine_validation.py` | Separate deterministic synthetic/transcript longitudinal lane with code-defined scenarios and JSON artifacts. | Docs explicitly say this is separate from the game-level scenario-spine lane. Its CLI can fail on failed verdicts. |
| N1 scenario tests | `tests/test_n1_scenario_spine_validation.py`; `tests/test_n1_scenario_spine_cli.py`; `tests/test_n1_analyzer_regression.py` | Harness, CLI/artifact, and analyzer regression coverage. | Not named `golden_replay`; promotion should not silently conflate it with the golden suite. |
| Transcript replay-adjacent tests | `tests/test_transcript_runner_smoke.py`; `tests/test_transcript_regression.py`; `tests/test_transcript_gauntlet_actor_addressing.py`; `tests/test_transcript_gauntlet_campaign_cleanliness.py`; `tests/test_narration_transcript_regressions.py`; `tests/test_anti_railroading_transcript_regressions.py`; `tests/test_gauntlet_regressions.py` | Existing multi-turn/transcript or gauntlet-style regression evidence around routing, continuity, emission, reset, and scaffold leakage. | Most explicit transcript harness modules are marked `transcript` and/or `slow`; these are support evidence, not the named golden gate. |
| Runtime-lineage support | `game/runtime_lineage_telemetry.py`; `game/final_emission_meta.py`; `tests/test_runtime_lineage_telemetry.py`; `tests/test_run_scenario_spine_validation.py` | Projects gate outcome, fallback, speaker repair, and mutation events; summarizes frequencies/recurrence for artifacts. | Current counters are observational/reporting surfaces, not golden replay pass thresholds. |
| Replay / validation docs | `tests/README_TESTS.md`; `docs/testing.md`; `docs/scenario_spine_validation.md`; `docs/n1_scenario_spine_validation.md`; `docs/convergence_ci_inventory.md` | Commands, lane ownership, scenario-spine semantics, artifact layout, and CI inventory. | `tests/README_TESTS.md` is the clearest current golden replay usage document. |
| CI workflows | `.github/workflows/content-lint.yml`; `.github/workflows/convergence-checks.yml` | Existing GitHub Actions enforcement. | Neither workflow explicitly invokes golden replay. |
| Pytest configuration | `pytest.ini` | Registers `golden_replay`, `failure_dashboard_probe`, `transcript`, `slow`, and other markers; configures test paths and repo-local base temp. | Default `pytest` has no marker exclusion, so golden replay is part of the full/default suite. |

## Current Replay Entry Points

### Named golden replay suite

| Command | Discovered At | Current Role | Hard/Soft | CI/Default/Manual |
|---|---|---|---|---|
| `python -m pytest tests/test_golden_replay.py -q` | `tests/README_TESTS.md`; `audits/golden_replay_baseline_2026-05-11.md` | Direct golden replay execution. | Hard: pytest assertions fail the command. | Documented manual/local command; not explicit in CI. |
| `python -m pytest -m golden_replay -q` | `tests/README_TESTS.md`; `pytest.ini` | Marker-selected equivalent golden replay execution. | Hard. | Documented manual/local command; not explicit in CI. |
| `pytest` or `pytest tests/` | `pytest.ini`; `tests/README_TESTS.md` | Full/default pytest lane. | Hard. | Includes golden replay because `pytest.ini` applies no exclusion filter. |
| `pytest -m "not transcript and not slow"` | `tests/README_TESTS.md`; `pytest.ini` | Fast developer lane. | Hard. | Includes `tests/test_golden_replay.py` by inference: that module is marked `integration` + `golden_replay`, not `transcript` or `slow`. |

### Golden replay diagnostics

| Command | Output | Hard/Soft | Notes |
|---|---|---|---|
| `python -m pytest -m golden_replay -q --write-failure-dashboard` | Writes `audits/failure_dashboard_latest.md`. | Replay assertions remain hard; dashboard output is diagnostic. | Registered by `tests/conftest.py`; normal replay does not write this file. |
| `ASHEN_WRITE_FAILURE_DASHBOARD=1 python -m pytest -m golden_replay -q` | Writes the same latest dashboard artifact. | Same. | Documented POSIX-style environment example in `tests/README_TESTS.md`; PowerShell equivalent sets `$env:ASHEN_WRITE_FAILURE_DASHBOARD='1'`. |
| `python -m pytest -m failure_dashboard_probe -q --write-failure-dashboard` | Exercises known-bad replay-shaped classifier probes and writes dashboard evidence. | Tests are hard when opted in. | Probe suite is skipped during ordinary collection unless explicitly selected or environment-enabled. |

### Scenario-spine adjacent lanes

| Command | Purpose | Hard/Soft | Promotion Meaning |
|---|---|---|---|
| `python tools/run_scenario_spine_validation.py` | Runs default `frontier_gate_long_session` branch through `/api/chat` and writes timestamped artifacts under `artifacts/scenario_spine_validation/`. | Advisory for evaluated health: after a completed run, the CLI returns `0` without checking `session_health.overall_passed`. It returns nonzero for invalid fixture/arguments. | Not usable as a required acceptance gate without explicit exit-policy work. |
| `python tools/run_scenario_spine_validation.py --all-branches` | Runs all JSON-defined branches and writes aggregate health/divergence/runtime-lineage artifacts. | Same advisory health behavior. | Strong evidence candidate after hard-fail semantics are deliberately chosen. |
| `python -m pytest tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_run_scenario_spine_validation.py` | Tests schema/evaluator/runner contracts. | Hard pytest. | Tests machinery and deterministic evaluator behavior; does not itself execute canonical live replay. |
| `python tools/run_n1_scenario_spine_validation.py run --all` | Separate N1 deterministic synthetic scenario execution. | Hard at CLI verdict boundary: returns `1` if any executed branch has `final_session_verdict == "fail"`; `2` for operator/config errors. | Potential separate longitudinal gate, not the existing golden replay gate. |

### Marking and artifacts

- `tests/test_golden_replay.py` is marked `pytest.mark.integration` and `pytest.mark.golden_replay`; it is not marked `slow`, `optional`, `manual`, or `transcript`.
- Golden scenario failures are hard pytest failures through `assert_golden_turn_observation(...)`.
- Golden result artifact writing is optional: only the failure dashboard has a wired output path, and only when requested.
- The committed `audits/golden_replay_baseline_2026-05-11.md` records nine passing baseline scenarios, but is not regenerated or checked by the ordinary pytest command.

## Current Replay Coverage

### Golden replay canonical baseline scenarios

| Scenario/Test | Path | Protects | Canonicality | Dependencies | Notes |
|---|---|---|---|---|---|
| `directed_npc_question` / `test_golden_replay_directed_npc_question_structural_invariants` | `tests/test_golden_replay.py` | Full pipeline social/dialogue routing, selected speaker, target trace, final source, no scaffold leakage. | Canonical: listed in canonical baseline. | Inline seeded scene/world; `run_golden_replay`; mocked GPT response. | One end-to-end turn. |
| `vocative_override_after_prior_continuity` / `test_golden_replay_vocative_override_after_prior_continuity_structural_invariants` | `tests/test_golden_replay.py` | Full pipeline continuity override by spoken vocative and target/speaker routing. | Canonical: listed in canonical baseline. | Inline runner/guard continuity setup; mocked response chain. | Two-turn social routing case. |
| `wrong_speaker_strict_social_emission` / `test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants` | `tests/test_golden_replay.py` | Full pipeline strict-social correction of illegal speaker attribution; final emission text safety. | Canonical: listed in canonical baseline. | Inline continuity setup; mocked wrong-speaker candidate. | Protects speaker and final emission; source may be unavailable and is then only conditionally asserted. |
| `declared_alias_dialogue_plan` / `test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants` | `tests/test_golden_replay.py` | Gate/dialogue-plan handling of declared speaker aliases and canonical target preservation. | Canonical baseline, but direct-seam rather than full replay. | Imports fixtures from `tests/test_final_emission_gate.py` and `tests/test_block_s_speaker_local_rebind_equivalence.py`; calls `apply_final_emission_gate`. | Strong gate contract; not an end-to-end chat turn. |
| `thin_answer_action_outcome_final_emission` / `test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants` | `tests/test_golden_replay.py` | Full pipeline action-outcome contract survival, upstream-prepared repair, final source, and no thin/no-information output. | Canonical: listed in canonical baseline. | Inline notice-board scene fixture; mocked thin GPT output. | Protects planner-to-final-emission outcome behavior. |
| `sanitizer_scaffold_leakage` / `test_golden_replay_sanitizer_scaffold_leakage_structural_invariants` | `tests/test_golden_replay.py` | Full pipeline removal/replacement of planner/router/validator/scaffold leakage in final text. | Canonical: listed in canonical baseline. | Inline scene fixture; mocked leaked candidate. | Protects final emission/sanitizer behavior; final source is conditionally checked when observable. |
| `opening_fallback_path` / `test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership` | `tests/test_golden_replay.py` | Gate-level canonical opening fallback source, response-type repair, authorship owner bucket, family/timeframe, no compatibility-local ownership. | Canonical baseline, but direct-seam rather than full replay. | `_opening_gm_output` imported from `tests/test_final_emission_gate.py`; `apply_final_emission_gate`; FEM helper. | Strong final-emission/fallback ownership lock; companion test prevents compatibility-local reporting. |
| `lead_followup_with_dialogue_lock` / `test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants` | `tests/test_golden_replay.py` | Full pipeline multi-turn dialogue lock persistence and lead-follow-up speaker/route continuity. | Canonical: listed in canonical baseline. | Inline tavern/milestone/runner setup; mocked response chain. | Two-turn continuity/lead scenario. |
| `scenario_spine_three_branch` / `test_golden_replay_scenario_spine_three_branch_structural_smoke` | `tests/test_golden_replay.py` | Compact branch identity/turn-count/divergence smoke plus no scaffold leakage through golden harness. | Canonical baseline label, but locally constructed smoke fixture. | Inline `ScenarioSpine` dataclass; `minimal_complete_transcript_turn_meta`; inline seeds. | Does not consume either committed JSON scenario-spine fixture; each branch is only one turn. |

### Supporting and adjacent replay coverage

| Scenario/Test | Path | Protects | Canonicality | Dependencies | Notes |
|---|---|---|---|---|---|
| Golden observation, drift bucket, renderer, fallback-owner and sanitizer/runtime-lineage projection contracts | `tests/test_golden_replay.py` (tests before the nine scenario tests); `tests/helpers/golden_replay.py` | Reliability of replay projection and diagnostic classification surface. | Canonical support for golden replay plumbing. | FEM metadata, trace projections, classifier/dashboard helpers. | Necessary for trustworthy failures; not player scenarios themselves. |
| Failure dashboard known-bad probes | `tests/test_failure_dashboard_controlled_failures.py`; `tests/test_failure_classifier.py`; `tests/test_failure_classification_contract.py` | Triage categories, owners, severity, evidence rendering, taxonomy. | Diagnostic/support; intentionally non-canonical gameplay. | `tests/helpers/failure_classifier.py`; `tests/helpers/failure_dashboard_report.py`. | Keep out of scenario acceptance count. |
| `frontier_gate_long_session`: `branch_social_inquiry`, `branch_direct_intrusion`, `branch_cautious_observe` | `data/validation/scenario_spines/frontier_gate_long_session.json`; exercised by scenario-spine tests/CLI | Long-session continuity, referents, progression, grounding, branch coherence, convergence, divergence. | Canonical for the game-level scenario-spine lane. | `game/scenario_spine*.py`; `tools/run_scenario_spine_validation.py`. | 25/25/10 scripted turns; not currently golden CI execution. |
| C1-A opening convergence paths | `data/validation/scenario_spines/c1a_opening_convergence_paths.json`; `tests/test_scenario_spine_opening_convergence.py` | Observational opening convergence paths and opening seam evidence. | Fixture/smoke for scenario-spine convergence; not named golden canonical. | Opening convergence evaluator. | Valuable adjacent coverage, not an existing golden scenario. |
| N1 `n1_anchor_persistence`, `n1_branch_divergence`, `n1_investigation_revisit`, `n1_progression_chain` | `tests/helpers/n1_scenarios.py`; N1 tests/CLI | Synthetic longitudinal continuity, branching, revisit and progression reason-code signals. | Canonical only inside the separate N1 lane. | N1 test-only harness/analyzer. | Explicitly separate from game-level scenario-spine and golden replay. |
| Transcript flows and transcript gauntlets | `tests/test_transcript_regression.py`; `tests/test_transcript_gauntlet_actor_addressing.py`; `tests/test_transcript_gauntlet_campaign_cleanliness.py`; `tests/test_narration_transcript_regressions.py` | Broader multi-turn regressions around continuity, actor address, campaign reset, narration/emission behavior. | Regression/adjacent, not the named golden baseline. | Transcript runner and inline fixtures. | Usually excluded from fast lane due to `transcript`/`slow` markers. |

## Protected Scenario Candidates

| Scenario | Recommendation | Reason | Required Cleanup |
|---|---|---|---|
| `directed_npc_question` | Promote now | Existing canonical end-to-end baseline with route, speaker, target, emission, and leakage invariants. | None required for initial promotion. |
| `vocative_override_after_prior_continuity` | Promote now | Existing canonical multi-turn routing/continuity case; protects a high-value regression surface. | None required for initial promotion. |
| `wrong_speaker_strict_social_emission` | Promote now | Existing canonical end-to-end illegal-speaker containment case with a crisp final-output invariant. | Later strengthen mandatory emitted-source observability if this becomes a release-level diagnostic contract. |
| `thin_answer_action_outcome_final_emission` | Promote now | Existing canonical pipeline case protects answer/action survival and upstream-prepared final repair. | None required for initial promotion. |
| `sanitizer_scaffold_leakage` | Promote now | Existing canonical full-pipeline safety case; internal scaffold leakage is an acceptance-level failure. | Later decide whether `final_emitted_source` must be mandatory rather than conditionally observable. |
| `lead_followup_with_dialogue_lock` | Promote now | Existing canonical multi-turn behavioral contract for dialogue continuity and lead follow-up. | None required for initial promotion. |
| `opening_fallback_path` | Promote now as protected direct-seam companion | Existing baseline explicitly protects canonical fallback authorship/source and rejects compatibility-local ownership. It is acceptance-relevant even though it is not end-to-end. | Label its scope clearly as direct-seam in any protected-scenario manifest/job output. |
| `declared_alias_dialogue_plan` | Needs cleanup before promotion | Useful gate contract, but it depends on private fixtures imported from other test modules and is direct-seam, not replay-through-chat. | Establish whether protected replay includes direct-seam contract rows; reduce cross-test fixture coupling or explicitly bless it. |
| `scenario_spine_three_branch` | Needs cleanup before promotion | Its branch structure is valuable, but it is an inline one-turn smoke spine that does not execute the committed canonical long-session JSON fixture. | Reconcile naming with `frontier_gate_long_session.json`, or explicitly keep it as golden smoke while promoting long-session execution separately. |
| Failure dashboard controlled probes | Keep non-canonical | They validate failure explanation, not acceptable gameplay behavior. | Keep opt-in and out of protected scenario totals. |
| Broad transcript regression/gauntlet suites | Keep non-canonical | Valuable regression evidence but marked heavy/transcript and not declared as golden baseline. | Select individual future scenarios deliberately rather than promoting the entire family. |
| N1 scenarios | Keep non-canonical for golden replay | Already a separate deterministic longitudinal lane with its own contract and CLI. | Decide separately whether N1 should become a second required CI job. |
| No existing golden scenario | Remove/deprecate candidate | No current canonical golden scenario is contradicted by repo evidence strongly enough to recommend removal. | N/A. |

## Drift / Threshold Inventory

| Existing Mechanism | Path | What It Measures | Hard/Soft | Promotion Usefulness |
|---|---|---|---|---|
| Field-level golden expectations: `equals`, `one_of`, `not_equals`, presence and unavailable handling | `tests/helpers/golden_replay.py`; `tests/test_golden_replay.py` | Structural route/speaker/FEM/fallback/trace invariants. | Hard when invoked by pytest scenario assertions. | Strong foundation for initial required golden gate. |
| Semantic golden predicates: required/forbidden fragments and `scaffold_leakage` | `tests/helpers/golden_replay.py`; `tests/test_golden_replay.py` | Semantic safety and final-text contract failures without locking all prose. | Hard when invoked by pytest assertions. | Strong for acceptance failures such as leaked scaffolding or wrong speaker. |
| Exact text hash drift, opt-in | `tests/helpers/golden_replay.py` (`normalize_golden_text`, `golden_text_hash`, `classify_golden_drift`) | Exact normalized `final_text` hash mismatch only when `exact_text` is supplied. | Hard only if a test asserts classifier failure/status; not enabled as the default baseline contract. | Suitable for rare deliberately fixed prose, not broad primary policy. |
| Drift categorization: `exact_drift`, `structural_drift`, `semantic_drift` | `tests/helpers/golden_replay.py`; `audits/golden_replay_baseline_2026-05-11.md` | Per-observation bucketed mismatch rows and summary counts. | Diagnostic inside helper; scenario assertions independently hard-fail. | Good vocabulary for promotion reporting; not yet an aggregate threshold policy. |
| Failure classification/dashboard | `tests/helpers/failure_classifier.py`; `tests/helpers/failure_dashboard_report.py`; contract/probe tests | Category, severity, primary/secondary owner, investigate-first target, evidence. | Classifier/contract tests hard; generated dashboard opt-in diagnostic. | Strong ergonomics once enabled on required CI failure paths. |
| Runtime-lineage event projection and frequency summary | `game/runtime_lineage_telemetry.py`; `game/final_emission_meta.py`; `tests/helpers/golden_replay.py`; `tools/run_scenario_spine_validation.py`; `tests/test_run_scenario_spine_validation.py` | Fallback selections, mutations, speaker repair, gate outcome paths, frequency and recurrence keys. | Observational; golden tests confirm projection but do not impose count ceilings. | Nearest existing support for fallback-count, mutation-count, and gate-path-frequency thresholds. |
| Scenario-spine narrative health scoring | `game/scenario_spine_eval.py`; `tests/test_scenario_spine_eval.py` | Failures deduct 24, warnings deduct 7, API-majority deducts 30; classification and `overall_passed`; degradation signals. | Evaluator tests hard; API runner's evaluated health is not enforced by CLI exit code. | Useful longitudinal candidate only after enforcement semantics are chosen. |
| Scenario-spine branch divergence | `game/scenario_spine_eval.py`; `tests/test_scenario_spine_eval.py` | Deterministic branch transcript divergence; tests assert divergent example `>= 0.12` and near-identical example `<= 0.1`. | Hard in evaluator tests; not a golden run threshold. | Existing quantitative comparison precedent for future protected branch scenarios. |
| Opening/transition convergence counts/verdicts | `game/scenario_spine_opening_convergence.py`; `game/scenario_spine_transition_convergence.py`; associated tests | Missing/invalid plan, seam failures, grounding failures, plan/output divergence; repeated opening style signal warns after at least 3 repetitions. | Hard inside evaluator verdict logic; advisory when only run via current CLI. | Useful scenario-spine gate input, distinct from golden drift. |
| N1 session-health/analyzer verdict and reason codes | `tests/helpers/n1_scenario_spine_harness.py`; `tests/helpers/n1_continuity_analysis.py`; `tools/run_n1_scenario_spine_validation.py` | Deterministic continuity/progression/revisit/branch codes and failed verdicts. | Hard in tests and N1 CLI exit status. | Candidate separate longitudinal required lane, not a threshold already attached to golden replay. |

No current golden replay mechanism was found for allowed line-count/token-count drift, aggregate fallback-count ceilings, aggregate mutation-count ceilings, gate-path frequency bounds, or evaluator-score thresholds attached directly to the golden scenarios. The closest existing inputs are replay-projected FEM/sanitizer/runtime-lineage fields and the scenario-spine runtime-lineage summary, which already counts these event families without using them for pass/fail.

## CI Promotion Assessment

### Current CI jobs

| Workflow / Job | Current Commands Relevant To Replay | Replay Included? | Enforcement |
|---|---|---|---|
| `.github/workflows/content-lint.yml` / `content-lint` | `python tools/planner_convergence_audit.py`; `python -m pytest tests/test_ownership_registry.py -q`; content lint/report upload. | No golden replay; no scenario execution. | Planner/ownership steps hard; content lint Phase 1 uses `continue-on-error: true`. |
| `.github/workflows/convergence-checks.yml` / `convergence-checks` | Hard pytest slices include `tests/test_scenario_spine_eval.py`; strict validation/final-emission/coverage audits; informational architecture/realization/C1/UI tools. | Includes scenario-spine evaluator unit coverage only. No `tests/test_golden_replay.py`, no `-m golden_replay`, no scenario-spine CLI run. | Listed pytest/strict audit steps hard; informational tools use `continue-on-error: true`. |

### Missing replay job pieces

- No explicit required step or job for `python -m pytest tests/test_golden_replay.py -q`.
- No workflow artifact upload for replay dashboard output on failure.
- No protected-scenario manifest independent of test source; canonical expectations and scenario seeds remain inline.
- No policy deciding whether direct-seam golden rows are part of required replay acceptance or companion contract checks.
- No hard-fail execution of the canonical JSON long-session scenario spine.

### Likely command to add

Initial required golden acceptance step:

```bash
python -m pytest tests/test_golden_replay.py -q
```

Equivalent marker-based form if future golden files are added:

```bash
python -m pytest -m golden_replay -q
```

The marker-based form is the better long-term job contract because it can include future protected golden modules without editing the workflow command.

### Risks / blockers

- **Low blocker for initial promotion:** golden replay is already deterministic, fake-GPT/fixture driven in its scenario tests, and hard-failing under pytest.
- **Medium governance risk:** inline baseline expectations make protected scenario review less obvious than a dedicated manifest/fixture registry.
- **Medium diagnostic risk:** dashboard artifact creation is opt-in and is not wired for CI failure collection.
- **High blocker for promoting game-level long-session CLI as required:** `tools/run_scenario_spine_validation.py` does not convert evaluator failure into process failure.
- **Unknown runtime budget:** prior audit records give pass counts but not reliable CI timing; a focused golden run should be timed before setting job expectations. It is likely much smaller than full scenario-spine execution because current golden scenarios use mocked deterministic model responses and short turns.

Replay could be added as a separate required job or a hard-fail step in `convergence-checks`. A separate job would make the acceptance mechanism legible and preserve independent status/reporting; a step is the smallest initial wiring change.

## Failure Ergonomics

### Currently good

- A failing golden expectation includes `field_path`, `expected`, `actual`, and the reason for failure from `assert_golden_turn_observation(...)`.
- Scenario tests pass `format_golden_replay_debug(...)` or equivalent context, which includes scenario identity and per-turn projected/debug context.
- The observed row captures route, selected speaker/source, final emission source, response-type repair fields, fallback family/timeframe, sanitizer lineage, owner buckets, trace fields, unavailable fields, and runtime-lineage events.
- The classifier/dashboard layer can add category, severity, owner, investigate-first target, evidence, final source, fallback, and mutation signals.
- Controlled known-bad probe tests validate that diagnostic vocabulary and rendering remain stable.

### Missing or awkward for an acceptance gate

- Ordinary golden replay failures do not automatically write an artifact; a developer or CI job must request `--write-failure-dashboard`.
- There is no one command in CI logs today labeled as the required replay acceptance gate.
- The committed baseline report is not executable expected data, so a reviewer cannot diff baseline changes independently of test-code edits.
- Scenario names are visible in test node IDs/debug output, but fixtures are mostly inline setup functions rather than a path printed as a scenario fixture source.
- Golden assertions are per-field and predicate-oriented; there is no rendered expected-versus-actual consolidated replay report on ordinary failure.
- Runtime-lineage counters are captured/optionally rendered, but no golden acceptance rule currently tells a developer when a fallback/mutation/gate-path count constitutes unacceptable drift.
- The game-level scenario-spine CLI can report evaluator failure in artifacts without failing the shell command, which is unsuitable for a required acceptance developer experience until addressed.
- No documented reproduction command is emitted inside assertion failures themselves, although it is easy to find in `tests/README_TESTS.md`.

## Proposed Cycle K Blocks

### Block K1 — Canonical Protected Replay Declaration

- **Goal:** Name the existing golden replay acceptance set explicitly, including whether direct-seam rows are protected companions or members of the primary replay gate.
- **Files likely touched:** `tests/test_golden_replay.py`; `tests/README_TESTS.md`; `audits/golden_replay_baseline_2026-05-11.md` or a successor report; possibly a new test-only protected-scenario manifest.
- **Acceptance criteria:** Every promoted scenario has a stable ID, scope (`end-to-end` or `direct-seam`), protected invariant summary, and one documented reproduction command; non-canonical probes/N1/transcript lanes remain separately labelled.
- **Risk level:** Low.

### Block K2 — Required Golden Replay CI Gate

- **Goal:** Make new work fail CI when protected golden replay fails.
- **Files likely touched:** `.github/workflows/convergence-checks.yml` or a new replay workflow; `docs/convergence_ci_inventory.md`; `tests/README_TESTS.md`.
- **Acceptance criteria:** CI runs `python -m pytest -m golden_replay -q` (or the narrowly equivalent test path) as a hard-fail required check; CI documentation records it as required acceptance.
- **Risk level:** Low.

### Block K3 — Failure Artifact and Reproduction Ergonomics

- **Goal:** Make a failed required replay job immediately actionable.
- **Files likely touched:** `.github/workflows/convergence-checks.yml` or replay workflow; `tests/helpers/failure_dashboard_report.py`; `tests/conftest.py`; `tests/README_TESTS.md`.
- **Acceptance criteria:** Required replay failure produces or uploads a deterministic diagnostic artifact containing scenario ID, failed field, expected/actual, owner classification when available, runtime-lineage summary when available, and reproduction command.
- **Risk level:** Low-medium.

### Block K4 — Drift Threshold Policy

- **Goal:** Turn existing observational signals into deliberate acceptance policy only where stable and meaningful.
- **Files likely touched:** `tests/helpers/golden_replay.py`; `tests/test_golden_replay.py`; possibly replay test-only fixtures/manifest; docs.
- **Acceptance criteria:** Policy declares which signals are exact hard failures, structural hard failures, semantic hard failures, and which aggregate counters have permitted bounds or remain report-only; thresholds are exercised by deterministic tests.
- **Risk level:** Medium.

### Block K5 — Canonical Longitudinal Replay Decision

- **Goal:** Decide whether the JSON-defined game-level scenario spine or N1 lane should join golden replay as an additional required longitudinal gate.
- **Files likely touched:** `tools/run_scenario_spine_validation.py` and tests/docs if game-level lane is selected; or N1 docs/workflow if N1 is selected; CI only after deliberate selection.
- **Acceptance criteria:** One selected longitudinal lane has canonical scenario identity, bounded runtime expectations, hard failure exit behavior, artifacts, and an explicit relationship to the short golden gate; the other lanes remain clearly non-canonical/advisory.
- **Risk level:** Medium-high.

## Files To Pass Back To ChatGPT

Minimum high-signal set for the next planning step:

1. `docs/audits/cycle_k_replay_promotion_recon_2026-05-26.md`
2. `tests/test_golden_replay.py`
3. `tests/helpers/golden_replay.py`
4. `audits/golden_replay_baseline_2026-05-11.md`
5. `tests/helpers/failure_classifier.py`
6. `tests/helpers/failure_dashboard_report.py`
7. `tests/conftest.py`
8. `.github/workflows/convergence-checks.yml`
9. `.github/workflows/content-lint.yml`
10. `pytest.ini`
11. `tests/README_TESTS.md`

Add these only if the next plan includes longitudinal replay or threshold/counter promotion:

12. `data/validation/scenario_spines/frontier_gate_long_session.json`
13. `data/validation/scenario_spines/c1a_opening_convergence_paths.json`
14. `game/scenario_spine_eval.py`
15. `tools/run_scenario_spine_validation.py`
16. `tests/test_scenario_spine_eval.py`
17. `tests/test_run_scenario_spine_validation.py`
18. `game/runtime_lineage_telemetry.py`
19. `game/final_emission_meta.py`
20. `docs/scenario_spine_validation.md`
21. `docs/convergence_ci_inventory.md`

## Validation Performed

Command run from repository root:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_golden_replay.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_k_validation
```

- **Status:** Pass (`exit code 0`; output reached `[100%]`).
- **Collection failures:** None observed.
- **Scope:** Focused existing golden replay pytest module only; scenario-spine/N1 manual CLIs and CI workflows were not executed or changed.
