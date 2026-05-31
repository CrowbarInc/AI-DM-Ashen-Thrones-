# Cycle Q - Replay Cost Compression Recon (2026-05-29)

Goal: preserve replay authority while reducing replay operational drag. This pass is reconnaissance only; no runtime or test behavior changes were made.

## 1. Replay Suite Map

| Path | Purpose | Owner / likely responsibility | Classification |
|---|---|---|---|
| `tests/test_golden_replay.py` | Required golden replay suite, protected scenarios, projection/renderer contract tests, inline seed fixtures, direct-seam companion locks, 20-turn Frontier Gate stability replay. | Protected replay acceptance owner. | Authoritative |
| `tests/helpers/golden_replay.py` | Golden replay runner, observed-turn projection, drift assertion/classification bridge, long-session summaries, scenario-spine continuity bridge, debug formatting. | Golden replay helper/projection owner. | Helper-only, but authority-critical |
| `docs/testing/protected_replay_manifest.md` | Governance declaration for protected/supporting/advisory/deprecated replay lanes and scenario IDs. | Protected replay governance owner. | Documentation-only, authority declaration |
| `.github/workflows/convergence-checks.yml` | Hard-fail CI runs `python -m pytest -m golden_replay -q` and uploads protected replay failure report on failure. | CI acceptance owner. | Authoritative execution wiring |
| `tests/conftest.py` | Opt-in failure dashboard CLI flag and session-finish protected replay failure report hook. | Pytest diagnostic plumbing owner. | Helper-only |
| `tests/helpers/failure_dashboard_report.py` | Builds dashboard rows and protected replay failure report at `artifacts/golden_replay/replay_failure_report.md`. | Replay diagnostics/reporting owner. | Helper/artifact writer |
| `tests/helpers/failure_classifier.py` | Classifies replay drift rows into category, owner, severity, tags, source-family, and investigation target. | Replay triage taxonomy owner. | Helper-only, taxonomy-authoritative |
| `tests/failure_classification_contract.py` | Allowed replay diagnostic categories, owners, severities, tags, source families, and required row fields. | Replay diagnostic schema owner. | Authoritative schema |
| `tests/test_failure_classifier.py` | Classifier behavior coverage. | Diagnostic helper tests. | Authoritative for helper behavior |
| `tests/test_failure_dashboard_controlled_failures.py` | Known-bad replay-shaped probes for dashboard classification/rendering. | Diagnostic probe owner. | Supporting |
| `tests/test_failure_classification_contract.py` | Contract tests for classifier/dashboard schema. | Diagnostic schema tests. | Authoritative schema tests |
| `docs/archive/dead_governance/2026-05-31/golden_replay_baseline_2026-05-11.md` | Historical human-readable golden baseline (archived). Not loaded by tests. | Replay baseline documentation. | Documentation-only |
| `docs/archive/dead_governance/2026-05-31/golden_replay_readiness_2026-05-11.md` | Historical readiness assessment (archived). | Replay audit history. | Documentation-only |
| `audits/replay_failure_corpus.md` | Historical replay failure corpus. | Replay audit history. | Documentation-only |
| `audits/failure_dashboard_latest.md` | Opt-in latest failure dashboard path. | Generated diagnostic artifact. | Artifact-only |
| `audits/failure_dashboard_*.md` | Historical dashboard probes/audits/samples. | Diagnostic audit history. | Documentation/artifact-only |
| `artifacts/golden_replay/replay_failure_report.md` | CI-uploaded protected replay failure report when failures are recorded. May not exist locally on a passing run. | Generated protected replay failure artifact. | Artifact-only |
| `tests/helpers/transcript_runner.py` | Shared transcript harness: storage patch, bootstrap scenes, clean campaign, chat turn snapshots. | Transcript harness owner. | Helper-only |
| `tests/helpers/transcript_snapshots.py` | Snapshot projection, compact summaries, target/source extraction, turn debug blocks. | Transcript snapshot owner. | Helper-only |
| `tests/test_transcript_runner_smoke.py` | Smoke coverage for transcript runner. | Transcript helper test owner. | Supporting |
| `tests/test_transcript_regression.py` | Transcript-backed multi-turn regressions for consequence-first behavior. | Transcript regression owner. | Supporting/advisory |
| `tests/test_transcript_gauntlet_actor_addressing.py` | Slow transcript gauntlet for actor addressing. | Transcript gauntlet owner. | Supporting/advisory |
| `tests/test_transcript_gauntlet_campaign_cleanliness.py` | Slow transcript gauntlet for reset/campaign cleanliness. | Transcript gauntlet owner. | Supporting/advisory |
| `tests/test_narration_transcript_regressions.py` | Narration transcript regression matrix and local transcript fixture utilities. | Narration regression owner. | Supporting/advisory |
| `tests/test_anti_railroading_transcript_regressions.py` | Transcript-shaped anti-railroading regression evidence. | Anti-railroading owner. | Supporting/advisory |
| `tests/test_gauntlet_regressions.py` | Gauntlet-style regression coverage. | Regression owner. | Supporting/advisory |
| `data/validation/scenario_spines/frontier_gate_long_session.json` | Canonical long-session scenario-spine source; `branch_social_inquiry` first 20 prompts feed protected golden replay. | Scenario-spine fixture owner. | Authoritative fixture |
| `data/validation/scenario_spines/c1a_opening_convergence_paths.json` | Opening convergence scenario-spine smoke fixture. | Scenario-spine fixture owner. | Supporting fixture |
| `game/scenario_spine.py` | Scenario-spine dataclasses, JSON conversion, schema validation. | Scenario-spine schema owner. | Authoritative runtime/tool schema |
| `game/scenario_spine_eval.py` | Scenario-spine evaluator, metadata completeness, branch divergence, long-session health, `minimal_complete_transcript_turn_meta`. | Scenario-spine evaluation owner. | Authoritative evaluator/helper |
| `tools/run_scenario_spine_validation.py` | API-backed scenario-spine runner and artifact writer (`transcript.json`, `session_health_summary.json`, `compact_operator_summary.md`, aggregate summaries). | Scenario-spine operational tool owner. | Advisory artifact generator |
| `tests/test_scenario_spine_contracts.py` | Scenario-spine schema/fixture validation. | Scenario-spine contract tests. | Authoritative for schema |
| `tests/test_scenario_spine_eval.py` | Deterministic evaluator coverage for health, degradation, metadata, branch divergence. | Evaluator tests. | Authoritative evaluator tests |
| `tests/test_scenario_spine_opening_convergence.py` | Opening convergence fixture/evaluator coverage. | Opening convergence tests. | Supporting |
| `tests/test_scenario_spine_continuation_convergence.py` | Continuation convergence evaluator coverage. | Continuation convergence tests. | Supporting |
| `tests/test_run_scenario_spine_validation.py` | Scenario-spine CLI/artifact/runtime-lineage contracts without live model. | Runner artifact tests. | Authoritative for artifact shape |
| `tests/helpers/n1_scenario_spine_contract.py` | N1 synthetic long-session typed contracts. | N1 tooling owner. | Authoritative for N1 lane only |
| `tests/helpers/n1_scenario_spine_harness.py` | N1 synthetic branch execution, health summaries, JSON artifacts, branch comparison. | N1 tooling owner. | Helper-only |
| `tests/helpers/n1_scenarios.py` | Code-defined N1 scenario registry and fake-GM scripts. | N1 fixture owner. | Authoritative for N1 fixtures |
| `tools/run_n1_scenario_spine_validation.py` | N1 CLI with hard-fail synthetic verdict behavior. | N1 operational tool owner. | Advisory/separate lane |
| `tests/test_n1_scenario_spine_validation.py`, `tests/test_n1_scenario_spine_cli.py`, `tests/test_n1_analyzer_regression.py` | N1 contract, CLI, and analyzer tests. | N1 tests. | Supporting/separate lane |
| `tests/README_TESTS.md` | Replay commands, protected replay CI status, dashboard commands, marker docs, full/fast lane commands. | Test operations docs. | Documentation-only |
| `docs/testing.md`, `docs/scenario_spine_validation.md`, `docs/n1_scenario_spine_validation.md` | Validation lane documentation and scenario-spine/N1 commands. | Validation docs. | Documentation-only |
| `docs/audits/cycle_k_*.md`, `docs/cycles/cycle_n_*.md` | Replay promotion, protected declaration, failure artifact, 20-turn replay, long-session stability history. | Audit/report history. | Documentation-only |
| `pytest.ini` | Registers `golden_replay`, `transcript`, `slow`, and `failure_dashboard_probe` markers; sets repo-local basetemp. | Test configuration owner. | Authoritative config |

