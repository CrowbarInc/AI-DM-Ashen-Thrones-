# CV Corrective Locality Confirmation Discovery

## Scope / Commit Range

Range examined: `19167c1..8aefe23`, immediately after CQ completion.

CQ completion commit:

- `19167c1` - 2026-06-28 - `CQ: Foundation Completion Assessment`

Post-CQ commits available in the current branch:

- `bf97ba8` - 2026-06-28 - `CR: Protected Replay Recurrence Separation`
- `1225af0` - 2026-06-28 - `CS: Compact Golden Drift Harness`
- `845e6db` - 2026-06-28 - `CT: Runtime Fallback Incidence Baseline`
- `8aefe23` - 2026-06-29 - `CU: Semantic Mutation Write-Site Attribution`

Only four post-CQ commits exist in the current history. This is smaller than the requested 5-10 commit sample, so the conclusion is evidence-limited.

## Method

Evidence gathered from:

- `git log --oneline --decorate --date=short --pretty=format:"%h %ad %s" -n 120`
- `git show --name-status --stat --summary --date=short --pretty=fuller <commit>`
- Targeted reads/searches of committed discovery, audit, and closeout files for recurrence, drift, fallback, projection, and validation claims.

Classification rules:

- `production`: runtime files under `game/`.
- `test`: files under `tests/`, including helpers and test-owned contracts.
- `governance`: audit, maintenance, testing, convergence, discovery, and closeout documentation used as governance/evidence.
- `fixture/golden`: generated or committed replay/report artifacts under `artifacts/golden_replay/`.
- `tooling/config`: CLI/report/migration scripts under `tools/` or config/workflow files.
- `documentation`: general documentation not clearly acting as governance evidence.
- `unknown`: none in this sample.

Locality class:

- Local: 1-3 files.
- Moderate: 4-7 files.
- Diffuse: 8+ files or crossing multiple unrelated owner surfaces.

## Selected Corrective Sample

### `bf97ba8` - CR: Protected Replay Recurrence Separation

- Date: 2026-06-28
- Likely corrective intent: separate protected replay recurrence health from session and synthetic/test artifact diagnostic recurrence.
- Qualifies as corrective because committed discovery identified contamination risk in recurrence vocabulary and shared diagnostic lanes; closeout records explicit separation of protected, session diagnostic, synthetic/test artifact, and compatibility recurrence surfaces.
- Tied to recurrence/replay/audit: yes. Directly modifies recurrence event logs, recurrence histories, recurrence writers, dashboard helpers, migration tooling, and governance audits.

### `1225af0` - CS: Compact Golden Drift Harness

- Date: 2026-06-28
- Likely corrective intent: add a compact golden drift harness and committed compact trend artifacts to measure route, speaker, source, fallback, mutation, and hash drift over the compact protected replay set.
- Qualifies as corrective-adjacent because it establishes a narrower drift evidence path after CQ and updates protected replay manifest/convergence governance. It is more evidence/harness corrective than runtime corrective.
- Tied to recurrence/replay/audit: yes for replay drift. No direct recurrence count changes observed.

### `845e6db` - CT: Runtime Fallback Incidence Baseline

- Date: 2026-06-28
- Likely corrective intent: improve fallback incidence baseline and projection fidelity evidence, including an upstream-fast projection owner-bucket correction in `game/final_emission_replay_projection.py`.
- Qualifies as corrective because `CT_projection_fidelity_audit.md` names a CT6 root cause: upstream-fast fallback was already classified but lost its retry owner bucket in `_fem_preserved_fallback_owner_bucket`; the commit changes the production projector and report/test evidence.
- Tied to recurrence/replay/audit: yes for fallback incidence and projection fidelity; report artifacts were refreshed.

### `8aefe23` - CU: Semantic Mutation Write-Site Attribution

- Date: 2026-06-29
- Likely corrective intent: replace projection-inferred semantic mutation ownership with passive write-site attribution and reconciliation evidence.
- Qualifies as corrective-adjacent because it addresses attribution gaps that can cause mislocalized semantic mutation, fallback, sanitizer, policy, and projection evidence. It is broad instrumentation/governance work rather than a small regression patch.
- Tied to recurrence/replay/audit: yes for semantic mutation projection/classifier recurrence risk; no direct recurrence-count artifact was updated.

