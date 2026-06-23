# Cycle S - Runtime Drift Compression Recon

Date: 2026-05-30

## Executive Summary

Cycle S should start with measurement and artifact stabilization, not runtime behavior changes. The repo already has strong protected replay coverage for structural invariants, bounded long-session behavior, fallback escalation, lineage projection, and scenario-spine health. What is still thin is rerun-to-rerun comparison: the suite can tell whether one run violates declared invariants, but it does not yet summarize whether two legal runs drift in speaker choice, route choice, fallback frequency, continuity wording/shape, or response-delta frequency.

Recommended first direction:

- Add a lightweight replay rerun comparison artifact around existing golden replay observations.
- Keep exact prose comparison report-only except for explicitly curated cases.
- Add semantic-delta frequency reporting from existing response-delta/FEM metadata rather than adding a new semantic judge.
- Stabilize fixture/report identity fields before touching runtime selection logic.
- Treat model-backed scenario-spine CLI runs as advisory unless mocked/stubbed into deterministic pytest coverage.

## Existing Replay / Drift Infrastructure

| Path | Purpose | Variance already measured | Variance not yet measured |
|---|---|---|---|
| `tests/test_golden_replay.py` | Protected and supporting golden replay scenarios, including sustained 25-turn social inquiry, direct-intrusion diagnostic, and resume persistence probe. | Route/speaker/fallback structural invariants, scaffold leakage, bounded long-session route/speaker changes, fallback escalation, mutation/lineage recurrence, continuity/degradation bridge. | Rerun-to-rerun distributions for legal variants; semantic-delta frequency deltas across repeated runs; prose-level continuity phrasing variance. |
| `tests/helpers/golden_replay.py` | Golden replay runner, observed-turn projection, drift classification, long-session summaries, scenario-spine projection bridge. | Exact drift when `exact_text` is opt-in, structural drift, semantic predicate drift, route/speaker/fallback summaries, runtime-lineage summary. | No first-class multi-run comparator; no baseline-vs-current variance artifact for legal differences; no semantic similarity/delta trend summary beyond existing predicates. |
| `docs/testing/protected_replay_manifest.md` | Governance declaration for protected/supporting/advisory replay status. | Declares what failures block acceptance and which long-session paths are protected. | Does not define rerun variance thresholds or distribution policy. |
| `.github/workflows/convergence-checks.yml` | CI hard-fail gate for `python -m pytest -m golden_replay -q`; uploads protected failure report on failure. | Blocks protected replay assertion failures and uploads `artifacts/golden_replay/replay_failure_report.md` on failure. | Does not run repeated replay passes, scenario-spine aggregate CLI, or variance scorecards. |
| `tests/conftest.py` | Pytest plumbing for protected replay failure reporting/dashboard options. | Captures classified protected assertion failures for reporting. | No passing-run variance artifact or rerun comparison hook. |
| `tests/helpers/failure_classifier.py` and `tests/failure_classification_contract.py` | Replay failure taxonomy and schema. | Classifies exact/structural/semantic drift rows into route, speaker, fallback, emission, continuity, sanitizer, projection, and replay-drift ownership. | Classification only receives observed failures/probes; it does not compare two successful runs or quantify legal variance. |
| `tests/helpers/failure_dashboard_report.py` | Failure dashboard and protected replay report rendering. | Human-readable failure rows and investigation targets. | No successful-run scorecard, no rerun drift matrix. |
| `audits/replay_failure_corpus.md` | Historical controlled replay failure examples. | Concrete misleading-output examples: wrong speaker, forced fallback, missing route metadata, emission mutation, sanitizer leakage, continuity break. | Historical corpus, not executable rerun measurement. |
| `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md` | Drift policy memo. | Defines exact/structural/semantic/fallback/runtime-lineage/mutation drift categories and keeps non-asserted signals report-only/future-monitoring. | Explicitly defers thresholds for gate-path frequency, runtime-lineage counts, recurrence, broad fallback, and exact prose drift. |
| `data/validation/scenario_spines/frontier_gate_long_session.json` | Canonical long-session fixture. | Stable scripted player prompts for 25-turn social inquiry, 25-turn direct intrusion, and 10-turn cautious observe branch. | Fixture alone does not record rerun outputs or compare legal transcript variants. |
| `tools/run_scenario_spine_validation.py` | Advisory API-backed scenario-spine runner and artifact writer. | Per-branch `transcript.json`, `session_health_summary.json`, `run_debug.json`, `compact_operator_summary.md`; aggregate branch health/divergence/lineage with `--all-branches`. | May call live/model-backed app path; not a deterministic rerun comparator; branch divergence compares branches, not repeated runs of one branch. |
| `tests/test_run_scenario_spine_validation.py` | Stubbed runner/artifact tests. | Artifact shape, aggregate health, runtime lineage summary, 50-turn aggregate accounting. | Does not execute repeated real branch runs or compare legal output drift. |
| `game/scenario_spine_eval.py` and `tests/test_scenario_spine_eval.py` | Deterministic evaluator for scenario-spine health and branch divergence. | Continuity, referent persistence, progression, grounding, branch coherence, degradation windows, branch divergence. | Heuristic health over one transcript set; no multi-run variance scorecard for speaker/route/fallback metadata. |
| `docs/scenario_spine_validation.md` | Scenario-spine lane docs. | Documents deterministic health evaluator, artifacts, aggregate long-branch 50-turn path, and manual commands. | Keeps CLI review path advisory; no rerun variance command yet. |
| `tools/run_n1_scenario_spine_validation.py` and `docs/n1_scenario_spine_validation.md` | Separate deterministic synthetic long-session tooling. | Seeded synthetic configs, stable JSON, continuity reports, branch comparison. | Synthetic/test-only lane; does not measure real golden replay runtime drift. |
| `tests/helpers/transcript_runner.py` and `tests/helpers/transcript_snapshots.py` | Transcript harness and snapshot projection helpers. | Multi-turn API/chat snapshots, target/source extraction, compact turn summaries. | No protected rerun baseline or drift scorecard by itself. |
| `tests/test_transcript_regression.py`, `tests/test_transcript_gauntlet_*`, `tests/test_narration_transcript_regressions.py` | Replay-adjacent transcript regressions. | Multi-turn behavior and actor-addressing regressions. | Advisory; broader and slower; not unified with golden rerun variance. |
| `audits/cycle_q_replay_cost_compression_recon_2026-05-29.md` | Replay suite map and artifact ergonomics recon. | Maps replay owners, artifacts, metadata shapes, CI gate, and compression risks. | Maintenance/cost focus, not drift compression metrics. |

