# BRL2 — Bug-Fix Locality Regression Guard

Guard date: 2026-06-20

Scope: reporting and validation only. No runtime behavior, ownership, commit classification methodology, or hotspot calculation rule changes.

Implementation: `tests/helpers/bug_fix_locality_regression_guard.py`

Generator CLI: `tools/bug_fix_locality_regression_guard_report.py`

Related: `docs/audits/metrics/BRL1_bug_fix_locality_metric.md`, `tests/helpers/bug_fix_locality_metric.py`

Artifact: `artifacts/bug_fix_locality_regression_guard_report.md`

Validation:

```powershell
pytest tests/test_bug_fix_locality_metric.py tests/test_bug_fix_locality_regression_guard.py -q
python tools/bug_fix_locality_regression_guard_report.py
python tools/bug_fix_locality_regression_guard_report.py --strict-exit
```

---

## 1. Purpose

BRL2 prevents future repository changes from **silently degrading** bug-fix locality economics.

BRL1 established repeatable measurement, hotspot reporting, maintenance concentration, and trend support. BRL2 adds **guardrails** that fail fast when guarded metrics regress beyond recorded BRL1 baselines.

---

## 2. Guarded Metrics

| Metric | Guard rule | Source |
|---|---|---|
| **Bug-fix median files touched** | Must not exceed BRL1 baseline (9.0) | BRL1 `current.bug_fix.median_files_touched` |
| **Refactor median files touched** | Must not exceed BRL1 baseline (16.0) | BRL1 `current.refactor_architecture.median_files_touched` |
| **Bug-fix maintenance top-5 share** | Must not exceed baseline (3.98%) | BRL1 `hotspots.maintenance_concentration.bug_fix.top5_share_pct` |
| **Bug-fix maintenance top-file share** | Must not exceed baseline (1.02%) | BRL1 `hotspots.maintenance_concentration.bug_fix.top_file_share_pct` |
| **Bug-fix hotspot top-cluster share** | Must not exceed baseline (13.85%) | BRL1 `hotspots.hotspot_concentration.bug_fix.top_cluster_share_pct` |

All checks consume `build_bug_fix_locality_report()` from BRL1 — no parallel scoring logic.

---

## 3. Acceptable Movement

### Allowed without baseline update

- Bug-fix median **decreasing** (more local corrective commits)
- Maintenance/hotspot concentration **decreasing** (less churn concentrated in top paths)
- Refactor median stable during periods without new refactor cohort commits
- Metrics unchanged when classification CSV is unchanged

### Requires baseline update (same PR)

- Intentional BRL1 baseline refresh after documented corpus expansion
- Deliberate threshold relaxation with economics rationale (avoid using this to hide regressions)

### Regression (guard fails)

- Bug-fix median **increases** above 9.0
- Refactor median **increases** above 16.0
- Maintenance top-5 or top-file share **increases** above recorded baselines
- Hotspot top-cluster share **increases** above 13.85%

Higher concentration share means **worse** economics (more maintenance focused on fewer paths).

---

## 4. Regression Definitions

| Signal | Definition |
|---|---|
| **Bug-fix locality regression** | `bug_fix_median_files_touched > BRL2_GUARD_THRESHOLDS.bug_fix_median_files_touched_max` |
| **Refactor locality regression** | `refactor_median_files_touched > BRL2_GUARD_THRESHOLDS.refactor_median_files_touched_max` |
| **Maintenance concentration regression** | Top-5 or top-file share exceeds recorded baseline ceiling |
| **Hotspot concentration regression** | Top bug-fix production cluster share exceeds recorded baseline ceiling |

Use `assert_locality_metrics_not_regressed()` in tests/CI or `--strict-exit` on the CLI tool.

---

## 5. Maintenance Expectations

### When to regenerate

1. After updating `docs/reports/BR_commit_classification.csv`
2. After regenerating `artifacts/bug_fix_locality_report.md`
3. Before locality-focused cycle closeout

### When to update frozen thresholds

Update `BRL2_RECORDED_BASELINE` and `BRL2_GUARD_THRESHOLDS` only when:

- BRL1 baselines are intentionally refreshed and documented
- New classification history legitimately shifts medians/concentration with audit trail

Do **not** raise ceilings to absorb accidental regressions.

### Periodic workflow

```powershell
python tools/bug_fix_locality_report.py
python tools/bug_fix_locality_regression_guard_report.py --strict-exit
pytest tests/test_bug_fix_locality_metric.py tests/test_bug_fix_locality_regression_guard.py -q
```

---

## 6. Future Maintainer Guidance

### When bug-fix locality worsens

1. Regenerate BRL1 and BRL2 artifacts to confirm the median increase is real.
2. Inspect newly classified `bug_fix` commits in `BR_commit_classification.csv` — look for broad recovery commits or test-tree contamination (`codex_pytest_tmp*`).
3. Compare production-file medians in BRL1 (CSV columns) when raw file counts spike.
4. Revert or decompose broad corrective commits; do not raise the guard ceiling without documented baseline refresh.

### When refactor locality worsens

1. Confirm new commits were classified as `refactor_architecture` rather than misfiling bug-fix work.
2. Review largest refactor commits in `docs/reports/BR_bug_fix_locality_measurement.md` outlier tables.
3. Refactor median increases may be acceptable during planned architecture cycles — document separately, but BRL2 still flags them for visibility.

### When hotspot concentration worsens

1. Check BRL1 hotspot section for the dominant cluster/path.
2. Determine whether repeated touches reflect true defect frontier vs missing ownership consolidation.
3. If concentration rises because fixes repeatedly hit the same module without boundary extraction, treat as economics debt — plan ownership or gate work.
4. Update baseline only after intentional hotspot redistribution with documented rationale.

### Guard helper reference

| Function | Role |
|---|---|
| `evaluate_bug_fix_locality_guard()` | Bug-fix median ceiling check |
| `evaluate_refactor_locality_guard()` | Refactor median ceiling check |
| `evaluate_maintenance_concentration_guard()` | Maintenance share ceiling checks |
| `evaluate_hotspot_concentration_guard()` | Hotspot cluster share ceiling check |
| `evaluate_locality_regression_guard()` | Full evaluation payload |
| `assert_locality_metrics_not_regressed()` | Raises on required failures |

---

## 7. Success Criteria

- Locality regressions are detectable in tests and artifacts
- Future economics degradation is visible via pass/fail guard report
- No runtime behavior changes
- No ownership changes