## Per-Commit Touched-File Analysis

### `bf97ba8` Touched Files

Total files: 32

Production/runtime files: 0

Tests: 11

- `tests/helpers/failure_dashboard_drift.py` - test
- `tests/helpers/failure_dashboard_paths.py` - test
- `tests/helpers/failure_dashboard_recurrence.py` - test
- `tests/helpers/failure_dashboard_report.py` - test
- `tests/helpers/replay_bug_recurrence_events.py` - test
- `tests/helpers/replay_bug_recurrence_statistics.py` - test
- `tests/test_failure_dashboard_paths.py` - test
- `tests/test_failure_dashboard_recurrence.py` - test
- `tests/test_failure_dashboard_report.py` - test
- `tests/test_migrate_bug_recurrence_event_log.py` - test
- `tests/test_replay_bug_class_recurrence.py` - test

Governance/audit/docs: 7

- `docs/audits/BQ16_recurrence_graduation_audit.md` - governance
- `docs/audits/BQ37_recurrence_history_migration.md` - governance
- `docs/audits/BQC3_confidence_calibration_audit.md` - governance
- `docs/audits/BQC4_final_graduation_decision.md` - governance
- `docs/audits/BQC5_effectiveness_validation.md` - governance
- `docs/audits/CR_protected_replay_recurrence_separation_closeout.md` - governance
- `docs/maintenance/CR_protected_replay_recurrence_separation_discovery.md` - governance

Fixtures/goldens/replay artifacts: 12

- `artifacts/golden_replay/bug_recurrence_event_log.json` - fixture/golden
- `artifacts/golden_replay/bug_recurrence_history.json` - fixture/golden
- `artifacts/golden_replay/bug_recurrence_history.md` - fixture/golden
- `artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json` - fixture/golden
- `artifacts/golden_replay/bug_recurrence_session_event_log.json` - fixture/golden
- `artifacts/golden_replay/bug_recurrence_synthetic_test_artifact_event_log.json` - fixture/golden
- `artifacts/golden_replay/owner_drift_hotspots.json` - fixture/golden
- `artifacts/golden_replay/owner_drift_hotspots.md` - fixture/golden
- `artifacts/golden_replay/owner_drift_risk.json` - fixture/golden
- `artifacts/golden_replay/owner_drift_risk.md` - fixture/golden
- `artifacts/golden_replay/owner_drift_trends.md` - fixture/golden
- `artifacts/golden_replay/recurrence_trajectory_history.json` - fixture/golden

Tooling/config: 2

- `tools/migrate_bug_recurrence_event_log.py` - tooling/config
- `tools/regenerate_bug_recurrence_history.py` - tooling/config

Owner/surface spread:

- Primary surface: protected replay recurrence reporting and recurrence artifact writers.
- Secondary surfaces: failure dashboard drift/risk outputs, migration tooling, historical audit documents.
- Cross-surface: yes, but centered on recurrence and dashboard/governance surfaces.
- Required changes outside expected owner surface: yes. Golden artifacts and historical governance docs changed alongside test helpers and migration tools.

Locality:

- Production/non-production ratio: `0:32`.
- Test/governance/fixture files: 30.
- Locality class: diffuse.

Recurrence impact:

- Impact: strong.
- Evidence: new explicit session and synthetic/test artifact logs, protected-only recurrence history, writer mode tests, migration/regeneration tooling, and closeout claims that protected recurrence outputs remain byte-identical across supported emission modes.

### `1225af0` Touched Files

Total files: 16

Production/runtime files: 0

Tests: 3

- `tests/helpers/golden_replay_trend.py` - test
- `tests/helpers/protected_replay_registry.py` - test
- `tests/test_golden_replay_trend.py` - test

Governance/audit/docs: 2

- `docs/convergence_ci_inventory.md` - governance
- `docs/testing/protected_replay_manifest.md` - governance

Fixtures/goldens/replay artifacts: 10