## 2. Duplicate Fixture Inventory

| Duplicate family | Files involved | Duplicated setup / metadata / assertion pattern | Safe to consolidate? | Recommended owner/helper |
|---|---|---|---|---|
| Golden replay scene/world/session seeds | `tests/test_golden_replay.py` local `_seed_*`; related setup patterns in `tests/test_transcript_regression.py`, `tests/test_transcript_gauntlet_*`, `tests/test_narration_transcript_regressions.py` | Repeated `default_scene`, `default_world`, `storage._save_json`, `storage.load_session`, `active_scene_id`, `visited_scene_ids`, NPC/topic fixtures. | Partly. Safe inside golden replay first; broader transcript consolidation needs human review because scenarios encode different intent. | New `tests/helpers/replay_fixtures.py` or narrow `tests/helpers/golden_replay_fixtures.py` with `seed_scene`, `seed_world_npcs`, `set_active_scene`. |
| Repeated no-scaffold expectation | `tests/test_golden_replay.py` protected scenarios; transcript regression helpers; failure classifier/dashboard tests | Repeated forbidden terms: `planner`, `router`, `validator`, `adjudication`, `scaffold`, plus `scaffold_leakage: False`. | Yes for golden replay. Needs review before changing transcript prose assertions. | `tests/helpers/golden_replay.py` expectation builder such as `protected_no_scaffold_expectation(...)` or constants for forbidden scaffold terms. |
| Golden protected expectation boilerplate | `tests/test_golden_replay.py` protected scenarios | Repeated `require_present`, `allow_unavailable`, route `one_of`, `not_equals final_emitted_source`, no-scaffold fields. | Yes if additive and local to tests. | `tests/helpers/golden_replay.py` expectation composition helpers. |
| Scenario-spine branch prompt/id loading | `tests/test_golden_replay.py` `_frontier_gate_branch_prompts`, `_frontier_gate_branch_turn_ids`, `_frontier_gate_long_session_spine`; `tools/run_scenario_spine_validation.py` fixture loading | JSON is read repeatedly from the same canonical fixture; prompt/id extraction logic is local. | Yes for read-only helper. | `tests/helpers/golden_replay.py` or new `tests/helpers/scenario_spine_fixtures.py`; avoid moving runtime schema logic out of `game/scenario_spine.py`. |
| Transcript metadata envelope construction | `tests/test_golden_replay.py`, `tests/helpers/golden_replay.py`, `tools/run_scenario_spine_validation.py`, `tests/test_run_scenario_spine_validation.py` | Repeated `spine_id`, `branch_id`, `turn_id`, `turn_index`, `smoke`, `max_turns`, `resume` checks around `minimal_complete_transcript_turn_meta`. | Mostly yes. Do not alter metadata shape; consolidate only test-side assertions/builders. | Keep canonical shape in `game/scenario_spine_eval.py`; add test assertion helper near `tests/test_run_scenario_spine_validation.py` if reused. |
| Long-session artifact summary metrics | `tests/helpers/golden_replay.py`, `tools/run_scenario_spine_validation.py`, `tests/test_run_scenario_spine_validation.py` | Both summarize route/speaker/fallback/runtime-lineage/operator-facing metrics, but formats differ. | Needs human review. Signals overlap but protected replay and CLI artifacts have different audiences. | Clarify ownership first: protected replay summary in `tests/helpers/golden_replay.py`; scenario-spine operator artifact in `tools/run_scenario_spine_validation.py`. |
| Failure report rows and dashboard rows | `tests/helpers/golden_replay.py`, `tests/helpers/failure_dashboard_report.py`, `tests/helpers/failure_classifier.py` | Drift rows are classified then rendered in two paths: opt-in dashboard and protected replay failure report. | Yes for naming/shape helpers; avoid changing taxonomy. | `tests/helpers/failure_dashboard_report.py` owns rendering; `tests/helpers/failure_classifier.py` owns taxonomy. |
| Manual gauntlet artifact naming | `tools/run_manual_gauntlet.py`, `tools/aggregate_manual_gauntlets.py`, `tests/test_manual_gauntlet_report.py`, `tests/test_manual_gauntlet_aggregation.py` | `_summary.json`, `_transcript.md`, operator verdict/notes normalization. | Out of Cycle Q scope unless "replay artifact ergonomics" explicitly includes manual gauntlets. | Leave in manual gauntlet tooling. |

