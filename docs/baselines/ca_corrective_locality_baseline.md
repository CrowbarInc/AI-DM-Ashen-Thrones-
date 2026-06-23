# CA Corrective Change Locality Baseline

**Baseline version:** 1  
**Created:** 2026-06-22  
**Primary metric:** Files Touched Per Fix  
**Comparison ready:** yes

## Why this cohort was selected

This baseline freezes the first evidence-reviewed corrective-fix cohort produced by CA1–CA3. The repository needed a locality measurement grounded in genuine defect repairs rather than keyword-led `bug_fix` classification from BR.

Manual review of BR bug-fix candidates identified **10 genuine corrective fixes** between 2026-03-21 and 2026-05-20. That window is the earliest trustworthy sample large enough for an initial 8–12 commit baseline while remaining small enough to audit commit-by-commit.

## Cohort boundaries

| Boundary | Value |
|---|---|
| Start date | 2026-03-21 |
| End date | 2026-05-20 |
| Qualifying fixes | 10 |
| Exclusion controls | 1 (`EX-01`) |
| Source cohort | `docs/audits/CA_corrective_change_locality_cohort.csv` |
| Source measurement | `artifacts/ca3_corrective_locality_report.json` |

## Qualifying criteria

A commit enters the corrective cohort only when all of the following hold:

1. **Concrete defect response** — wrong, failing, missing, leaked, shortened, misrouted, or unsafe behavior is identified in subject/body, audit, or matching diff/test evidence.
2. **Repair action** — at least one production/runtime source file changes under `game/` or `static/`.
3. **Primary intent is corrective** — the repair is the dominant purpose; planned architecture, extraction, or feature work is excluded unless the defect boundary is separable and evidenced.
4. **Reviewable boundary** — the commit is not a merge and repair fanout can be attributed honestly.

Only **high** and **medium** confidence rows enter the primary cohort.

## Exclusion criteria

Commits are excluded when they fail any qualifying condition. The baseline retains one explicit exclusion control:

- **EX-01** (`2b293b2`) — snapshot/data-only change with no production source repair, regression lock, or replay evidence. It remains in the authority CSV to test that metric pipelines omit non-qualifying rows.

## Frozen baseline values

| Metric | Value |
|---|---:|
| Cohort size | 10 |
| Median files touched (raw) | 12.5 |
| Median files touched (effective) | 7.0 |
| Mean files touched | 87.7 |
| P75 files touched | 44.0 |
| P90 files touched | 248.2 |
| Maximum files touched | 538 |
| Median production files | 2.5 |
| Median test files | 2.0 |
| Generated-artifact median distortion | 44.0% |
| Fixes with generated pollution | 3 (30.0%) |
| Largest repair family | `opening_fallback` (60.0%) |

Machine-readable values live in `docs/baselines/ca_corrective_locality_baseline.json`.

## Known limitations

- **Small sample size (N=10)** — distribution tails are driven by a few polluted commits; medians are more stable than means.
- **Generated-artifact distortion** — three commits include accidentally tracked `codex_pytest_tmp*` trees. Raw Git fanout is preserved as the primary metric; effective totals subtract generated paths.
- **Repair-family concentration** — six of ten fixes concern opening/fallback behavior. The baseline describes observed fixes in this repository, not a balanced defect taxonomy.
- **No recurrence linkage** — same-area sequential repairs are family evidence only; recurrence keys are not joined to commits in this baseline.
- **Historical window only** — commits after 2026-05-20 are out of scope until a future cohort is reviewed and locked separately.
- **Authority not re-mined** — future comparisons should use the same CA1 cohort definition and CA2 path buckets; do not re-infer qualifying fixes from keywords alone.

## Future comparison guidance

When a new reviewed corrective cohort exists:

1. Run CA3 (or its successor) on the new cohort using the same qualifying definition.
2. Compare **median files touched per fix (raw and effective)**, **median production files**, and **median test files** against this baseline JSON.
3. Report sample size alongside every comparison; do not claim trend significance from small deltas.
4. Bump `baseline_version` only when intentionally replacing this historical lock — never silently mutate version 1 values.