- `artifacts/golden_replay/trend_window/_storage/run-000/data/combat.json` - fixture/golden
- `artifacts/golden_replay/trend_window/_storage/run-000/data/session.json` - fixture/golden
- `artifacts/golden_replay/trend_window/_storage/run-000/data/session_log.jsonl` - fixture/golden
- `artifacts/golden_replay/trend_window/_storage/run-001/data/combat.json` - fixture/golden
- `artifacts/golden_replay/trend_window/_storage/run-001/data/session.json` - fixture/golden
- `artifacts/golden_replay/trend_window/_storage/run-001/data/session_log.jsonl` - fixture/golden
- `artifacts/golden_replay/trend_window/compact_golden_drift_summary.json` - fixture/golden
- `artifacts/golden_replay/trend_window/golden_transcript_drift.json` - fixture/golden
- `artifacts/golden_replay/trend_window/runs/run-000.json` - fixture/golden
- `artifacts/golden_replay/trend_window/runs/run-001.json` - fixture/golden

Tooling/config: 1

- `tools/run_protected_replay_trend.py` - tooling/config

Owner/surface spread:

- Primary surface: compact protected replay drift harness.
- Secondary surfaces: protected replay manifest and convergence inventory governance.
- Cross-surface: yes, between test helper, trend tool, committed artifacts, and governance.
- Required changes outside expected owner surface: yes, because artifact and governance updates were part of making the harness evidence-bearing.

Locality:

- Production/non-production ratio: `0:16`.
- Test/governance/fixture files: 15.
- Locality class: diffuse.

Recurrence impact:

- Impact: moderate.
- Evidence: compact drift summary records `route_drift_count`, `speaker_drift_count`, `source_drift_count`, `fallback_drift_count`, and `mutation_drift_count`; governance says all should be `0` for the compact manual signal. This affects replay drift detection, not recurrence counts.

### `845e6db` Touched Files

Total files: 9

Production/runtime files: 1

- `game/final_emission_replay_projection.py` - production

Tests: 2

- `tests/test_fallback_incidence_report.py` - test
- `tests/test_runtime_lineage_telemetry.py` - test

Governance/audit/docs: 2

- `CT_projection_fidelity_audit.md` - governance
- `CT_runtime_fallback_incidence_baseline_discovery.md` - governance

Fixtures/goldens/replay artifacts: 2

- `artifacts/golden_replay/bv1b_fallback_incidence_report.json` - fixture/golden
- `artifacts/golden_replay/bv1b_fallback_incidence_report.md` - fixture/golden

Tooling/config: 2

- `tools/bv1b_fallback_incidence_validation.py` - tooling/config
- `tools/fallback_incidence_report.py` - tooling/config

Owner/surface spread:

- Primary surface: fallback incidence reporting and FEM runtime lineage projection.
- Secondary surfaces: fallback incidence validation artifact, runtime lineage telemetry tests, projection fidelity audit.
- Cross-surface: yes, but all surfaces are tied to fallback incidence/projection evidence.
- Required changes outside expected owner surface: yes. Production projector change required report tooling, artifact refresh, tests, and audit docs.

Locality:

- Production/non-production ratio: `1:8`.
- Test/governance/fixture files: 6.
- Locality class: diffuse by count, though conceptually centered on one projection/reporting surface.

Recurrence impact:

- Impact: moderate.
- Evidence: audit records high projection fidelity and a CT6 root-cause correction preserving `fallback_owner_bucket="retry"` for upstream-fast fallback projection. Report artifacts were refreshed, and tests cover incidence/report and runtime lineage behavior.

### `8aefe23` Touched Files

Total files: 36

Production/runtime files: 15

- `game/fallback_provenance_debug.py` - production
- `game/final_emission_acceptance_quality.py` - production
- `game/final_emission_finalize.py` - production
- `game/final_emission_gate_preflight_defaults.py` - production
- `game/final_emission_meta.py` - production
- `game/final_emission_opening_fallback.py` - production
- `game/final_emission_response_type.py` - production
- `game/final_emission_sealed_fallback.py` - production
- `game/final_emission_terminal_pipeline.py` - production
- `game/final_emission_visibility_fallback.py` - production
- `game/output_sanitizer.py` - production
- `game/response_policy_enforcement.py` - production
- `game/runtime_lineage_telemetry.py` - production
- `game/semantic_mutation_attribution.py` - production
- `game/upstream_response_repairs.py` - production