## Current Deterministic Controls

| Path | Owner function / class / test | Current invariant | Suspected drift seam |
|---|---|---|---|
| `game/model_routing.py` | `resolve_model_route` | Model route is selected from explicit inputs: purpose, policy, retry, strict-social, high-precision flag. | Route metadata is deterministic, but live model output remains unseeded; repeated model-backed CLI runs may produce legal prose variance. |
| `game/gm.py` | `call_gpt` | Wraps OpenAI call, attaches selected model/route metadata, returns schema-safe fallback on API error. | No `temperature`, `top_p`, or seed control in the call; live output variance is upstream. |
| `game/diegetic_fallback_narration.py` | `_stable_u32`, deterministic fallback renderers | Fallback line variants are chosen from stable seed keys, not process randomness. | Seed-key composition may include fields whose ordering/identity can shift; legal fallback phrasing may vary if seed inputs drift. |
| `game/interaction_context.py` | `rank_open_social_solicitation_candidates` | Candidate ordering is deterministic: active interlocutor tier, address priority, lexicographic id. | Missing or unstable address-priority/roster fields can change selected speaker while staying legal. |
| `game/interaction_context.py` | `resolve_declared_actor_switch`, `resolve_directed_social_entry` | Pre-classification route/speaker entry uses deterministic text/roster/continuity cues and addressability checks. | Ambiguous prompts can flip between social/dialogue/action routes when prior context or addressability projection shifts. |
| `game/api.py` | `chat` route selection path around `choose_interaction_route`, `parse_social_intent`, `parse_exploration_intent` | Route choice and canonical entry are recorded into trace/resolution metadata. | Multiple parsers are tried in order; legal route shifts can occur when an earlier parse becomes available/unavailable. |
| `game/speaker_contract_enforcement.py` | `_apply_speaker_contract_repairs` | Wrong/uncued speaker attribution is repaired through local rebind, canonical rewrite, or narrator-neutral fallback. | Narrator-neutral fallback uses a seed based partly on Python `hash(...)`, which is process-randomized unless hash seed is fixed; this is a likely Cycle S measurement target before behavior change. |
| `game/interaction_continuity.py` | `build_interaction_continuity_contract`, `validate_interaction_continuity`, `repair_interaction_continuity` | Continuity contract and repair are deterministic, pure reads/repairs over resolved contract and candidate text. | Repair phrasing/bridge insertion is deterministic for a given input, but warning/violation counts can vary with legal text shape. |
| `game/final_emission_gate.py` | `apply_final_emission_gate` | Deterministic gate ordering; response type, answer completeness, response delta, social response structure, authenticity, tone, authority, anti-railroading, context, continuity, fallback behavior, and final packaging are ordered. | Gate-path/final-source frequency is observed but not compared across repeated successful runs. |
| `game/final_emission_repairs.py` | `_default_response_delta_meta`, `_apply_response_delta_layer` | Response-delta legality metadata is canonical, semantic repair disabled at boundary. | Frequency of `response_delta_failed` / `response_delta_repaired` / echo overlap is not summarized across reruns. |
| `game/final_emission_validators.py` | `validate_response_delta` | Deterministic token overlap and delta-kind heuristics. | Current signal is turn-local; no aggregate semantic-delta frequency comparison for replay reruns. |
| `game/fallback_provenance_debug.py` and `game/stage_diff_telemetry.py` | `fingerprint_player_facing`, stage snapshots/diffs | Bounded fingerprints and stage diffs expose text/route mutation after gate stages. | Good observability, but no variance threshold or run-pair reporting. |
| `game/runtime_lineage_telemetry.py` | `make_runtime_lineage_event`, `summarize_runtime_lineage_events` | Canonical read-side event vocabulary and stable frequency/recurrence buckets. | Recurrence/frequency shifts are report-only; no baseline or rerun comparator. |
| `game/final_emission_replay_projection.py` | `build_fem_runtime_lineage_events` | Projects FEM fallback/gate/speaker/mutation evidence into lineage events. | Projection can reveal shifts but does not decide whether a shift is legal or concerning. |
| `tests/helpers/golden_replay.py` | `classify_golden_drift` | Exact text is opt-in; structural and semantic predicates are classified. | No fuzzy semantic comparison; exact hash drift is intentionally report-only unless explicitly asserted. |
| `tests/helpers/golden_replay.py` | `summarize_long_session_replay_observations`, `summarize_fallback_escalation_observations` | Counts route changes, speaker changes/missing, fallback totals/streaks/owners, mutation turns, continuity warnings/violations. | Single-run summary only; no expected distribution or per-field rerun delta artifact. |

