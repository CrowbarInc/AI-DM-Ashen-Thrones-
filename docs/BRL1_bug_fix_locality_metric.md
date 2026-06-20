# BRL1 — Bug-Fix Locality Repository Metric

Metric date: 2026-06-20

Scope: reporting and measurement only. No runtime behavior, ownership, replacement, or attribution changes.

Implementation: `tests/helpers/bug_fix_locality_metric.py`

Generator CLI: `tools/bug_fix_locality_report.py`

Classification source: `docs/reports/BR_commit_classification.csv`

Discovery reference: `docs/reports/BR_bug_fix_locality_measurement.md`

Artifact: `artifacts/bug_fix_locality_report.md`

Validation:

```powershell
pytest tests/test_bug_fix_locality_metric.py -q
python tools/bug_fix_locality_report.py
```

---

## 1. Metric Purpose

BRL1 converts the point-in-time BR bug-fix locality discovery into a **repeatable repository metric** so locality economics can be tracked over time.

The metric answers:

- How many files do corrective (`bug_fix`) commits typically touch?
- How does that compare to refactor, governance, and feature cohorts?
- Which paths and directory clusters absorb the most maintenance churn?
- Is maintenance becoming more or less concentrated over time?

Primary operational headline: **bug-fix median files touched**.

Secondary comparison headlines: refactor median, governance median, and feature median.

---

## 2. Denominator Definitions

### Unit of analysis

One **classified commit** from `BR_commit_classification.csv`.

Merge commits and commits without a defensible primary intent are classified as `mixed_or_unclear` and excluded from cohort medians.

### Files touched (primary locality denominator)

Per commit, `files_touched_count` is the count of changed paths from Git's `diff-tree --name-only` inventory. Renames count as changed paths. Line churn is not used.

### Path buckets (supporting denominators)

Path bucketing follows the BR discovery methodology:

| Bucket | Rule |
|---|---|
| `production` | Runtime code, static UI, runtime data — paths not classified as test or docs/tooling |
| `test` | `tests/`, `test_*`, `*_test.py`, pytest cache/coverage paths, tracked `codex_pytest_tmp*` |
| `docs_tooling` | `docs/`, `audits/`, `tools/`, `.github/`, `artifacts/`, Markdown/text artifacts, root build/test config |

The CSV stores all three bucket counts per commit. BRL1 headline medians use **total files touched** unless noted otherwise.

### Cohort denominators

| Cohort | CSV category | Used for |
|---|---|---|
| Bug-fix locality | `bug_fix` | Corrective commit fan-out |
| Refactor locality | `refactor_architecture` | Planned architecture/program fan-out |
| Governance locality | `governance_observability` | Audit/telemetry/instrumentation fan-out |
| Feature locality | `feature_work` | New capability fan-out |

Do **not** pool bug-fix commits with refactor or governance cohorts when interpreting corrective locality.

---

## 3. Classification Methodology

Classification is **frozen in the CSV** using the BR discovery precedence:

1. Merge or explicit mixed intent → `mixed_or_unclear`
2. Governance/observability signals → `governance_observability`
3. Architecture/refactor signals → `refactor_architecture`
4. Path-only docs/tests → `docs_only` / `test_only`
5. Explicit corrective signals (fix, repair, recover, restore, preserve, guard, prevent, stabilize) → `bug_fix`
6. Feature/behavioral-contract signals → `feature_work`
7. Otherwise → `mixed_or_unclear`

Each row preserves `notes` for audit. BRL1 does not reclassify commits at report time; it consumes the CSV as the source of truth.

To extend the metric after new history accumulates, append rows to the CSV using the same methodology, then regenerate the artifact.

---

## 4. Report Metrics

### Bug-fix and refactor locality

For each cohort, the report publishes:

- Median files touched
- P75 files touched
- P90 files touched
- Max files touched

### Governance and feature locality

Median files touched (with baseline / current / delta trend columns).

### Repository economics summary

| Score | Formula | Interpretation |
|---|---|---|
| Bug-fix locality score | `100 / max(median_files, 1)` | Higher = more local (fewer files) |
| Refactor locality score | same | Separate cohort; not comparable to bug-fix targets |
| Maintenance concentration | Top-5 file touch share within cohort | Higher = maintenance concentrated in fewer paths |

Hotspot section (git-backed):

- Most frequently touched files (all classified cohorts)
- Most common bug-fix production directory clusters
- Most common refactor production directory clusters

---

## 5. Trend Support

Each headline metric table includes:

| Column | Source |
|---|---|
| **Baseline** | Frozen `BRL1_BASELINE_LOCALITY` snapshot from BR discovery through `3f5ee0c` |
| **Current** | Live computation from the classification CSV |
| **Delta** | `current − baseline` |

When the CSV is unchanged, current equals baseline and deltas are zero. After new commits are classified and appended, current moves while baseline remains fixed until a maintainer intentionally rebaselines.

---

## 6. Interpretation Guidance

### Bug-fix median files touched

The BR discovery baseline is **9 files** (11 commits) with **5 production files** median. This replaces the prior pooled ~17.5-file figure that mixed corrective work with architecture cycles.

Large raw file counts in the bug-fix cohort may reflect tracked test artifacts (`codex_pytest_tmp*`). Use production-file medians from the CSV when evaluating product footprint; use total files touched when evaluating repository churn cost.

### Refactor and governance medians

Higher refactor/governance medians are **expected** — they measure planned program work, not defect response locality. Never use refactor median as the bug-fix target.

### Locality score

The score is a convenience index for trend dashboards. A rising bug-fix locality score means corrective commits touch fewer files on median — desirable for maintenance economics.

### Maintenance concentration

High top-5 share in bug-fix cohorts signals that fixes repeatedly touch the same paths — useful for ownership review and hotspot remediation, not automatically bad if those paths are true defect frontiers.

### P75 / P90 / max

Tail metrics expose outlier commits (large test-tree commits, broad recovery work). Review max commits in the BR discovery tables before treating tail movement as systemic regression.

---

## 7. Maintenance Expectations

### When to regenerate

1. After appending newly classified commits to `BR_commit_classification.csv`
2. Before locality-focused cycle closeout reports
3. When comparing BR/BRL cycle movement

### When to update the frozen baseline

Update `BRL1_BASELINE_LOCALITY` only when intentionally rebasing the repository metric snapshot (for example after a major history rewrite or a deliberate baseline refresh). Do not rebaseline to hide locality regressions.

### Acceptable movement

- Bug-fix median stable or decreasing after locality-focused remediation
- Refactor/governance median increasing during planned architecture cycles (document separately)
- Concentration shifting toward known ownership boundaries after gate extraction work

### Regression signals

- Bug-fix median increasing without documented increase in corrective scope
- Bug-fix P90 rising while median stays flat (outlier contamination returning)
- Maintenance concentration increasing without corresponding ownership consolidation

---

## 8. Success Criteria

- Bug-fix locality is a repeatable repository metric
- Future cycles can measure locality movement via baseline / current / delta columns
- No runtime behavior changes
