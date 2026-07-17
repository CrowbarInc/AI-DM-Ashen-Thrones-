# BS5 Projection Convergence Report

> Read-side attribution completeness before (BS1 baseline) vs after BS5 projection convergence.

## Summary

| Metric | Before (BS1) | After (BS5) | Delta |
|---|---:|---:|---:|
| Strict completeness | 0.0% | 0.0% | 0.0 |
| Resolved completeness | 5.36% | 85.71% | 80.35 |
| Strict complete records | 0/56 | 0/56 | +0 |
| Resolved complete records | 3/56 | 48/56 | +45 |

## Field-Level Improvements

| Field | Missing before | Missing after | Slots recovered |
|---|---:|---:|---:|
| `owner_bucket` | 44 | 0 | +44 |
| `source_family` | 8 | 0 | +8 |
| `repair_kind` | 45 | 0 | +45 |
| `recurrence_key` | 5 | 0 | +5 |
| `mutation_classification` | 16 | 8 | +8 |

## Path-Level Improvements (resolved complete)

| Replacement path | Before complete | After complete | Delta |
|---|---:|---:|---:|
| visibility replacement | 0 | 4 | +4 |
| first mention replacement | 0 | 4 | +4 |
| referential replacement | 0 | 4 | +4 |
| sealed replacement | 0 | 4 | +4 |
| response type replacement | 0 | 5 | +5 |
| sanitizer replacement | 0 | 9 | +9 |
| repair mutation | 0 | 7 | +7 |
| opening fallback | 3 | 6 | +3 |
| strict social replacement | 0 | 5 | +5 |