Tests: 14

- `tests/failure_classification_contract.py` - test
- `tests/helpers/failure_classification_alignment.py` - test
- `tests/helpers/failure_classifier.py` - test
- `tests/helpers/golden_replay_projection.py` - test
- `tests/helpers/runtime_lineage_reporting.py` - test
- `tests/test_failure_classifier.py` - test
- `tests/test_final_emission_boundary_no_semantic_repair.py` - test
- `tests/test_final_emission_meta.py` - test
- `tests/test_golden_replay_projection_semantic.py` - test
- `tests/test_output_sanitizer.py` - test
- `tests/test_runtime_lineage_telemetry.py` - test
- `tests/test_semantic_mutation_attribution_cu4.py` - test
- `tests/test_semantic_mutation_attribution_governance.py` - test
- `tests/test_semantic_mutation_contract_adoption.py` - test

Governance/audit/docs: 7

- `docs/audits/CU2_passive_semantic_mutation_write_site_envelope.md` - governance
- `docs/audits/CU3_semantic_mutation_evidence_reconciliation.md` - governance
- `docs/audits/CU4_prompt_policy_semantic_write_site_attribution.md` - governance
- `docs/audits/CU5_semantic_mutation_attribution_governance.md` - governance
- `docs/audits/CU6_semantic_mutation_contract_adoption.md` - governance
- `docs/audits/CU7_semantic_mutation_acceptance_audit.md` - governance
- `docs/audits/CU_semantic_mutation_write_site_attribution_discovery.md` - governance

Fixtures/goldens/replay artifacts: 0

Tooling/config: 0

Owner/surface spread:

- Primary surface: semantic mutation write-site attribution across final emission, sanitizer, fallback, policy/prompt, and runtime lineage.
- Secondary surfaces: golden replay projection, failure classifier, runtime lineage reporting, governance contracts.
- Cross-surface: yes, across many production owners and multiple test/governance owners.
- Required changes outside expected owner surface: yes. The commit deliberately creates a cross-cutting attribution envelope and wires many writers/consumers.

Locality:

- Production/non-production ratio: `15:21`.
- Test/governance/fixture files: 21.
- Locality class: diffuse.

Recurrence impact:

- Impact: moderate.
- Evidence: CU docs state that explicit write-site evidence is preferred over projection-derived inference, classifier rows gain authoritative mutation evidence, and governance tests enforce adoption. This should reduce semantic attribution recurrence risk, but no direct recurrence count or replay artifact update was committed.

## Locality Summary Table

| Commit | Corrective Reason | Total Files | Prod Files | Test/Gov/Fixture Files | Primary Surface | Cross-Surface? | Locality Class | Recurrence Impact | Notes |
|---|---:|---:|---:|---:|---|---|---|---|---|
| `bf97ba8` | Separate protected replay recurrence health from diagnostic/session/synthetic recurrence lanes | 32 | 0 | 30 | Protected replay recurrence reporting | Yes | Diffuse | Strong | No runtime files, but broad artifact/test/governance/tool churn |
| `1225af0` | Add compact replay drift harness and committed compact drift evidence | 16 | 0 | 15 | Compact golden drift harness | Yes | Diffuse | Moderate | Evidence/harness corrective, not runtime corrective |
| `845e6db` | Correct fallback incidence/projection baseline, including upstream-fast owner-bucket projection evidence | 9 | 1 | 6 | FEM fallback incidence projection/reporting | Yes | Diffuse | Moderate | Conceptually focused but above diffuse file-count threshold |
| `8aefe23` | Add semantic mutation write-site attribution to replace projection-only ownership inference | 36 | 15 | 21 | Semantic mutation attribution across final emission/policy/fallback/sanitizer | Yes | Diffuse | Moderate | Broad cross-cutting instrumentation and governance |

## Aggregate Metrics