## Legal-But-Different Examples Found

The repo already documents several classes where output can be acceptable but still drift-prone:

- `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md` states exact prose drift is report-only and unsafe as a global failure rule; it also defers thresholds for broad fallback, mutation, gate-path, runtime-lineage, and recurrence frequencies.
- `audits/replay_failure_corpus.md` notes fallback substitution can look plausible while the source/family is wrong, missing route metadata can leave final text acceptable but diagnostics ambiguous, and emission repairs can make text acceptable while hiding sublayer cause.
- `tests/test_final_emission_boundary_no_semantic_repair.py` protects awkward-but-legal narration from semantic rewriting. That is a direct signal that legal phrasing differences should not be normalized away by broad repairs.
- `docs/scenario_spine_validation.md` treats `branch_divergence` as useful cross-branch signal, but branch divergence is not rerun drift. It compares intended branch outcomes from the same fixture, not repeated executions of one branch.
- `docs/cycles/cycle_u_sustained_session_validation_closure_2026-05-30.md` records that Cycle U stayed metrics-first and avoided exact prose validation. This keeps replay robust, but leaves Cycle S room to add report-only variance summaries.

## Drift Seam Map

| Seam | Current coverage | Files involved | Missing measurement | Lowest-risk implementation point | Tests that should protect behavior |
|---|---|---|---|---|---|
| Speaker drift | Protected replay bounds `speaker_change_count` / `speaker_missing_count`; direct speaker tests protect enforcement. | `tests/test_golden_replay.py`, `tests/helpers/golden_replay.py`, `game/interaction_context.py`, `game/speaker_contract_enforcement.py` | Rerun-to-rerun selected speaker sequence delta, target-source delta, repair-mode frequency. | Add report-only speaker sequence comparison to golden replay helper/artifact. Flag process-randomized `hash(...)` seed use separately before changing it. | `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, direct speaker contract tests if seed logic later changes. |
| Route drift | Protected replay bounds route changes and route availability; classifier maps route mismatch. | `game/api.py`, `game/interaction_context.py`, `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py` | Repeated-run route sequence edit/delta count and parse-path reason delta. | Add run-pair route sequence/frequency comparison over observed golden rows. | `tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability`, route/social contract tests. |
| Fallback escalation drift | Long-session summary counts fallback totals, windows, owners, streaks, behavior repairs, sanitizer fallback. | `tests/helpers/golden_replay.py`, `game/final_emission_gate.py`, `game/final_emission_replay_projection.py`, `game/runtime_lineage_telemetry.py` | Baseline-vs-rerun fallback family/owner/gate-path frequency delta for successful runs. | Extend existing fallback escalation summary with optional comparison function and markdown section. | `tests/test_golden_replay.py`, `tests/test_run_scenario_spine_validation.py`, `tests/test_runtime_lineage_telemetry.py` if present. |
| Continuity phrasing drift | Scenario-spine evaluator catches reset/referent/progression failures; interaction continuity validator counts violations/warnings. | `game/scenario_spine_eval.py`, `game/interaction_continuity.py`, `tests/helpers/golden_replay.py`, `docs/scenario_spine_validation.md` | Legal phrasing drift such as narrator bridge vs direct dialogue, warning-code frequency, and late-window continuity-shape changes across reruns. | Report continuity reason-code/warning-code frequencies and text hashes per turn; do not compare full prose. | `tests/test_scenario_spine_eval.py`, `tests/test_interaction_continuity_validation.py`, `tests/test_golden_replay.py`. |
| Semantic delta frequency | Response-delta validator and FEM metadata exist; final-boundary tests keep semantic repair disabled. | `game/final_emission_validators.py`, `game/final_emission_repairs.py`, `game/final_emission_gate.py`, `tests/helpers/golden_replay.py` | Per-run counts of response-delta checked/failed/repaired/kind/echo-overlap; no aggregate or rerun trend. | Project existing `response_delta_*` FEM fields into golden observed rows and report-only aggregate. | `tests/test_final_emission_gate.py`, `tests/test_response_delta_requirement.py`, `tests/test_final_emission_boundary_no_semantic_repair.py`, `tests/test_golden_replay.py`. |

## Recommended Cycle S Implementation Blocks

### S1 - Golden Rerun Drift Scorecard

- Goal: Add a report-only comparator for two lists of golden observed turns: speaker sequence, route sequence, fallback family/owner frequency, final text hashes, scaffold predicate, and runtime-lineage frequency deltas.
- Files likely touched: `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py`.
- Tests likely added/updated: helper-level synthetic comparison test; no protected assertion loosening.
- Validation commands:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py -q`
  - `.\.venv\Scripts\python.exe -m pytest -m golden_replay -q`