## 3. Overlapping Replay Assertion Inventory

| Invariant | Files involved | Intentional defense-in-depth or drag? | Recommendation |
|---|---|---|---|
| No scaffold/internal planning leakage in final player text | `tests/test_golden_replay.py`, `tests/helpers/golden_replay.py`, `tests/test_failure_classifier.py`, transcript/narration regressions | Intentional across acceptance, classifier, and transcript lanes; maintenance drag in repeated literal terms. | Keep invariant everywhere; consolidate golden replay term list/expectation helper only. |
| Speaker/target selected correctly for directed social turns | `tests/test_golden_replay.py`, `tests/test_transcript_gauntlet_actor_addressing.py`, many speaker/social contract tests | Intentional defense-in-depth. Golden replay owns acceptance-level pipeline outcomes; direct owner tests own fine-grained contracts. | Keep; add ownership comments/helper names rather than deleting. |
| Route kind remains social/dialogue/question-shaped | `tests/test_golden_replay.py`, route/social tests, transcript gauntlets | Intentional. Replay validates cross-pipeline observed route; direct tests validate routing logic. | Keep; consolidate allowed route tuple if repeated inside golden replay only. |
| Final emitted source/fallback family not global fallback | `tests/test_golden_replay.py`, final-emission/fallback tests, failure classifier | Intentional, but golden expectations repeat optional/unavailable handling. | Keep; move repeated expectation fragments to golden helper. |
| Opening fallback canonical owner/source | `tests/test_golden_replay.py`, `tests/helpers/opening_fallback_evidence.py`, final-emission/fallback ownership tests/docs | Intentional direct-seam acceptance companion plus direct owner tests. | Keep; clarify direct-seam ownership in names/docs if touched. |
| Sanitizer lineage and legacy rewrite disabled | `tests/test_golden_replay.py`, sanitizer tests, failure dashboard/classifier | Intentional. Replay protects acceptance-visible projection; sanitizer tests protect local behavior. | Keep; do not collapse. |
| Runtime-lineage event projection and summaries | `tests/test_golden_replay.py`, `tests/helpers/golden_replay.py`, `tests/test_run_scenario_spine_validation.py`, `game/runtime_lineage_telemetry.py` | Partly drag: projection paths and summaries overlap; artifacts serve different users. | Clarify ownership; keep both summaries unless a shared pure summarizer already exists in `game/runtime_lineage_telemetry.py`. |
| Long-session degradation/continuity health | `tests/test_golden_replay.py`, `tests/helpers/golden_replay.py`, `game/scenario_spine_eval.py`, `tests/test_scenario_spine_eval.py` | Intentional bridge: golden replay consumes scenario-spine evaluator to harden 20-turn replay. | Keep; avoid changing evaluator semantics. |
| Scenario-spine metadata completeness | `game/scenario_spine_eval.py`, `tools/run_scenario_spine_validation.py`, `tests/test_run_scenario_spine_validation.py`, `tests/helpers/golden_replay.py` projection bridge | Intentional, but metadata field ownership could be clearer. | Keep; document canonical shape and avoid extra local construction. |
| Failure dashboard row schema | `tests/failure_classification_contract.py`, `tests/test_failure_classification_contract.py`, `tests/helpers/failure_dashboard_report.py`, `tests/test_failure_dashboard_controlled_failures.py` | Intentional schema lock. | Keep; do not weaken. |

