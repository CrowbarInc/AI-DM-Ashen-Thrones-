# CI - Corrective Cohort Validation #2 Discovery

## Scope

Inspected the strict post-cohort range `5f0ad53..HEAD` on `feature/stabilized-foundation`, covering commits dated 2026-06-23 through 2026-06-26. The previous corrective cohort authority is `5f0ad53` / `CA: Corrective Change Locality Cohort`, with frozen baseline values:

- Effective median: 7 files touched
- Production median: 2.5 files touched
- Test median: 2 files touched

Selection rule used here: include only real corrective fixes that corrected actual failing behavior, regression, test failure, recurrence issue, classification issue, projection issue, ownership/governance enforcement issue, or runtime/contract mismatch. Excluded refactors, fixture-only updates, formatting-only changes, documentation-only changes, broad governance moves, and exploratory/audit commits.

Commands/evidence inspected:

- `git log --format="%H%x09%ad%x09%s" --date=short 5f0ad53..HEAD`
- `git show --stat --oneline 5f0ad53..HEAD`
- `git show --name-only --format="%H%n%s" 5f0ad53..HEAD`
- `git show --stat ba8b29af8aa38385dd8217a7d636748b63117680`
- `git show --name-only ba8b29af8aa38385dd8217a7d636748b63117680`
- Existing CA evidence: `docs/audits/CA_corrective_change_locality_cohort.csv`, `docs/audits/CA_post_baseline_exclusions.csv`, `artifacts/ca11_corrective_fix_watch_report.md`

Result: no strict post-CA commit qualified as a real corrective fix. The cohort cannot be extended yet without violating the exclusion rules.

Screened post-CA commits:

| Commit | Date | Subject | Files | Screening Outcome |
|---|---:|---|---:|---|
| `85855df` | 2026-06-26 | CH: Governance Hub Redistribution | 26 | Excluded: broad governance/test ownership redistribution; not a discrete failing-behavior fix. |
| `5ea6608` | 2026-06-25 | CG: Failure Classification Synchronization Audit | 43 | Excluded: audit/synchronization program with registries and helper restructuring; no separable corrective fix boundary. |
| `c98dfa6` | 2026-06-25 | CF: Replay Projection Responsibility Audit | 34 | Excluded: audit/projection responsibility decomposition; no standalone failing projection correction selected. |
| `66b8b32` | 2026-06-25 | CE: Golden Replay Concentration Audit | 77 | Excluded: broad golden replay concentration/audit decomposition with generated artifacts and helper splits. |
| `ba8b29a` | 2026-06-23 | Restore evaluator convergence closeout path contract | 1 | Excluded: documentation-only restoration (`docs/evaluator_convergence_closeout.md`). |
| `247e634` | 2026-06-23 | CC: Feature Readiness Closeout Discovery | 144 | Excluded: discovery/documentation reorganization and historical development artifacts; no corrective production fix. |
| `ce36d0c` | 2026-06-23 | CB: Feature Boundary Readiness Audit | 28 | Excluded: readiness audit/governance instrumentation; not a discrete real corrective fix. |

## Candidate Corrective Fixes

| Fix ID | Commit / Reference | Fix Summary | Problem Type | Recurrence Related? Yes/No | Total Files | Production Files | Test Files | Fixture/Golden Files | Docs/Tooling Files | Multi-Area? Yes/No | Notes |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| None | N/A | No qualifying strict post-CA corrective fixes found | N/A | No | 0 | 0 | 0 | 0 | 0 | No | All inspected commits were excluded by the target rules. |

## File-Touch Details

No selected fixes.

Excluded evidence highlights:

- `ba8b29a` touched only `docs/evaluator_convergence_closeout.md`; it is documentation-only.
- `ce36d0c`, `247e634`, `66b8b32`, `c98dfa6`, `5ea6608`, and `85855df` touched audit, helper, registry, artifact, and tooling/test ownership surfaces, but their commit scopes are audit/discovery/governance/decomposition programs rather than discrete corrective fixes.
- Existing CA11 watch evidence records zero new CA1-qualifying fixes outside the frozen cohort at the time of that report; this inspection extends that conclusion through `85855df` under the same strict corrective-fix definition.

## Recurrence Outcomes

No recurrence-related corrective fixes qualified in this strict post-CA range.

Relevant excluded recurrence/golden activity:

- `66b8b32` and `5ea6608` changed recurrence/golden replay artifacts, recurrence helpers, taxonomy/registry material, and classification synchronization surfaces.
- These were excluded because the commits are broad audit/synchronization/decomposition work, not isolated corrections of a proven recurrence failure.
- No selected fix added local recurrence protection.

## Locality Findings

Selected corrective fixes: 0.

Current cohort medians cannot be computed:

- Median total files touched: N/A
- Median production files touched: N/A
- Median test files touched: N/A

Baseline comparison:

- Effective median baseline: 7 files touched
- Production median baseline: 2.5 files touched
- Test median baseline: 2 files touched

Assessment: locality improvement is not measurable from this strict post-CA window because there are no qualifying real corrective fixes. The evidence does not show locality improved, worsened, or remained unchanged; it shows insufficient qualifying corrective-fix intake.

## Burden Patterns

Although no commits qualified for the cohort, the excluded range shows repeated burden patterns that would likely inflate files-touched if treated as corrective work:

- Shared helper coupling: CE/CF/CG/CH repeatedly split or rewired test helpers and ownership helpers.
- Attribution/contract synchronization: CG touched attribution read views, final emission metadata/schema/projection files, classification helpers, and contract tests.
- Dashboard or fixture coupling: CE and CG touched failure dashboard fixtures, recurrence dashboards, drift reports, and generated golden replay artifacts.
- Recurrence infrastructure touch-points: CE and CG modified recurrence history, recurrence event logs, taxonomy/audit material, and replay recurrence helper modules.
- Golden replay churn: CE had the largest excluded blast radius, including golden replay manifests, projection helpers, fallback projection tests, generated event logs, and `.bak` monolith snapshots.
- Ownership/governance registry involvement: CB and CH touched ownership registry tests, governance inventory, ownership guard helpers, and documentation governance surfaces.

These patterns support the existing CA conclusion that recent corrective pressure is mostly absorbed into planned governance, replay, and decomposition programs rather than appearing as standalone real corrective fixes.

## Files to Pass Back

The report is sufficient for the strict discovery conclusion. For review/audit of the exclusion boundary, pass back:

- `CI_corrective_cohort_validation_2_discovery.md`
- `docs/audits/CA_corrective_change_locality_cohort.csv`
- `docs/audits/CA_post_baseline_exclusions.csv`
- `artifacts/ca11_corrective_fix_watch_report.md`
- `docs/audits/CH_governance_hub_redistribution_discovery.md`
- `docs/audits/CG_failure_classification_synchronization_discovery.md`
- `docs/audits/CF_replay_projection_responsibility_discovery.md`
- `CE_golden_replay_concentration_audit_discovery.md`