- Parallelizable: Yes, if no one else edits long-session summary rendering.
- Risk: Low. Reporting-only.

### S2 - Long-Session Rerun Artifact Writer

- Goal: Add an opt-in local artifact path for successful replay diagnostics, such as `artifacts/golden_replay/rerun_drift_scorecard.json` / `.md`, without changing CI pass/fail.
- Files likely touched: `tests/conftest.py`, `tests/helpers/failure_dashboard_report.py`, `tests/helpers/golden_replay.py`, maybe `tests/README_TESTS.md`.
- Tests likely added/updated: controlled artifact writer test using synthetic rows.
- Validation commands:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py tests/test_golden_replay.py -q`
- Parallelizable: Partly. Can run beside S3/S4 if helper APIs are agreed first.
- Risk: Low-medium. Artifact plumbing can be noisy, but no gameplay behavior changes.

### S3 - Semantic Delta Frequency Projection

- Goal: Project existing response-delta FEM fields into golden observed rows and long-session summaries: checked, failed, repaired, kind detected, echo overlap band.
- Files likely touched: `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py`.
- Tests likely added/updated: synthetic observed-turn projection test and long-session summary renderer test.
- Validation commands:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py::test_long_session_replay_summary_renderer_surfaces_operator_metrics -q`
  - `.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py -q`
