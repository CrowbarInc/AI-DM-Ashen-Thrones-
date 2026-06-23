# CA4 Corrective Locality Baseline Lock Report

> CA4 frozen historical baseline for future corrective-fix cohort comparison.

## Lock status

- **Validation status:** PASS
- **Baseline version:** 1
- **Created date:** 2026-06-22
- **Comparison ready:** True
- **Primary metric:** files_touched_per_fix

## Frozen baseline values

- **Cohort size:** 10
- **Median files touched (raw):** 12.5
- **Median files touched (effective):** 7.0
- **Mean files touched:** 87.7
- **P75 files touched:** 44.0
- **P90 files touched:** 248.2
- **Max files touched:** 538
- **Median production files:** 2.5
- **Median test files:** 2.0
- **Generated-artifact median distortion:** 44.0%
- **Polluted fixes:** 3 (30.0%)
- **Largest repair family:** opening_fallback (concentration ratio 0.6)

## Validation results

- PASS: baseline schema valid
- PASS: required metrics present
- PASS: values match CA3 report artifact
- PASS: values reproducible from CA1 cohort authority
- PASS: on-disk baseline matches CA4 frozen record

## Future comparison guidance

1. Build a new reviewed corrective cohort with the same CA1 qualifying definition.
2. Run CA3 measurement on the new cohort without changing metric definitions.
3. Compare raw and effective median files touched, median production files, and median test files against this baseline.
4. Record cohort date range; this baseline covers 2026-03-21 through 2026-05-20.
5. Bump `baseline_version` only when intentionally superseding this lock.