## 4. Fixture Helper Consolidation Candidates

Helpers that should remain as-is:

- `tests/helpers/transcript_runner.py`: clean transcript harness used beyond golden replay.
- `tests/helpers/transcript_snapshots.py`: snapshot-only projection; already split from runner.
- `tests/helpers/golden_replay.py`: primary golden replay helper/projection owner.
- `game/scenario_spine_eval.py::minimal_complete_transcript_turn_meta`: canonical metadata envelope builder.
- `tests/helpers/failure_classifier.py` and `tests/helpers/failure_dashboard_report.py`: classifier/rendering separation is useful.
- N1 helpers under `tests/helpers/n1_*`: intentionally separate synthetic lane.

Helpers too local and worth promoting:

- Golden seed setup helpers in `tests/test_golden_replay.py` (`_seed_directed_runner_question_context`, `_seed_runner_and_guard_context`, `_seed_runner_continuity_context`, `_seed_tavern_patrol_lead_context`, `_seed_scene_object_investigation_context`, `_seed_spine_three_branch_context`, `_seed_frontier_gate_long_session_context`).
- Frontier Gate fixture readers in `tests/test_golden_replay.py` (`_frontier_gate_branch_prompts`, `_frontier_gate_branch_turn_ids`, `_frontier_gate_long_session_spine`).
- Common protected expectation fragments in `tests/test_golden_replay.py`: no-scaffold terms, route allowlists, standard unavailable lists.