- Sample size: 4 commits.
- Average files touched per fix: 23.25.
- Median files touched per fix: 24.
- Average production files touched per fix: 4.0.
- Average test/governance/fixture files touched per fix: 18.0.
- Percentage local: 0%.
- Percentage moderate: 0%.
- Percentage diffuse: 100%.
- Percentage with moderate/strong recurrence impact: 100%.

Most commonly touched production surfaces:

- Final emission and fallback projection/metadata surfaces under `game/final_emission_*`.
- Runtime lineage and replay projection production support.
- Sanitizer, response policy, upstream repair, and fallback provenance surfaces.

Most commonly touched test/governance surfaces:

- `tests/helpers/*` replay, dashboard, projection, classifier, and lineage helpers.
- `tests/test_*` focused regression and governance tests.
- `docs/audits/*` discovery/closeout/evidence reports.
- `artifacts/golden_replay/*` committed replay, drift, recurrence, and fallback-incidence artifacts.

## Recurrence Impact Findings

The available post-CQ sample does not confirm small local corrective fixes. It shows that recurrence/replay/fallback/projection corrections continue to carry substantial evidence churn:

- CR is the strongest recurrence-impact commit. It changes recurrence lane semantics and regenerated recurrence/dashboards artifacts, with test and governance updates.
- CS improves drift detection and compact replay evidence rather than recurrence counts. It is still broad because the harness is evidence-bearing and commits trend artifacts.
- CT is the closest to a focused runtime correction, but the single production projection change still required tests, tooling, artifacts, and audit docs.
- CU reduces semantic mutation attribution recurrence risk by adding first-writer evidence and governance adoption tests, but it is intentionally cross-cutting and broad.

The main driver of broadness is not production edit size alone. It is the project practice of pairing corrective changes with committed golden/replay artifacts, governance/audit evidence, and multiple diagnostic consumers.

## Files / Artifacts To Pass Back If More Evidence Is Needed

Evidence is incomplete because only four post-CQ commits exist. To expand beyond this report, pass:

- `git log --oneline --decorate --date=short --pretty=format:"%h %ad %s" -n 120`
- `git show --name-status --stat --summary --date=short --pretty=fuller bf97ba8`
- `git show --name-status --stat --summary --date=short --pretty=fuller 1225af0`
- `git show --name-status --stat --summary --date=short --pretty=fuller 845e6db`
- `git show --name-status --stat --summary --date=short --pretty=fuller 8aefe23`
- `docs/audits/CR_protected_replay_recurrence_separation_closeout.md`
- `docs/maintenance/CR_protected_replay_recurrence_separation_discovery.md`
- `docs/convergence_ci_inventory.md`
- `docs/testing/protected_replay_manifest.md`
- `CT_runtime_fallback_incidence_baseline_discovery.md`
- `CT_projection_fidelity_audit.md`
- `docs/audits/CU_semantic_mutation_write_site_attribution_discovery.md`
- `docs/audits/CU2_passive_semantic_mutation_write_site_envelope.md`
- `docs/audits/CU3_semantic_mutation_evidence_reconciliation.md`
- `docs/audits/CU4_prompt_policy_semantic_write_site_attribution.md`
- Relevant replay/audit outputs before and after the selected commits, if available outside git history.
- Any uncommitted or external cycle completion notes from CQ onward.

## Preliminary Conclusion

Locality baseline appears disproven for the available post-CQ sample by the requested file-count rule.

The conclusion should be treated as provisional because the sample has only four commits and two are more evidence/harness/instrumentation corrective than narrow defect patches. Still, all available post-CQ corrective or corrective-adjacent commits are diffuse by touched-file count, and the average files touched per fix is 23.25. The evidence suggests that real corrective work after CQ still causes broad test/governance/artifact churn, especially when recurrence, replay drift, fallback incidence, projection fidelity, or semantic attribution evidence must be updated alongside code.

## Recommended Next Block

Run a reconciliation block that separates two measures:

- Runtime locality: production files touched per corrective fix and owner/surface spread among runtime files.
- Evidence locality: total files touched after including tests, governance docs, tools, and committed replay/golden artifacts.

Then compare post-CQ commits against the earlier CP corrective-locality cohort. That will show whether runtime fixes are becoming local while evidence updates remain diffuse, or whether both runtime and evidence surfaces are still broadly coupled.