- Parallelizable: Yes with S4; coordinate with S1 if both edit summary dict shape.
- Risk: Low. Additive metadata/read-side only.

### S4 - Scenario-Spine Rerun Delta Advisory

- Goal: Add a small advisory comparator for two scenario-spine artifact directories from the same spine/branch, using existing `transcript.json`, `session_health_summary.json`, and `runtime_lineage_summary.json`.
- Files likely touched: new tool under `tools/` or helper in `tools/run_scenario_spine_validation.py`, plus `tests/test_run_scenario_spine_validation.py`, `docs/scenario_spine_validation.md`.
- Tests likely added/updated: fixture-directory comparator test with stubbed JSON; no live model/API.
- Validation commands:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_scenario_spine_validation.py tests/test_scenario_spine_eval.py -q`
- Parallelizable: Yes. Separate from golden replay if implemented as standalone advisory tool.
- Risk: Medium. Tool UX and artifact path handling need care; keep advisory.

### S5 - Deterministic Seed Seam Audit

- Goal: Add a narrow static/test audit for drift-prone process randomness in replay-sensitive fallback/speaker paths, starting with Python `hash(...)` in `game/speaker_contract_enforcement.py` narrator-neutral seed construction.
- Files likely touched: new or existing static audit test, possibly `tests/test_speaker_contract_enforcement.py` or a narrow `tests/test_runtime_drift_seed_audit.py`.
- Tests likely added/updated: static check first. Only replace runtime seed with stable hash in a later, separately reviewed block if the audit is accepted.
- Validation commands:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py tests/test_speaker_contract_enforcement.py -q`
- Parallelizable: Yes. Measurement/audit first.
- Risk: Low for audit-only; medium if it later changes runtime seed behavior.

### S6 - Protected Manifest Drift Policy Addendum

- Goal: Document Cycle S policy: rerun drift scorecards are advisory/report-only until repeated data justifies thresholds; protected assertions remain zero-violation.
- Files likely touched: `docs/testing/protected_replay_manifest.md`, maybe `docs/scenario_spine_validation.md`.
- Tests likely added/updated: None required; optionally docs-link smoke if repo has one.
- Validation commands:
  - `.\.venv\Scripts\python.exe -m pytest -m golden_replay -q`
- Parallelizable: Yes.
- Risk: Low. Documentation-only.

## Validation Commands