Redundant helpers:

- No fully redundant helper module found. Most overlap is local boilerplate inside `tests/test_golden_replay.py`, not duplicate modules.
- `tests/helpers/opening_fallback_evidence.py` overlaps with direct hand-built turn dicts in golden replay tests but is already a focused fixture helper; prefer reuse rather than replacement.

Naming inconsistencies:

- `scenario_id` in golden replay vs `spine_id` in scenario-spine JSON vs `scenario_spine_id` in N1 contracts.
- `branch_id_requested` / `branch_id_resolved` in the scenario-spine runner vs plain `branch_id` in metadata and golden replay bridge.
- `final_text` in golden observed rows vs `gm_text` in transcript rows vs `player_facing_text` in runtime payloads.
- `fallback_family`, `fallback_family_used`, and `realization_fallback_family` are intentionally projected aliases, but tests must keep remembering which view they assert.
- `smoke`, `smoke_only`, and `scope_label` refer to related but not identical concepts.

Safest one-cluster consolidation candidate:

Extract golden replay expectation fragments and fixture readers only:

- Add helper constants/functions in `tests/helpers/golden_replay.py` for no-scaffold forbidden terms, standard optional projection fields, and `load_scenario_spine_branch_turns(...)`.
- Touch `tests/test_golden_replay.py` only to use those helpers.
- No runtime behavior changes, no assertion weakening, and the protected replay file remains the owner of scenario-specific expectations.

## 5. Replay Metadata Normalization

Observed canonical shapes:

- Golden observed turn rows in `tests/helpers/golden_replay.py::_observed_turn`: `scenario_id`, `turn_index`, `player_text`, `final_text`, route/speaker/FEM/fallback/sanitizer/projection fields, `trace`, `snapshot_summary`, `raw_signal_presence`, `normalized_signal_presence`, `missing_source_by_field`, `runtime_lineage_events`, `unavailable`.
- Scenario-spine transcript metadata in `game/scenario_spine_eval.py::minimal_complete_transcript_turn_meta`: envelope keys plus nested `scenario_spine` identity keys (`spine_id`, `branch_id`, `turn_id`, `turn_index`, `smoke`, `max_turns`, `resume`).
- Scenario-spine fixture JSON: `spine_id`, `title`, `smoke_only`, `fixed_start_state`, anchors/checkpoints, `branches[].branch_id`, `turns[].turn_id`, `player_prompt`.
- N1 contracts: `scenario_spine_id`, `branch_id`, deterministic config, branch point IDs, metadata dict.
- Failure rows: `scenario_id`, `turn_index`, `field_path`, `expected`, `actual`, `drift_bucket`, `category`, `primary_owner`, `severity`, tags and evidence fields per `tests/failure_classification_contract.py`.