Targeted protected long-session replay:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability -q
```

Supporting long-session diagnostics:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability -q
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting -q
```

Protected replay validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py -q
```

Replay diagnostics / classifier slice:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py -q
```

Scenario-spine deterministic evaluator/runner tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py -q
```

Full relevant replay/drift subset:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_golden_replay.py tests/test_scenario_spine_contracts.py tests/test_scenario_spine_eval.py tests/test_scenario_spine_continuation_convergence.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py tests/test_transcript_runner_smoke.py -q
```

CI protected replay gate:

```bash
python -m pytest -m golden_replay -q
```

Local protected failure dashboard generation:

```powershell
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --write-failure-dashboard
```

Advisory scenario-spine artifact generation:

```powershell
.\.venv\Scripts\python.exe tools/run_scenario_spine_validation.py --list
.\.venv\Scripts\python.exe tools/run_scenario_spine_validation.py --branch branch_social_inquiry --smoke
.\.venv\Scripts\python.exe tools/run_scenario_spine_validation.py --branch branch_social_inquiry
.\.venv\Scripts\python.exe tools/run_scenario_spine_validation.py --all-branches
```

Separate synthetic N1 artifact generation:

```powershell
.\.venv\Scripts\python.exe tools/run_n1_scenario_spine_validation.py list
.\.venv\Scripts\python.exe tools/run_n1_scenario_spine_validation.py run --all
```

## Risks / Non-goals

- Do not broaden protected failure criteria from advisory frequency signals without repeated evidence and explicit review.
- Do not make exact prose identity a default replay gate.
- Do not use semantic comparison to rewrite acceptable prose; final-boundary tests intentionally protect awkward-but-legal output from semantic repair.
- Do not merge N1 synthetic tooling into golden replay or scenario-spine runtime validation.
- Do not update golden snapshots or scenario-spine fixtures just to reduce variance.
- Do not loosen existing protected assertions.
- Do not change live model route behavior or fallback selection behavior in the recon/measurement blocks.

## Completion Notes

Cycle S completed as advisory/reporting-first work:

- S1 added a report-only golden rerun comparator.
- S2 added opt-in golden rerun scorecard artifacts.
- S3 projected semantic delta frequency from existing response-delta/FEM metadata only.
- S4 added an advisory scenario-spine artifact-directory rerun comparator.
- S5 added a replay-sensitive seed audit and replaced the isolated narrator-neutral Python `hash(...)` seed with a stable fingerprint.
- S6 records the policy addendum in `docs/testing/protected_replay_manifest.md`: rerun scorecards remain advisory until repeated evidence, explicit review, and manifest updates justify hard thresholds.

## Files Inspected

- `.github/workflows/convergence-checks.yml`
- `audits/cycle_q_replay_cost_compression_recon_2026-05-29.md`
- `audits/replay_failure_corpus.md`
- `data/validation/scenario_spines/frontier_gate_long_session.json`
- `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md`
- `docs/n1_scenario_spine_validation.md`
- `docs/cycles/cycle_n_long_session_stability_closure_2026-05-27.md`
- `docs/cycles/cycle_u_sustained_session_validation_closure_2026-05-30.md`
- `docs/scenario_spine_validation.md`
- `docs/testing/protected_replay_manifest.md`
- `game/api.py`
- `game/diegetic_fallback_narration.py`
- `game/fallback_provenance_debug.py`
- `game/final_emission_gate.py`
- `game/final_emission_repairs.py`
- `game/final_emission_replay_projection.py`
- `game/final_emission_validators.py`
- `game/gm.py`
- `game/interaction_context.py`
- `game/interaction_continuity.py`
- `game/model_routing.py`
- `game/runtime_lineage_telemetry.py`
- `game/scenario_spine_eval.py`
- `game/speaker_contract_enforcement.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/transcript_runner.py`
- `tests/helpers/transcript_snapshots.py`
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tools/run_n1_scenario_spine_validation.py`
- `tools/run_scenario_spine_validation.py`