Inconsistencies / drift:

- `scenario_id` vs `spine_id` vs `scenario_spine_id` is the main naming mismatch. It is not necessarily wrong because lanes differ, but bridge code should be explicit.
- `turn_id` exists in scenario-spine fixtures and transcript metadata; golden replay synthetic/protected short scenarios mostly use `turn_index`, except long-session bridge pulls turn IDs from JSON.
- `player_prompt` in fixture JSON becomes `player_text` in transcript/golden rows.
- `final_text`, `gm_text`, and `player_facing_text` represent related projections at different layers.
- `branch_id_requested` and `branch_id_resolved` are runner-specific; artifact readers must know which one is canonical.
- Fallback metadata is intentionally normalized across `fallback_family_used`, `realization_fallback_family`, and `fallback_family`, but the projection layer carries that complexity.

Missing required metadata:

- Golden short scenarios do not carry fixture path, branch ID, or turn ID because they are inline scenarios. That is acceptable today, but it increases review cost.
- Direct-seam protected rows use hand-built observed turn dicts, not the full golden row shape; this is intentional but should remain visibly labeled.
- Failure reports include scenario IDs and fields, but not always fixture source path or branch/turn ID for short inline scenarios.

Duplicated metadata construction:

- `minimal_complete_transcript_turn_meta(...)` is called from both golden replay bridge and scenario-spine runner/tests.
- Golden replay constructs observed rows by hand/projection; direct-seam tests construct subsets manually.
- N1 has separate scenario metadata contracts and should not be merged silently.

Projection drift:

- Golden replay now bridges `frontier_gate_long_session.json` into scenario-spine evaluator rows. The canonical metadata shape already exists in `game/scenario_spine_eval.py`, so Cycle Q should reuse it rather than inventing a replay-specific metadata schema.
- Docs have caught up with CI and 20-turn replay, but older Cycle K audit language still describes scenario-spine as advisory; treat older audit docs as historical, not current truth.

Suggested canonical metadata shape:

Keep lane-specific wrappers, but normalize bridge metadata around this shape when possible:

```text
replay_identity:
  scenario_id: protected replay scenario id
  source_path: optional fixture/doc source
  scope: end_to_end | direct_seam | supporting | advisory
  branch_id: optional scenario-spine branch
  turn_id: optional source turn id
  turn_index: zero-based observed turn index
  smoke: bool when scenario-spine-backed
  max_turns: optional cap
```

Implementation should start by documenting/projecting this shape in helpers only. Do not migrate all tests at once.

## 6. Replay Artifact Ergonomics

Artifacts and outputs:

- `artifacts/golden_replay/replay_failure_report.md`: protected replay failure report, written only when failures are recorded.
- `audits/failure_dashboard_latest.md`: opt-in classifier/dashboard artifact.
- `artifacts/scenario_spine_validation/<UTC>/<spine>/<branch>/transcript.json`: scenario-spine runner transcript.
- `artifacts/scenario_spine_validation/<UTC>/<spine>/<branch>/session_health_summary.json`: evaluator output.
- `artifacts/scenario_spine_validation/<UTC>/<spine>/<branch>/run_debug.json`: runner debug artifact.
- `artifacts/scenario_spine_validation/<UTC>/<spine>/<branch>/compact_operator_summary.md`: human summary.
- `artifacts/scenario_spine_validation/<UTC>/<spine>/_aggregate/*`: aggregate health/runtime-lineage/operator summaries.
- Manual gauntlet artifacts use `_summary.json`, `_transcript.md`, and aggregate reports under `artifacts/manual_gauntlets/`; adjacent, but not protected replay.

Hard to compare / interpret:

- Golden replay ordinary failures rely mostly on assertion text/debug context; the artifact exists only after recorded protected assertion failures.
- Long-session debug context is comprehensive but dense; it mixes route/speaker/fallback/continuity/lineage summaries.
- Scenario-spine runner artifacts are clear but use multiple files per branch plus aggregate files; comparing a golden replay failure against scenario-spine output requires knowing both formats.
- Historical docs/audits live in `audits/`, `docs/audits/`, and `docs/reports/`, which makes "latest current replay state" less obvious.

Duplicate output formats:

- Golden protected failure report and opt-in dashboard both render classified replay rows.
- Golden long-session markdown summary and scenario-spine compact operator summary both expose health/lineage/fallback-adjacent signals.
- Manual gauntlet transcript/summary naming is a separate format; leave it outside Cycle Q unless explicitly scoped.

Stale or confusing paths:

- Historical replay baseline archived at `docs/archive/dead_governance/2026-05-31/golden_replay_baseline_2026-05-11.md`; current protected status lives in `docs/testing/protected_replay_manifest.md` and Cycle N docs.
- Older Cycle K recon says scenario-spine is advisory and CI not yet wired; newer workflow/docs show protected replay is now CI-wired.
- `artifacts/golden_replay/replay_failure_report.md` may be absent locally after passing runs, which is correct but can confuse operators looking for it.

Clearer failure output opportunities:

- Add fixture source/branch/turn identity to long-session failure reports where available.
- Add a compact "replay identity" block to protected failure report rows.
- Reuse one summary row formatter for scenario ID, field, expected/actual, owner, and first investigation target.
- In assertion failures, include the exact marker command already used by CI.

Lowest-risk ergonomic improvement:

Add fixture source/branch/turn identity to golden replay debug/report rows for scenario-spine-backed protected replay, without changing pass/fail logic.

## 7. Risk Boundaries

Do not modify during Cycle Q unless explicitly targeted and reviewed:

- `game/final_emission_gate.py`, `game/final_emission_meta.py`, `game/speaker_contract_enforcement.py`, `game/output_sanitizer.py`, routing/social runtime modules: authoritative runtime behavior outside replay cost compression.
- `game/scenario_spine_eval.py` scoring/evaluator semantics: authoritative and shared by protected replay bridge and scenario-spine tests.
- `data/validation/scenario_spines/frontier_gate_long_session.json`: canonical fixture source for protected 20-turn replay.
- `docs/testing/protected_replay_manifest.md`: authority declaration; edit only when scenario status/ownership changes deliberately.
- `.github/workflows/convergence-checks.yml`: already hard-fails protected replay; avoid CI churn unless artifact/report commands change.
- `tests/failure_classification_contract.py`: taxonomy-authoritative; only change with classifier schema updates and tests.
- `tests/test_golden_replay.py` protected assertion thresholds for the 20-turn replay: do not relax under "compression."
- N1 synthetic lane helpers and CLI: separate lane; do not merge into golden replay in Cycle Q.
- Broad transcript/slow gauntlet files: valuable advisory evidence; do not thin them based solely on similarity to golden replay.

## 8. Recommended Cycle Q Block Plan

| Block | Goal | Exact files likely touched | Why safe | Tests to run | Parallel? |
|---|---|---|---|---|---|
| Q1 - Golden Expectation Fragment Helpers | Reduce repeated protected expectation boilerplate inside golden replay. | `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py` | Test-only helper extraction; no expectation weakening if helpers preserve exact values. | `python -m pytest tests/test_golden_replay.py -q --tb=short`; `python -m pytest -m golden_replay -q --tb=short` | Can run with Q3 if touching distinct helper sections, but easier serial. |
| Q2 - Golden Fixture Reader Extraction | Centralize reads from `frontier_gate_long_session.json` and branch prompt/turn-id extraction. | `tests/helpers/golden_replay.py` or new `tests/helpers/scenario_spine_fixtures.py`, `tests/test_golden_replay.py` | Read-only fixture helper; protected test still asserts same turns/counts. | `python -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability -q --tb=short`; full golden replay file | Can run parallel with Q1 only with careful merge. |
| Q3 - Replay Identity Metadata Projection | Add optional source/branch/turn identity to golden observed rows/debug/report inputs. | `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py`, possibly `tests/helpers/failure_dashboard_report.py` | Additive metadata/reporting only; no pass/fail changes. | `python -m pytest tests/test_golden_replay.py tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q --tb=short` | Can run parallel with Q4. |
| Q4 - Protected Failure Report Ergonomics | Make protected replay failure report show replay identity, source path/branch/turn when present, and reproduction command consistently. | `tests/helpers/failure_dashboard_report.py`, `tests/test_golden_replay.py`, possibly `tests/test_failure_dashboard_controlled_failures.py` | Reporting-only; assertion failures remain hard. | `python -m pytest tests/test_golden_replay.py::test_protected_golden_assertion_failure_records_canonical_report tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q --tb=short` | Parallel with Q2/Q3 if report API stable. |
| Q5 - Scenario-Spine Metadata Ownership Notes | Clarify canonical metadata shape and lane boundaries in docs, not code. | `docs/testing/protected_replay_manifest.md`, `tests/README_TESTS.md`, possibly this report's successor | Documentation-only; reduces future accidental merging of N1/scenario-spine/golden lanes. | Docs-only; optionally `python -m pytest tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_run_scenario_spine_validation.py -q --tb=short` | Can run parallel with all code blocks. |
| Q6 - Broader Replay Slice Verification Script/Docs | Document exact replay-only validation set after helper changes. | `tests/README_TESTS.md` only, unless adding a script is explicitly requested | Documentation-only; no behavior change. | See validation commands below. | Parallel with Q5. |

## Validation Commands

Replay-only / protected:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_golden_replay.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_q_golden
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_cycle_q_marker
```

Replay diagnostics:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_failure_classifier.py tests\test_failure_classification_contract.py tests\test_failure_dashboard_controlled_failures.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_q_dashboard
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -m golden_replay -q --tb=short --write-failure-dashboard --basetemp=codex_pytest_tmp_cycle_q_dashboard_write
```

Scenario-spine / long-session machinery:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_scenario_spine_contracts.py tests\test_scenario_spine_eval.py tests\test_scenario_spine_continuation_convergence.py tests\test_run_scenario_spine_validation.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_q_spine
```

Broader replay-adjacent slice after helper/report changes:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_golden_replay.py tests\test_scenario_spine_contracts.py tests\test_scenario_spine_eval.py tests\test_scenario_spine_continuation_convergence.py tests\test_run_scenario_spine_validation.py tests\test_failure_classifier.py tests\test_failure_classification_contract.py tests\test_failure_dashboard_controlled_failures.py tests\test_transcript_runner_smoke.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_q_replay_slice
```

Full-suite safety:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -q --tb=short --basetemp=codex_pytest_tmp_cycle_q_full
```

No validation commands were run during this recon pass.

## Short Findings

Top maintenance drag sources:

1. `tests/test_golden_replay.py` mixes protected scenarios, helper tests, inline fixtures, expectation boilerplate, direct-seam rows, and the 20-turn replay in one large file.
2. Repeated no-scaffold/unavailable/route/fallback expectation fragments make each replay fix touch more lines than the invariant actually requires.
3. Metadata names differ across lanes (`scenario_id`, `spine_id`, `scenario_spine_id`; `final_text`, `gm_text`, `player_facing_text`), so bridge/report code carries avoidable translation cost.

Safest first implementation block:

- Q1 - Golden Expectation Fragment Helpers, followed by Q2 - Golden Fixture Reader Extraction. This compresses repeated test maintenance without changing replay authority or runtime behavior.

Files to pass back for block generation:

- `tests/test_golden_replay.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/failure_classifier.py`
- `tests/failure_classification_contract.py`
- `tests/conftest.py`
- `docs/testing/protected_replay_manifest.md`
- `tests/README_TESTS.md`
- `data/validation/scenario_spines/frontier_gate_long_session.json`
- `game/scenario_spine_eval.py`
- `tests/test_run_scenario_spine_validation.py`
- `.github/workflows/convergence-checks.yml`
